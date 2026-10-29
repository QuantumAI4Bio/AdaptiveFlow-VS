from queue import Queue
from types import SimpleNamespace

import afvs_run as runner
import pytest


@pytest.mark.parametrize("program", ["vina", "qvina02", "qvina_w", "gwovina"])
def test_vina_command_and_score_parsing(program):
    item = {
        "program": program, "threads_per_docking": 2, "tools_path": "/engines",
        "config_path": "/scenario/config.txt", "ligand_path": "/library/ligand.pdbqt",
        "output_path": "/results/pose.pdbqt", "log": {},
    }
    command = runner.program_runstring_array(item)
    assert command[0] == f"/engines/{program}"
    assert command[command.index("--ligand") + 1] == "/library/ligand.pdbqt"
    runner.process_docking_completion(item, SimpleNamespace(stdout="   1    -7.5    0.0    0.0\n"))
    assert item["status"] == "success"
    assert item["score"] == -7.5


def test_malformed_vina_output_is_failed():
    item = {"program": "vina", "log": {}}
    runner.process_docking_completion(item, SimpleNamespace(stdout="No docking modes found\n"))
    assert item["status"] == "failed"
    assert "score" not in item


def test_single_ligand_pipeline_creates_summary_and_cleans_scratch(tmp_path, monkeypatch):
    inputs = tmp_path / "af_input" / "input-files"
    inputs.mkdir(parents=True)
    scenario = {"program": "vina", "key": "ds1"}
    ctx = {
        "temp_dir": str(tmp_path), "tools_path": "/engines",
        "main_config": {"program_timeout": "10", "threads_per_docking": "1",
                        "docking_scenarios": {"ds1": dict(scenario, config="config.txt", replicas=1,
                                                         program_long="vina")}},
    }
    docking_queue = Queue()
    summary_queue = Queue()
    runner.submit_ligand_for_docking(
        ctx, docking_queue, "ligand1", "/ligand1.pdbqt", "AA_1", "AA_1", {}, str(tmp_path)
    )
    item = docking_queue.get_nowait()
    monkeypatch.setattr(
        runner.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="   1 -8.0 0 0\n", stderr=""),
    )
    runner.docking_process_batch(summary_queue, scenario, [item], str(tmp_path))
    summary = summary_queue.get_nowait()
    assert summary["type"] == "docking_complete"
    assert summary["items"][0]["score"] == -8.0
    assert not item["tmp_run_dir"].exists()
