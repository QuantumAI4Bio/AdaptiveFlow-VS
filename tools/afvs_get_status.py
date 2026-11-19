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
# Description: Get status of the AWS Batch jobs
#
# Revision history:
# 2021-06-29  Original version
#
# ---------------------------------------------------------------------------


import os
import sys
import json
import boto3
import botocore
import re
import tempfile
import gzip
import time
import pprint
import hashlib
from botocore.config import Config
from pathlib import Path
import argparse
import gzip
import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue
from queue import Empty
import logging
import shutil

import afvs_gcpbatch
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))
import afvs_gcs



def downloader(download_queue, summary_queue, tmp_dir, config):

    temp_dir = tempfile.mkdtemp(prefix=tmp_dir)

    botoconfig = Config(
       retries = {
          'max_attempts': 25,
          'mode': 'standard'
       }
    )

    s3 = boto3.client('s3', config=botoconfig)

    while True:
        try:
            item = download_queue.get(timeout=20.5)
        except Empty:
            continue

        if item is None:
            summary_queue.put(None)
            break

        local_path= f"{temp_dir}/tmp.{item['workunit_id']}.{item['subjob_id']}.json.gz"
        remote_path = item['s3_path']
        job_bucket = config['object_store_job_bucket']

        try:
            with open(local_path, 'wb') as f:
                s3.download_fileobj(job_bucket, remote_path, f)
            logging.debug(f"downloaded to {local_path}")
        except botocore.exceptions.ClientError as error:
                logging.error(f"Failed to download from S3 {job_bucket}/{remote_path} to {local_path}, ({error})")
                continue


        with gzip.open(local_path, "rb") as read_file:
            item['result'] = json.load(read_file)

        # Move it to the next step if there's space
        while summary_queue.qsize() > 1000:
            time.sleep(0.2)

        summary_queue.put(item)
        os.remove(local_path)


def parse_config(filename):
    with open(filename, "r") as read_file:
        config = json.load(read_file)

    return config


def process(config):

    statuses = ['SUBMITTED','PENDING','RUNNABLE','STARTING','RUNNING','SUCCEEDED','FAILED']


    aws_config = Config(
        region_name=config['aws_region']
    )


    parser = argparse.ArgumentParser()
    parser.add_argument('--detailed', action='store_true',
        help="Get detailed ligand information (this can take a long time!)")
    args = parser.parse_args()

    client = boto3.client('batch', config=aws_config)

    # load the status file that is keeping track of the data
    with open("../workflow/status.json", "r") as read_file:
        complete = json.load(read_file)


    status = complete['workunits']
    finished = []

    use_list_jobs_status = ['SUBMITTED', 'PENDING']
    final_states = ['SUCCEEDED', 'FAILED']

    vcpus_per_job = int(config['aws_batch_subjob_vcpus'])

    # Which ones do we need to check
    workunits_to_check = []
    for workunit_id, workunit in status.items():
        if 'status' not in workunit:
            # workunit has not been submitted yet
            continue

        if(workunit['status'] in use_list_jobs_status):
            workunits_to_check.append({
                    'workunit_id': workunit_id,
                    'batch_jobid': workunit['job_id']
                }
                )

    workunits_to_recompute = {}
    subjobs_to_check = []
    failed_downloads = []

    print("Getting workunit status")

    # Check the array parents
    for status_index_begin in range(0, len(workunits_to_check), 100):

        job_keys_to_check = []
        job_key_mapping = {}

        for status_item in workunits_to_check[status_index_begin:(status_index_begin+100)]:

            workunit_id = status_item['workunit_id']
            batch_jobid = status_item['batch_jobid']

            job_keys_to_check.append(batch_jobid)
            job_key_mapping[batch_jobid] = { 'workunit_id': workunit_id }

        response = client.describe_jobs(jobs=job_keys_to_check)

        if 'jobs' in response:

            for job in response['jobs']:
                mapping = job_key_mapping[job['jobId']]
                workunit_id = mapping['workunit_id']
                workunit = status[workunit_id]

                # Has something changed?
                workunit_has_changed = 0

                if(workunit['status'] != job['status']):
                    workunit['status'] = job['status']
                    workunit_has_changed = 1

                if('status_summary' in workunit):

                    for status_val in job['arrayProperties']['statusSummary']:
                        if status_val not in workunit['status_summary']:
                            workunit['status_summary'][status_val] = job['arrayProperties']['statusSummary'][status_val]
                            workunit_has_changed = 1
                        elif(workunit['status_summary'][status_val] != job['arrayProperties']['statusSummary'][status_val]):
                            workunit['status_summary'][status_val] = job['arrayProperties']['statusSummary'][status_val]
                            workunit_has_changed = 1
                else:
                    workunit['status_summary'] = job['arrayProperties']['statusSummary'].copy()
                    workunit_has_changed = 1


                if(workunit_has_changed == 1):
                    # status has changed
                    workunits_to_recompute[workunit_id] = 1

                    for subjob_id, subjob in workunit['subjobs'].items():
                        if(subjob['status'] not in final_states):
                            subjobs_to_check.append({
                                    'workunit_id': workunit_id,
                                    'subjob_id': subjob_id,
                                    'batch_jobid': f"{job['jobId']}:{subjob_id}"
                                }
                            )
        else:
            logging.error(f"Did not get jobs response from AWS Batch")


    # Now let's check on the ones that have finished

    print("Getting subjob status")

    subjobs_to_parse = []


    for status_index_begin in range(0, len(subjobs_to_check), 100):
        job_keys_to_check = []
        job_key_mapping = {}

        for status_item in subjobs_to_check[status_index_begin:(status_index_begin+100)]:
            workunit_id = status_item['workunit_id']
            subjob_id = status_item['subjob_id']
            batch_jobid = status_item['batch_jobid']

            job_keys_to_check.append(batch_jobid)
            job_key_mapping[batch_jobid] = { 'workunit_id': workunit_id, 'subjob_id': subjob_id}

        response = client.describe_jobs(jobs=job_keys_to_check)

        if 'jobs' in response:
            for job in response['jobs']:
                mapping = job_key_mapping[job['jobId']]

                workunit_id = mapping['workunit_id']
                subjob_id = mapping['subjob_id']
                subjob = status[workunit_id]['subjobs'][subjob_id]

                subjob['status'] = job['status']

                if subjob['status'] in final_states:

                    if(subjob['status'] == "SUCCEEDED"):
                        subjobs_to_parse.append({ 'workunit_id': workunit_id, 'subjob_id': subjob_id})

                    subjob['vcpu_seconds_interrupted'] = 0
                    subjob['vcpu_seconds'] = 0

                    last_attempt_index = len(job['attempts']) - 1
                    for attempt_index, attempt in enumerate(job['attempts']):
                        if ( 'stoppedAt' in attempt and 'startedAt' in attempt):
                            vcpu_time = (attempt['stoppedAt'] - attempt['startedAt']) / 1000 * vcpus_per_job

                            if(attempt_index == last_attempt_index):
                                subjob['vcpu_seconds'] = vcpu_time
                            else:
                                subjob['vcpu_seconds_interrupted'] += vcpu_time

                    complete['summary']['vcpu_seconds'] += subjob['vcpu_seconds']
                    complete['summary']['vcpu_seconds_interrupted'] += subjob['vcpu_seconds_interrupted']


                else:
                    pass
                    # Non-final state.



    # Now, we need to go check the files to see how many ligands there actually were

    download_queue = Queue()
    summary_queue = Queue()

    number_of_downloaders = multiprocessing.cpu_count() * 2
    downloader_processes = []
    for i in range(number_of_downloaders):
        downloader_processes.append(Process(target=downloader, args=(download_queue, summary_queue, config['temp_dir'], config)))
        downloader_processes[i].start()


    for item in subjobs_to_parse:
        workunit_id = item['workunit_id']
        subjob_id = item['subjob_id']

        # Get the link to the output
        item['s3_path'] = f"{config['object_store_job_prefix']}/{config['job_name']}/summary/{workunit_id}/{subjob_id}.json.gz"

        download_queue.put(item)

    for i in range(number_of_downloaders):
        download_queue.put(None)


    print("Downloading result files ")

    download_procs_finished = 0
    download_count = 0
    while True:
        try:
            item = summary_queue.get()
        except Empty:
            #print('unpacker: gave up waiting...', flush=True)
            continue

        # check for stop
        if item is None:
            download_procs_finished += 1
            if(download_procs_finished == number_of_downloaders):
                break
            continue


        download_count += 1

        # Print  flush=True
        if(download_count % 100 == 0):
            print(f".", flush=True, end="")


        # Otherwise process
        workunit_id = item['workunit_id']
        subjob_id = item['subjob_id']
        subjob = status[workunit_id]['subjobs'][subjob_id]

        subjob['overview'] = {
           'total_dockings' : item['result']['total_dockings'],
           'docking_succeeded' : item['result']['dockings_status']['success'],
           'docking_failed' : item['result']['dockings_status']['failed'],
           'skipped_ligands' : item['result']['skipped_ligands'],
           'failed_downloads' : item['result']['failed_downloads'],
           'failed_downloads_dockings' : item['result']['failed_downloads_dockings']
        }

        for log_item in item['result']['failed_downloads_log']:
            failed_downloads.append([str(workunit_id), str(subjob_id), log_item['base_collection_key'], str(log_item['dockings']), log_item['reason']  ])

        for attr, attr_val in subjob['overview'].items():
            complete['summary'][attr] += attr_val

    print("")


    # submitted only workunits



    # re-calc workunits as needed

    for workunit_id in workunits_to_recompute:
        workunit = status[workunit_id]

        workunit['overview_status'] = {}
        for status_val in statuses:
            workunit['overview_status'][status_val] = {
                'ligands': 0,
                'workunits': 0,
                'subjobs': 0
            }

        workunit['overview_status'][workunit['status']]['workunits'] += 1

        for subjob_id, subjob in workunit['subjobs'].items():
            subjob_status = subjob['status']

            workunit['overview_status'][subjob_status]['subjobs'] += 1
            workunit['overview_status'][subjob_status]['ligands'] += subjob['ligands_expected']

    # now do new sum

    complete['overview_status'] = {}
    for status_val in statuses:
        complete['overview_status'][status_val] = {
            'ligands': 0,
            'workunits': 0,
            'subjobs': 0
        }

    for workunit_id, workunit in status.items():
        if 'status' not in workunit:
            # workunit has not been submitted yet
            continue

        for status_val in statuses:
            complete['overview_status'][status_val]['ligands'] += workunit['overview_status'][status_val]['ligands']
            complete['overview_status'][status_val]['workunits'] += workunit['overview_status'][status_val]['workunits']
            complete['overview_status'][status_val]['subjobs'] += workunit['overview_status'][status_val]['subjobs']


    # Output all failed downloads

    with open("../workflow/failed_downloads.csv", "a") as failed_downloads_out:
        for failed_download in failed_downloads:
            failed_downloads_out.write(",".join(failed_download))
            failed_downloads_out.write("\n")



    # output a nice summary

    status_header = "Status"
    workunits_header = "Workunits"
    subjobs_header = "Subjobs"
    ligands_header = "Dockings (est.)"

    print(f"-----------------------------------------------------------------")
    print("AWS Batch Progress")
    print(f"-----------------------------------------------------------------")
    print(f"")


    print(f"Docking count is inaccurate for prescreens. Correct value will")
    print(f"be in 'Completed Summary' when finished.")
    print(f"")

    print(f"{status_header:>15}   {workunits_header:^10}   {subjobs_header:^15}  {ligands_header:^15}")
    for status_val in statuses:
        print(f"{status_val:>15}   {complete['overview_status'][status_val]['workunits']:^10}   {complete['overview_status'][status_val]['subjobs']:^15}   {complete['overview_status'][status_val]['ligands']:^15}")


    vcpu_hrs = complete['summary']['vcpu_seconds'] / 60 / 60
    vcpu_hrs_interrupted = complete['summary']['vcpu_seconds_interrupted'] / 60 / 60

    print(f"")
    active_vcpus = (complete['overview_status']['RUNNING']['subjobs'] + complete['overview_status']['STARTING']['subjobs']) * vcpus_per_job
    print(f"Active vCPUs: {active_vcpus}")


    print(f"")
    print(f"-----------------------------------------------------------------")
    print("Completed Summary")
    print(f"-----------------------------------------------------------------")
    print(f"")
    print(f"* Total Dockings  : {complete['summary']['total_dockings']}")
    print(f"  - Succeeded     : {complete['summary']['docking_succeeded']}")
    print(f"  - Failed        : {complete['summary']['docking_failed']}")
    print(f"* Skipped ligands : {complete['summary']['skipped_ligands']}")
    print(f"* Failed Downloads: {complete['summary']['failed_downloads']} (est. {complete['summary']['failed_downloads_dockings']} dockings)")
    if(complete['summary']['failed_downloads'] != 0):
        print(f"     (failed downloads are in '../workflow/failed_downloads.csv')")
    print(f"")


    if(complete['summary']['total_dockings'] != 0):
        vcpu_sec = complete['summary']['vcpu_seconds'] / complete['summary']['total_dockings']
        print(f"* vCPU seconds per docking: {vcpu_sec:0.2f}")
    else:
        print(f"* vCPU seconds per docking: N/A")
    print(f"* vCPU hours total        : {vcpu_hrs:0.2f}")
    print(f"* vCPU hours interrupted  : {vcpu_hrs_interrupted:0.2f}")
    print(f"")

    # Output the condensed version
    with open("../workflow/status.tmp.json", "w") as json_out:
        json.dump(complete, json_out)

    shutil.move("../workflow/status.tmp.json", "../workflow/status.json")



def process_gcpbatch(config, local_object_store=None):
    """Reports status for a native Google Cloud Batch workflow.

    Two independent sources are combined, because neither alone is
    sufficient: the scheduler knows whether tasks ran, and the output
    manifests know whether the science they were supposed to produce
    actually landed in storage.
    """
    config = afvs_gcpbatch.config_defaults_applied(config)

    with open("../workflow/status.json", "r") as read_file:
        complete = json.load(read_file)

    workunits = complete['workunits']
    transport = afvs_gcpbatch.transport_from_config(config)
    object_store = afvs_gcs.object_store_from_env(
        project=config.get('gcp_project'), local_root=local_object_store)

    task_states = {}
    manifest_states = {'empty': 0, 'partial': 0, 'complete': 0}
    dockings = {'total': 0, 'succeeded': 0, 'failed': 0, 'skipped': 0}
    unreachable = []

    for workunit_id, workunit in sorted(workunits.items(), key=lambda item: int(item[0])):
        records = workunit.get('gcp_batch_parts')
        if not records:
            # Not submitted yet.
            continue

        try:
            reconciliation = afvs_gcpbatch.reconcile_workunit(config, transport, records)
            workunit['gcp_batch_reconciliation'] = reconciliation
            for state, count in reconciliation['task_state_summary'].items():
                task_states[state] = task_states.get(state, 0) + count
        except afvs_gcpbatch.LiveTransportDisabled as error:
            unreachable.append(str(error))

        expected_subjobs = sorted(workunit.get('subjobs', {}).keys(),
                                  key=lambda value: int(value))
        manifest_report = afvs_gcpbatch.reconcile_manifests(
            config, object_store, workunit_id, expected_subjobs)
        workunit['gcp_batch_output_manifest'] = manifest_report

        manifest_states[manifest_report['state']] += 1
        for key in dockings:
            dockings[key] += int(manifest_report['dockings'].get(key, 0) or 0)

    print("-----------------------------------------------------------------")
    print("Google Cloud Batch Progress")
    print("-----------------------------------------------------------------")
    print("")

    if unreachable:
        print("Scheduler state was not read: the live Google Cloud Batch transport is disabled.")
        print(f"  {unreachable[0]}")
        print("")

    if task_states:
        print(f"{'Task state':>24}   {'Tasks':^10}")
        for state, count in sorted(task_states.items()):
            print(f"{state:>24}   {count:^10}")
        print("")

    print("Output manifests (scientific completion, independent of scheduler state)")
    for state in ("complete", "partial", "empty"):
        print(f"{state:>24}   {manifest_states[state]:^10} workunits")
    print("")

    print(f"* Total dockings  : {dockings['total']}")
    print(f"  - Succeeded     : {dockings['succeeded']}")
    print(f"  - Failed        : {dockings['failed']}")
    print(f"* Skipped ligands : {dockings['skipped']}")
    print("")

    with open("../workflow/status.tmp.json", "w") as json_out:
        json.dump(complete, json_out)

    shutil.move("../workflow/status.tmp.json", "../workflow/status.json")


def main():

    config = parse_config("../workflow/config.json")

    if(config['job_storage_mode'] == "s3" and config['batchsystem'] == "awsbatch"):
        with tempfile.TemporaryDirectory(prefix=os.path.join(config['tempdir_default'], '')) as temp_dir:
            config['temp_dir'] = temp_dir
            process(config)
    elif(config['batchsystem'] == afvs_gcpbatch.BATCH_SYSTEM):
        parser = argparse.ArgumentParser()
        parser.add_argument('--detailed', action='store_true',
            help="Accepted for symmetry with the AWS path; GCP status is always per subjob")
        parser.add_argument('--local-object-store', default=None,
            help="Read output manifests from a filesystem-backed object store rooted here")
        args = parser.parse_args()
        process_gcpbatch(config, local_object_store=args.local_object_store)
    else:
        print(f"Configuration with job_storage_mode={config['job_storage_mode']} and batchsystem={config['batchsystem']} is not supported")


if __name__ == '__main__':
    main()
