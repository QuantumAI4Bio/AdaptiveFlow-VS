import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from types import SimpleNamespace
from unittest.mock import Mock

import afvs_prepare_folders as folders
import afvs_prepare_workunits as workunits
import afvs_submit_jobs as submit
import pytest


@pytest.fixture
def workflow(tmp_path, monkeypatch, repo_root):
    """Materialize a two-collection local workflow with the real prepare CLI."""
    tools = tmp_path / "tools"
    templates = tools / "templates"
    templates.mkdir(parents=True)
    scenarios = tmp_path / "input-files" / "ds1"
    scenarios.mkdir(parents=True)
    (scenarios / "config.txt").write_text("receptor=receptor.pdbqt\n")
    library = tmp_path / "library"
    library.mkdir()
    settings = (repo_root / "tools/templates/all.ctrl").read_text()
    settings += (
        "\njob_name=ci-test\nbatchsystem=bash\njob_storage_mode=sharedfs\n"
        "data_storage_mode=sharedfs\ndata_collection_addressing_mode=metatranche\n"
        "docking_scenario_names=ds1\ndocking_scenario_methods=vina\n"
        "docking_scenario_replicas=2\ndocking_scenario_batchsizes=1\n"
        "collection_folder=../library\ndocking_scenario_basefolder=../input-files\n"
        "collection_list_type=standard\ncollection_list_file=templates/todo.all\n"
        "prescreen_mode=0\ndockings_per_subjob=4\nbash_array_job_size=2\n"
        f"tempdir_default={tmp_path}\n"
    )
    (templates / "all.ctrl").write_text(settings)
    (templates / "todo.all").write_text("AA_0000001 2\nBB_0000002 1\n")
    monkeypatch.chdir(tools)
    result = subprocess.run(
        [sys.executable, str(repo_root / "tools/afvs_prepare_folders.py")],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    config = json.loads((tmp_path / "workflow/config.json").read_text())
    return SimpleNamespace(root=tmp_path, tools=tools, config=config)


def test_parse_multiple_scenarios_and_defaults(tmp_path):
    path = tmp_path / "all.ctrl"
    path.write_text(
        "# ignored comment\ndocking_scenario_names=ds1:ds2\n"
        "docking_scenario_methods=vina:smina\ndocking_scenario_replicas=2:3\n"
        "docking_scenario_batchsizes=1:4\nsummary_formats=csv.gz,parquet\n"
        "print_smi_in_summary=1\ntempdir_default=/tmp\n"
    )
    config = folders.parse_config(path)
    assert config["docking_scenario_methods"] == ["vina", "smina"]
    assert config["docking_scenarios_internal"]["ds2"]["replicas"] == 3
    assert config["summary_formats"] == ["csv.gz", "parquet"]
    assert config["print_attrs_in_summary"] == ["smi"]
    assert config["collection_list_file"] == "templates/todo.all"
    assert config["tempdir_default"] == "/tmp/"


def test_prepare_collections_and_aliases(workflow):
    config = workflow.config
    assert config["job_letter"] == "ci-test"
    assert Path(config["sharedfs_collection_path"]) == workflow.root / "library"
    collections = json.loads((workflow.root / "workflow/collections.json").read_text())
    assert collections["AA_0000001"] == {"count": 2, "mode": "all"}
    assert collections["BB_0000002"] == {"count": 1, "mode": "all"}


def test_prepare_refuses_to_overwrite_existing_workflow(workflow, repo_root):
    marker = workflow.root / "workflow" / "keep-me"
    marker.write_text("existing results")
    result = subprocess.run(
        [sys.executable, str(repo_root / "tools/afvs_prepare_folders.py")],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert marker.read_text() == "existing results"


def test_workunit_generation_preserves_collections_and_replica_counts(workflow):
    workunits.process({"config": workflow.config})
    status = json.loads((workflow.root / "workflow/status.json").read_text())
    assert len(status["workunits"]) == 1
    unit = status["workunits"]["1"]
    assert sorted(s["ligands_expected"] for s in unit["subjobs"].values()) == [2, 4]
    with tarfile.open(unit["download_path"]) as archive:
        content = json.load(archive.extractfile("af_input/config.json"))
        collection_keys = {
            key for subjob in content["subjobs"].values() for key in subjob["collections"]
        }
        assert collection_keys == {"AA_0000001", "BB_0000002"}
        assert "af_input/input-files/ds1/config.txt" in archive.getnames()


@pytest.mark.parametrize("storage", ["s3", "sharedfs"])
@pytest.mark.parametrize("addressing", ["hash", "metatranche"])
def test_collection_addressing_preserves_padded_collection_numbers(storage, addressing):
    config = {
        "object_store_data_collection_addressing_mode": addressing,
        "object_store_data_collection_identifier": "library-v1",
        "object_store_data_collection_prefix": "library",
        "sharedfs_collection_path": "/library",
        "ligand_library_format": "pdbqt",
    }
    generate = workunits.gen_s3_download_path if storage == "s3" else workunits.gen_sharedfs_path
    base = "library" if storage == "s3" else "/library"
    if addressing == "hash":
        digest = hashlib.sha256(b"AA_BB/0000042").hexdigest()
        expected = f"{base}/{digest[:2]}/{digest[2:4]}/library-v1/pdbqt/AA_BB/0000042.tar.gz"
    else:
        expected = f"{base}/AA/BB/0000042.tar.gz"
    assert generate({"config": config}, "AA_BB", "0000042") == expected


@pytest.mark.parametrize(
    "backend,output,job_id", [("slurm", "Submitted batch job 321\n", 321),
                              ("lsf", "Job <654> is submitted to queue <normal>.\n", 654)]
)
def test_scheduler_submission_renders_array_and_records_job_id(
    backend, output, job_id, workflow, repo_root, monkeypatch
):
    config = dict(workflow.config)
    config[f"{backend}_template"] = str(repo_root / f"tools/templates/template1.{backend}.sh")
    config[f"{backend}_job_submission_timeout"] = "10"
    fake_run = Mock(return_value=SimpleNamespace(returncode=0, stdout=output))
    monkeypatch.setattr(submit.subprocess, "run", fake_run)
    monkeypatch.setattr(submit.time, "sleep", lambda _: None)
    unit = {"subjobs": {"0": {}, "1": {}}, "download_path": "/tmp/unit.tar.gz"}
    getattr(submit, f"submit_{backend}")(config, None, unit, 1)
    assert unit["status"]["job_id"] == job_id
    assert unit["status"]["af_job_status"] == "SUBMITTED"
    script = Path(config["sharedfs_workunit_path"]) / "1" / f"submit.{backend}"
    assert "{{" not in script.read_text()
    assert fake_run.call_args.args[0][0] == ("sbatch" if backend == "slurm" else "bsub")


def test_aws_single_subjob_uses_valid_array_and_queue_rotation(workflow, monkeypatch):
    client = Mock()
    client.submit_job.return_value = {"jobId": "fake-job-id"}
    config = dict(workflow.config, aws_batch_number_of_queues="2")
    unit = {"subjobs": {"0": {}}, "s3_download_path": "jobs/1.tar.gz"}
    monkeypatch.setattr(submit.time, "sleep", lambda _: None)
    submit.submit_aws_batch(config, client, unit, 4)
    params = client.submit_job.call_args.kwargs
    assert params["arrayProperties"] == {"size": 2}
    assert params["jobQueue"].endswith("-queue2")
    assert unit["job_id"] == "fake-job-id"
    assert unit["subjobs"]["0"]["status"] == "SUBMITTED"


def test_failed_scheduler_submission_does_not_mark_workunit_submitted(workflow, repo_root, monkeypatch):
    config = dict(workflow.config, slurm_template=str(repo_root / "tools/templates/template1.slurm.sh"))
    monkeypatch.setattr(submit.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=1)))
    unit = {"subjobs": {"0": {}}, "download_path": "/tmp/unit.tar.gz"}
    with pytest.raises(Exception, match="sbatch did not return successfully"):
        submit.submit_slurm(config, None, unit, 1)
    assert "status" not in unit
