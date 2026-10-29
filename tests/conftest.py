"""Import the script-style project and keep tests isolated from live services."""

from pathlib import Path
import sys

import boto3
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools/templates")]


@pytest.fixture(autouse=True)
def forbid_aws_clients(monkeypatch):
    def unexpected_client(*args, **kwargs):
        raise AssertionError("Tests must supply a fake AWS client")

    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setattr(boto3, "client", unexpected_client)


@pytest.fixture
def repo_root():
    return ROOT
