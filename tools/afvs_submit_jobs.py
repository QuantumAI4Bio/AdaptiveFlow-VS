#!/usr/bin/env python3

# Copyright (C) 2019 Christoph Gorgulla
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
# Description: Submit jobs
#
# ---------------------------------------------------------------------------


import os
import json
import boto3
import botocore
import re
import argparse
import sys
import time
from botocore.config import Config
from pathlib import Path
import shutil
import jinja2
import subprocess

import afvs_gcpbatch


def parse_config(filename):
    with open(filename, "r") as read_file:
        config = json.load(read_file)

    return config


def run_bash(config, current_workunit, jobline):

    # Get the template
    try:
        with open(config['bash_template']) as f:
            bash_template = jinja2.Template(f.read())
    except IOError as error:
        print(f"Cannot open the bash_template ({config['bash_template']})")
        raise error

    jobline_str = str(jobline)

    # how many jobs are there that we need to submit?
    subjobs_count = len(current_workunit['subjobs'])

    # Where are we putting this file?
    batch_workunit_base=Path(config['sharedfs_workunit_path']) / jobline_str
    batch_workunit_base.mkdir(parents=True, exist_ok=True)
    batch_submit_file = batch_workunit_base / "run.bash"

    template_values = {
        "job_letter": config['job_letter'],
        "job_name": config['job_name'],
        "threads_to_use": config['threads_to_use'],
        "array_start": "0",
        "array_end": (subjobs_count - 1),
        "workunit_id": jobline_str,
        "job_storage_mode": config['job_storage_mode'],
        "job_tgz": current_workunit['download_path'],
        "batch_workunit_base": batch_workunit_base.resolve().as_posix()
    }
    render_output = bash_template.render(template_values)

    try:
        with open(batch_submit_file, "w") as f:
            f.write(render_output)
    except IOError as error:
        print(f"Cannot write the workunit bash file ({batch_submit_file})")
        raise error

    with open("../workflow/run.bash", "a") as bash_out:
        bash_out.write(f"{batch_submit_file}\n")

def submit_slurm(config, client, current_workunit, jobline):


    # Get the template
    try:
        with open(config['slurm_template']) as f:
            slurm_template = jinja2.Template(f.read())
    except IOError as error:
        print(f"Cannot open the slurm_template ({config['slurm_template']})")
        raise error


    jobline_str = str(jobline)

    # how many jobs are there that we need to submit?
    subjobs_count = len(current_workunit['subjobs'])

    # Where are we putting this file?
    batch_workunit_base=Path(config['sharedfs_workunit_path']) / jobline_str
    batch_workunit_base.mkdir(parents=True, exist_ok=True)
    batch_submit_file = batch_workunit_base / "submit.slurm"


    #
    template_values = {
        "job_letter": config['job_letter'],
        "job_name": config['job_name'],
        "threads_to_use": config['threads_to_use'],
        "array_start": "0",
        "array_end": (subjobs_count - 1),
        "slurm_cpus": config['slurm_cpus'],
        "slurm_account": config['slurm_account'],
        "slurm_partition": config['slurm_partition'],
        "workunit_id": jobline_str,
        "job_storage_mode": config['job_storage_mode'],
        "slurm_array_job_throttle": config['slurm_array_job_throttle'],
        "job_tgz": current_workunit['download_path'],
        "batch_workunit_base": batch_workunit_base.resolve().as_posix()
    }
    render_output = slurm_template.render(template_values)

    try:
        with open(batch_submit_file, "w") as f:
            f.write(render_output)
    except IOError as error:
        print(f"Cannot write the workunit slurm file ({batch_submit_file})")
        raise error


    # Run the slurm submit command and capture the job ID
    # information

    cmd = [
        "sbatch",
        batch_submit_file
    ]

    try:
        ret = subprocess.run(cmd, capture_output=True,
                         text=True, timeout=int(config['slurm_job_submission_timeout']))
    except subprocess.TimeoutExpired as err:
        raise Exception("timeout on submission to sbatch")

    if ret.returncode == 0:
        match = re.search(
                r'^Submitted batch job (?P<value>[-0-9]+)', ret.stdout, flags=re.MULTILINE)
        if(match):
            matches = match.groupdict()
            job_id = int(matches['value'])
        else:
            raise Exception("sbatch returned, but cannot parse output")
    else:
        raise Exception("sbatch did not return successfully")

    current_workunit['status'] = {
        'af_job_status': 'SUBMITTED',
        'job_name': f"afvs-{config['job_letter']}-{jobline_str}", 
        'job_id': job_id
    }

    # Slow ourselves down a bit
    time.sleep(0.1)


def submit_lsf(config, client, current_workunit, jobline):

    # Get the template
    try:
        with open(config['lsf_template']) as f:
            lsf_template = jinja2.Template(f.read())
    except IOError as error:
        print(f"Cannot open the lsf_template ({config['lsf_template']})")
        raise error

    jobline_str = str(jobline)

    # how many jobs are there that we need to submit?
    subjobs_count = len(current_workunit['subjobs'])

    # Where are we putting this file?
    batch_workunit_base=Path(config['sharedfs_workunit_path']) / jobline_str
    batch_workunit_base.mkdir(parents=True, exist_ok=True)
    batch_submit_file = batch_workunit_base / "submit.lsf"

    #
    template_values = {
        "job_letter": config['job_letter'],
        "job_name": config['job_name'],
        "threads_to_use": config['threads_to_use'],
        "array_start": "1",
        "array_end": subjobs_count,
        "lsf_cpus": config['lsf_cpus'],
        "lsf_queue": config['lsf_queue'],
        "lsf_walltime": config['lsf_walltime'],
        "lsf_memory": config['lsf_memory'],
        "workunit_id": jobline_str,
        "job_storage_mode": config['job_storage_mode'],
        "lsf_array_job_throttle": config['lsf_array_job_throttle'],
        "job_tgz": current_workunit['download_path'],
        "batch_workunit_base": batch_workunit_base.resolve().as_posix()
    }
    render_output = lsf_template.render(template_values)

    try:
        with open(batch_submit_file, "w") as f:
            f.write(render_output)
    except IOError as error:
        print(f"Cannot write the workunit lsf file ({batch_submit_file})")
        raise error

    # Run the lsf submit command and capture the job ID
    # information. bsub takes the script on stdin.

    cmd = ["bsub"]

    try:
        with open(batch_submit_file, "r") as f:
            ret = subprocess.run(cmd, stdin=f, capture_output=True,
                             text=True, timeout=int(config['lsf_job_submission_timeout']))
    except subprocess.TimeoutExpired as err:
        raise Exception("timeout on submission to bsub")

    if ret.returncode == 0:
        match = re.search(
                r'^Job <(?P<value>[-0-9]+)> is submitted', ret.stdout, flags=re.MULTILINE)
        if(match):
            matches = match.groupdict()
            job_id = int(matches['value'])
        else:
            raise Exception("bsub returned, but cannot parse output")
    else:
        raise Exception("bsub did not return successfully")

    current_workunit['status'] = {
        'af_job_status': 'SUBMITTED',
        'job_name': f"afvs-{config['job_letter']}-{jobline_str}",
        'job_id': job_id
    }

    # Slow ourselves down a bit
    time.sleep(0.1)


def submit_aws_batch(config, client, current_workunit, jobline):

    jobline_str = str(jobline)

    # how many jobs are there that we need to submit?
    subjobs_count = len(current_workunit['subjobs'])

    # AWS Batch doesn't allow an array job of only 1 -- so if it's one
    # we will launch 2, but the second will exit quickly since it has
    # no work

    if(subjobs_count == 1):
        subjobs_count = 2

    # Path to the data files
    object_store_input_path = f"{config['object_store_job_prefix_full']}"

    # Which queue to submit to
    batch_queue_number = ((jobline - 1) % int(config['aws_batch_number_of_queues'])) + 1


    try:
        response = client.submit_job(
            jobName=f'afvs-{config["job_letter"]}-{jobline}',
            timeout={
                'attemptDurationSeconds': int(config["aws_batch_subjob_timeout"])
            },
            jobQueue=f"{config['aws_batch_prefix']}-queue{batch_queue_number}",
            arrayProperties={
                'size': subjobs_count
            },
            jobDefinition=f"{config['aws_batch_jobdef']}",
            containerOverrides={
                'resourceRequirements': [
                    {
                        'type': 'VCPU',
                        'value': config['aws_batch_subjob_vcpus'],
                    },
                    {
                        'type': 'MEMORY',
                        'value': config['aws_batch_subjob_memory'],
                    },
                ],
                'environment': [
                
                    {
                        'name': 'AFVS_RUN_MODE',
                        'value': "awsbatch"
                    },
                    {
                        'name': 'AFVS_JOB_STORAGE_MODE',
                        'value': "s3"
                    },
                    {
                        'name': 'AFVS_VCPUS',
                        'value': config['threads_to_use']
                    },
                    {
                        'name': 'AFVS_TMP_PATH',
                        'value': config['tempdir_default']
                    },
                    {
                        'name': 'AFVS_RUN_SEQUENTIAL',
                        'value': "0"
                    },
                    {
                        'name': 'AFVS_WORKUNIT',
                        'value': jobline_str
                    },
                    {
                        'name': 'AFVS_CONFIG_JOB_OBJECT',
                        'value': current_workunit['s3_download_path']
                    },
                    {
                        'name': 'AFVS_CONFIG_JOB_BUCKET',
                        'value': config['object_store_job_bucket']
                    },
                    
                ]
            }
        )

        current_workunit['status'] = "SUBMITTED"
        current_workunit['job_id'] = response['jobId']

        for subjob_id, subjob in current_workunit['subjobs'].items():
            subjob['status'] = "SUBMITTED"



    except botocore.exceptions.ClientError as error: 
        print("invalid")
        raise error

    # Slow ourselves down a bit
    time.sleep(0.1)

def submit_gcp_batch(config, transport, current_workunit, jobline, status_path):
    """Submits one AFVS workunit to Google Cloud Batch.

    A workunit becomes one Batch job per array part. Submission intent for
    every part is written to the status file before the provider is called,
    so an interrupted submission can be reconciled against the provider
    instead of being repeated.
    """
    jobline_str = str(jobline)
    subjob_ids = sorted(current_workunit['subjobs'].keys(), key=lambda value: int(value))

    recorded_parts = {}
    for record in current_workunit.get('gcp_batch_parts', []):
        recorded_parts[record['part_index']] = record

    def persist_intent(record):
        recorded_parts[record['part_index']] = record
        current_workunit['gcp_batch_parts'] = [
            recorded_parts[key] for key in sorted(recorded_parts)]
        current_workunit['status'] = "SUBMISSION_INTENT"
        _write_status_file(status_path)

    records = afvs_gcpbatch.submit_workunit(
        config, transport, jobline_str, subjob_ids,
        persist_intent=persist_intent,
        recorded_parts=recorded_parts)

    current_workunit['gcp_batch_parts'] = records
    current_workunit['status'] = "SUBMITTED"
    current_workunit['job_id'] = records[0]['job_id'] if records else None
    current_workunit['provider_job_names'] = [
        record.get('provider_job_name') for record in records]

    for subjob_id, subjob in current_workunit['subjobs'].items():
        subjob['status'] = "SUBMITTED"

    # Slow ourselves down a bit
    time.sleep(0.1)


#: Set by process() so that persist_intent can flush the status file before
#: each provider call without threading the whole status structure through.
_STATUS_STATE = {}


def _write_status_file(status_path):
    status = _STATUS_STATE.get('status')
    if status is None:
        return
    temp_path = f"{status_path}.tmp"
    with open(temp_path, "w") as json_out:
        json.dump(status, json_out, indent=4)
    Path(temp_path).replace(status_path)


def process(config, start, stop, preview=False, status_path="../workflow/status.json"):

    submit_type=config['batchsystem']

    if preview and submit_type != afvs_gcpbatch.BATCH_SYSTEM:
        # Refused before anything is opened for writing. A preview must not
        # touch the workflow directory at all, not even to re-initialize
        # the bash run script.
        raise SystemExit(
            f"--preview is only available for batchsystem={afvs_gcpbatch.BATCH_SYSTEM}")

    client = None
    transport = None

    if submit_type == "awsbatch":
        aws_config = Config(
            region_name=config['aws_region']
        )
        client = boto3.client('batch', config=aws_config)
    elif submit_type == afvs_gcpbatch.BATCH_SYSTEM:
        config = afvs_gcpbatch.config_defaults_applied(config)
        for warning in afvs_gcpbatch.cross_provider_warnings(config):
            print(f"WARNING: {warning}")
        if not preview:
            transport = afvs_gcpbatch.transport_from_config(config)

    status = {}


    # If this is batch, let's init a file
    if submit_type == "bash":
        with open("../workflow/run.bash", "w") as bash_out:
            bash_out.write("#!/usr/bin/env bash\n")

    # load the status file that is keeping track of the data
    with open(status_path, "r") as read_file:
        status = json.load(read_file)
        workunits = status['workunits']

    _STATUS_STATE['status'] = status

    for jobline in range(start, stop + 1):

        jobline_str = str(jobline)
        if jobline_str not in workunits:
            print(f"Jobline {jobline_str} was not found")
            continue

        current_workunit = workunits[jobline_str]

        if preview:
            subjob_ids = sorted(current_workunit['subjobs'].keys(),
                                key=lambda value: int(value))
            print(json.dumps(
                afvs_gcpbatch.preview_workunit(config, jobline_str, subjob_ids), indent=2))
            continue

        print(f"Submitting jobline {jobline_str}... ")

        # Now see if any of them have been submitted before
        if 'status' in current_workunit and current_workunit['status'] != "SUBMISSION_INTENT":
            print("jobs were already submitted for this....")
        else:
            if current_workunit.get('status') == "SUBMISSION_INTENT":
                # A previous run recorded intent but did not finish. The
                # recorded job IDs are deterministic, so resubmission
                # adopts whatever the provider already created rather than
                # launching the same work twice.
                print("resuming an interrupted submission for this workunit")

            if(submit_type == "awsbatch"):
                submit_aws_batch(config, client, current_workunit, jobline)
            elif(submit_type == afvs_gcpbatch.BATCH_SYSTEM):
                submit_gcp_batch(config, transport, current_workunit, jobline, status_path)
            elif(submit_type == "slurm"):
                submit_slurm(config, client, current_workunit, jobline)
            elif(submit_type == "bash"):
                run_bash(config, current_workunit, jobline)
            elif(submit_type == "lsf"):
                submit_lsf(config, client, current_workunit, jobline)
            else:
                print(f"Unknown submit type {submit_type}")




    if preview:
        # A preview never changes recorded state.
        return

    # Output all of the information about the workunits into JSON so we can easily grab this data in the future

    print("Writing the json status file out")

    with open(f"{status_path}.tmp", "w") as json_out:
        json.dump(status, json_out, indent=4)

    Path(f"{status_path}.tmp").replace(status_path)

    print("Making copy for status.submission as backup")
    # The backup lives beside the status file it is a backup of, so that
    # --status points both of them at the same workflow directory.
    shutil.copyfile(status_path, Path(status_path).parent / "status.submission.json")

    print("Done")

    if submit_type == "bash":
        os.chmod('../workflow/run.bash', 0o755)
        print("Run ../workflow/run.bash to run these job steps")


def main(argv=None):

    parser = argparse.ArgumentParser(
        description="Submit a range of AdaptiveFlow workunits to the configured batch system",
        epilog="Joblines start from 1")
    parser.add_argument('start_jobline', type=int, help="First jobline to submit")
    parser.add_argument('stop_jobline', type=int, help="Last jobline to submit")
    parser.add_argument('--preview', action='store_true',
                        help="Print the rendered Google Cloud Batch job JSON for each jobline "
                             "and exit without submitting or recording anything")
    parser.add_argument('--config', default="../workflow/config.json",
                        help="Path to the workflow config.json")
    parser.add_argument('--status', default="../workflow/status.json",
                        help="Path to the workflow status.json")

    args = parser.parse_args(argv)

    config = parse_config(args.config)
    process(config, args.start_jobline, args.stop_jobline,
            preview=args.preview, status_path=args.status)


if __name__ == '__main__':
    main()
