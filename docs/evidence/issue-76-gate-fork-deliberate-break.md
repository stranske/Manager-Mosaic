# Deliberate-break evidence: fork Gate read-only-token fallback (#76 / #74)

This is a fresh replay against current `main` at merge `46ee06cbac8a0ac885a511479ad2ccc89635bd47`
(merged PR #75). It records evidence that was not preserved in the historical
squash diff; it does not reconstruct or claim historical output.

## Named gate and baseline

Command:

```text
python -m pytest tests/test_gate_commit_status_fork_tolerance.py -q --no-cov
```

Literal baseline output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.2, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/teacher/.codex/automations/pd-workloop-resume/worktrees/Manager-Mosaic-issue-76
configfile: pyproject.toml
plugins: langsmith-0.10.9, cov-7.1.0, xdist-3.8.0, rerunfailures-16.3, datadir-1.8.0, typeguard-4.5.1, asyncio-1.3.0, pytest_httpserver-1.1.3, hypothesis-6.155.7, regressions-2.11.0, Faker-40.39.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 14 items

tests/test_gate_commit_status_fork_tolerance.py ..............           [100%]

============================== 14 passed in 0.40s ==============================
```

## RED: deliberate break

In `.github/workflows/pr-00-gate.yml`, temporarily replace only the production
`readOnlyForkToken` predicate:

```javascript
const readOnlyForkToken =
  errorStatus === 403 &&
  isForkPullRequest &&
  !hitRateLimit &&
  isIntegrationPermissionError;
```

with:

```javascript
const readOnlyForkToken = false;
```

Re-run the named gate. Literal output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.2, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/teacher/.codex/automations/pd-workloop-resume/worktrees/Manager-Mosaic-issue-76
configfile: pyproject.toml
plugins: langsmith-0.10.9, cov-7.1.0, xdist-3.8.0, rerunfailures-16.3, datadir-1.8.0, typeguard-4.5.1, asyncio-1.3.0, pytest_httpserver-1.1.3, hypothesis-6.155.7, regressions-2.11.0, Faker-40.39.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 14 items

tests/test_gate_commit_status_fork_tolerance.py FFFFFF........           [100%]

=================================== FAILURES ===================================
________________ test_fork_read_only_403_does_not_fail_the_gate ________________
E       AssertionError: assert {'status': 403, 'message': 'Resource not accessible by integration'} is None
tests/test_gate_commit_status_fork_tolerance.py:261: AssertionError
_______________ test_fork_read_only_403_reports_the_real_verdict _______________
E       AssertionError: assert 'read-only' in ''
tests/test_gate_commit_status_fork_tolerance.py:269: AssertionError
______________ test_fork_read_only_403_preserves_failure_verdict _______________
E       AssertionError: assert {'status': 403, 'message': 'Resource not accessible by integration'} is None
tests/test_gate_commit_status_fork_tolerance.py:283: AssertionError
_ test_fork_read_only_403_fails_closed_for_other_non_success_verdicts[error-runner errored] _
E       AssertionError: assert {'status': 403, 'message': 'Resource not accessible by integration'} is None
tests/test_gate_commit_status_fork_tolerance.py:302: AssertionError
_ test_fork_read_only_403_fails_closed_for_other_non_success_verdicts[pending-checks still pending] _
E       AssertionError: assert {'status': 403, 'message': 'Resource not accessible by integration'} is None
tests/test_gate_commit_status_fork_tolerance.py:302: AssertionError
_____________ test_deleted_fork_read_only_403_reports_the_verdict ______________
E       AssertionError: assert {'status': 403, 'message': 'Resource not accessible by integration'} is None
tests/test_gate_commit_status_fork_tolerance.py:314: AssertionError
=========================== short test summary info ============================
FAILED tests/test_gate_commit_status_fork_tolerance.py::test_fork_read_only_403_does_not_fail_the_gate
FAILED tests/test_gate_commit_status_fork_tolerance.py::test_fork_read_only_403_reports_the_real_verdict
FAILED tests/test_gate_commit_status_fork_tolerance.py::test_fork_read_only_403_preserves_failure_verdict
FAILED tests/test_gate_commit_status_fork_tolerance.py::test_fork_read_only_403_fails_closed_for_other_non_success_verdicts[error-runner errored]
FAILED tests/test_gate_commit_status_fork_tolerance.py::test_fork_read_only_403_fails_closed_for_other_non_success_verdicts[pending-checks still pending]
FAILED tests/test_gate_commit_status_fork_tolerance.py::test_deleted_fork_read_only_403_reports_the_verdict
========================= 6 failed, 8 passed in 0.46s ==========================
```

## GREEN: exact restoration

Restore the predicate exactly and rerun the same command. Literal output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.2, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/teacher/.codex/automations/pd-workloop-resume/worktrees/Manager-Mosaic-issue-76
configfile: pyproject.toml
plugins: langsmith-0.10.9, cov-7.1.0, xdist-3.8.0, rerunfailures-16.3, datadir-1.8.0, typeguard-4.5.1, asyncio-1.3.0, pytest_httpserver-1.1.3, hypothesis-6.155.7, regressions-2.11.0, Faker-40.39.0, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 14 items

tests/test_gate_commit_status_fork_tolerance.py ..............           [100%]

============================== 14 passed in 0.46s ==============================
```

The following restoration proof then exited 0 with no output:

```text
git diff --exit-code HEAD -- .github/workflows/pr-00-gate.yml tests/test_gate_commit_status_fork_tolerance.py
```

Production workflow and test sources are unchanged on this branch; only this
evidence document is added.
