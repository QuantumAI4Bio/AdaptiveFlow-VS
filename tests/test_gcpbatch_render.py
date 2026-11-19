"""Job rendering, array splitting and configuration validation for gcpbatch."""

import json

import pytest

import afvs_gcpbatch


# ---------------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------------

def test_valid_configuration_has_no_problems(gcp_config):
    assert afvs_gcpbatch.check_config(gcp_config) == []


def test_missing_required_keys_are_reported(gcp_config):
    del gcp_config['gcp_project']
    gcp_config['gcp_batch_worker_image'] = ""

    problems = afvs_gcpbatch.check_config(gcp_config)

    assert any("gcp_project" in problem for problem in problems)
    assert any("gcp_batch_worker_image" in problem for problem in problems)


def test_sharedfs_job_storage_is_rejected_for_gcpbatch(gcp_config):
    gcp_config['job_storage_mode'] = "sharedfs"

    problems = afvs_gcpbatch.check_config(gcp_config)

    assert any("job_storage_mode" in problem for problem in problems)


def test_oversubscribed_threads_are_reported(gcp_config):
    gcp_config['gcp_batch_subjob_vcpus'] = "2"
    gcp_config['threads_to_use'] = "16"

    problems = afvs_gcpbatch.check_config(gcp_config)

    assert any("oversubscribed" in problem for problem in problems)


def test_array_size_above_provider_limit_is_rejected(gcp_config):
    gcp_config['gcp_batch_array_job_size'] = str(afvs_gcpbatch.BATCH_MAX_TASK_COUNT + 1)

    problems = afvs_gcpbatch.check_config(gcp_config)

    assert any("gcp_batch_array_job_size" in problem for problem in problems)


def test_s3_library_with_gcp_batch_is_flagged_as_cross_provider(gcp_config):
    gcp_config['data_storage_mode'] = "s3"

    warnings = afvs_gcpbatch.cross_provider_warnings(gcp_config)

    assert len(warnings) == 1
    assert "cross-provider" in warnings[0]
    assert "egress" in warnings[0]


def test_gcs_library_with_gcp_batch_is_not_flagged(gcp_config):
    assert afvs_gcpbatch.cross_provider_warnings(gcp_config) == []


def test_defaults_do_not_enable_live_transport(gcp_config):
    del gcp_config['gcp_batch_live_transport']

    merged = afvs_gcpbatch.config_defaults_applied(gcp_config)

    assert merged['gcp_batch_live_transport'] == "0"


def test_task_scratch_is_disk_backed_not_shared_memory(gcp_config):
    """AFVS_TMP_PATH must not inherit tempdir_default on Batch.

    tempdir_default is /dev/shm, which is correct on a cluster node and
    fatal in a container: Batch gives a task 64 MiB there and the worker
    refuses to start with under 1 GiB free.
    """
    gcp_config['tempdir_default'] = "/dev/shm/"
    part = afvs_gcpbatch.plan_workunit_parts(["0"], 200)[0]

    variables = (afvs_gcpbatch.render_batch_job(gcp_config, "1", part)
                 ['taskGroups'][0]['taskSpec']['environment']['variables'])

    assert variables['AFVS_TMP_PATH'] == "/tmp"
    assert not variables['AFVS_TMP_PATH'].startswith("/dev/shm")


def test_configured_task_scratch_is_used(gcp_config):
    gcp_config['gcp_batch_task_scratch_path'] = "/mnt/disks/scratch"
    part = afvs_gcpbatch.plan_workunit_parts(["0"], 200)[0]

    variables = (afvs_gcpbatch.render_batch_job(gcp_config, "1", part)
                 ['taskGroups'][0]['taskSpec']['environment']['variables'])

    assert variables['AFVS_TMP_PATH'] == "/mnt/disks/scratch"


def test_shared_memory_scratch_is_rejected(gcp_config):
    gcp_config['gcp_batch_task_scratch_path'] = "/dev/shm"

    problems = afvs_gcpbatch.check_config(gcp_config)

    assert any("gcp_batch_task_scratch_path" in problem and "/dev/shm" in problem
               for problem in problems)


def test_relative_task_scratch_is_rejected(gcp_config):
    gcp_config['gcp_batch_task_scratch_path'] = "scratch"

    problems = afvs_gcpbatch.check_config(gcp_config)

    assert any("absolute path" in problem for problem in problems)


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

def test_job_id_is_deterministic(gcp_config):
    first = afvs_gcpbatch.build_job_id(gcp_config, "7", 0)
    second = afvs_gcpbatch.build_job_id(gcp_config, "7", 0)

    assert first == second
    assert first == "afvs-fixture-prescreen-7-0"


def test_job_id_differs_per_workunit_and_part(gcp_config):
    ids = {
        afvs_gcpbatch.build_job_id(gcp_config, workunit, part)
        for workunit in ("1", "2")
        for part in (0, 1)
    }

    assert len(ids) == 4


def test_job_id_respects_the_provider_character_rules(gcp_config):
    gcp_config['job_name'] = "ATG_Primary/Screen 2026 (replica 3)"

    job_id = afvs_gcpbatch.build_job_id(gcp_config, "1", 0)

    assert afvs_gcpbatch.JOB_ID_RE.match(job_id), job_id
    assert len(job_id) <= afvs_gcpbatch.JOB_ID_MAX_LENGTH


def test_long_job_names_stay_unique_and_within_the_limit(gcp_config):
    base = "atg-primaryscreen-ds2-" + ("x" * 80)

    gcp_config['job_name'] = base + "-a"
    first = afvs_gcpbatch.build_job_id(gcp_config, "1", 0)
    gcp_config['job_name'] = base + "-b"
    second = afvs_gcpbatch.build_job_id(gcp_config, "1", 0)

    assert len(first) <= afvs_gcpbatch.JOB_ID_MAX_LENGTH
    assert len(second) <= afvs_gcpbatch.JOB_ID_MAX_LENGTH
    assert first != second


def test_run_tag_is_stable_and_unique_per_part(gcp_config):
    assert (afvs_gcpbatch.build_run_tag(gcp_config, "1", 0)
            == afvs_gcpbatch.build_run_tag(gcp_config, "1", 0))
    assert (afvs_gcpbatch.build_run_tag(gcp_config, "1", 0)
            != afvs_gcpbatch.build_run_tag(gcp_config, "1", 1))


# ---------------------------------------------------------------------------
# Array splitting
# ---------------------------------------------------------------------------

def test_small_workunit_is_a_single_part():
    parts = afvs_gcpbatch.plan_workunit_parts(["0", "1"], 200)

    assert len(parts) == 1
    assert parts[0]['task_count'] == 2
    assert parts[0]['subjob_index_offset'] == 0


def test_single_subjob_keeps_task_count_of_one():
    # Unlike AWS Batch, which requires an array of at least two and makes
    # AdaptiveFlow pad a one-subjob workunit, Batch accepts taskCount=1.
    parts = afvs_gcpbatch.plan_workunit_parts(["0"], 200)

    assert len(parts) == 1
    assert parts[0]['task_count'] == 1


def test_oversized_workunit_splits_deterministically():
    subjob_ids = [str(index) for index in range(450)]

    parts = afvs_gcpbatch.plan_workunit_parts(subjob_ids, 200)

    assert [part['task_count'] for part in parts] == [200, 200, 50]
    assert [part['subjob_index_offset'] for part in parts] == [0, 200, 400]
    assert parts[2]['subjob_ids'][0] == "400"

    # Every subjob is covered exactly once.
    covered = [subjob for part in parts for subjob in part['subjob_ids']]
    assert covered == subjob_ids


def test_task_index_maps_onto_the_right_subjob():
    parts = afvs_gcpbatch.plan_workunit_parts([str(index) for index in range(450)], 200)

    assert afvs_gcpbatch.subjob_id_for_task(parts[0], 0) == "0"
    assert afvs_gcpbatch.subjob_id_for_task(parts[1], 0) == "200"
    assert afvs_gcpbatch.subjob_id_for_task(parts[2], 49) == "449"


def test_task_index_outside_the_part_is_rejected():
    parts = afvs_gcpbatch.plan_workunit_parts(["0", "1"], 200)

    with pytest.raises(IndexError):
        afvs_gcpbatch.subjob_id_for_task(parts[0], 2)


def test_empty_workunit_produces_no_parts():
    assert afvs_gcpbatch.plan_workunit_parts([], 200) == []


# ---------------------------------------------------------------------------
# Rendered job
# ---------------------------------------------------------------------------

def test_rendered_job_sets_task_count_from_real_subjobs(gcp_config):
    part = afvs_gcpbatch.plan_workunit_parts(["0", "1"], 200)[0]

    job = afvs_gcpbatch.render_batch_job(gcp_config, "1", part)

    task_group = job['taskGroups'][0]
    assert task_group['taskCount'] == 2
    assert task_group['parallelism'] == 2


def test_parallelism_is_capped_by_configuration(gcp_config):
    gcp_config['gcp_batch_parallelism'] = "1"
    part = afvs_gcpbatch.plan_workunit_parts(["0", "1", "2"], 200)[0]

    job = afvs_gcpbatch.render_batch_job(gcp_config, "1", part)

    assert job['taskGroups'][0]['taskCount'] == 3
    assert job['taskGroups'][0]['parallelism'] == 1


def test_rendered_job_carries_compute_shape_and_limits(gcp_config):
    gcp_config['gcp_batch_boot_disk_mib'] = "51200"
    part = afvs_gcpbatch.plan_workunit_parts(["0"], 200)[0]

    task_spec = afvs_gcpbatch.render_batch_job(gcp_config, "1", part)['taskGroups'][0]['taskSpec']

    assert task_spec['computeResource'] == {
        'cpuMilli': 2000,
        'memoryMib': 4096,
        'bootDiskMib': 51200,
    }
    assert task_spec['maxRunDuration'] == "1800s"
    assert task_spec['maxRetryCount'] == 1


def test_rendered_job_pins_image_service_account_and_machine(gcp_config):
    part = afvs_gcpbatch.plan_workunit_parts(["0"], 200)[0]

    job = afvs_gcpbatch.render_batch_job(gcp_config, "1", part)

    container = job['taskGroups'][0]['taskSpec']['runnables'][0]['container']
    assert container['imageUri'] == gcp_config['gcp_batch_worker_image']
    assert container['entrypoint'].endswith("template1.gcpbatch.sh")

    allocation = job['allocationPolicy']
    assert allocation['instances'][0]['policy']['machineType'] == "c2d-standard-8"
    assert allocation['serviceAccount']['email'] == gcp_config['gcp_batch_service_account']


def test_task_environment_carries_the_subjob_offset(gcp_config):
    part = afvs_gcpbatch.plan_workunit_parts([str(index) for index in range(450)], 200)[1]

    job = afvs_gcpbatch.render_batch_job(gcp_config, "3", part)
    variables = job['taskGroups'][0]['taskSpec']['environment']['variables']

    assert variables['AFVS_WORKUNIT'] == "3"
    assert variables['AFVS_SUBJOB_INDEX_OFFSET'] == "200"
    assert variables['AFVS_JOB_STORAGE_MODE'] == "gcs"
    assert variables['AFVS_CONFIG_JOB_GCS_BUCKET'] == gcp_config['object_store_job_bucket']
    assert variables['AFVS_CONFIG_JOB_GCS_OBJECT'].endswith("/input/tasks/3.tar.gz")
    # The task's own subjob is derived at runtime from BATCH_TASK_INDEX, so
    # no per-task subjob ID is baked into the shared environment.
    assert 'AFVS_WORKUNIT_SUBJOB' not in variables


def test_job_environment_never_carries_credentials(gcp_config):
    # Secrets that a real control file can end up holding, so that this
    # asserts the renderer copies named keys rather than the whole
    # configuration, instead of only that the fixture has no secrets.
    gcp_config['aws_access_key_id'] = "AKIAFIXTUREACCESSKEY"
    gcp_config['aws_secret_access_key'] = "fixture-secret-access-key-value"
    gcp_config['gcp_service_account_private_key'] = "fixture-private-key-value"

    part = afvs_gcpbatch.plan_workunit_parts(["0"], 200)[0]

    rendered = json.dumps(afvs_gcpbatch.render_batch_job(gcp_config, "1", part)).lower()

    for forbidden in ("secret", "password", "private_key", "access_key", "session_token",
                      "bearer", "credential"):
        assert forbidden not in rendered

    for value in ("AKIAFIXTUREACCESSKEY", "fixture-secret-access-key-value",
                  "fixture-private-key-value"):
        assert value.lower() not in rendered


def test_network_policy_is_only_rendered_when_configured(gcp_config):
    part = afvs_gcpbatch.plan_workunit_parts(["0"], 200)[0]

    assert 'network' not in afvs_gcpbatch.render_batch_job(
        gcp_config, "1", part)['allocationPolicy']

    gcp_config['gcp_batch_network'] = "projects/fixture-project/global/networks/afvs"
    gcp_config['gcp_batch_subnetwork'] = (
        "projects/fixture-project/regions/us-central1/subnetworks/afvs")

    allocation = afvs_gcpbatch.render_batch_job(gcp_config, "1", part)['allocationPolicy']

    interface = allocation['network']['networkInterfaces'][0]
    assert interface['network'].endswith("/afvs")
    assert interface['noExternalIpAddress'] is True


def test_preview_renders_every_part_without_a_transport(gcp_config):
    subjob_ids = [str(index) for index in range(250)]
    gcp_config['gcp_batch_array_job_size'] = "100"

    preview = afvs_gcpbatch.preview_workunit(gcp_config, "2", subjob_ids)

    assert preview['parent'] == "projects/fixture-project/locations/us-central1"
    assert [part['task_count'] for part in preview['parts']] == [100, 100, 50]
    assert [part['job_id'] for part in preview['parts']] == [
        "afvs-fixture-prescreen-2-0",
        "afvs-fixture-prescreen-2-1",
        "afvs-fixture-prescreen-2-2",
    ]
    assert preview['parts'][0]['resource_name'].startswith(
        "projects/fixture-project/locations/us-central1/jobs/")
    assert preview['job_input_object'].startswith("gs://fixture-job-bucket/")


def test_preview_reports_cross_provider_reads(gcp_config):
    gcp_config['data_storage_mode'] = "s3"

    preview = afvs_gcpbatch.preview_workunit(gcp_config, "1", ["0"])

    assert any("cross-provider" in warning for warning in preview['warnings'])


# ---------------------------------------------------------------------------
# Object layout
# ---------------------------------------------------------------------------

def test_metatranche_collection_layout_matches_the_s3_convention(gcp_config):
    object_name = afvs_gcpbatch.gen_gcs_collection_object_name(
        gcp_config, "CADBCCCDCCAACCAAAA", "0000001")

    assert object_name == "fixture-library/CADBCCCDCCAACCAAAA/0000001.tar.gz"


def test_hash_collection_layout_is_preserved(gcp_config):
    gcp_config['object_store_data_collection_addressing_mode'] = "hash"
    gcp_config['object_store_data_collection_identifier'] = "Fixture_Library_2026"

    object_name = afvs_gcpbatch.gen_gcs_collection_object_name(
        gcp_config, "CADBCCCDCCAACCAAAA", "0000001")

    digest = afvs_gcpbatch.get_collection_hash("CADBCCCDCCAACCAAAA", 1)
    assert object_name == (
        f"fixture-library/{digest[0:2]}/{digest[2:4]}/Fixture_Library_2026/pdbqt/"
        f"CADBCCCDCCAACCAAAA/0000001.tar.gz")


def test_job_input_layout_supports_both_addressing_modes(gcp_config):
    assert afvs_gcpbatch.gen_job_input_object_name(gcp_config, 4) == (
        "AF/AFVS/jobs/fixture-prescreen/input/tasks/4.tar.gz")

    gcp_config['object_store_job_addressing_mode'] = "hash"
    digest = afvs_gcpbatch.get_collection_hash(gcp_config['job_letter'], 4)

    assert afvs_gcpbatch.gen_job_input_object_name(gcp_config, 4) == (
        f"AF/AFVS/jobs/{digest[0:2]}/{digest[2:4]}/fixture-prescreen/input/tasks/4.tar.gz")


def test_canonical_output_layout_matches_the_aws_layout(gcp_config):
    assert afvs_gcpbatch.gen_output_object_name(
        gcp_config, "ds-fixture", "csv", "1", "0", "csv.gz") == (
        "AF/AFVS/jobs/fixture-prescreen/ds-fixture/csv/1/0.csv.gz")

    assert afvs_gcpbatch.gen_output_object_name(
        gcp_config, None, "summary", "1", "0", "json.gz") == (
        "AF/AFVS/jobs/fixture-prescreen/summary/1/0.json.gz")


def test_attempt_and_manifest_layouts_are_separate(gcp_config):
    assert afvs_gcpbatch.gen_attempt_object_name(
        gcp_config, "1", "0", "01-abcdef", "summary.json.gz") == (
        "AF/AFVS/jobs/fixture-prescreen/attempts/1/0/01-abcdef/summary.json.gz")

    assert afvs_gcpbatch.gen_manifest_object_name(gcp_config, "1", "0") == (
        "AF/AFVS/jobs/fixture-prescreen/manifests/1/0.json")
