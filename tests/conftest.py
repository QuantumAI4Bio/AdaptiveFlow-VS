"""Shared fixtures for the offline AdaptiveFlow test suite.

Every fixture here is offline by construction: ligand collections, workunit
archives and job output all live in a temporary directory, and the
object store is the filesystem-backed LocalObjectStore. The
`forbid_live_cloud_clients` fixture is applied automatically and fails any
test that tries to construct a real Google Cloud or AWS client, which is
how the suite enforces that no live API is called rather than assuming it.
"""

import gzip
import json
import os
import sys
import tarfile
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
TEMPLATES_DIR = TOOLS_DIR / "templates"

for path in (str(TOOLS_DIR), str(TEMPLATES_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)


# ---------------------------------------------------------------------------
# Live API guard
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def forbid_live_cloud_clients(monkeypatch):
    """Makes the construction of any live cloud client a test failure.

    The GCP submission and storage paths are exercised in full by this
    suite. This guard is what turns "no cloud spend" from an intention
    into an assertion: if a code path under test reached for a real
    client, the test fails here instead of quietly contacting a provider.
    """
    def refuse(name):
        def _refuse(*args, **kwargs):
            raise AssertionError(
                f"The offline test suite attempted to construct a live {name} client")
        return _refuse

    try:
        from google.cloud import batch_v1
        monkeypatch.setattr(batch_v1, "BatchServiceClient", refuse("Google Batch"))
    except ImportError:
        pass

    try:
        from google.cloud import storage
        monkeypatch.setattr(storage, "Client", refuse("Google Cloud Storage"))
    except ImportError:
        pass

    import boto3
    monkeypatch.setattr(boto3, "client", refuse("AWS"))

    yield


# ---------------------------------------------------------------------------
# Library fixtures
# ---------------------------------------------------------------------------

#: Two collections in distinct tranches. Collection keys follow the AFVS
#: <tranche>_<collection number> convention with an 18 letter tranche ID.
COLLECTIONS = {
    "CADBCCCDCCAACCAAAA_0000001": [
        "m_fixture____000001____000001____000001_S1_T0",
        "m_fixture____000001____000001____000002_S1_T1",
        "m_fixture____000001____000001____000003_S2_T0",
    ],
    "EBDCEBCDCCAACCAAAB_0000002": [
        "m_fixture____000002____000002____000001_S1_T0",
        "m_fixture____000002____000002____000002_S3_T2",
    ],
}

#: Zero-based representative index of each ligand within its collection,
#: as the sparse .listing file records it.
SPARSE_INDEX = {
    "m_fixture____000001____000001____000001_S1_T0": 0,
    "m_fixture____000001____000001____000002_S1_T1": 1,
    "m_fixture____000001____000001____000003_S2_T0": 2,
    "m_fixture____000002____000002____000001_S1_T0": 0,
    "m_fixture____000002____000002____000002_S3_T2": 1,
}


def ligand_pdbqt(ligand_name, tranche):
    """Builds a minimal but valid PDBQT ligand record.

    The header lines are the ones the worker actually reads: the SMILES
    attribute ends up in the summary file and the tranche line is what
    dynamic tranche filtering matches against.
    """
    suffix = ligand_name.rsplit("_", 2)[-2:]
    smiles = "CCO" if suffix[0] == "S1" else "CCN"
    return textwrap.dedent(f"""\
        REMARK  Name = {ligand_name}
        REMARK  SMILES: {smiles}
        REMARK  SMILES_current: {smiles}
        REMARK  * Heavy atom count: 3
        REMARK  Tranche: {tranche}
        ROOT
        ATOM      1  C   LIG d   1       1.000   0.000   0.000  1.00  0.00    +0.000 C
        ATOM      2  C   LIG d   1       2.500   0.000   0.000  1.00  0.00    +0.000 C
        ATOM      3  O   LIG d   1       3.200   1.100   0.000  1.00  0.00    -0.300 OA
        ENDROOT
        TORSDOF 1
        """)


def expected_score(ligand_name):
    """The score the fixture engine produces for a ligand.

    Deterministic and distinct per ligand, so a test can tell whether a
    score was attributed to the right molecule.
    """
    return -4.0 - (sum(ord(char) for char in ligand_name) % 50) / 10.0


@pytest.fixture
def library_root(tmp_path):
    """Creates paired sparse and full ligand collection archives.

    The sparse archive carries a .listing file with the source collection,
    ligand ID and zero-based representative index of every ligand, which
    is what prescreen_mode uses to pick representatives.
    """
    root = tmp_path / "library"
    full_dir = root / "full"
    sparse_dir = root / "sparse"
    full_dir.mkdir(parents=True)
    sparse_dir.mkdir(parents=True)

    staging = tmp_path / "library-staging"

    for collection_key, ligands in COLLECTIONS.items():
        tranche, collection_number = collection_key.split("_")

        collection_dir = staging / collection_key / collection_number
        collection_dir.mkdir(parents=True)

        for ligand in ligands:
            (collection_dir / f"{ligand}.pdbqt").write_text(
                ligand_pdbqt(ligand, tranche), encoding="utf-8")

        with tarfile.open(full_dir / f"{collection_key}.tar.gz", "x:gz") as archive:
            archive.add(collection_dir, arcname=collection_number)

        listing_lines = [
            f"{collection_key},{ligand},{SPARSE_INDEX[ligand]}" for ligand in ligands
        ]
        (collection_dir / ".listing").write_text("\n".join(listing_lines) + "\n",
                                                 encoding="utf-8")

        with tarfile.open(sparse_dir / f"{collection_key}.tar.gz", "x:gz") as archive:
            archive.add(collection_dir, arcname=collection_number)

    return root


# ---------------------------------------------------------------------------
# Workflow configuration
# ---------------------------------------------------------------------------

@pytest.fixture
def scenario_dir(tmp_path):
    """Creates the docking scenario input directory for the fixture campaign."""
    base = tmp_path / "input-files"
    scenario = base / "ds-fixture"
    scenario.mkdir(parents=True)

    receptor = base / "receptor-fixture.pdbqt"
    receptor.write_text(textwrap.dedent("""\
        REMARK  fixture receptor
        ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00    -0.300 N
        ATOM      2  CA  ALA A   1       1.458   0.000   0.000  1.00  0.00     0.100 C
        TER
        """), encoding="utf-8")

    (scenario / "config.txt").write_text(textwrap.dedent(f"""\
        receptor={receptor.as_posix()}
        center_x=2.0
        center_y=0.5
        center_z=0.0
        size_x=20
        size_y=20
        size_z=20
        exhaustiveness=8
        """), encoding="utf-8")

    return base


@pytest.fixture
def gcp_config(tmp_path, scenario_dir):
    """A workflow configuration for batchsystem=gcpbatch with GCS storage."""
    return {
        'job_name': "fixture-prescreen",
        'job_letter': "fixture-prescreen",
        'batchsystem': "gcpbatch",
        'threads_to_use': "2",
        'threads_per_docking': "1",
        'program_timeout': "90",

        'gcp_project': "fixture-project",
        'gcp_region': "us-central1",
        'gcp_batch_array_job_size': "200",
        'gcp_batch_machine_type': "c2d-standard-8",
        'gcp_batch_worker_image': "us-central1-docker.pkg.dev/fixture/afvs/worker:pinned",
        'gcp_batch_service_account': "afvs-worker@fixture-project.iam.gserviceaccount.com",
        'gcp_batch_subjob_vcpus': "2",
        'gcp_batch_subjob_memory': "4096",
        'gcp_batch_subjob_timeout': "1800",
        'gcp_batch_subjob_retry_count': "1",
        'gcp_batch_live_transport': "0",

        'job_storage_mode': "gcs",
        'data_storage_mode': "gcs",
        'object_store_job_bucket': "fixture-job-bucket",
        'object_store_job_prefix': "AF/AFVS/jobs",
        'object_store_job_prefix_full': "AF/AFVS/jobs/fixture-prescreen",
        'object_store_job_addressing_mode': "metatranche",
        'object_store_data_bucket': "fixture-library-bucket",
        'object_store_data_collection_prefix': "fixture-library",
        'object_store_data_collection_addressing_mode': "metatranche",
        'object_store_data_collection_identifier': "",

        'ligand_library_format': "pdbqt",
        'collection_list_type': "standard",
        'collection_list_file': "templates/todo.all",
        'dockings_per_subjob': "1",
        'dynamic_tranche_filtering': "0",
        'dynamic_tranche_filtering_regex': ".*",
        'run_atom_check': "1",
        'tempdir_default': str(tmp_path / "scratch") + os.sep,

        'summary_formats': ["csv.gz", "parquet"],
        'print_attrs_in_summary': ["smi", "heavy_atom_count"],

        'docking_scenario_names': ["ds-fixture"],
        'docking_scenario_methods': ["qvina02"],
        'docking_scenario_replicas': ["1"],
        'docking_scenario_batchsizes': ["1"],
        'docking_scenario_basefolder': str(scenario_dir),
        'docking_scenarios_internal': {
            'ds-fixture': {'key': "ds-fixture", 'replicas': 1, 'batchcount': 1},
        },

        'prescreen_mode': 1,
        'prescreen_ligands_per_tranche': 2,
    }


@pytest.fixture
def object_store(tmp_path, monkeypatch):
    """A filesystem-backed object store standing in for Google Cloud Storage.

    AFVS_GCS_LOCAL_ROOT is set so that the worker and tool code paths which
    build their own store from the environment, as they do inside a real
    Batch task, resolve to this same local store.
    """
    import afvs_gcs

    root = tmp_path / "object-store"
    monkeypatch.setenv(afvs_gcs.LOCAL_OBJECT_STORE_ENV, str(root))
    return afvs_gcs.LocalObjectStore(root)


@pytest.fixture
def staged_workunit(gcp_config, library_root, object_store, tmp_path):
    """Stages one workunit with two distinct subjobs into the mock object store.

    Returns a dict describing what was staged: the workunit ID, the subjob
    IDs and, for each subjob, the collection it covers and the ligands the
    worker is expected to dock.
    """
    import afvs_gcpbatch

    collection_keys = list(COLLECTIONS)
    subjobs = {}
    expected = {}

    for index, collection_key in enumerate(collection_keys):
        subjob_id = str(index)
        collection_name, collection_number = collection_key.split("_")

        object_name = afvs_gcpbatch.gen_gcs_collection_object_name(
            gcp_config, collection_name, collection_number)
        object_store.upload_file(
            library_root / "sparse" / f"{collection_key}.tar.gz",
            gcp_config['object_store_data_bucket'], object_name)

        subjobs[subjob_id] = {
            'collections': {
                collection_key: {
                    'count': len(COLLECTIONS[collection_key]),
                    'mode': "prescreen_mode",
                    'prescreen_ligands_per_tranche': gcp_config['prescreen_ligands_per_tranche'],
                    'collection_name': collection_name,
                    'collection_number': collection_number,
                    'gcs_bucket': gcp_config['object_store_data_bucket'],
                    'gcs_download_path': object_name,
                    'dockings': len(COLLECTIONS[collection_key]),
                }
            }
        }

        expected[subjob_id] = {
            'collection_key': collection_key,
            'ligands': [
                ligand for ligand in COLLECTIONS[collection_key]
                if SPARSE_INDEX[ligand] < gcp_config['prescreen_ligands_per_tranche']
            ],
        }

    workunit_id = "1"
    archive_path = tmp_path / "workunit-1.tar.gz"
    _build_workunit_archive(gcp_config, subjobs, archive_path, tmp_path)

    job_object = afvs_gcpbatch.gen_job_input_object_name(gcp_config, workunit_id)
    object_store.upload_file(archive_path, gcp_config['object_store_job_bucket'], job_object)

    return {
        'workunit_id': workunit_id,
        'subjob_ids': sorted(subjobs, key=int),
        'subjobs': subjobs,
        'expected': expected,
        'job_object': job_object,
        'archive_path': archive_path,
    }


def _build_workunit_archive(config, subjobs, archive_path, tmp_path):
    """Packages a workunit archive the same way afvs_prepare_workunits does."""
    import shutil

    staging = tmp_path / f"workunit-staging-{archive_path.stem}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    with open(staging / "config.json", "w") as json_out:
        json.dump({'config': config, 'subjobs': subjobs}, json_out, indent=4)

    shutil.copytree(config['docking_scenario_basefolder'], staging / "input-files")

    with tarfile.open(archive_path, "x:gz") as archive:
        archive.add(staging, arcname="af_input")

    return archive_path


@pytest.fixture
def read_gzip_csv():
    """Returns a helper that reads a gzipped CSV object into dict rows."""
    def _read(store, bucket, object_name, destination):
        store.download_file(bucket, object_name, destination)
        with gzip.open(destination, "rt") as read_file:
            lines = [line.rstrip("\n") for line in read_file if line.strip()]
        header = lines[0].split(",")
        return [dict(zip(header, line.split(","))) for line in lines[1:]]
    return _read
