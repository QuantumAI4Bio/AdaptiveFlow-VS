"""Executable reproductions of open findings; strict xfail forces cleanup when fixed.

See docs/development/code-review-2026-10-29.md. These tests assert desired behavior,
and do not submit jobs, invoke docking engines, or contact AWS.
"""

from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock

import afvs_prepare_workunits as workunits
import afvs_run as runner
import afvs_verify_collections as verify
from botocore.exceptions import ClientError
import pytest


@pytest.mark.xfail(raises=AssertionError, reason="Review R1: tranche rejection stops the entire subjob")
def test_tranche_filter_keeps_later_matching_collections(tmp_path, monkeypatch):
    queued_collections = []

    def fake_flush(queue, processes, description):
        if description == "download":
            while not queue.empty():
                queued_collections.append(queue.get_nowait()["collection_key"])

    monkeypatch.setattr(runner, "Queue", Queue)
    monkeypatch.setattr(runner, "Process", Mock(return_value=SimpleNamespace(start=lambda: None)))
    monkeypatch.setattr(runner, "get_workunit_information", lambda: ("1", "0"))
    monkeypatch.setattr(runner, "setup_job_storage_mode", lambda ctx: None)
    monkeypatch.setattr(runner, "get_subjob_config", lambda *args: None)
    monkeypatch.setattr(runner, "flush_queue", fake_flush)
    runner.process({
        "temp_dir": str(tmp_path),
        "main_config": {
            "ligand_library_format": "pdbqt", "prescreen_mode": 0,
            "dynamic_tranche_filtering": 1, "dynamic_tranche_filtering_regex": "^BB$",
            "docking_scenario_names": ["ds1"], "docking_scenario_methods": ["vina"],
            "docking_scenario_replicas": [1], "docking_scenario_batchsizes": [1],
        },
        "subjob_config": {"collections": {"AA_0000001": {}, "BB_0000002": {}}},
    })
    assert queued_collections == ["BB_0000002"]


@pytest.mark.parametrize(
    "program,score_file",
    [("CovDock", "min_score_covdock.txt"), ("Glide_SP", "min_score.txt"),
     ("Glide_XP", "min_score_xp.txt"), ("Glide_HTVS", "min_score_htvs.txt")],
)
@pytest.mark.xfail(raises=TypeError, reason="Review R2: Glide/CovDock completion callbacks accept one argument")
def test_glide_completion_accepts_runner_callback_contract(program, score_file, tmp_path):
    (tmp_path / score_file).write_text("-8.25")
    item = {"program": program, "tmp_run_dir": str(tmp_path)}
    runner.process_docking_completion(item, SimpleNamespace(stdout="", stderr="", returncode=0))
    assert item["status"] == "success"
    assert item["score"] == -8.25


@pytest.mark.xfail(raises=AssertionError, reason="Review R3: unrequested heavy-atom attribute stops SMILES search")
def test_smiles_extraction_ignores_unrequested_attributes(tmp_path):
    ligand = tmp_path / "ligand.pdbqt"
    ligand.write_text("REMARK * Heavy atom count: 3\nREMARK SMILES: CCO\n")
    assert runner.get_attrs("pdbqt", str(ligand), attrs=["smi"])["smi"] == "CCO"


@pytest.mark.parametrize("page", [1, 2])
@pytest.mark.xfail(raises=NameError, reason="Review R4: collection verifier never imports ClientError")
def test_collection_verifier_handles_s3_errors(page):
    error = ClientError({"Error": {"Code": "AccessDenied", "Message": "test failure"}}, "ListObjectsV2")
    client = Mock()
    first_page = {"Contents": [{"Key": "AA/0000001.tar.gz"}], "NextContinuationToken": "next"}
    client.list_objects_v2.side_effect = [error] if page == 1 else [first_page, error]
    result = verify.get_collection_list({
        "s3": client,
        "config": {"object_store_data_collection_prefix": "library", "object_store_data_bucket": "test-bucket"},
    }, "AA", "AA")
    assert result is None


@pytest.mark.xfail(raises=NameError, reason="Review R4: workunit publisher never imports ClientError")
def test_failed_s3_upload_propagates_original_error(tmp_path):
    inputs = tmp_path / "input-files"
    inputs.mkdir()
    client = Mock()
    client.upload_file.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "test failure"}}, "PutObject"
    )
    config = {
        "tempdir_default": str(tmp_path), "docking_scenario_basefolder": str(inputs),
        "job_storage_mode": "s3", "object_store_job_addressing_mode": "metatranche",
        "object_store_job_prefix_full": "jobs/test", "object_store_job_bucket": "test-bucket",
    }
    with pytest.raises(ClientError):
        workunits.publish_workunit({"config": config, "s3": client}, 1, {})
