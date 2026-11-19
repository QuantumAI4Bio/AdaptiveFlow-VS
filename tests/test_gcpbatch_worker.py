"""Worker I/O acceptance tests for native Google Cloud Batch.

The first test is the acceptance criterion for the scheduler integration:
one workunit with two distinct subjobs is rendered, two indexed tasks are
replayed against filesystem-backed mock object storage, and the outputs
are checked to be attributed to the right ligands and readable by the
ranker. The remaining tests replay a missing archive, a failed upload, an
interrupted task, and reconcile the resulting manifests.

No test in this module reaches a network: the object store is local and
the autouse guard in conftest fails any attempt to build a cloud client.
"""

import gzip
import json

import pytest

import afvs_gcpbatch
import afvs_gcs
import replay
from conftest import COLLECTIONS, SPARSE_INDEX, expected_score


@pytest.fixture(autouse=True)
def stub_engine(monkeypatch):
    replay.install_stub_engine(monkeypatch)


def _canonical_csv_object(config, scenario, workunit_id, subjob_id):
    return afvs_gcpbatch.gen_output_object_name(
        config, scenario, "csv", workunit_id, subjob_id, "csv.gz")


# ---------------------------------------------------------------------------
# Acceptance: two indexed tasks of one workunit
# ---------------------------------------------------------------------------

def test_two_indexed_tasks_produce_results_for_the_right_ligands(
        gcp_config, staged_workunit, object_store, tmp_path, read_gzip_csv):
    workunit_id = staged_workunit['workunit_id']
    subjob_ids = staged_workunit['subjob_ids']
    assert len(subjob_ids) == 2

    # The workunit renders as one Batch job with one task per subjob, and
    # each task index maps onto exactly one subjob.
    preview = afvs_gcpbatch.preview_workunit(gcp_config, workunit_id, subjob_ids)
    assert len(preview['parts']) == 1
    part = preview['parts'][0]
    assert part['task_count'] == 2
    assert [afvs_gcpbatch.subjob_id_for_task(part, index) for index in range(2)] == subjob_ids

    results = {}
    for task_index, subjob_id in enumerate(subjob_ids):
        assert afvs_gcpbatch.subjob_id_for_task(part, task_index) == subjob_id
        results[subjob_id] = replay.replay_task(
            gcp_config, workunit_id, subjob_id, object_store,
            replay.make_scratch(tmp_path, f"task-{task_index}"))

    for subjob_id in subjob_ids:
        expected = staged_workunit['expected'][subjob_id]

        rows = read_gzip_csv(
            object_store, gcp_config['object_store_job_bucket'],
            _canonical_csv_object(gcp_config, "ds-fixture", workunit_id, subjob_id),
            tmp_path / f"summary-{subjob_id}.csv.gz")

        scores = replay.ligand_scores_from_summary(rows)

        # Only this subjob's collection appears in this subjob's output,
        # and only the sparse representatives below the per-tranche limit.
        assert sorted(scores) == sorted(expected['ligands'])
        assert all(row['collection_key'] == expected['collection_key'] for row in rows)

        # Each score belongs to the molecule it was computed for.
        for ligand, score in scores.items():
            assert score == pytest.approx(expected_score(ligand))

        # The attributes the ranker and the optional ML path depend on
        # survived into the summary.
        assert all(row['attr_smi'] in ("CCO", "CCN") for row in rows)
        assert all(row['scenario'] == "ds-fixture" for row in rows)

    # No ligand was reported by both tasks.
    first, second = (set(replay.ligand_scores_from_summary(read_gzip_csv(
        object_store, gcp_config['object_store_job_bucket'],
        _canonical_csv_object(gcp_config, "ds-fixture", workunit_id, subjob_id),
        tmp_path / f"overlap-{subjob_id}.csv.gz"))) for subjob_id in subjob_ids)
    assert first.isdisjoint(second)


def test_results_are_readable_by_the_ranker(
        gcp_config, staged_workunit, object_store, tmp_path):
    """The parquet shards are readable with the columns the ranker selects.

    afvs_get_top_results.py registers the parquet output with the column
    set ligand, collection_key, scenario, score_min, score_average,
    score_<replica> and attr_<name>, then orders by score_min. Reading the
    shards back with exactly that contract is what makes the GCP output
    usable by the existing ranking path.
    """
    import pandas

    workunit_id = staged_workunit['workunit_id']

    for subjob_id in staged_workunit['subjob_ids']:
        replay.replay_task(gcp_config, workunit_id, subjob_id, object_store,
                           replay.make_scratch(tmp_path, f"rank-{subjob_id}"))

    frames = []
    for subjob_id in staged_workunit['subjob_ids']:
        object_name = afvs_gcpbatch.gen_output_object_name(
            gcp_config, "ds-fixture", "parquet", workunit_id, subjob_id, "parquet")
        local_path = tmp_path / f"shard-{subjob_id}.parquet"
        object_store.download_file(
            gcp_config['object_store_job_bucket'], object_name, local_path)
        frames.append(pandas.read_parquet(local_path))

    combined = pandas.concat(frames, ignore_index=True)

    for column in ('ligand', 'collection_key', 'scenario', 'score_min', 'score_average',
                   'score_0', 'attr_smi', 'attr_heavy_atom_count'):
        assert column in combined.columns, column

    ranked = combined.sort_values('score_min', ascending=True)
    all_expected = [ligand
                    for subjob in staged_workunit['expected'].values()
                    for ligand in subjob['ligands']]
    assert len(ranked) == len(all_expected)

    # Lower is better, and the best row is the ligand with the lowest
    # fixture score.
    best_expected = min(all_expected, key=expected_score)
    assert ranked.iloc[0]['ligand'] == best_expected

    # The per-dimension tranche columns the activity map relies on are
    # exploded out of the collection key.
    assert combined.iloc[0]['tranche_0'] == combined.iloc[0]['collection_key'][0]


def test_sparse_representatives_below_the_limit_are_the_only_ones_docked(
        gcp_config, staged_workunit, object_store, tmp_path, read_gzip_csv):
    """prescreen_ligands_per_tranche bounds the representatives per collection."""
    workunit_id = staged_workunit['workunit_id']
    subjob_id = "0"
    collection_key = staged_workunit['expected'][subjob_id]['collection_key']

    replay.replay_task(gcp_config, workunit_id, subjob_id, object_store,
                       replay.make_scratch(tmp_path, "sparse"))

    rows = read_gzip_csv(
        object_store, gcp_config['object_store_job_bucket'],
        _canonical_csv_object(gcp_config, "ds-fixture", workunit_id, subjob_id),
        tmp_path / "sparse.csv.gz")

    docked = {row['ligand'] for row in rows}
    limit = gcp_config['prescreen_ligands_per_tranche']

    assert docked == {ligand for ligand in COLLECTIONS[collection_key]
                      if SPARSE_INDEX[ligand] < limit}
    # The collection holds three ligands but only two are representatives.
    assert len(COLLECTIONS[collection_key]) == 3
    assert len(docked) == 2


def test_full_library_archive_docks_every_ligand(
        gcp_config, library_root, object_store, tmp_path, read_gzip_csv):
    """With prescreen_mode off, the full archive's ligands are all docked."""
    from conftest import _build_workunit_archive

    gcp_config['prescreen_mode'] = 0
    gcp_config['prescreen_ligands_per_tranche'] = 0

    collection_key = "CADBCCCDCCAACCAAAA_0000001"
    collection_name, collection_number = collection_key.split("_")
    object_name = afvs_gcpbatch.gen_gcs_collection_object_name(
        gcp_config, collection_name, collection_number)
    object_store.upload_file(library_root / "full" / f"{collection_key}.tar.gz",
                             gcp_config['object_store_data_bucket'], object_name)

    subjobs = {
        "0": {
            'collections': {
                collection_key: {
                    'count': len(COLLECTIONS[collection_key]),
                    'mode': "all",
                    'collection_name': collection_name,
                    'collection_number': collection_number,
                    'gcs_bucket': gcp_config['object_store_data_bucket'],
                    'gcs_download_path': object_name,
                    'dockings': len(COLLECTIONS[collection_key]),
                }
            }
        }
    }

    archive_path = tmp_path / "workunit-full.tar.gz"
    _build_workunit_archive(gcp_config, subjobs, archive_path, tmp_path)
    object_store.upload_file(
        archive_path, gcp_config['object_store_job_bucket'],
        afvs_gcpbatch.gen_job_input_object_name(gcp_config, "1"))

    replay.replay_task(gcp_config, "1", "0", object_store,
                       replay.make_scratch(tmp_path, "full"))

    rows = read_gzip_csv(
        object_store, gcp_config['object_store_job_bucket'],
        _canonical_csv_object(gcp_config, "ds-fixture", "1", "0"),
        tmp_path / "full.csv.gz")

    assert {row['ligand'] for row in rows} == set(COLLECTIONS[collection_key])


# ---------------------------------------------------------------------------
# Manifests
# ---------------------------------------------------------------------------

def test_manifest_is_finalized_after_uploads_and_lists_stored_objects(
        gcp_config, staged_workunit, object_store, tmp_path):
    workunit_id = staged_workunit['workunit_id']

    outcome = replay.replay_task(gcp_config, workunit_id, "0", object_store,
                                 replay.make_scratch(tmp_path, "manifest"))

    manifest = outcome['manifest']
    assert manifest is not None
    assert manifest['workunit_id'] == workunit_id
    assert manifest['subjob_id'] == "0"
    assert manifest['dockings']['succeeded'] == 2
    assert manifest['dockings']['failed'] == 0

    # Every object the manifest claims really is in the store.
    for entry in manifest['objects']:
        assert object_store.exists(entry['bucket'], entry['object_name'])
        assert entry['md5']

    stored = afvs_gcpbatch.read_manifest(gcp_config, object_store, workunit_id, "0")
    assert stored['attempt_id'] == manifest['attempt_id']


def test_manifest_reconciliation_distinguishes_empty_partial_and_complete(
        gcp_config, staged_workunit, object_store, tmp_path):
    workunit_id = staged_workunit['workunit_id']
    subjob_ids = staged_workunit['subjob_ids']

    empty = afvs_gcpbatch.reconcile_manifests(
        gcp_config, object_store, workunit_id, subjob_ids)
    assert empty['state'] == "empty"
    assert empty['complete_subjobs'] == 0

    replay.replay_task(gcp_config, workunit_id, subjob_ids[0], object_store,
                       replay.make_scratch(tmp_path, "partial"))

    partial = afvs_gcpbatch.reconcile_manifests(
        gcp_config, object_store, workunit_id, subjob_ids)
    assert partial['state'] == "partial"
    assert partial['complete_subjobs'] == 1
    assert partial['subjobs'][subjob_ids[1]]['status'] == "missing"

    replay.replay_task(gcp_config, workunit_id, subjob_ids[1], object_store,
                       replay.make_scratch(tmp_path, "complete"))

    complete = afvs_gcpbatch.reconcile_manifests(
        gcp_config, object_store, workunit_id, subjob_ids)
    assert complete['state'] == "complete"
    assert complete['complete_subjobs'] == 2
    assert complete['dockings']['succeeded'] == 4


def test_manifest_reconciliation_detects_a_deleted_result_object(
        gcp_config, staged_workunit, object_store, tmp_path):
    workunit_id = staged_workunit['workunit_id']

    replay.replay_task(gcp_config, workunit_id, "0", object_store,
                       replay.make_scratch(tmp_path, "deleted"))

    object_store.delete_object(
        gcp_config['object_store_job_bucket'],
        _canonical_csv_object(gcp_config, "ds-fixture", workunit_id, "0"))

    report = afvs_gcpbatch.reconcile_manifests(gcp_config, object_store, workunit_id, ["0"])

    assert report['subjobs']["0"]['status'] == "objects_missing"
    assert report['state'] == "empty"


def test_retry_keeps_the_earlier_attempt_artifacts(
        gcp_config, staged_workunit, object_store, tmp_path):
    workunit_id = staged_workunit['workunit_id']

    first = replay.replay_task(
        gcp_config, workunit_id, "0", object_store,
        replay.make_scratch(tmp_path, "attempt-0"), attempt_index=0, attempt_uid="aaaa")
    second = replay.replay_task(
        gcp_config, workunit_id, "0", object_store,
        replay.make_scratch(tmp_path, "attempt-1"), attempt_index=1, attempt_uid="bbbb")

    assert first['manifest']['attempt_id'] == "00-aaaa"
    assert second['manifest']['attempt_id'] == "01-bbbb"

    attempt_prefix = (f"{afvs_gcpbatch.job_output_prefix(gcp_config)}/attempts/"
                      f"{workunit_id}/0/")
    stored = object_store.list_objects(
        gcp_config['object_store_job_bucket'], attempt_prefix)

    assert any("/00-aaaa/" in name for name in stored)
    assert any("/01-bbbb/" in name for name in stored)

    # The manifest records the latest successful attempt.
    current = afvs_gcpbatch.read_manifest(gcp_config, object_store, workunit_id, "0")
    assert current['attempt_id'] == "01-bbbb"


# ---------------------------------------------------------------------------
# Failure replays
# ---------------------------------------------------------------------------

def test_missing_workunit_archive_fails_the_task_clearly(
        gcp_config, staged_workunit, object_store, tmp_path):
    object_store.delete_object(
        gcp_config['object_store_job_bucket'], staged_workunit['job_object'])

    with pytest.raises(SystemExit) as error:
        replay.replay_task(gcp_config, staged_workunit['workunit_id'], "0", object_store,
                           replay.make_scratch(tmp_path, "missing-archive"))

    assert error.value.code == 1

    report = afvs_gcpbatch.reconcile_manifests(
        gcp_config, object_store, staged_workunit['workunit_id'], ["0"])
    assert report['state'] == "empty"


def test_missing_collection_archive_is_recorded_as_a_failed_download(
        gcp_config, staged_workunit, object_store, tmp_path):
    collection_key = staged_workunit['expected']["0"]['collection_key']
    collection_name, collection_number = collection_key.split("_")

    object_store.delete_object(
        gcp_config['object_store_data_bucket'],
        afvs_gcpbatch.gen_gcs_collection_object_name(
            gcp_config, collection_name, collection_number))

    outcome = replay.replay_task(
        gcp_config, staged_workunit['workunit_id'], "0", object_store,
        replay.make_scratch(tmp_path, "missing-collection"))

    assert outcome['docking_counts']['failed_downloads'] == 1
    assert outcome['docking_counts']['total'] == 0

    # The task still finalizes a manifest, and the manifest says plainly
    # that nothing was docked.
    assert outcome['manifest']['dockings']['failed_downloads'] == 1
    report = afvs_gcpbatch.reconcile_manifests(
        gcp_config, object_store, staged_workunit['workunit_id'], ["0"])
    assert report['dockings']['succeeded'] == 0


def test_corrupt_collection_archive_is_rejected_by_verification(
        gcp_config, staged_workunit, object_store, tmp_path, monkeypatch):
    collection_key = staged_workunit['expected']["0"]['collection_key']
    collection_name, collection_number = collection_key.split("_")
    object_name = afvs_gcpbatch.gen_gcs_collection_object_name(
        gcp_config, collection_name, collection_number)

    # Model a truncated transfer: the stored object's metadata no longer
    # matches the bytes that arrive locally.
    real_download = afvs_gcs.LocalObjectStore.download_file

    def truncating_download(self, bucket, name, local_path):
        metadata = real_download(self, bucket, name, local_path)
        if name == object_name:
            with open(local_path, "r+b") as handle:
                handle.truncate(16)
        return metadata

    monkeypatch.setattr(afvs_gcs.LocalObjectStore, "download_file", truncating_download)

    outcome = replay.replay_task(
        gcp_config, staged_workunit['workunit_id'], "0", object_store,
        replay.make_scratch(tmp_path, "corrupt-collection"))

    assert outcome['docking_counts']['failed_downloads'] == 1
    assert outcome['docking_counts']['succeeded'] == 0


def test_failed_upload_leaves_no_manifest(
        gcp_config, staged_workunit, object_store, tmp_path):
    workunit_id = staged_workunit['workunit_id']

    outcome = replay.replay_task(
        gcp_config, workunit_id, "0", object_store,
        replay.make_scratch(tmp_path, "failed-upload"),
        upload_failure=lambda item: item.get('content_type') == "csv")

    assert outcome['manifest'] is None
    assert outcome['failed_upload']['content_type'] == "csv"

    # A subjob whose upload failed is not reported as complete.
    report = afvs_gcpbatch.reconcile_manifests(gcp_config, object_store, workunit_id, ["0"])
    assert report['state'] == "empty"
    assert report['subjobs']["0"]['status'] == "missing"

    # A later attempt completes it.
    retry = replay.replay_task(
        gcp_config, workunit_id, "0", object_store,
        replay.make_scratch(tmp_path, "failed-upload-retry"),
        attempt_index=1, attempt_uid="retry")

    assert retry['manifest'] is not None
    assert afvs_gcpbatch.reconcile_manifests(
        gcp_config, object_store, workunit_id, ["0"])['state'] == "complete"


@pytest.mark.parametrize("stop_after", ["download", "docking"])
def test_interrupted_task_publishes_nothing_and_leaves_no_manifest(
        gcp_config, staged_workunit, object_store, tmp_path, stop_after):
    workunit_id = staged_workunit['workunit_id']

    outcome = replay.replay_task(
        gcp_config, workunit_id, "0", object_store,
        replay.make_scratch(tmp_path, f"interrupted-{stop_after}"),
        stop_after=stop_after)

    assert outcome['manifest'] is None
    assert outcome['uploads'] == []

    prefix = afvs_gcpbatch.job_output_prefix(gcp_config)
    published = [name for name in object_store.list_objects(
        gcp_config['object_store_job_bucket'], prefix)
        if "/input/tasks/" not in name]
    assert published == []

    report = afvs_gcpbatch.reconcile_manifests(gcp_config, object_store, workunit_id, ["0"])
    assert report['state'] == "empty"


def test_ligand_with_forbidden_elements_is_skipped_not_failed(
        gcp_config, library_root, object_store, tmp_path):
    """run_atom_check removes ligands containing B, Si or Sn."""
    import tarfile
    from conftest import _build_workunit_archive, ligand_pdbqt

    collection_key = "CADBCCCDCCAACCAAAA_0000001"
    tranche, collection_number = collection_key.split("_")
    staging = tmp_path / "boron" / collection_number
    staging.mkdir(parents=True)

    good = "m_fixture____000001____000001____000001_S1_T0"
    bad = "m_fixture____000001____000001____000009_S1_T0"
    (staging / f"{good}.pdbqt").write_text(ligand_pdbqt(good, tranche), encoding="utf-8")
    (staging / f"{bad}.pdbqt").write_text(
        ligand_pdbqt(bad, tranche).replace(
            "ATOM      3  O   LIG d   1       3.200   1.100   0.000  1.00  0.00    -0.300 OA",
            "ATOM      3  Si  LIG d   1       3.200   1.100   0.000  1.00  0.00    -0.300  Si "),
        encoding="utf-8")

    archive = tmp_path / "boron-collection.tar.gz"
    with tarfile.open(archive, "x:gz") as handle:
        handle.add(staging, arcname=collection_number)

    gcp_config['prescreen_mode'] = 0
    object_name = afvs_gcpbatch.gen_gcs_collection_object_name(
        gcp_config, tranche, collection_number)
    object_store.upload_file(archive, gcp_config['object_store_data_bucket'], object_name)

    subjobs = {"0": {'collections': {collection_key: {
        'count': 2,
        'mode': "all",
        'collection_name': tranche,
        'collection_number': collection_number,
        'gcs_bucket': gcp_config['object_store_data_bucket'],
        'gcs_download_path': object_name,
        'dockings': 2,
    }}}}

    archive_path = tmp_path / "workunit-boron.tar.gz"
    _build_workunit_archive(gcp_config, subjobs, archive_path, tmp_path)
    object_store.upload_file(
        archive_path, gcp_config['object_store_job_bucket'],
        afvs_gcpbatch.gen_job_input_object_name(gcp_config, "1"))

    outcome = replay.replay_task(gcp_config, "1", "0", object_store,
                                 replay.make_scratch(tmp_path, "boron"))

    assert outcome['docking_counts']['skipped'] == 1
    assert outcome['docking_counts']['succeeded'] == 1
    assert outcome['docking_counts']['failed'] == 0


# ---------------------------------------------------------------------------
# Storage addressing safety
# ---------------------------------------------------------------------------

def test_collection_records_never_carry_a_gs_uri(gcp_config, staged_workunit):
    for subjob in staged_workunit['subjobs'].values():
        for collection in subjob['collections'].values():
            assert not collection['gcs_download_path'].startswith("gs://")
            assert "gcs_bucket" in collection


def test_object_store_rejects_a_uri_where_a_key_is_expected(object_store):
    with pytest.raises(afvs_gcs.ObjectStoreError, match="not a URI"):
        object_store.stat("fixture-job-bucket", "gs://fixture-job-bucket/some/object")

    with pytest.raises(afvs_gcs.ObjectStoreError):
        afvs_gcs.validate_object_name("s3://bucket/key")


def test_object_store_rejects_path_traversal(object_store):
    with pytest.raises(afvs_gcs.ObjectStoreError):
        object_store.stat("fixture-job-bucket", "a/../../etc/passwd")


def test_gs_uri_helpers_round_trip():
    bucket, name = afvs_gcs.parse_gcs_uri("gs://bucket/a/b/c.tar.gz")

    assert (bucket, name) == ("bucket", "a/b/c.tar.gz")
    assert afvs_gcs.format_gcs_uri(bucket, name) == "gs://bucket/a/b/c.tar.gz"

    with pytest.raises(afvs_gcs.ObjectStoreError):
        afvs_gcs.parse_gcs_uri("/local/path.tar.gz")


def test_overview_summary_object_is_published_for_each_task(
        gcp_config, staged_workunit, object_store, tmp_path):
    workunit_id = staged_workunit['workunit_id']

    replay.replay_task(gcp_config, workunit_id, "0", object_store,
                       replay.make_scratch(tmp_path, "overview"))

    object_name = afvs_gcpbatch.gen_output_object_name(
        gcp_config, None, "summary", workunit_id, "0", "json.gz")
    local_path = tmp_path / "overview.json.gz"
    object_store.download_file(
        gcp_config['object_store_job_bucket'], object_name, local_path)

    with gzip.open(local_path, "rt") as read_file:
        overview = json.load(read_file)

    assert overview['metadata']['workunit_id'] == workunit_id
    assert overview['metadata']['subunit_id'] == "0"
    assert overview['dockings_status']['success'] == 2
