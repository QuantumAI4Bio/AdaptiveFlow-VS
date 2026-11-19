"""Checks on the pinned qvina02 binary that ships in tools/bin.

What this module establishes:

  * the binary is present and is the pinned build, identified by digest;
  * it is a Linux x86-64 ELF executable, which is the platform contract
    the worker image and any Slurm node have to satisfy;
  * where the host can execute it, that it runs and reports its usage.

What it deliberately does not establish: that a particular receptor and
ligand produce a particular score. That needs real prepared inputs and is
verified in the workbench repository, which owns the receptor preparation
and library fixtures. On a host that cannot execute Linux binaries the
execution test is skipped and names the exact dependency, rather than
being reported as a pass.
"""

import hashlib
import platform
import subprocess
import sys
from pathlib import Path

import pytest

BIN_DIR = Path(__file__).resolve().parents[1] / "tools" / "bin"
QVINA02 = BIN_DIR / "qvina02"

#: Digest of the qvina02 build pinned in this repository. A change here is
#: a change of docking engine and must be a deliberate, reviewed edit:
#: scores from two builds are not comparable within one campaign.
QVINA02_SHA256 = "f8ac045235025e98b15fd90aae6617edfdcc125081f72a5a5315db22be1f46e0"

ELF_MAGIC = b"\x7fELF"


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as read_file:
        for chunk in iter(lambda: read_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _can_execute_linux_elf():
    return sys.platform.startswith("linux") and platform.machine() in ("x86_64", "AMD64")


def test_pinned_engine_binary_is_present():
    assert QVINA02.is_file(), f"{QVINA02} is missing"


def test_pinned_engine_binary_matches_its_recorded_digest():
    assert _sha256(QVINA02) == QVINA02_SHA256


def test_pinned_engine_binary_is_a_linux_x86_64_executable():
    with open(QVINA02, "rb") as read_file:
        header = read_file.read(20)

    assert header[:4] == ELF_MAGIC, "qvina02 is expected to be an ELF binary"
    assert header[4] == 2, "qvina02 is expected to be 64-bit"
    assert header[5] == 1, "qvina02 is expected to be little-endian"
    # e_machine at offset 18: 0x3e is x86-64.
    assert header[18] == 0x3E, "qvina02 is expected to target x86-64"


@pytest.mark.skipif(
    not _can_execute_linux_elf(),
    reason=("qvina02 is a Linux x86-64 ELF binary. Executing it requires a Linux "
            "x86-64 host, WSL2, or the worker container image; this host cannot "
            "run it, so its executable capability stays unverified here."))
def test_pinned_engine_binary_runs_on_this_host():
    QVINA02.chmod(0o755)

    result = subprocess.run([str(QVINA02), "--help"], capture_output=True, text=True,
                            timeout=60)

    assert result.returncode == 0, result.stderr
    combined = f"{result.stdout}\n{result.stderr}"
    assert "--receptor" in combined
    assert "--exhaustiveness" in combined


@pytest.mark.skipif(
    not _can_execute_linux_elf(),
    reason="requires a Linux x86-64 host to execute the pinned binary")
def test_engine_rejects_a_missing_receptor_with_a_nonzero_status(tmp_path):
    QVINA02.chmod(0o755)

    config = tmp_path / "config.txt"
    config.write_text(
        "receptor=/nonexistent/receptor.pdbqt\n"
        "center_x=0\ncenter_y=0\ncenter_z=0\n"
        "size_x=20\nsize_y=20\nsize_z=20\nexhaustiveness=1\n",
        encoding="utf-8")
    ligand = tmp_path / "ligand.pdbqt"
    ligand.write_text("ROOT\nENDROOT\nTORSDOF 0\n", encoding="utf-8")

    result = subprocess.run(
        [str(QVINA02), "--config", str(config), "--ligand", str(ligand),
         "--out", str(tmp_path / "out.pdbqt")],
        capture_output=True, text=True, timeout=120)

    # The worker treats a non-zero status as a failed docking and records
    # the reason, so the binary has to report failure this way.
    assert result.returncode != 0
