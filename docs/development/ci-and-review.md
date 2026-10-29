# CI and code review

Pull requests run CI and CodeQL. Pushes to `develop` also run both workflows.
Each workflow supports manual dispatch once present on the default branch.
The setup uses GitHub-hosted Linux runners, pins external Actions to verified
commit SHAs, and requires no repository secrets or cloud credentials.

## Local validation

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest
python scripts/check_lint.py
python -m ruff check --select E4,E7,E9,F tests scripts
python -m compileall -q tools tests scripts -x '(^|/)bin/'
```

`tools/` remains the working directory for normal AFVS commands. Tests use
temporary workflow directories and fake scheduler/AWS responses. They cover
configuration parsing, overwrite refusal, workunit archives and replica counts,
hash and metatranche addressing, SLURM/LSF submission, AWS array constraints,
and a single-ligand worker path. GitHub tests Python 3.12 and 3.13; this matrix
does not establish compatibility with every older Python version.

CI additionally checks tracked shell scripts with `bash -n` and validates
GitHub Actions with actionlint 1.7.12. CodeQL runs Python security-extended
queries and uploads its results to GitHub code scanning. Check its findings in
the repository's Security tab; a completed scan does not mean there are no
alerts. If CodeQL default setup is already enabled in repository settings,
switch to advanced setup before using the checked-in workflow to avoid
duplicate configurations.

## Existing issues are visible

The initial review is recorded in [the review report](code-review-2026-10-29.md).
Seven existing Ruff findings are listed in `.github/ruff-baseline.json` by file,
rule, message, and count. `scripts/check_lint.py` rejects new selected findings
and stale baseline entries. Fixing an old finding requires removing its baseline
entry/count in the same change. The baseline is not an exemption for a whole file.
The four `structure` references are in unreachable legacy code after a `return`;
the missing `ClientError` imports affect live failure paths.

`tests/test_review_findings.py` contains strict expected failures for the four
review findings. These are open defects, not passing regression tests. A fix
must remove the relevant `xfail` marker, and then pass the assertion. Unexpected
exceptions outside each specified failure type fail the test normally.

The initial suite does not execute real docking binaries, submit cluster jobs,
access S3/Athena, build the worker Docker image, or train the optional
PyTorch/RDKit classifier. Changes to these paths need appropriate environment
validation in addition to CI. Bundled engine scripts in `tools/bin/` have their
own runtime and licensing requirements and are excluded from the Python gate.

## Pull request review

Keep the change focused, explain its user-visible result, and include the
validation actually performed. For workflow changes, reviewers should check:

- Configuration defaults, aliases, invalid inputs, and overwrite behavior.
- Collection/ligand coverage, replica counts, and preservation of padded IDs.
- Scheduler indexing, resource requests, retries, and submission status.
- Storage failure propagation, temporary paths, and archive extraction.
- Docking callback contracts and score parsing; docking scores alone do not
  establish binding affinity or experimental target specificity.
- Optional ML input provenance, missing SMILES, train/validation leakage, and
  the meaning of predicted probabilities.

The PR template supplies a short validation checklist. Once this setup is merged
and its checks have run, a repository administrator can require
`Python and shell checks`, `GitHub Actions validation`, both `Workflow tests`
checks, and the CodeQL analysis check in the rule for `develop`, alongside at
least one approving review. Select the exact check names shown by GitHub.
Repository rules and review requirements are separate from workflow files.

Codex automatic PR reviews are also a separate account/repository integration;
CodeQL supplies automated security analysis and does not enable Codex reviews.
