# AdaptiveFlow-VS code review — 2026-10-29

Reviewed `develop` commit `df74e005e456e94654fa93a40d748de399450b81`.
This is a focused review of configuration, workunit preparation, scheduler
submission, worker dispatch, and the ML filtering integration. Production code
is unchanged by the CI setup. Source line numbers below refer to that commit.

## R1 — P1: dynamic tranche filtering drops later matching collections

Location: `tools/templates/afvs_run.py:4199–4202`, inside `process()`.

When dynamic filtering is enabled and prescreen mode is disabled, the first
nonmatching collection executes `break`. This ends the loop over every
collection in the subjob. For collections `AA_0000001` followed by
`BB_0000002` and regex `^BB$`, nothing is queued, although the second collection
matches. This silently reduces screening coverage and makes results depend on
collection order. Continue to the next collection after a rejection.

Reproduction: `test_tranche_filter_keeps_later_matching_collections` uses the
real dispatch loop with fake child processes and queues; it expects the matching
second collection to be queued and currently fails that assertion.

## R2 — P1: Glide and CovDock completion callbacks have incompatible signatures

Location: `tools/templates/afvs_run.py:1146`, with callback definitions at
`1808`, `1888`, `1964`, and `2120`.

`process_docking_completion()` calls every registered completion handler with
`(item, ret)`. CovDock, Glide SP, Glide XP, and Glide HTVS handlers accept only
`task`. Each therefore raises `TypeError` after an otherwise successful docking
process, before reading the score. The exception propagates out of the docking
worker. Align these handlers with the runner's two-argument callback contract.

Reproduction: `test_glide_completion_accepts_runner_callback_contract` creates
each expected score file and dispatches through the real registry. All four
cases currently raise `TypeError`; no proprietary package is needed to expose
the callback mismatch. Proprietary runtime behavior remains untested.

## R3 — P2: an unrequested attribute can hide SMILES from the ML filter

Location: `tools/templates/afvs_run.py:407–416`; caller at
`tools/afvs_apply_ml_classifier_atg-primaryscreen.py:249`.

`get_attrs(..., attrs=['smi'])` increments its completion counter when it sees a
heavy-atom-count line, even though that attribute was not requested. If that line
precedes the SMILES line, it stops reading and returns `smi='N/A'`. The ML filter
then substitutes an empty string and discards the ligand. Count only requested
attributes, and track unique requested keys rather than matched lines.

Reproduction: `test_smiles_extraction_ignores_unrequested_attributes` supplies a
two-line PDBQT header containing a heavy-atom count followed by valid `CCO` SMILES.
The expected SMILES is currently missing.

## R4 — P2: S3 error handlers raise an unrelated NameError

Location: `tools/afvs_prepare_workunits.py:132` and
`tools/afvs_verify_collections.py:74,88`.

These handlers use `except ClientError` without importing that name. A failed
workunit upload or initial/paginated collection listing therefore raises
`NameError`, masking the actual AWS error and bypassing the intended handling.
Import the correct botocore exception. A failed workunit upload should propagate
the original failure and must not publish a successful status/download path.

Reproduction: `test_collection_verifier_handles_s3_errors` covers both initial
and paginated listings; `test_failed_s3_upload_propagates_original_error` covers
publication. Fake clients raise `AccessDenied`; all three cases currently raise
`NameError` instead.

## Validation and limits

The four findings have nine executable expected-failure cases in
`tests/test_review_findings.py`. Strict expected failures keep the open defects
visible while allowing an initial CI baseline; an unexpected pass requires
removing the marker and reviewing the fix. The other workflow/runner tests
exercise working behavior. See [CI and code review](ci-and-review.md) for exact
commands, lint scope, and environments not exercised.

No affinity, enrichment, generalization, or performance conclusion follows from
these tests. Full cluster/cloud campaigns, licensed docking engines, container
builds, and ML training require their own validation.
