#!/usr/bin/env python3

# Copyright (C) 2019 Christoph Gorgulla
#
# This file is part of AdaptiveFlow.
#
# AdaptiveFlow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# AdaptiveFlow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AdaptiveFlow.  If not, see <https://www.gnu.org/licenses/>.

# ---------------------------------------------------------------------------
#
# Description: Native Google Cloud Batch scheduler support for AdaptiveFlow.
#
#   This module owns everything about the gcpbatch batch system that is not
#   worker-side I/O:
#
#     * deterministic job identity and array splitting
#     * rendering the Batch job resource (read-only preview included)
#     * the injected transport boundary, with a live transport that is
#       disabled unless explicitly enabled, plus an in-memory fake used by
#       the offline test suite
#     * submission with idempotency, lifecycle reconciliation and
#       cancellation of the recorded job only
#     * output manifest reconciliation against the expected subjobs
#
#   Nothing in this module performs a Google API call unless a live
#   transport is constructed, which requires gcp_batch_live_transport=1
#   in the workflow configuration.
#
#   The module is also usable as a command line tool:
#
#     ./afvs_gcpbatch.py preview  --workunit 1
#     ./afvs_gcpbatch.py status   --workunit 1
#     ./afvs_gcpbatch.py cancel   --workunit 1
#     ./afvs_gcpbatch.py manifest --workunit 1
#
# Revision history:
# 2026-11-18  Original version
#
# ---------------------------------------------------------------------------

import argparse
import copy
import hashlib
import json
import logging
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

from afvs_gcs import (  # noqa: E402  (path set up above so the worker copy is reused)
    LocalObjectStore,
    ObjectNotFound,
    ObjectStoreError,
    object_store_from_env,
    format_gcs_uri,
    validate_object_name,
)

logger = logging.getLogger(__name__)

BATCH_SYSTEM = "gcpbatch"
STORAGE_MODE = "gcs"

#: Google Cloud Batch caps the number of tasks in a single job. AdaptiveFlow
#: splits a workunit across several Batch jobs when it would exceed the
#: configured array size, which must never exceed this value.
BATCH_MAX_TASK_COUNT = 100000

#: Job IDs must match [a-z]([a-z0-9-]{0,61}[a-z0-9])? per the Batch API.
JOB_ID_MAX_LENGTH = 63
JOB_ID_RE = re.compile(r'^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$')

#: Terminal provider job states.
TERMINAL_JOB_STATES = ("SUCCEEDED", "FAILED", "CANCELLED", "DELETION_IN_PROGRESS")
#: Terminal provider task states.
TERMINAL_TASK_STATES = ("SUCCEEDED", "FAILED", "UNEXECUTED")

#: Configuration keys required when batchsystem=gcpbatch.
REQUIRED_CONFIG_KEYS = (
    'gcp_project',
    'gcp_region',
    'gcp_batch_array_job_size',
    'gcp_batch_machine_type',
    'gcp_batch_worker_image',
    'gcp_batch_subjob_vcpus',
    'gcp_batch_subjob_memory',
    'gcp_batch_subjob_timeout',
)

DEFAULTS = {
    'gcp_batch_job_prefix': 'afvs',
    'gcp_batch_subjob_retry_count': '1',
    'gcp_batch_parallelism': '0',
    'gcp_batch_provisioning_model': 'STANDARD',
    'gcp_batch_boot_disk_mib': '0',
    'gcp_batch_service_account': '',
    'gcp_batch_network': '',
    'gcp_batch_subnetwork': '',
    'gcp_batch_no_external_ip': '1',
    'gcp_batch_live_transport': '0',
    'gcp_batch_task_scratch_path': '/mnt/scratch',
}


class LiveTransportDisabled(Exception):
    """Raised when a live Google Batch call is attempted while disabled.

    The shipped configuration disables the live transport. Enabling it is a
    separate, explicit decision because every live submission can incur
    charges in the user's Google Cloud project.
    """


class DuplicateSubmission(Exception):
    """Raised when a submission is attempted for an already recorded job."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def config_defaults_applied(config):
    """Returns a copy of the configuration with gcpbatch defaults filled in."""
    merged = dict(config)
    for key, value in DEFAULTS.items():
        if key not in merged or merged[key] == "":
            merged[key] = value
    return merged


def check_config(config):
    """Validates the gcpbatch portion of a workflow configuration.

    Args:
        config (dict): Parsed all.ctrl / workflow config.json contents.

    Returns:
        A list of human readable problem strings. Empty when the
        configuration is usable.
    """
    problems = []
    merged = config_defaults_applied(config)

    for key in REQUIRED_CONFIG_KEYS:
        if not str(merged.get(key, "")).strip():
            problems.append(f"* '{key}' must be set if batchsystem is 'gcpbatch'")

    array_size = _optional_int(merged.get('gcp_batch_array_job_size'))
    if array_size is not None and (array_size < 1 or array_size > BATCH_MAX_TASK_COUNT):
        problems.append(
            f"* 'gcp_batch_array_job_size' must be between 1 and {BATCH_MAX_TASK_COUNT}")

    vcpus = _optional_int(merged.get('gcp_batch_subjob_vcpus'))
    if vcpus is not None and vcpus < 1:
        problems.append("* 'gcp_batch_subjob_vcpus' must be at least 1")

    memory = _optional_int(merged.get('gcp_batch_subjob_memory'))
    if memory is not None and memory < 1:
        problems.append("* 'gcp_batch_subjob_memory' must be at least 1 (MiB)")

    timeout = _optional_int(merged.get('gcp_batch_subjob_timeout'))
    if timeout is not None and timeout < 1:
        problems.append("* 'gcp_batch_subjob_timeout' must be at least 1 (seconds)")

    threads_to_use = _optional_int(merged.get('threads_to_use'))
    if vcpus is not None and threads_to_use is not None and threads_to_use > vcpus * 2:
        problems.append(
            "* 'threads_to_use' is more than twice 'gcp_batch_subjob_vcpus'; "
            "the Batch task will be oversubscribed")

    if merged.get('job_storage_mode') != STORAGE_MODE:
        problems.append(
            "* 'job_storage_mode' must be 'gcs' if batchsystem is 'gcpbatch' "
            "(Batch tasks have no shared filesystem by default)")
    else:
        if not str(merged.get('object_store_job_bucket', "")).strip():
            problems.append("* 'object_store_job_bucket' must be set if job_storage_mode is 'gcs'")
        if not str(merged.get('object_store_job_prefix', "")).strip():
            problems.append("* 'object_store_job_prefix' must be set if job_storage_mode is 'gcs'")

    data_storage_mode = merged.get('data_storage_mode')
    if data_storage_mode == STORAGE_MODE:
        if not str(merged.get('object_store_data_bucket', "")).strip():
            problems.append("* 'object_store_data_bucket' must be set if data_storage_mode is 'gcs'")
        if not str(merged.get('object_store_data_collection_prefix', "")).strip():
            problems.append(
                "* 'object_store_data_collection_prefix' must be set if data_storage_mode is 'gcs'")

    return problems


def cross_provider_warnings(config):
    """Reports configurations that read the ligand library from another cloud.

    Running Batch tasks in Google Cloud while the ligand library lives in S3
    works, but every collection download is a cross-provider read: the user
    pays AWS egress and the read is slower than an in-region read. The
    warning names the cost so it is not discovered on an invoice.
    """
    warnings = []
    if config.get('batchsystem') != BATCH_SYSTEM:
        return warnings

    data_storage_mode = config.get('data_storage_mode')
    if data_storage_mode == "s3":
        warnings.append(
            "Ligand library reads are cross-provider: data_storage_mode=s3 with "
            "batchsystem=gcpbatch. Each collection is read from AWS S3 into Google Cloud, "
            "which incurs S3 GET charges plus AWS egress on the library owner's account "
            "and adds latency. Mirror the library into GCS to avoid both.")
    elif data_storage_mode == "sharedfs":
        warnings.append(
            "data_storage_mode=sharedfs with batchsystem=gcpbatch requires every Batch task "
            "to mount that filesystem; no such mount is configured by AdaptiveFlow.")

    return warnings


def _optional_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Identity and array splitting
# ---------------------------------------------------------------------------

def sanitize_job_id(value):
    """Coerces a string into something the Batch API accepts as a job ID."""
    lowered = str(value).lower()
    cleaned = re.sub(r'[^a-z0-9-]+', '-', lowered).strip('-')
    cleaned = re.sub(r'-{2,}', '-', cleaned)
    if not cleaned:
        cleaned = "job"
    if not cleaned[0].isalpha():
        cleaned = f"j{cleaned}"
    return cleaned[:JOB_ID_MAX_LENGTH].rstrip('-')


def build_job_id(config, workunit_id, part_index):
    """Builds the deterministic Batch job ID for one workunit part.

    The ID is a pure function of the job name, workunit and part index. A
    retried submission therefore targets the same provider job, so a
    duplicate create is rejected by the API as ALREADY_EXISTS instead of
    launching a second copy of the same work.

    Args:
        config (dict): Workflow configuration.
        workunit_id (int|str): AFVS workunit ID.
        part_index (int): Zero-based index of the split part.

    Returns:
        A Batch-legal job ID string.
    """
    raw_job_name = str(config.get('job_name') or config.get('job_letter') or "job")

    prefix = sanitize_job_id(config.get('gcp_batch_job_prefix') or DEFAULTS['gcp_batch_job_prefix'])
    job_name = sanitize_job_id(raw_job_name)
    suffix = f"-{workunit_id}-{part_index}"

    budget = JOB_ID_MAX_LENGTH - len(prefix) - 1 - len(suffix)
    if budget < 1:
        raise ValueError(
            f"gcp_batch_job_prefix '{prefix}' leaves no room for a job ID; shorten it")

    if len(job_name) > budget:
        # Keep the ID readable and still collision free by folding the
        # overflow into a short digest. The digest is taken from the
        # original job name, not from the sanitized and truncated form,
        # because two long names can share a truncation but must not share
        # a job ID.
        digest = hashlib.sha256(raw_job_name.encode()).hexdigest()[:8]
        keep = max(1, budget - len(digest) - 1)
        job_name = f"{job_name[:keep]}-{digest}"[:budget].rstrip('-')

    job_id = f"{prefix}-{job_name}{suffix}"
    if not JOB_ID_RE.match(job_id):
        job_id = sanitize_job_id(job_id)
    return job_id


def build_run_tag(config, workunit_id, part_index):
    """Builds the unique run tag used to find orphaned submissions.

    The tag is recorded before the provider call and attached to the job as
    a label, so a worker that dies between submission and receipt storage
    can find the job it created instead of submitting a second one.
    """
    source = "/".join([
        str(config.get('job_name') or config.get('job_letter') or ""),
        str(workunit_id),
        str(part_index),
    ])
    return hashlib.sha256(source.encode()).hexdigest()[:32]


def job_resource_name(config, job_id):
    """Returns the fully qualified Batch job resource name."""
    return f"projects/{config['gcp_project']}/locations/{config['gcp_region']}/jobs/{job_id}"


def job_parent(config):
    """Returns the Batch job collection parent for this project and region."""
    return f"projects/{config['gcp_project']}/locations/{config['gcp_region']}"


def plan_workunit_parts(subjob_ids, max_tasks_per_job):
    """Splits a workunit's subjobs into deterministic Batch job parts.

    Google Cloud Batch bounds the task count of a single job, and sites
    bound it further with gcp_batch_array_job_size. Oversized workunits are
    split into consecutive parts; each part records the offset that maps
    BATCH_TASK_INDEX back onto the AFVS subjob ID.

    Args:
        subjob_ids (iterable): Subjob IDs in the workunit, in AFVS order.
        max_tasks_per_job (int): Maximum tasks per Batch job.

    Returns:
        A list of dicts with part_index, subjob_index_offset, task_count
        and subjob_ids.
    """
    ordered = [str(subjob_id) for subjob_id in subjob_ids]
    if max_tasks_per_job < 1:
        raise ValueError("max_tasks_per_job must be at least 1")
    if not ordered:
        return []

    parts = []
    for part_index, start in enumerate(range(0, len(ordered), max_tasks_per_job)):
        chunk = ordered[start:start + max_tasks_per_job]
        parts.append({
            'part_index': part_index,
            'subjob_index_offset': start,
            'task_count': len(chunk),
            'subjob_ids': chunk,
        })
    return parts


def subjob_id_for_task(part, task_index):
    """Maps a BATCH_TASK_INDEX back onto the AFVS subjob ID for a part.

    Args:
        part (dict): A part produced by plan_workunit_parts().
        task_index (int): The zero-based BATCH_TASK_INDEX of the task.

    Returns:
        The AFVS subjob ID as a string.

    Raises:
        IndexError: If the task index is outside the part.
    """
    if task_index < 0 or task_index >= part['task_count']:
        raise IndexError(
            f"task index {task_index} is outside part {part['part_index']} "
            f"(task_count={part['task_count']})")
    return str(part['subjob_index_offset'] + task_index)


# ---------------------------------------------------------------------------
# Object layout
# ---------------------------------------------------------------------------

def get_collection_hash(collection_name, collection_number):
    """Reproduces the AFVS hash addressing digest for a collection."""
    formatted = f"{int(collection_number):07}"
    return hashlib.sha256(f"{collection_name}/{formatted}".encode()).hexdigest()


def gen_job_input_object_name(config, workunit_id):
    """Returns the object name of a workunit's input archive.

    Mirrors the S3 layout so that the two clouds stay structurally
    identical, including the hash addressing mode.
    """
    if config.get('object_store_job_addressing_mode') == "hash":
        hash_string = get_collection_hash(config['job_letter'], workunit_id)
        parts = [
            config['object_store_job_prefix'],
            hash_string[0:2],
            hash_string[2:4],
            config['job_letter'],
            "input",
            "tasks",
            f"{workunit_id}.tar.gz",
        ]
    else:
        parts = [
            config['object_store_job_prefix_full'],
            "input",
            "tasks",
            f"{workunit_id}.tar.gz",
        ]
    return validate_object_name("/".join(str(part).strip("/") for part in parts))


def gen_gcs_collection_object_name(config, collection_name, collection_number):
    """Returns the object name of a ligand collection archive in GCS.

    Both AFVS addressing modes are preserved so a GCS mirror of a library
    can be a byte-for-byte copy of its S3 original.
    """
    if config.get('object_store_data_collection_addressing_mode') == "hash":
        format_type = config['ligand_library_format']
        hash_string = get_collection_hash(collection_name, int(collection_number))

        identifier = config.get('object_store_data_collection_identifier', "")
        remote_dir = [
            config['object_store_data_collection_prefix'],
            hash_string[0:2],
            hash_string[2:4],
        ]
        if identifier != "":
            remote_dir.append(identifier)
        remote_dir.extend([format_type, collection_name])

        object_name = "/".join(str(part).strip("/") for part in remote_dir)
        object_name = f"{object_name}/{int(collection_number):07}.tar.gz"
    else:
        collection_name_dir = collection_name.replace("_", "/")
        object_name = "/".join([
            str(config['object_store_data_collection_prefix']).strip("/"),
            collection_name_dir,
            f"{collection_number}.tar.gz",
        ])

    return validate_object_name(object_name)


def job_output_prefix(config):
    """Returns the object prefix that holds all output for this job."""
    prefix = str(config['object_store_job_prefix']).strip("/")
    job_name = config.get('job_name') or config['job_letter']
    return f"{prefix}/{job_name}"


def gen_output_object_name(config, scenario_key, content_type, workunit_id, subjob_id, extension):
    """Returns the canonical output object name for a subjob artifact.

    The canonical layout is identical to the AWS Batch layout, which is what
    lets the shared CSV/Parquet ranking path read GCP results unchanged.
    """
    base = job_output_prefix(config)
    if scenario_key is not None:
        name = f"{base}/{scenario_key}/{content_type}/{workunit_id}/{subjob_id}.{extension}"
    else:
        name = f"{base}/{content_type}/{workunit_id}/{subjob_id}.{extension}"
    return validate_object_name(name)


def gen_attempt_object_name(config, workunit_id, subjob_id, attempt_id, artifact):
    """Returns the per-attempt object name for a task artifact.

    Retries and interrupted attempts each publish under their own attempt
    prefix, so a failed attempt never overwrites the evidence of an earlier
    one and a late-finishing attempt cannot corrupt a completed result.
    """
    base = job_output_prefix(config)
    name = f"{base}/attempts/{workunit_id}/{subjob_id}/{attempt_id}/{artifact}"
    return validate_object_name(name)


def gen_manifest_object_name(config, workunit_id, subjob_id):
    """Returns the object name of a subjob's output manifest."""
    base = job_output_prefix(config)
    return validate_object_name(f"{base}/manifests/{workunit_id}/{subjob_id}.json")


# ---------------------------------------------------------------------------
# Job rendering
# ---------------------------------------------------------------------------

def task_environment(config, workunit_id, part, extra=None):
    """Builds the environment every task in a part receives.

    BATCH_TASK_INDEX is supplied by Batch at runtime; the entrypoint adds
    AFVS_SUBJOB_INDEX_OFFSET to it to recover the AFVS subjob ID.
    """
    variables = {
        'AFVS_RUN_MODE': BATCH_SYSTEM,
        'AFVS_JOB_STORAGE_MODE': STORAGE_MODE,
        'AFVS_VCPUS': str(config['threads_to_use']),
        'AFVS_TMP_PATH': str(config.get('tempdir_default', '/dev/shm')),
        'AFVS_RUN_SEQUENTIAL': "0",
        'AFVS_WORKUNIT': str(workunit_id),
        'AFVS_SUBJOB_INDEX_OFFSET': str(part['subjob_index_offset']),
        'AFVS_CONFIG_JOB_GCS_BUCKET': str(config['object_store_job_bucket']),
        'AFVS_CONFIG_JOB_GCS_OBJECT': gen_job_input_object_name(config, workunit_id),
        'AFVS_GCP_PROJECT': str(config['gcp_project']),
        'AFVS_TOOLS_PATH': "/opt/af/tools/bin",
    }
    if extra:
        variables.update({key: str(value) for key, value in extra.items()})
    return variables


def render_batch_job(config, workunit_id, part, run_tag=None, extra_environment=None):
    """Renders the Google Cloud Batch job resource for one workunit part.

    The result is a plain dict in Batch REST shape. It is what the live
    transport submits and what `afvs_gcpbatch.py preview` prints, so the
    preview is the submitted document and not a separate approximation.

    Args:
        config (dict): Workflow configuration.
        workunit_id (int|str): AFVS workunit ID.
        part (dict): A part from plan_workunit_parts().
        run_tag (str): Optional unique run tag for reconciliation.
        extra_environment (dict): Optional additional task environment.

    Returns:
        A dict describing the Batch job.
    """
    config = config_defaults_applied(config)

    vcpus = int(config['gcp_batch_subjob_vcpus'])
    memory_mib = int(config['gcp_batch_subjob_memory'])
    timeout_seconds = int(config['gcp_batch_subjob_timeout'])
    retry_count = int(config['gcp_batch_subjob_retry_count'])
    task_count = int(part['task_count'])

    configured_parallelism = int(config['gcp_batch_parallelism'])
    parallelism = task_count if configured_parallelism <= 0 else min(configured_parallelism,
                                                                    task_count)

    labels = {
        'afvs-job': sanitize_job_id(config.get('job_name') or config['job_letter']),
        'afvs-workunit': str(workunit_id),
        'afvs-part': str(part['part_index']),
    }
    if run_tag:
        labels['afvs-run-tag'] = run_tag

    compute_resource = {
        'cpuMilli': vcpus * 1000,
        'memoryMib': memory_mib,
    }
    boot_disk_mib = int(config['gcp_batch_boot_disk_mib'])
    if boot_disk_mib > 0:
        compute_resource['bootDiskMib'] = boot_disk_mib

    instance_policy = {
        'machineType': str(config['gcp_batch_machine_type']),
        'provisioningModel': str(config['gcp_batch_provisioning_model']).upper(),
    }

    allocation_policy = {
        'instances': [{'policy': instance_policy}],
        'labels': labels,
    }

    service_account = str(config['gcp_batch_service_account']).strip()
    if service_account:
        allocation_policy['serviceAccount'] = {'email': service_account}

    network = str(config['gcp_batch_network']).strip()
    subnetwork = str(config['gcp_batch_subnetwork']).strip()
    if network or subnetwork:
        interface = {}
        if network:
            interface['network'] = network
        if subnetwork:
            interface['subnetwork'] = subnetwork
        if str(config['gcp_batch_no_external_ip']) == "1":
            interface['noExternalIpAddress'] = True
        allocation_policy['network'] = {'networkInterfaces': [interface]}

    job = {
        'taskGroups': [{
            'taskCount': task_count,
            'parallelism': parallelism,
            'taskSpec': {
                'runnables': [{
                    'container': {
                        'imageUri': str(config['gcp_batch_worker_image']),
                        'entrypoint': "/opt/af/tools/templates/template1.gcpbatch.sh",
                        'commands': [],
                    },
                }],
                'computeResource': compute_resource,
                'maxRunDuration': f"{timeout_seconds}s",
                'maxRetryCount': retry_count,
                'environment': {
                    'variables': task_environment(config, workunit_id, part,
                                                  extra=extra_environment),
                },
            },
        }],
        'allocationPolicy': allocation_policy,
        'logsPolicy': {'destination': "CLOUD_LOGGING"},
        'labels': labels,
    }

    return job


def preview_workunit(config, workunit_id, subjob_ids):
    """Renders every Batch job a workunit would submit, without submitting.

    Returns:
        A dict with the parts, their job IDs, resource names and rendered
        job bodies, plus any cross-provider cost warnings.
    """
    config = config_defaults_applied(config)
    parts = plan_workunit_parts(subjob_ids, int(config['gcp_batch_array_job_size']))

    rendered = []
    for part in parts:
        run_tag = build_run_tag(config, workunit_id, part['part_index'])
        job_id = build_job_id(config, workunit_id, part['part_index'])
        rendered.append({
            'workunit_id': str(workunit_id),
            'part_index': part['part_index'],
            'job_id': job_id,
            'resource_name': job_resource_name(config, job_id),
            'run_tag': run_tag,
            'subjob_index_offset': part['subjob_index_offset'],
            'task_count': part['task_count'],
            'subjob_ids': part['subjob_ids'],
            'job': render_batch_job(config, workunit_id, part, run_tag=run_tag),
        })

    return {
        'parent': job_parent(config),
        'job_input_object': format_gcs_uri(config['object_store_job_bucket'],
                                           gen_job_input_object_name(config, workunit_id)),
        'parts': rendered,
        'warnings': cross_provider_warnings(config),
    }


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------

class BatchTransport:
    """The injected boundary between AdaptiveFlow and the Batch API.

    Every implementation records whether it can reach Google Cloud. The
    offline test suite asserts that `live` is False for the transports it
    uses, which is how "zero calls to live APIs" is enforced rather than
    assumed.
    """

    #: True only for transports that talk to Google Cloud.
    live = False
    #: Human readable name used in logs and persisted submission records.
    name = "abstract"

    def create_job(self, parent, job_id, job, request_id=None):
        raise NotImplementedError

    def get_job(self, name):
        raise NotImplementedError

    def list_tasks(self, job_name, task_group="group0"):
        raise NotImplementedError

    def cancel_job(self, name):
        raise NotImplementedError


class DisabledBatchTransport(BatchTransport):
    """The shipped default: refuses every call and records the intent.

    Shipping the submission path behind this transport is what keeps cloud
    spend at zero while the implementation itself is complete and
    exercised. Turning it off is a separate, explicit decision.
    """

    live = False
    name = "disabled"

    def __init__(self):
        self.intents = []

    def _refuse(self, operation, detail):
        self.intents.append({
            'operation': operation,
            'detail': detail,
            'recorded_at': datetime.now(timezone.utc).isoformat(),
        })
        raise LiveTransportDisabled(
            f"Live Google Cloud Batch transport is disabled; refused {operation} ({detail}). "
            "Set gcp_batch_live_transport=1 in all.ctrl to enable it. Enabling it allows "
            "submissions that incur charges in your Google Cloud project.")

    def create_job(self, parent, job_id, job, request_id=None):
        self._refuse("create_job", f"{parent}/jobs/{job_id}")

    def get_job(self, name):
        self._refuse("get_job", name)

    def list_tasks(self, job_name, task_group="group0"):
        self._refuse("list_tasks", job_name)

    def cancel_job(self, name):
        self._refuse("cancel_job", name)


class FakeBatchTransport(BatchTransport):
    """In-memory Batch transport used by the offline test suite.

    It models the parts of the provider contract AdaptiveFlow depends on:
    deterministic job IDs reject duplicates, tasks move through states, and
    cancellation only affects the named job.
    """

    live = False
    name = "fake"

    def __init__(self, clock=None):
        self.jobs = {}
        self.calls = []
        self.request_ids = {}
        self._clock = clock or (lambda: time.time())

    # -- helpers used by tests -------------------------------------------------

    def set_task_state(self, job_name, task_index, state):
        job = self.jobs[job_name]
        job['tasks'][task_index]['state'] = state
        self._recompute_job_state(job)

    def set_job_state(self, job_name, state):
        self.jobs[job_name]['state'] = state

    def _recompute_job_state(self, job):
        if job['state'] in ("CANCELLED", "CANCELLATION_IN_PROGRESS"):
            return
        states = [task['state'] for task in job['tasks']]
        if all(state == "SUCCEEDED" for state in states):
            job['state'] = "SUCCEEDED"
        elif any(state == "FAILED" for state in states):
            job['state'] = "FAILED" if all(
                state in TERMINAL_TASK_STATES for state in states) else "RUNNING"
        elif any(state == "RUNNING" for state in states):
            job['state'] = "RUNNING"

    # -- transport contract ----------------------------------------------------

    def create_job(self, parent, job_id, job, request_id=None):
        name = f"{parent}/jobs/{job_id}"
        self.calls.append(('create_job', name, request_id))

        if name in self.jobs:
            if request_id is not None and self.request_ids.get(name) == request_id:
                # Same idempotency token: the provider replays the original
                # job rather than creating a second one.
                view = self._job_view(self.jobs[name])
                view['already_existed'] = True
                return view
            raise DuplicateSubmission(f"Job already exists: {name}")

        task_count = int(job['taskGroups'][0]['taskCount'])
        record = {
            'name': name,
            'uid': f"fake-{uuid.uuid4().hex[:12]}",
            'job': copy.deepcopy(job),
            'state': "QUEUED",
            'create_time': self._clock(),
            'tasks': [{'index': index, 'state': "PENDING", 'attempts': 0}
                      for index in range(task_count)],
        }
        self.jobs[name] = record
        if request_id is not None:
            self.request_ids[name] = request_id
        return self._job_view(record)

    def get_job(self, name):
        self.calls.append(('get_job', name, None))
        if name not in self.jobs:
            raise KeyError(f"No such job: {name}")
        return self._job_view(self.jobs[name])

    def list_tasks(self, job_name, task_group="group0"):
        self.calls.append(('list_tasks', job_name, task_group))
        if job_name not in self.jobs:
            raise KeyError(f"No such job: {job_name}")
        return [
            {
                'name': f"{job_name}/taskGroups/{task_group}/tasks/{task['index']}",
                'index': task['index'],
                'state': task['state'],
                'attempts': task['attempts'],
            }
            for task in self.jobs[job_name]['tasks']
        ]

    def cancel_job(self, name):
        self.calls.append(('cancel_job', name, None))
        if name not in self.jobs:
            raise KeyError(f"No such job: {name}")
        job = self.jobs[name]
        job['state'] = "CANCELLED"
        for task in job['tasks']:
            if task['state'] not in TERMINAL_TASK_STATES:
                task['state'] = "UNEXECUTED"
        return self._job_view(job)

    def _job_view(self, record):
        return {
            'name': record['name'],
            'uid': record['uid'],
            'state': record['state'],
            'task_count': len(record['tasks']),
            'job': copy.deepcopy(record['job']),
        }


class GoogleBatchTransport(BatchTransport):
    """Live Google Cloud Batch transport.

    Constructing this class is the only way AdaptiveFlow reaches the Batch
    API. It refuses to be built unless the caller passes enabled=True, which
    `transport_from_config` only does when gcp_batch_live_transport=1.
    """

    live = True
    name = "google"

    def __init__(self, client=None, enabled=False):
        if not enabled:
            raise LiveTransportDisabled(
                "Refusing to construct the live Google Cloud Batch transport: "
                "set gcp_batch_live_transport=1 in all.ctrl to enable live submission.")
        if client is not None:
            self._client = client
        else:
            try:
                from google.cloud import batch_v1
            except ImportError as error:  # pragma: no cover - depends on env
                raise RuntimeError(
                    "google-cloud-batch is required for live submission. "
                    "Install it with 'pip install google-cloud-batch'.") from error
            self._client = batch_v1.BatchServiceClient()

    def create_job(self, parent, job_id, job, request_id=None):  # pragma: no cover - live API
        from google.api_core import exceptions as api_exceptions
        from google.cloud import batch_v1
        from google.protobuf import json_format

        job_message = json_format.ParseDict(job, batch_v1.Job()._pb)
        request = batch_v1.CreateJobRequest(
            parent=parent,
            job_id=job_id,
            job=batch_v1.Job.wrap(job_message),
        )
        if request_id is not None:
            request.request_id = request_id

        try:
            response = self._client.create_job(request=request)
        except api_exceptions.AlreadyExists as error:
            raise DuplicateSubmission(f"Job already exists: {parent}/jobs/{job_id}") from error

        return {
            'name': response.name,
            'uid': response.uid,
            'state': response.status.state.name,
            'task_count': response.task_groups[0].task_count if response.task_groups else 0,
            'job': job,
        }

    def get_job(self, name):  # pragma: no cover - live API
        response = self._client.get_job(name=name)
        return {
            'name': response.name,
            'uid': response.uid,
            'state': response.status.state.name,
            'task_count': response.task_groups[0].task_count if response.task_groups else 0,
            'job': None,
        }

    def list_tasks(self, job_name, task_group="group0"):  # pragma: no cover - live API
        parent = f"{job_name}/taskGroups/{task_group}"
        tasks = []
        for task in self._client.list_tasks(parent=parent):
            index = int(str(task.name).rsplit("/", 1)[-1])
            tasks.append({
                'name': task.name,
                'index': index,
                'state': task.status.state.name,
                'attempts': len(task.status.status_events),
            })
        return sorted(tasks, key=lambda item: item['index'])

    def cancel_job(self, name):  # pragma: no cover - live API
        from google.cloud import batch_v1

        operation = self._client.cancel_job(request=batch_v1.CancelJobRequest(name=name))
        operation.result()
        return {'name': name, 'state': "CANCELLATION_IN_PROGRESS"}


def transport_from_config(config, client=None):
    """Returns the transport the configuration asks for.

    The live transport is constructed only when gcp_batch_live_transport=1.
    Everything else gets the disabled transport, which records intents and
    raises LiveTransportDisabled.
    """
    if str(config.get('gcp_batch_live_transport', "0")).strip() == "1":
        logger.warning(
            "Live Google Cloud Batch transport is enabled; submissions can incur charges")
        return GoogleBatchTransport(client=client, enabled=True)
    return DisabledBatchTransport()


# ---------------------------------------------------------------------------
# Submission, reconciliation and cancellation
# ---------------------------------------------------------------------------

def submission_intent(config, workunit_id, part):
    """Builds the record that must be persisted before any provider call.

    Persisting the intent first is what makes recovery possible: if the
    process dies during submission, the recorded job ID and run tag
    identify whatever the provider may already have created.
    """
    job_id = build_job_id(config, workunit_id, part['part_index'])
    return {
        'provider': "gcpbatch",
        'workunit_id': str(workunit_id),
        'part_index': part['part_index'],
        'job_id': job_id,
        'resource_name': job_resource_name(config, job_id),
        'run_tag': build_run_tag(config, workunit_id, part['part_index']),
        'request_id': str(uuid.uuid5(uuid.NAMESPACE_URL,
                                     f"afvs/{job_id}")),
        'subjob_index_offset': part['subjob_index_offset'],
        'task_count': part['task_count'],
        'subjob_ids': list(part['subjob_ids']),
        'af_job_status': "SUBMISSION_INTENT",
        'intent_recorded_at': datetime.now(timezone.utc).isoformat(),
    }


def submit_workunit(config, transport, workunit_id, subjob_ids, persist_intent=None,
                    recorded_parts=None):
    """Submits one AFVS workunit as one or more Google Cloud Batch jobs.

    Args:
        config (dict): Workflow configuration.
        transport (BatchTransport): Injected transport.
        workunit_id (int|str): AFVS workunit ID.
        subjob_ids (iterable): Subjob IDs in the workunit.
        persist_intent (callable): Optional callback invoked with each
            submission intent before the provider call is made.
        recorded_parts (dict): Optional mapping of part index to an already
            recorded submission, used to resume an interrupted submission.

    Returns:
        A list of submission records, one per part.
    """
    config = config_defaults_applied(config)
    parts = plan_workunit_parts(subjob_ids, int(config['gcp_batch_array_job_size']))
    recorded_parts = recorded_parts or {}
    parent = job_parent(config)

    records = []
    for part in parts:
        existing = recorded_parts.get(part['part_index']) or recorded_parts.get(
            str(part['part_index']))
        record = dict(existing) if existing else submission_intent(config, workunit_id, part)

        if existing and existing.get('af_job_status') == "SUBMITTED":
            logger.info("Part %s of workunit %s was already submitted as %s",
                        part['part_index'], workunit_id, existing.get('resource_name'))
            records.append(record)
            continue

        if persist_intent is not None:
            # A snapshot, so that the persisted intent stays an intent even
            # after this record is updated with the provider's response.
            # Recovery depends on being able to tell the two apart.
            persist_intent(dict(record))

        job_body = render_batch_job(config, workunit_id, part, run_tag=record['run_tag'])

        try:
            response = transport.create_job(parent, record['job_id'], job_body,
                                            request_id=record['request_id'])
            if response.get('already_existed'):
                # The provider recognised the idempotency token and
                # replayed the original job instead of creating a second.
                logger.warning("Job %s was replayed by the provider for request %s",
                               record['resource_name'], record['request_id'])
                record['adopted_existing_job'] = True
        except DuplicateSubmission:
            # The job ID is already taken, which means this work was
            # submitted by an earlier attempt whose idempotency token is
            # gone. Adopt that job rather than creating a second copy.
            logger.warning("Job %s already exists at the provider; reconciling instead",
                           record['resource_name'])
            response = transport.get_job(record['resource_name'])
            record['adopted_existing_job'] = True

        record['af_job_status'] = "SUBMITTED"
        record['provider_job_name'] = response.get('name', record['resource_name'])
        record['provider_job_uid'] = response.get('uid')
        record['provider_state'] = response.get('state', "QUEUED")
        record['submitted_at'] = datetime.now(timezone.utc).isoformat()
        records.append(record)

    return records


def reconcile_workunit(config, transport, submission_records):
    """Reads provider state for a workunit's recorded jobs.

    Only recorded resource names are queried, so reconciliation can never
    touch a job this run did not create.

    Returns:
        A dict with per-part provider state and an aggregate task state
        summary keyed by Batch task state.
    """
    parts = []
    summary = {}
    missing = []

    for record in submission_records:
        name = record.get('provider_job_name') or record.get('resource_name')
        part_view = {
            'part_index': record.get('part_index'),
            'job_id': record.get('job_id'),
            'resource_name': name,
            'subjob_index_offset': record.get('subjob_index_offset', 0),
            'task_count': record.get('task_count', 0),
        }

        try:
            job = transport.get_job(name)
        except KeyError:
            part_view['provider_state'] = "NOT_FOUND"
            part_view['tasks'] = []
            missing.append(name)
            parts.append(part_view)
            continue

        part_view['provider_state'] = job.get('state', "STATE_UNSPECIFIED")

        tasks = transport.list_tasks(name)
        task_views = []
        for task in tasks:
            subjob_id = str(int(part_view['subjob_index_offset']) + int(task['index']))
            task_views.append({
                'task_index': task['index'],
                'subjob_id': subjob_id,
                'state': task['state'],
                'attempts': task.get('attempts', 0),
            })
            summary[task['state']] = summary.get(task['state'], 0) + 1

        part_view['tasks'] = task_views
        parts.append(part_view)

    terminal = all(part.get('provider_state') in TERMINAL_JOB_STATES + ("NOT_FOUND",)
                   for part in parts) if parts else False

    return {
        'parts': parts,
        'task_state_summary': summary,
        'all_parts_terminal': terminal,
        'missing_jobs': missing,
    }


def cancel_workunit(config, transport, submission_records):
    """Cancels only the Batch jobs recorded for this workunit.

    Returns:
        A list of per-part cancellation outcomes.
    """
    outcomes = []
    for record in submission_records:
        name = record.get('provider_job_name') or record.get('resource_name')
        if not name:
            outcomes.append({'part_index': record.get('part_index'),
                             'resource_name': None,
                             'outcome': "no_recorded_job"})
            continue
        try:
            response = transport.cancel_job(name)
        except KeyError:
            outcomes.append({'part_index': record.get('part_index'),
                             'resource_name': name,
                             'outcome': "not_found"})
            continue
        outcomes.append({
            'part_index': record.get('part_index'),
            'resource_name': name,
            'outcome': "cancellation_requested",
            'provider_state': response.get('state'),
            'requested_at': datetime.now(timezone.utc).isoformat(),
        })
    return outcomes


# ---------------------------------------------------------------------------
# Output manifests
# ---------------------------------------------------------------------------

def read_manifest(config, object_store, workunit_id, subjob_id):
    """Reads one subjob output manifest, or returns None when absent."""
    import tempfile

    object_name = gen_manifest_object_name(config, workunit_id, subjob_id)
    bucket = config['object_store_job_bucket']

    with tempfile.TemporaryDirectory() as temp_dir:
        local_path = os.path.join(temp_dir, "manifest.json")
        try:
            object_store.download_file(bucket, object_name, local_path)
        except ObjectNotFound:
            return None
        with open(local_path, "r") as read_file:
            return json.load(read_file)


def reconcile_manifests(config, object_store, workunit_id, expected_subjob_ids):
    """Compares published manifests against the expected subjobs.

    A scheduler that reports success is not enough: the campaign is only
    complete when every expected subjob published a finalized manifest whose
    recorded objects exist and whose docking counts are known. Empty,
    partial and complete states are reported distinctly.

    Returns:
        A dict with per-subjob status, aggregate docking counts and an
        overall state of 'empty', 'partial' or 'complete'.
    """
    subjobs = {}
    present = 0
    dockings = {'total': 0, 'succeeded': 0, 'failed': 0, 'skipped': 0}

    for subjob_id in [str(value) for value in expected_subjob_ids]:
        manifest = read_manifest(config, object_store, workunit_id, subjob_id)
        if manifest is None:
            subjobs[subjob_id] = {'status': "missing"}
            continue

        objects = manifest.get('objects', [])
        missing_objects = []
        for entry in objects:
            bucket = entry.get('bucket', config['object_store_job_bucket'])
            if not object_store.exists(bucket, entry['object_name']):
                missing_objects.append(entry['object_name'])

        counts = manifest.get('dockings', {})
        for key in dockings:
            dockings[key] += int(counts.get(key, 0) or 0)

        status = "complete" if not missing_objects else "objects_missing"
        if status == "complete":
            present += 1

        subjobs[subjob_id] = {
            'status': status,
            'attempt_id': manifest.get('attempt_id'),
            'finalized_at': manifest.get('finalized_at'),
            'objects': len(objects),
            'missing_objects': missing_objects,
            'dockings': counts,
        }

    expected_count = len(list(expected_subjob_ids))
    if present == 0:
        state = "empty"
    elif present < expected_count:
        state = "partial"
    else:
        state = "complete"

    return {
        'workunit_id': str(workunit_id),
        'expected_subjobs': expected_count,
        'complete_subjobs': present,
        'state': state,
        'dockings': dockings,
        'subjobs': subjobs,
    }


# ---------------------------------------------------------------------------
# Command line interface
# ---------------------------------------------------------------------------

def _load_workflow(status_path="../workflow/status.json", config_path="../workflow/config.json"):
    with open(config_path, "r") as read_file:
        config = json.load(read_file)
    status = None
    if Path(status_path).is_file():
        with open(status_path, "r") as read_file:
            status = json.load(read_file)
    return config, status


def _workunit_subjob_ids(status, workunit_id):
    workunits = (status or {}).get('workunits', {})
    workunit = workunits.get(str(workunit_id))
    if workunit is None:
        raise SystemExit(f"Workunit {workunit_id} was not found in ../workflow/status.json")
    return sorted(workunit.get('subjobs', {}).keys(), key=lambda value: int(value))


def _submission_records(status, workunit_id):
    workunit = (status or {}).get('workunits', {}).get(str(workunit_id), {})
    records = workunit.get('gcp_batch_parts')
    if not records:
        raise SystemExit(
            f"Workunit {workunit_id} has no recorded Google Cloud Batch submission")
    if isinstance(records, dict):
        return [records[key] for key in sorted(records, key=lambda value: int(value))]
    return records


def main(argv=None):
    logging.basicConfig(level=os.environ.get('AFVS_LOGLEVEL', 'INFO').upper())

    parser = argparse.ArgumentParser(
        description="Inspect and control native Google Cloud Batch submissions")
    parser.add_argument('--config', default="../workflow/config.json",
                        help="Path to the workflow config.json")
    parser.add_argument('--status', default="../workflow/status.json",
                        help="Path to the workflow status.json")
    parser.add_argument('--local-object-store', default=None,
                        help="Use a filesystem-backed object store rooted here instead of GCS")

    subparsers = parser.add_subparsers(dest="command", required=True)

    preview_parser = subparsers.add_parser(
        "preview", help="Print the rendered Batch job JSON without submitting")
    preview_parser.add_argument('--workunit', required=True)

    status_parser = subparsers.add_parser(
        "status", help="Reconcile provider state for a submitted workunit")
    status_parser.add_argument('--workunit', required=True)

    cancel_parser = subparsers.add_parser(
        "cancel", help="Cancel the recorded Batch jobs of one workunit")
    cancel_parser.add_argument('--workunit', required=True)

    manifest_parser = subparsers.add_parser(
        "manifest", help="Reconcile published output manifests for a workunit")
    manifest_parser.add_argument('--workunit', required=True)

    args = parser.parse_args(argv)
    config, status = _load_workflow(args.status, args.config)
    config = config_defaults_applied(config)

    if config.get('batchsystem') != BATCH_SYSTEM:
        raise SystemExit(
            f"This workflow uses batchsystem={config.get('batchsystem')!r}, not {BATCH_SYSTEM!r}")

    if args.command == "preview":
        subjob_ids = _workunit_subjob_ids(status, args.workunit)
        print(json.dumps(preview_workunit(config, args.workunit, subjob_ids), indent=2))
        return 0

    if args.command == "manifest":
        object_store = object_store_from_env(project=config.get('gcp_project'),
                                             local_root=args.local_object_store)
        subjob_ids = _workunit_subjob_ids(status, args.workunit)
        print(json.dumps(
            reconcile_manifests(config, object_store, args.workunit, subjob_ids), indent=2))
        return 0

    transport = transport_from_config(config)
    records = _submission_records(status, args.workunit)

    try:
        if args.command == "status":
            print(json.dumps(reconcile_workunit(config, transport, records), indent=2))
        elif args.command == "cancel":
            print(json.dumps(cancel_workunit(config, transport, records), indent=2))
    except LiveTransportDisabled as error:
        print(f"{error}", file=sys.stderr)
        return 2

    return 0


if __name__ == '__main__':
    sys.exit(main())
