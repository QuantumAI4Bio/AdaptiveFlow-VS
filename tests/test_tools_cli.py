"""End-to-end tests of the command line tools for a gcpbatch workflow.

These run the real scripts in a throwaway AdaptiveFlow tree:

    afvs_prepare_folders.py   -> validates the control file, writes
                                 workflow/config.json and collections.json
    afvs_prepare_workunits.py -> groups collections, packages workunits and
                                 publishes them to the object store
    afvs_submit_jobs.py       -> renders the Batch jobs (preview only)
    afvs_gcpbatch.py          -> preview, status and manifest subcommands

The object store is the filesystem-backed one, selected with
--local-object-store, so nothing here contacts a provider. Submission is
never attempted: the shipped control file keeps the live transport off,
and the tests assert that the tools refuse to submit while it is off.
"""

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_SOURCE = REPO_ROOT / "tools"


@pytest.fixture
def afvs_tree(tmp_path, library_root):
    """Builds a minimal AdaptiveFlow tree with a gcpbatch control file."""
    root = tmp_path / "campaign"
    tools = root / "tools"
    templates = tools / "templates"
    input_files = root / "input-files"
    scenario = input_files / "ds-cli"

    templates.mkdir(parents=True)
    scenario.mkdir(parents=True)

    # Only the scripts under test are copied; tools/bin is 64 MB of
    # docking binaries that none of these tools read.
    for name in ("afvs_prepare_folders.py", "afvs_prepare_workunits.py",
                 "afvs_submit_jobs.py", "afvs_get_status.py", "afvs_gcpbatch.py"):
        shutil.copy(TOOLS_SOURCE / name, tools / name)
    for name in ("afvs_gcs.py", "afvs_run.py", "template1.gcpbatch.sh",
                 "template1.bash", "template1.slurm.sh"):
        shutil.copy(TOOLS_SOURCE / "templates" / name, templates / name)

    receptor = input_files / "receptor-cli.pdbqt"
    receptor.write_text("REMARK fixture\nATOM      1  N   ALA A   1       0.000   0.000"
                        "   0.000  1.00  0.00    -0.300 N\nTER\n", encoding="utf-8")

    (scenario / "config.txt").write_text(textwrap.dedent(f"""\
        receptor={receptor.as_posix()}
        center_x=0.0
        center_y=0.0
        center_z=0.0
        size_x=20
        size_y=20
        size_z=20
        exhaustiveness=8
        """), encoding="utf-8")

    (templates / "todo.all").write_text(
        "CADBCCCDCCAACCAAAA_0000001 3\nEBDCEBCDCCAACCAAAB_0000002 2\n", encoding="utf-8")

    # /dev/shm is the right default on a Linux worker but does not exist
    # on every development host, so the tree under test uses a scratch
    # directory that does.
    scratch = tmp_path / "scratch"
    scratch.mkdir()

    (templates / "all.ctrl").write_text(
        control_file(tempdir_default=scratch.as_posix()), encoding="utf-8")

    return {
        'root': root,
        'tools': tools,
        'templates': templates,
        'object_store_root': tmp_path / "cli-object-store",
        'library_root': library_root,
        'scratch': scratch,
    }


def control_file(**overrides):
    values = {
        'job_name': "cli-prescreen",
        'batchsystem': "gcpbatch",
        'gcp_project': "fixture-project",
        'gcp_region': "us-central1",
        'gcp_batch_worker_image': "us-central1-docker.pkg.dev/fixture/afvs/worker:pinned",
        'gcp_batch_live_transport': "0",
        'data_storage_mode': "gcs",
        'tempdir_default': "",
    }
    values.update(overrides)

    return textwrap.dedent(f"""\
        job_name={values['job_name']}
        threads_per_docking=1
        threads_to_use=2
        program_timeout=90

        batchsystem={values['batchsystem']}

        gcp_project={values['gcp_project']}
        gcp_region={values['gcp_region']}
        gcp_batch_job_prefix=afvs
        gcp_batch_array_job_size=2
        gcp_batch_machine_type=c2d-standard-2
        gcp_batch_provisioning_model=STANDARD
        gcp_batch_worker_image={values['gcp_batch_worker_image']}
        gcp_batch_service_account=afvs-worker@fixture-project.iam.gserviceaccount.com
        gcp_batch_subjob_vcpus=2
        gcp_batch_subjob_memory=4096
        gcp_batch_subjob_timeout=1800
        gcp_batch_subjob_retry_count=1
        gcp_batch_parallelism=0
        gcp_batch_live_transport={values['gcp_batch_live_transport']}

        data_storage_mode={values['data_storage_mode']}
        job_storage_mode=gcs
        data_collection_addressing_mode=metatranche
        data_collection_identifier=Fixture_Library_2026
        job_addressing_mode=metatranche

        object_store_job_bucket=fixture-job-bucket
        object_store_job_prefix=AF/AFVS/jobs
        object_store_data_bucket=fixture-library-bucket
        object_store_data_collection_prefix=fixture-library

        collection_folder=../input-files/ligand-library

        summary_formats=parquet,csv.gz
        print_attrs_in_summary=smi,heavy_atom_count

        collection_list_type=standard
        collection_list_file=templates/todo.all
        dockings_per_subjob=1
        ligand_library_format=pdbqt
        dynamic_tranche_filtering=0
        dynamic_tranche_filtering_regex=.*
        tempdir_default={values['tempdir_default']}

        docking_scenario_names=ds-cli
        docking_scenario_methods=qvina02
        docking_scenario_replicas=1
        docking_scenario_batchsizes=1
        docking_scenario_basefolder=../input-files

        prescreen_mode=1
        prescreen_ligands_per_tranche=2
        run_atom_check=1
        """)


def run_tool(afvs_tree, script, *args, expect_success=True):
    """Runs one AFVS tool from the campaign's tools directory."""
    environment = dict(os.environ)
    environment['AFVS_GCS_LOCAL_ROOT'] = str(afvs_tree['object_store_root'])
    environment['PYTHONPATH'] = os.pathsep.join(
        [str(afvs_tree['tools']), str(afvs_tree['templates'])])

    result = subprocess.run(
        [sys.executable, str(afvs_tree['tools'] / script), *args],
        cwd=str(afvs_tree['tools']), capture_output=True, text=True,
        env=environment, timeout=300)

    if expect_success and result.returncode != 0:
        raise AssertionError(
            f"{script} {' '.join(args)} failed ({result.returncode})\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

    return result


def stage_library(afvs_tree):
    """Publishes the sparse fixture collections into the CLI object store."""
    import afvs_gcs

    store = afvs_gcs.LocalObjectStore(afvs_tree['object_store_root'])
    for archive in sorted((afvs_tree['library_root'] / "sparse").glob("*.tar.gz")):
        collection_key = archive.name[:-len(".tar.gz")]
        tranche, number = collection_key.split("_")
        store.upload_file(archive, "fixture-library-bucket",
                          f"fixture-library/{tranche}/{number}.tar.gz")
    return store


# ---------------------------------------------------------------------------
# afvs_prepare_folders.py
# ---------------------------------------------------------------------------

def test_prepare_folders_accepts_a_gcpbatch_control_file(afvs_tree):
    result = run_tool(afvs_tree, "afvs_prepare_folders.py")

    config = json.loads((afvs_tree['root'] / "workflow" / "config.json").read_text())
    assert config['batchsystem'] == "gcpbatch"
    assert config['job_storage_mode'] == "gcs"
    assert config['object_store_job_prefix_full'] == "AF/AFVS/jobs/cli-prescreen"
    assert "WARNING" not in result.stdout

    collections = json.loads(
        (afvs_tree['root'] / "workflow" / "collections.json").read_text())
    assert set(collections) == {"CADBCCCDCCAACCAAAA_0000001", "EBDCEBCDCCAACCAAAB_0000002"}
    assert collections["CADBCCCDCCAACCAAAA_0000001"]['mode'] == "prescreen_mode"
    assert collections["CADBCCCDCCAACCAAAA_0000001"]['prescreen_ligands_per_tranche'] == 2


def test_prepare_folders_rejects_an_incomplete_gcpbatch_control_file(afvs_tree):
    (afvs_tree['templates'] / "all.ctrl").write_text(
        control_file(gcp_project="", gcp_batch_worker_image="",
                     tempdir_default=afvs_tree['scratch'].as_posix()), encoding="utf-8")

    result = run_tool(afvs_tree, "afvs_prepare_folders.py", expect_success=False)

    assert result.returncode != 0
    assert "'gcp_project' must be set" in result.stdout
    assert "'gcp_batch_worker_image' must be set" in result.stdout
    assert not (afvs_tree['root'] / "workflow" / "config.json").exists()


def test_prepare_folders_warns_about_a_cross_provider_library(afvs_tree):
    (afvs_tree['templates'] / "all.ctrl").write_text(
        control_file(data_storage_mode="s3",
                     tempdir_default=afvs_tree['scratch'].as_posix()), encoding="utf-8")

    result = run_tool(afvs_tree, "afvs_prepare_folders.py")

    assert "WARNING" in result.stdout
    assert "cross-provider" in result.stdout
    assert "egress" in result.stdout


def test_prepare_folders_rejects_an_unknown_batch_system(afvs_tree):
    (afvs_tree['templates'] / "all.ctrl").write_text(
        control_file(batchsystem="azurebatch",
                     tempdir_default=afvs_tree['scratch'].as_posix()), encoding="utf-8")

    result = run_tool(afvs_tree, "afvs_prepare_folders.py", expect_success=False)

    assert result.returncode != 0
    assert "is not supported" in result.stdout


# ---------------------------------------------------------------------------
# afvs_prepare_workunits.py
# ---------------------------------------------------------------------------

def test_prepare_workunits_publishes_archives_and_records_their_digests(afvs_tree):
    run_tool(afvs_tree, "afvs_prepare_folders.py")
    store = stage_library(afvs_tree)

    result = run_tool(afvs_tree, "afvs_prepare_workunits.py",
                      "--local-object-store", str(afvs_tree['object_store_root']))

    assert "Generated 1 workunits" in result.stdout

    status = json.loads((afvs_tree['root'] / "workflow" / "status.json").read_text())
    workunit = status['workunits']["1"]

    assert sorted(workunit['subjobs'], key=int) == ["0", "1"]
    assert workunit['gcs_bucket'] == "fixture-job-bucket"
    assert workunit['gcs_download_path'] == "AF/AFVS/jobs/cli-prescreen/input/tasks/1.tar.gz"
    assert workunit['gcs_md5']

    # The published archive really exists and matches what was recorded.
    stored = store.stat("fixture-job-bucket", workunit['gcs_download_path'])
    assert stored['size'] == workunit['gcs_size']
    assert stored['md5'] == workunit['gcs_md5']


def test_prepare_workunits_records_collection_locations_without_uris(afvs_tree):
    run_tool(afvs_tree, "afvs_prepare_folders.py")
    stage_library(afvs_tree)
    run_tool(afvs_tree, "afvs_prepare_workunits.py",
             "--local-object-store", str(afvs_tree['object_store_root']))

    import tarfile

    archive = (afvs_tree['object_store_root'] / "fixture-job-bucket" / "AF" / "AFVS"
               / "jobs" / "cli-prescreen" / "input" / "tasks" / "1.tar.gz")
    with tarfile.open(archive) as handle:
        config = json.load(handle.extractfile("af_input/config.json"))

    for subjob in config['subjobs'].values():
        for collection in subjob['collections'].values():
            assert collection['gcs_bucket'] == "fixture-library-bucket"
            assert not collection['gcs_download_path'].startswith("gs://")
            assert 's3_download_path' not in collection
            assert 'sharedfs_path' not in collection


# ---------------------------------------------------------------------------
# afvs_submit_jobs.py and afvs_gcpbatch.py
# ---------------------------------------------------------------------------

def test_submit_preview_prints_the_job_without_submitting(afvs_tree):
    run_tool(afvs_tree, "afvs_prepare_folders.py")
    stage_library(afvs_tree)
    run_tool(afvs_tree, "afvs_prepare_workunits.py",
             "--local-object-store", str(afvs_tree['object_store_root']))

    status_before = (afvs_tree['root'] / "workflow" / "status.json").read_text()

    result = run_tool(afvs_tree, "afvs_submit_jobs.py", "1", "1", "--preview")

    preview = json.loads(result.stdout[result.stdout.index("{"):])
    assert preview['parts'][0]['job_id'] == "afvs-cli-prescreen-1-0"
    assert preview['parts'][0]['task_count'] == 2
    assert (preview['parts'][0]['job']['taskGroups'][0]['taskSpec']['runnables'][0]
            ['container']['imageUri'].endswith("worker:pinned"))

    # A preview changes nothing on disk.
    assert (afvs_tree['root'] / "workflow" / "status.json").read_text() == status_before


def test_submission_is_refused_while_the_live_transport_is_disabled(afvs_tree):
    run_tool(afvs_tree, "afvs_prepare_folders.py")
    stage_library(afvs_tree)
    run_tool(afvs_tree, "afvs_prepare_workunits.py",
             "--local-object-store", str(afvs_tree['object_store_root']))

    result = run_tool(afvs_tree, "afvs_submit_jobs.py", "1", "1", expect_success=False)

    assert result.returncode != 0
    assert "Live Google Cloud Batch transport is disabled" in (result.stdout + result.stderr)

    status = json.loads((afvs_tree['root'] / "workflow" / "status.json").read_text())
    workunit = status['workunits']["1"]

    # Intent is recorded before the provider is called, so it survives the
    # refusal. It must stay an intent: no provider job was created, and a
    # later submission with the same deterministic job ID resumes from here.
    assert workunit['status'] == "SUBMISSION_INTENT"
    assert len(workunit['gcp_batch_parts']) == 1
    intent = workunit['gcp_batch_parts'][0]
    assert intent['af_job_status'] == "SUBMISSION_INTENT"
    assert intent['job_id'] == "afvs-cli-prescreen-1-0"
    assert 'provider_job_name' not in intent
    assert 'provider_job_uid' not in intent


def test_gcpbatch_preview_subcommand_matches_the_submitter(afvs_tree):
    run_tool(afvs_tree, "afvs_prepare_folders.py")
    stage_library(afvs_tree)
    run_tool(afvs_tree, "afvs_prepare_workunits.py",
             "--local-object-store", str(afvs_tree['object_store_root']))

    from_submitter = run_tool(afvs_tree, "afvs_submit_jobs.py", "1", "1", "--preview")
    from_tool = run_tool(afvs_tree, "afvs_gcpbatch.py", "preview", "--workunit", "1")

    assert (json.loads(from_submitter.stdout[from_submitter.stdout.index("{"):])
            == json.loads(from_tool.stdout))


def test_gcpbatch_status_subcommand_reports_the_disabled_transport(afvs_tree):
    run_tool(afvs_tree, "afvs_prepare_folders.py")
    stage_library(afvs_tree)
    run_tool(afvs_tree, "afvs_prepare_workunits.py",
             "--local-object-store", str(afvs_tree['object_store_root']))

    result = run_tool(afvs_tree, "afvs_gcpbatch.py", "status", "--workunit", "1",
                      expect_success=False)

    assert "no recorded Google Cloud Batch submission" in (result.stdout + result.stderr)


def test_gcpbatch_manifest_subcommand_reports_an_empty_workunit(afvs_tree):
    run_tool(afvs_tree, "afvs_prepare_folders.py")
    stage_library(afvs_tree)
    run_tool(afvs_tree, "afvs_prepare_workunits.py",
             "--local-object-store", str(afvs_tree['object_store_root']))

    result = run_tool(afvs_tree, "afvs_gcpbatch.py",
                      "--local-object-store", str(afvs_tree['object_store_root']),
                      "manifest", "--workunit", "1")

    report = json.loads(result.stdout)
    assert report['state'] == "empty"
    assert report['expected_subjobs'] == 2
    assert report['subjobs']["0"]['status'] == "missing"


def test_get_status_reports_gcpbatch_without_a_live_transport(afvs_tree):
    run_tool(afvs_tree, "afvs_prepare_folders.py")
    stage_library(afvs_tree)
    run_tool(afvs_tree, "afvs_prepare_workunits.py",
             "--local-object-store", str(afvs_tree['object_store_root']))

    result = run_tool(afvs_tree, "afvs_get_status.py",
                      "--local-object-store", str(afvs_tree['object_store_root']))

    assert "Google Cloud Batch Progress" in result.stdout
    assert "Output manifests" in result.stdout


# ---------------------------------------------------------------------------
# Existing batch systems keep working
# ---------------------------------------------------------------------------

def test_bash_control_file_still_prepares_a_sharedfs_workflow(afvs_tree):
    """The local bash/sharedfs reference path is unaffected by the GCP work."""
    control = control_file(tempdir_default=afvs_tree['scratch'].as_posix())
    control = control.replace("batchsystem=gcpbatch", "batchsystem=bash")
    control = control.replace("job_storage_mode=gcs", "job_storage_mode=sharedfs")
    control = control.replace("data_storage_mode=gcs", "data_storage_mode=sharedfs")
    control += "bash_template=./templates/template1.bash\nbash_array_job_size=100\n"
    (afvs_tree['templates'] / "all.ctrl").write_text(control, encoding="utf-8")

    (afvs_tree['root'] / "input-files" / "ligand-library").mkdir(parents=True)

    result = run_tool(afvs_tree, "afvs_prepare_folders.py")

    config = json.loads((afvs_tree['root'] / "workflow" / "config.json").read_text())
    assert config['batchsystem'] == "bash"
    assert config['sharedfs_workunit_path'].endswith("workflow/workunits")
    assert "WARNING" not in result.stdout


def test_slurm_control_file_still_validates(afvs_tree):
    control = control_file(tempdir_default=afvs_tree['scratch'].as_posix())
    control = control.replace("batchsystem=gcpbatch", "batchsystem=slurm")
    control = control.replace("job_storage_mode=gcs", "job_storage_mode=sharedfs")
    control = control.replace("data_storage_mode=gcs", "data_storage_mode=sharedfs")
    control += textwrap.dedent("""\
        slurm_template=./templates/template1.slurm.sh
        slurm_array_job_throttle=100
        slurm_account=
        slurm_partition=debug
        slurm_cpus=2
        slurm_array_job_size=100
        slurm_job_submission_timeout=600
        """)
    (afvs_tree['templates'] / "all.ctrl").write_text(control, encoding="utf-8")
    (afvs_tree['root'] / "input-files" / "ligand-library").mkdir(parents=True)

    run_tool(afvs_tree, "afvs_prepare_folders.py")

    config = json.loads((afvs_tree['root'] / "workflow" / "config.json").read_text())
    assert config['batchsystem'] == "slurm"
