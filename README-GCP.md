# Running AdaptiveFlow on native Google Cloud Batch

AdaptiveFlow can submit a virtual screening campaign to [Google Cloud
Batch](https://docs.cloud.google.com/batch/docs/get-started) with ligand
libraries and job data in Google Cloud Storage. This is a first-class
backend alongside AWS Batch, Slurm, LSF and local bash: set
`batchsystem=gcpbatch` in `tools/templates/all.ctrl`.

**Live submission is disabled in the shipped configuration.** The
scheduler integration, job rendering, storage layout and worker I/O are
complete and covered by an offline test suite, but no Google Cloud API
call is made until `gcp_batch_live_transport=1` is set. That flag is the
single, deliberate step between a configured campaign and billable
resources in your project. See [Status of this
backend](#status-of-this-backend).

## What a workunit becomes

| AdaptiveFlow | Google Cloud Batch |
|---|---|
| Workunit | One Batch job per array part, named `<prefix>-<job name>-<workunit>-<part>` |
| Subjob | One task in that job's task group |
| `dockings_per_subjob` | Unchanged: it decides how many dockings a task performs |
| `gcp_batch_array_job_size` | Maximum tasks per Batch job; larger workunits split across parts |
| `gcp_batch_subjob_vcpus` | `cpuMilli` (vCPUs × 1000) |
| `gcp_batch_subjob_memory` | `memoryMib` |
| `gcp_batch_subjob_timeout` | `maxRunDuration` |
| `gcp_batch_subjob_retry_count` | `maxRetryCount` |

### Task scratch

A task needs local scratch for its workunit archive, the collections it
unpacks and the poses it produces, and the worker refuses to start with
under 1 GiB free. `gcp_batch_task_scratch_path` (default `/tmp`) is that
directory, and it is what `AFVS_TMP_PATH` is set to.

It deliberately does not follow `tempdir_default`, which is `/dev/shm`.
That is the right choice on a Slurm node with a large shared-memory
filesystem, but a Batch task's container provides 64 MiB there, so every
task would fail its free-space check before reading its input. Keep the
scratch path on disk and size `gcp_batch_boot_disk_mib` to hold one
subjob's collections and output. A path under `/dev/shm` is rejected by
`afvs_prepare_folders.py`.

`taskCount` is always the real number of subjobs in the part. Unlike the
AWS Batch path, which pads a one-subjob workunit to a two-element array
and lets the second element exit immediately, Batch accepts
`taskCount=1`, so nothing is padded and no empty task is launched.

Each task derives the subjob it is responsible for from the task index
and the part's offset:

```
AFVS_WORKUNIT_SUBJOB = BATCH_TASK_INDEX + AFVS_SUBJOB_INDEX_OFFSET
```

`tools/templates/template1.gcpbatch.sh` performs that addition and then
runs `afvs_run.py`. A workunit of 450 subjobs with
`gcp_batch_array_job_size=200` therefore becomes three Batch jobs with
offsets 0, 200 and 400, and subjob 400 is task 0 of part 2.

## Prerequisites

1. **A project, a region and the Batch API.** Enable `batch.googleapis.com`,
   `compute.googleapis.com` and `storage.googleapis.com` in the project
   named by `gcp_project`.
2. **A job bucket.** `object_store_job_bucket` holds workunit archives and
   all output. Keep it in the same region as `gcp_region`.
3. **A ligand library.** Either a GCS mirror of the library
   (`data_storage_mode=gcs`) or an S3 library read across providers; see
   [Cross-provider library reads](#cross-provider-library-reads).
4. **A service account.** `gcp_batch_service_account` needs
   `roles/storage.objectViewer` on the library bucket,
   `roles/storage.objectAdmin` on the job bucket, and the Batch agent
   permissions (`roles/batch.agentReporter`).
5. **A worker image.** Build it from `tools/docker/Dockerfile.gcpbatch`
   and push it to Artifact Registry, then pin it in
   `gcp_batch_worker_image`:

   ```sh
   cd tools
   docker build -f docker/Dockerfile.gcpbatch -t \
       us-central1-docker.pkg.dev/<project>/<repo>/afvs-worker:2026-11-18 .
   docker push us-central1-docker.pkg.dev/<project>/<repo>/afvs-worker:2026-11-18
   ```

   Pin an immutable tag or a digest. Two builds of the same Dockerfile can
   contain different engine builds, and docking scores from different
   engine builds are not comparable within one campaign.

## Configure the campaign

Set these in `tools/templates/all.ctrl`. Every key is documented inline in
that file.

```
batchsystem=gcpbatch

gcp_project=my-project
gcp_region=us-central1
gcp_batch_machine_type=c2d-standard-8
gcp_batch_worker_image=us-central1-docker.pkg.dev/my-project/afvs/afvs-worker:2026-11-18
gcp_batch_service_account=afvs-worker@my-project.iam.gserviceaccount.com
gcp_batch_subjob_vcpus=8
gcp_batch_subjob_memory=15000
gcp_batch_subjob_timeout=20800
gcp_batch_array_job_size=200

job_storage_mode=gcs
data_storage_mode=gcs
object_store_job_bucket=my-afvs-jobs
object_store_job_prefix=AF/AFVS/jobs
object_store_data_bucket=my-ligand-library
object_store_data_collection_prefix=Enamine_REAL_Space_2022q12
```

Job storage and ligand library storage are configured independently. A
campaign can read an S3 library while writing job data to GCS, or read a
GCS library while a separate team's bucket holds the job output.

## Run a campaign

```sh
cd tools

# 1. Validate the control file and build the workflow directory.
./afvs_prepare_folders.py

# 2. Group collections into subjobs and workunits, and publish each
#    workunit archive to GCS. Each archive is verified after upload: a
#    workunit whose archive is not readable back is an error here rather
#    than a task that cannot find its input later.
./afvs_prepare_workunits.py

# 3. Inspect exactly what would be submitted. This is read only.
./afvs_submit_jobs.py 1 1 --preview

# 4. Submit. Refused unless gcp_batch_live_transport=1.
./afvs_submit_jobs.py 1 500

# 5. Observe. Scheduler state and output manifests are reported separately.
./afvs_get_status.py

# 6. Cancel one workunit's jobs, and only those.
./afvs_gcpbatch.py cancel --workunit 1
```

`afvs_gcpbatch.py` also offers `preview`, `status` and `manifest`
subcommands for a single workunit.

### Ranking

GCP output uses the same layout as the AWS output, so the existing
CSV/Parquet ranking path applies unchanged:

```
<prefix>/<job name>/<scenario>/csv/<workunit>/<subjob>.csv.gz
<prefix>/<job name>/<scenario>/parquet/<workunit>/<subjob>.parquet
<prefix>/<job name>/summary/<workunit>/<subjob>.json.gz
```

`tools/afvs_get_top_results.py` is Athena-based and therefore AWS only.
On GCP, read the Parquet shards directly (for example with BigQuery
external tables over the GCS prefix, or with pandas for small campaigns);
the column contract is identical.

## Output addressing, attempts and manifests

Three kinds of object are written per subjob:

* **Canonical results** at the paths above. These are what the ranker
  reads, and they match the AWS layout exactly.
* **Per-attempt artifacts** under
  `<prefix>/<job name>/attempts/<workunit>/<subjob>/<attempt>/`. Batch
  retries a failed task in place, so every attempt keeps its own summary,
  overview and log/pose archives. A retry cannot erase the evidence from
  the attempt before it.
* **An output manifest** at
  `<prefix>/<job name>/manifests/<workunit>/<subjob>.json`, written last
  and only after every upload for that attempt succeeded. It lists each
  stored object with its size and MD5, plus the docking counts.

The manifest is the authoritative statement of scientific completion. A
task that the scheduler reports as succeeded but whose manifest is absent
is an incomplete subjob, and `afvs_get_status.py` reports scheduler state
and manifest state separately for exactly this reason. Manifest
reconciliation distinguishes `empty`, `partial` and `complete` for a
workunit, and reports a manifest whose objects have since been deleted as
`objects_missing`.

## Idempotency and recovery

Batch job IDs are a deterministic function of the job name, the workunit
and the part index, and each submission also carries a stable
`request_id`. Submission intent, including that identity, is written to
`workflow/status.json` *before* the provider is called. The consequences:

* A resubmitted part is replayed by the provider's idempotency token
  rather than creating a second job.
* If the token has expired, the duplicate job ID is rejected, and
  AdaptiveFlow adopts the existing job instead of launching the work twice.
* A process that dies between the provider call and recording the response
  leaves an intent behind. Re-running `afvs_submit_jobs.py` for that
  workunit resumes from the intent and reconciles against the provider.

Cancellation only ever touches the job names recorded for the workunit
being cancelled. Note that cancellation is not instantaneous: tasks
already running can continue to accrue charges until the cancellation
takes effect.

## Cross-provider library reads

Running Batch tasks in Google Cloud while the ligand library stays in S3
works, and `data_storage_mode=s3` with `batchsystem=gcpbatch` is a
supported combination. It is also a cross-provider read: every collection
download incurs S3 GET charges and AWS egress on the library owner's
account, and is slower than an in-region read. `afvs_prepare_folders.py`
and `afvs_submit_jobs.py` print a warning naming that cost. Mirroring the
library into a GCS bucket in `gcp_region` avoids both.

Bucket names and object keys are always kept separate in the workunit
configuration. A `gs://` URI is never stored where an object key is
expected, because the same records are read by filesystem and boto3
readers that cannot interpret one.

## Status of this backend

**Implemented and offline-verified.** The following are covered by
`tests/` and run without any cloud account, credentials or network:

* job rendering, including array splitting, task/subjob mapping,
  compute shape, retries, timeout, service account, network policy and the
  read-only preview;
* configuration validation and cross-provider cost warnings;
* submission intent, idempotency, duplicate submission, adoption of an
  existing job, lifecycle reconciliation and scoped cancellation against a
  fake transport;
* end-to-end worker I/O: a workunit with two distinct subjobs is staged to
  a filesystem-backed mock object store, two indexed tasks are replayed,
  and the outputs are verified to be attributed to the correct ligands and
  readable with the ranking column contract;
* replays of a missing workunit archive, a missing collection, a corrupt
  (truncated) collection, a failed upload, an interrupted task and a
  retry, each checked against the manifest state it should produce;
* that the suite makes no live API call: constructing a real Google or AWS
  client inside the test suite fails the test.

Run it with:

```sh
pip install pytest boto3 pandas pyarrow jinja2 google-cloud-batch google-cloud-storage
pytest
```

**Not verified.** No part of this backend has been run against a real
Google Cloud project. Quotas, IAM, image pull from Artifact Registry,
Batch scheduling behaviour under load, real preemption of SPOT instances
and actual GCS throughput are all untested. Enabling
`gcp_batch_live_transport=1` and running a small campaign in a real
project is the next step, and should be treated as the point at which
charges begin.

The pinned `tools/bin/qvina02` is a Linux x86-64 ELF binary. The test
suite verifies its digest and architecture, and executes it only on hosts
that can run it; on other hosts that check is skipped rather than
reported as passing.
