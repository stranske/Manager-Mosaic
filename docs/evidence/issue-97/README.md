# Public evidence identity proof

The identity helper was already implemented in `76d8aed`. Follow-up verification
adds an exact three-violation regression and compares the package's complete
violation list with the standalone CLI's JSON report for individual defects,
combined defects, and valid identity evidence. The existing valid and invalid
fixtures now also check their dispositions through the public package validator.

Verified task checklist:

- [x] `_check_document_identity` detects disagreement when both page keys exist.
- [x] The helper rejects invalid calendar dates and noncanonical date suffixes.
- [x] The helper rejects self-supersession and runs after schema validation.
- [x] Non-dict containers are handled safely; legacy evidence remains valid.
- [x] Package tests cover individual and combined defects, matching page 0,
  leap day, `unknown`, earlier supersession, and absent `document_ref`.
- [x] CLI/package parity tests cover all three defects.
- [x] Evidence tests pass; the combined regression returns exactly three
  violations and fails with the helper call disconnected.
- [x] All required positive cases return `[]`.
- [x] `rg -n 'validate_run_contract|scripts' src/manager_mosaic/evidence.py`
  returns no matches (exit 1).
- [x] Backplane fixture tests pass, preserving valid/invalid dispositions.
- [x] Deliberate-break failure and restored success are captured in
  [97-combined-gate.txt](97-combined-gate.txt).

Validation:

```text
pytest tests/test_evidence_validation.py tests/test_backplane_fixtures.py \
  -m 'not slow' --override-ini='addopts=-v'
29 passed

pytest -m 'not slow'
134 passed; total coverage 94.03% (80% gate passed)

ruff check src/manager_mosaic/evidence.py tests/test_evidence_validation.py \
  tests/test_backplane_fixtures.py
All checks passed!

mypy src/manager_mosaic/evidence.py
Success: no issues found in 1 source file
```

The focused test command omits the suite-wide coverage gate; the full suite
above uses the configured gate. Black formatted each changed Python file
individually at line length 100. The repository-wide Black check passed with
99 files unchanged using this launcher to avoid sandbox process/socket limits
and wake its event loop for worker-thread results:

```python
import signal
import sys

from black import patched_main

signal.signal(signal.SIGALRM, lambda signum, frame: None)
signal.setitimer(signal.ITIMER_REAL, 0.1, 0.1)
sys.argv = [
    "black", "--check", "--workers", "1", "--line-length", "100",
    "--exclude", r"(\.workflows-lib|node_modules)", ".",
]
patched_main()
```

Commit handoff is blocked by the environment: `git add` fails because `.git`
is read-only (`Unable to create .../.git/index.lock: Read-only file system`).
The changes and verification logs remain in the working tree. GitHub API access
also failed, so this run could not inspect or update the PR's task list/state.
