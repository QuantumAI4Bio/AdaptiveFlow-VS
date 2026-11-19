"""Replays a single AdaptiveFlow task against the mock object store.

The harness drives the worker's own stage functions from
tools/templates/afvs_run.py in one process: the GCS fetch and verification,
the archive unpacking (including the sparse .listing path), the docking
invocation and score parsing, the summary and ranking file generation, the
upload path and the manifest finalization are all production code.

What the harness replaces is only the process pool: instead of spawning
the downloader, unpacker, collection, docking, summary and uploader
processes, it runs those stages in sequence over list-backed queues. That
keeps the replay deterministic and portable, and keeps the test focused on
the storage and addressing contract rather than on process management.

The docking engine is a Python stub. This suite verifies that outputs are
attributed to the right ligands and are readable by the ranker; verifying
that the pinned qvina02 binary itself produces a correct score is a
separate concern, covered by test_engine_binary.py where the platform can
execute it.
"""

import contextlib
import os
import queue
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES_DIR = HERE.parents[0] / "tools" / "templates"
if str(TEMPLATES_DIR) not in sys.path:
    sys.path.insert(0, str(TEMPLATES_DIR))

import afvs_run  # noqa: E402

from conftest import expected_score  # noqa: E402


class ListQueue:
    """A minimal stand-in for multiprocessing.Queue used by the stages."""

    def __init__(self, items=None):
        self._items = queue.SimpleQueue()
        for item in items or []:
            self._items.put(item)

    def put(self, item):
        self._items.put(item)

    def get(self, timeout=None):
        try:
            return self._items.get_nowait()
        except queue.Empty as error:
            raise _Empty from error

    def qsize(self):
        return self._items.qsize()

    def drain(self):
        collected = []
        while True:
            try:
                collected.append(self._items.get_nowait())
            except queue.Empty:
                return collected


_Empty = __import__("queue").Empty


@contextlib.contextmanager
def preserved_cwd():
    """Restores the working directory after a worker stage has run.

    Several worker stages chdir into the directory they are working in. In
    the real worker each stage is its own process, so that never affects
    the others. The harness runs the stages in one process, so it restores
    the directory between them; on Windows a leaked cwd would also prevent
    the stage's temporary directory from being removed.
    """
    original = os.getcwd()
    try:
        yield
    finally:
        os.chdir(original)


def stub_docking_start(task):
    """Builds the command for the fixture docking engine.

    The stub is invoked exactly like the real engine: the worker passes
    --config, --ligand, --out and --cpu, and the stub prints a score table
    in the Vina family's output format, which the production
    docking_finish_vina parser then reads.
    """
    return [
        sys.executable,
        str(HERE / "fixture_engine.py"),
        '--cpu', str(task['threads_per_docking']),
        '--config', str(task['config_path']),
        '--ligand', str(task['ligand_path']),
        '--out', str(task['output_path']),
    ]


def install_stub_engine(monkeypatch):
    """Points the qvina02 registry entry at the fixture engine."""
    monkeypatch.setitem(afvs_run.DOCKING_PROGRAMS['qvina02'], 'start', stub_docking_start)


def replay_task(config, workunit_id, subjob_id, object_store, scratch_dir,
                attempt_index=0, attempt_uid="fixture", upload_failure=None,
                stop_after=None):
    """Runs one task of one workunit and returns what it produced.

    Args:
        config (dict): The workflow configuration.
        workunit_id (str): Workunit to run.
        subjob_id (str): The AFVS subjob ID this task is responsible for.
        object_store: The object store the task reads and writes.
        scratch_dir (Path): Local scratch directory for this task.
        attempt_index (int): Which attempt of the task this is.
        attempt_uid (str): Unique suffix for this attempt's output prefix.
        upload_failure (callable): Optional predicate taking an uploader
            item; when it returns True the upload raises, which models a
            failed upload.
        stop_after (str): Optional stage name after which to stop, used to
            model an interrupted task. One of 'download', 'docking'.

    Returns:
        A dict with the task context, the docking results, the uploaded
        objects and the finalized manifest (None when not finalized).
    """
    scratch_dir = Path(scratch_dir)
    scratch_dir.mkdir(parents=True, exist_ok=True)

    ctx = {
        'tools_path': str(TEMPLATES_DIR.parent / "bin"),
        'temp_dir': str(scratch_dir),
        'vcpus_to_use': 1,
        'attempt_index': attempt_index,
        'attempt_uid': attempt_uid,
        'attempt_id': f"{attempt_index:02d}-{attempt_uid}",
        'gcs': object_store,
        'job_storage_mode': config['job_storage_mode'],
        'job_bucket': config['object_store_job_bucket'],
    }

    import afvs_gcpbatch

    ctx['job_object'] = afvs_gcpbatch.gen_job_input_object_name(config, workunit_id)

    # Production code path: fetch and verify this task's workunit archive,
    # then select this task's subjob from it.
    with preserved_cwd():
        afvs_run.get_workunit_from_gcs(ctx, workunit_id, subjob_id,
                                       ctx['job_bucket'], ctx['job_object'],
                                       ctx['temp_dir'])

    afvs_run.process_config(ctx)
    ctx['workunit_id'] = workunit_id
    ctx['subjob_id'] = subjob_id

    summary_queue = ListQueue()
    download_queue = ListQueue()
    unpack_queue = ListQueue()
    collection_queue = ListQueue()
    docking_queue = ListQueue()
    upload_queue = ListQueue()

    for collection_key, collection in ctx['subjob_config']['collections'].items():
        collection_name, collection_number = collection_key.split("_", maxsplit=1)
        collection['collection_number'] = collection_number
        collection['collection_name'] = collection_name
        download_queue.put({
            'collection_key': collection_key,
            'collection': collection,
            'ext': "tar.gz",
        })

    # Stage 1: download and verify.
    download_queue.put(None)
    _patch_env(config)
    with preserved_cwd():
        afvs_run.downloader(download_queue, unpack_queue, summary_queue, ctx['temp_dir'])

    if stop_after == "download":
        return {
            'ctx': ctx,
            'summary_items': summary_queue.drain(),
            'uploads': [],
            'manifest': None,
            'interrupted_after': "download",
        }

    # Stage 2: unpack, honouring the sparse .listing representative limit.
    unpack_queue.put(None)
    with preserved_cwd():
        afvs_run.untar(unpack_queue, collection_queue)

    # Stage 3: validate ligands and enqueue dockings.
    collection_queue.put(None)
    with preserved_cwd():
        afvs_run.collection_process(ctx, collection_queue, docking_queue, summary_queue)

    # Stage 4: dock.
    docking_queue.put(None)
    with preserved_cwd():
        afvs_run.docking_process(ctx, docking_queue, summary_queue)

    if stop_after == "docking":
        return {
            'ctx': ctx,
            'summary_items': summary_queue.drain(),
            'uploads': [],
            'manifest': None,
            'interrupted_after': "docking",
        }

    # Stage 5: summarize, which also builds the ranking files.
    summary_items = summary_queue.drain()
    replay_summary_queue = ListQueue(summary_items + [None])
    metadata = {
        'workunit_id': workunit_id,
        'subunit_id': subjob_id,
        'ligand_library_format': config['ligand_library_format'],
        'vcpus_to_use': ctx['vcpus_to_use'],
    }
    with preserved_cwd():
        afvs_run.summary_process(ctx, replay_summary_queue, upload_queue, metadata)

    # Stage 6: upload.
    upload_items = upload_queue.drain()
    uploaded = []
    failure = None
    for item in upload_items:
        if upload_failure is not None and upload_failure(item):
            failure = item
            break
        single_queue = ListQueue([item, None])
        with preserved_cwd():
            afvs_run.upload_process(ctx, single_queue)
        uploaded.append(item)

    if failure is not None:
        # An upload failure leaves the manifest unwritten, exactly as a
        # real uploader exception would: flush_queue raises and
        # finalize_output_manifest is never reached.
        return {
            'ctx': ctx,
            'summary_items': summary_items,
            'uploads': uploaded,
            'failed_upload': failure,
            'manifest': None,
        }

    ctx['docking_counts'] = afvs_run.read_overview_counts(ctx)
    with preserved_cwd():
        manifest = afvs_run.finalize_output_manifest(ctx)

    return {
        'ctx': ctx,
        'summary_items': summary_items,
        'uploads': uploaded,
        'manifest': manifest,
        'docking_counts': ctx['docking_counts'],
    }


def _patch_env(config):
    """Sets the environment variables the worker stages read."""
    os.environ['AFVS_GCP_PROJECT'] = str(config.get('gcp_project', ""))
    os.environ.setdefault('AFVS_TOOLS_PATH', str(TEMPLATES_DIR.parent / "bin"))


def ligand_scores_from_summary(rows):
    """Maps a summary CSV's rows to {ligand: score_min}."""
    return {row['ligand']: float(row['score_min']) for row in rows}


def expected_scores_for(ligands):
    """The scores the fixture engine should have produced for these ligands."""
    return {ligand: expected_score(ligand) for ligand in ligands}


def make_scratch(tmp_path, name):
    """Creates an isolated scratch directory for one task attempt."""
    scratch = Path(tempfile.mkdtemp(prefix=f"{name}-", dir=str(tmp_path)))
    return scratch
