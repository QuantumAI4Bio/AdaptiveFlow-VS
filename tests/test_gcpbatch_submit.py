"""Submission, idempotency, reconciliation and cancellation for gcpbatch.

Every test here runs against the in-memory fake transport. The suite also
asserts that the shipped configuration refuses to reach Google Cloud at
all, which is what keeps the implementation complete while the live
transport stays off.
"""

import pytest

import afvs_gcpbatch


@pytest.fixture
def transport():
    return afvs_gcpbatch.FakeBatchTransport()


# ---------------------------------------------------------------------------
# The shipped transport is disabled
# ---------------------------------------------------------------------------

def test_default_configuration_yields_the_disabled_transport(gcp_config):
    chosen = afvs_gcpbatch.transport_from_config(gcp_config)

    assert isinstance(chosen, afvs_gcpbatch.DisabledBatchTransport)
    assert chosen.live is False


def test_disabled_transport_refuses_and_records_the_intent(gcp_config):
    chosen = afvs_gcpbatch.transport_from_config(gcp_config)

    with pytest.raises(afvs_gcpbatch.LiveTransportDisabled) as error:
        chosen.create_job(afvs_gcpbatch.job_parent(gcp_config), "afvs-x-1-0", {})

    assert "gcp_batch_live_transport=1" in str(error.value)
    assert chosen.intents[0]['operation'] == "create_job"


def test_live_transport_cannot_be_constructed_implicitly():
    with pytest.raises(afvs_gcpbatch.LiveTransportDisabled):
        afvs_gcpbatch.GoogleBatchTransport()


def test_enabling_live_transport_is_an_explicit_configuration_change(gcp_config, monkeypatch):
    gcp_config['gcp_batch_live_transport'] = "1"

    # The autouse guard makes any live client construction a failure, so
    # this asserts that enabling the flag is the only thing standing
    # between AdaptiveFlow and a billable submission.
    with pytest.raises(AssertionError, match="live Google Batch client"):
        afvs_gcpbatch.transport_from_config(gcp_config)


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------

def test_submission_records_intent_before_calling_the_provider(gcp_config, transport):
    intents = []

    records = afvs_gcpbatch.submit_workunit(
        gcp_config, transport, "1", ["0", "1"], persist_intent=intents.append)

    assert len(intents) == 1
    # The intent was recorded before the provider was called and already
    # carried the job identity that recovery depends on.
    assert intents[0]['af_job_status'] == "SUBMISSION_INTENT"
    assert intents[0]['job_id'] == records[0]['job_id']
    assert intents[0]['run_tag'] == records[0]['run_tag']
    assert transport.calls[0][0] == "create_job"


def test_submission_creates_one_job_with_two_tasks(gcp_config, transport):
    records = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])

    assert len(records) == 1
    assert records[0]['af_job_status'] == "SUBMITTED"
    assert records[0]['task_count'] == 2

    job = transport.jobs[records[0]['provider_job_name']]
    assert job['job']['taskGroups'][0]['taskCount'] == 2
    assert len(job['tasks']) == 2


def test_oversized_workunit_submits_one_job_per_part(gcp_config, transport):
    gcp_config['gcp_batch_array_job_size'] = "2"

    records = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1", "2"])

    assert [record['part_index'] for record in records] == [0, 1]
    assert [record['task_count'] for record in records] == [2, 1]
    assert [record['subjob_index_offset'] for record in records] == [0, 2]
    assert len(transport.jobs) == 2


def test_duplicate_submission_is_replayed_by_the_idempotency_token(gcp_config, transport):
    first = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])

    # A second submission with no recollection of the first one, which is
    # what a worker that died after calling the provider would do. The
    # request ID is derived from the job identity, so the provider
    # recognises the retry.
    second = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])

    assert len(transport.jobs) == 1, "a duplicate submission must not create a second job"
    assert second[0]['adopted_existing_job'] is True
    assert second[0]['provider_job_name'] == first[0]['provider_job_name']
    assert second[0]['af_job_status'] == "SUBMITTED"


def test_duplicate_job_id_without_the_token_adopts_the_existing_job(gcp_config, transport):
    first = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])

    # Simulate the provider having forgotten the idempotency token, which
    # it does once the token's retention window passes. The deterministic
    # job ID is then the only thing preventing a second copy of the work.
    transport.request_ids.clear()

    second = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])

    assert len(transport.jobs) == 1
    assert second[0]['adopted_existing_job'] is True
    assert second[0]['provider_job_name'] == first[0]['provider_job_name']
    assert ('get_job', first[0]['provider_job_name'], None) in transport.calls


def test_recorded_submission_is_not_resubmitted(gcp_config, transport):
    records = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])
    create_calls = [call for call in transport.calls if call[0] == "create_job"]

    again = afvs_gcpbatch.submit_workunit(
        gcp_config, transport, "1", ["0", "1"],
        recorded_parts={0: records[0]})

    assert again[0]['provider_job_name'] == records[0]['provider_job_name']
    assert [call for call in transport.calls if call[0] == "create_job"] == create_calls


def test_interrupted_submission_resumes_with_the_same_identity(gcp_config, transport):
    intents = []
    afvs_gcpbatch.submit_workunit(
        gcp_config, transport, "1", ["0", "1"], persist_intent=intents.append)

    # Replay the recorded intent as if the process had died before the
    # response was stored: the intent still has no SUBMITTED status.
    recovered_intent = dict(intents[0])
    assert recovered_intent['af_job_status'] == "SUBMISSION_INTENT"

    resumed = afvs_gcpbatch.submit_workunit(
        gcp_config, transport, "1", ["0", "1"],
        recorded_parts={0: recovered_intent})

    assert len(transport.jobs) == 1
    assert resumed[0]['job_id'] == recovered_intent['job_id']
    assert resumed[0]['adopted_existing_job'] is True


def test_request_id_is_stable_for_a_part(gcp_config):
    part = afvs_gcpbatch.plan_workunit_parts(["0", "1"], 200)[0]

    first = afvs_gcpbatch.submission_intent(gcp_config, "1", part)
    second = afvs_gcpbatch.submission_intent(gcp_config, "1", part)

    assert first['request_id'] == second['request_id']


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

def test_reconciliation_maps_tasks_onto_subjobs(gcp_config, transport):
    gcp_config['gcp_batch_array_job_size'] = "2"
    records = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1", "2"])

    second_part_job = records[1]['provider_job_name']
    transport.set_task_state(second_part_job, 0, "RUNNING")

    report = afvs_gcpbatch.reconcile_workunit(gcp_config, transport, records)

    running = [task for part in report['parts'] for task in part['tasks']
               if task['state'] == "RUNNING"]
    assert len(running) == 1
    # Task 0 of the second part is subjob 2, not subjob 0.
    assert running[0]['subjob_id'] == "2"
    assert running[0]['task_index'] == 0


def test_reconciliation_reports_task_failures_and_retries(gcp_config, transport):
    records = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])
    job_name = records[0]['provider_job_name']

    transport.set_task_state(job_name, 0, "SUCCEEDED")
    transport.set_task_state(job_name, 1, "FAILED")
    transport.jobs[job_name]['tasks'][1]['attempts'] = 2

    report = afvs_gcpbatch.reconcile_workunit(gcp_config, transport, records)

    assert report['task_state_summary'] == {'SUCCEEDED': 1, 'FAILED': 1}
    assert report['parts'][0]['provider_state'] == "FAILED"
    assert report['parts'][0]['tasks'][1]['attempts'] == 2
    assert report['all_parts_terminal'] is True


def test_reconciliation_reports_a_job_the_provider_does_not_have(gcp_config, transport):
    records = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0"])
    del transport.jobs[records[0]['provider_job_name']]

    report = afvs_gcpbatch.reconcile_workunit(gcp_config, transport, records)

    assert report['parts'][0]['provider_state'] == "NOT_FOUND"
    assert report['missing_jobs'] == [records[0]['provider_job_name']]


def test_reconciliation_only_queries_recorded_jobs(gcp_config, transport):
    records = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0"])
    other = afvs_gcpbatch.submit_workunit(gcp_config, transport, "2", ["0"])

    transport.calls.clear()
    afvs_gcpbatch.reconcile_workunit(gcp_config, transport, records)

    queried = {call[1] for call in transport.calls}
    assert other[0]['provider_job_name'] not in queried


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------

def test_cancellation_only_affects_the_recorded_job(gcp_config, transport):
    target = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])
    bystander = afvs_gcpbatch.submit_workunit(gcp_config, transport, "2", ["0"])

    outcomes = afvs_gcpbatch.cancel_workunit(gcp_config, transport, target)

    assert outcomes[0]['outcome'] == "cancellation_requested"
    assert transport.jobs[target[0]['provider_job_name']]['state'] == "CANCELLED"
    assert transport.jobs[bystander[0]['provider_job_name']]['state'] == "QUEUED"


def test_cancellation_leaves_already_finished_tasks_alone(gcp_config, transport):
    records = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])
    job_name = records[0]['provider_job_name']
    transport.set_task_state(job_name, 0, "SUCCEEDED")

    afvs_gcpbatch.cancel_workunit(gcp_config, transport, records)

    states = [task['state'] for task in transport.jobs[job_name]['tasks']]
    assert states == ["SUCCEEDED", "UNEXECUTED"]


def test_cancelling_an_unsubmitted_workunit_is_reported_not_raised(gcp_config, transport):
    outcomes = afvs_gcpbatch.cancel_workunit(
        gcp_config, transport, [{'part_index': 0, 'resource_name': None}])

    assert outcomes[0]['outcome'] == "no_recorded_job"


def test_cancelling_a_job_the_provider_lost_is_reported(gcp_config, transport):
    records = afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0"])
    del transport.jobs[records[0]['provider_job_name']]

    outcomes = afvs_gcpbatch.cancel_workunit(gcp_config, transport, records)

    assert outcomes[0]['outcome'] == "not_found"


# ---------------------------------------------------------------------------
# No live API calls
# ---------------------------------------------------------------------------

def test_no_live_api_calls_were_made(gcp_config, transport):
    afvs_gcpbatch.submit_workunit(gcp_config, transport, "1", ["0", "1"])
    afvs_gcpbatch.reconcile_workunit(
        gcp_config, transport,
        afvs_gcpbatch.submit_workunit(gcp_config, transport, "2", ["0"]))

    assert transport.live is False
    assert all(call[0] in ("create_job", "get_job", "list_tasks", "cancel_job")
               for call in transport.calls)
