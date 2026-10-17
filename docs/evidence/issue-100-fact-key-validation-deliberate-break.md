# Deliberate-break evidence: fact_key registry validation (#100)

Target test file: `tests/test_fact_key_registry.py`
Production change: `validate_fact_keys` / `UnregisteredFactKeyError` in
`src/manager_mosaic/fact_keys.py`, plus opt-in `strict_fact_keys=True` in
`src/manager_mosaic/thesis.py::evaluate_claim`.

## RED before the change

Before the validator existed, the new tests failed at collection:

```
ImportError: cannot import name 'UnregisteredFactKeyError' from 'manager_mosaic.fact_keys'
ERROR tests/test_fact_key_registry.py
1 error in 0.18s
```

## Deliberate break (scope change disconnected)

Temporarily replaced the body of `validate_fact_keys` in
`src/manager_mosaic/fact_keys.py` with an early `return []` (registry
validation disconnected), then ran:

```
python -m pytest tests/test_fact_key_registry.py::test_opted_in_validation_reports_unregistered_key_instead_of_insufficient_evidence tests/test_fact_key_registry.py::test_validate_fact_keys_returns_all_violations_in_one_pass -q --no-cov
```

Result: `2 failed`. Example failure:

```
FAILED tests/test_fact_key_registry.py::test_validate_fact_keys_returns_all_violations_in_one_pass
AssertionError: assert set() == {('claim-a', 'performance.irrr'), ('claim-b', 'fees.unknown'),
  ('ev-2', 'liquidity.unknown'), ('ev-3', 'performance.irrr')}
```

## GREEN after restore

Restored `src/manager_mosaic/fact_keys.py` and reran:

```
$ python -m pytest tests/test_fact_key_registry.py -q --no-cov
8 passed in 0.11s
```

The canonical `python -m pytest tests/test_fact_key_registry.py -q` also
collects 8 tests and reports `8 passed`; its total-coverage gate (80%,
configured repo-wide) reports 51.69% for this single-file run because
unrelated modules are barely exercised — a pre-existing single-file
coverage effect, not a test failure.

## Follow-up: discrepancy strict mode

Production change: opt-in `strict_fact_keys=True` in
`src/manager_mosaic/discrepancy.py::detect_numeric_discrepancies`, reusing
`validate_fact_keys` from `src/manager_mosaic/fact_keys.py`.

RED before: the two new discrepancy tests failed with
`TypeError: detect_numeric_discrepancies() got an unexpected keyword argument 'strict_fact_keys'` (2 failed, 8 passed).

Deliberate break: temporarily replaced the body of `validate_fact_keys`
in `src/manager_mosaic/fact_keys.py` with an early `return []`, then ran
`python -m pytest tests/test_fact_key_registry.py -q --no-cov`:
result `5 failed, 5 passed`, including both discrepancy regressions
(`DID NOT RAISE UnregisteredFactKeyError`). Restored the file and reran:
`10 passed`. The canonical `python -m pytest tests/test_fact_key_registry.py -q`
collects 10 tests and reports `10 passed` (exit 1 only from the repo-wide
80% total-coverage gate at 60.73% on this single-file run, as above).
Black: `black --check --line-length 100 --exclude '(\.workflows-lib|node_modules)' .` passes (99 files unchanged).

## Follow-up: primary-journey wiring parity

Production change: `detect_numeric_discrepancies` now accepts the same
`validate_fact_keys_opt_in=True` alias as `evaluate_claim`, and validates
`threshold_percent` before strict fact-key validation so legacy error
precedence is preserved. New regressions:
`test_primary_journey_pre_step_then_strict_steps_report_typo_end_to_end`
and `test_discrepancy_strict_mode_preserves_threshold_error_precedence`.

RED before: `2 failed` (`TypeError: ... unexpected keyword argument
'validate_fact_keys_opt_in'`; threshold test got
`UnregisteredFactKeyError` instead of the `threshold_percent` ValueError).

Deliberate break: temporarily replaced the body of `validate_fact_keys`
in `src/manager_mosaic/fact_keys.py` with an early `return []`, then ran
`python -m pytest tests/test_fact_key_registry.py -q --no-cov`:
result `6 failed, 6 passed`. Restored the file and reran:
`12 passed`. Canonical `python -m pytest tests/test_fact_key_registry.py -q`
collects 12 tests and reports `12 passed` (the repo-wide 80%
total-coverage gate still applies to this single-file run, as above).

## Follow-up: evaluate_claim opt-in alias and fact-only typo

New regressions:
`test_evaluate_claim_opt_in_alias_reports_fact_only_unregistered_key`
(registered claim, typo'd fact: legacy `insufficient_evidence`, both
`strict_fact_keys=True` and `validate_fact_keys_opt_in=True` raise with
`('ev-irr-typo', 'performance.irrr', 'fact')`) and
`test_evaluate_claim_opt_in_alias_evaluates_registered_keys`.
PRODUCT_CONTRACT journey step 5 now documents the alias for `evaluate_claim`.

Deliberate break: temporarily inserted an early `return []` in
`validate_fact_keys` in `src/manager_mosaic/fact_keys.py`, then ran
`python -m pytest tests/test_fact_key_registry.py -q --no-cov`:
result `7 failed, 7 passed`, including
`test_evaluate_claim_opt_in_alias_reports_fact_only_unregistered_key`
(`DID NOT RAISE UnregisteredFactKeyError`). Restored the file
(`git checkout -- src/manager_mosaic/fact_keys.py`) and reran the
canonical `python -m pytest tests/test_fact_key_registry.py -q`:
collects 14 tests, `14 passed` (exit non-zero only from the repo-wide
80% total-coverage gate at 61.06% on this single-file run, as above).
Black: `python -m black --check --line-length 100 --workers 1 --exclude '(\.workflows-lib|node_modules)' .`
passes (99 files unchanged; `--workers 1` avoids the sandbox socket limit).

## Follow-up: validator identity and registry edge paths

New regressions: `test_validate_fact_keys_reports_identity_for_generic_records`
(`record_id`/`id`/`repr` identity, `record_kind`, `kind`),
`test_validate_fact_keys_accepts_single_records_bare_keys_and_custom_registries`
(single record, bare key string, empty input, in-memory/`Path`/`registry_path`
registries), and `test_validate_fact_keys_rejects_records_without_fact_key_and_bad_registries`
(`TypeError` for a record without `fact_key`; `ValueError` for empty/missing
registry `keys`).

Deliberate break: temporarily inserted an early `return []` in
`validate_fact_keys` in `src/manager_mosaic/fact_keys.py`, then ran the two
new identity/input regressions plus
`test_opted_in_validation_reports_unregistered_key_instead_of_insufficient_evidence`:
result `3 failed`. Restored the file (`git checkout -- src/manager_mosaic/fact_keys.py`)
and reran: `19 passed`.

Canonical `python -m pytest tests/test_fact_key_registry.py -q` collects
19 tests and reports `19 passed` (total coverage 66.39% on this single-file
run, below the repo-wide 80% gate, as above). Targeted coverage
`pytest tests/test_fact_key_registry.py --cov=manager_mosaic.fact_keys --cov-report=term-missing -q -m "not slow" --override-ini="addopts=" --cov-config=/dev/null`
reports `src/manager_mosaic/fact_keys.py` at 99% (1 miss, line 81).
Black check above passes (99 files unchanged).

## Follow-up: claim-and-facts unregistered rather than insufficient_evidence

New regression:
`test_opted_in_validation_reports_claim_and_facts_rather_than_insufficient_evidence`
(claim `performance.irrr` + fact `liquidity.unknownn`: legacy
`insufficient_evidence`, explicit `validate_fact_keys` reports both with
`record_kind`/`kind`, strict `evaluate_claim` raises both).

Deliberate break: temporarily inserted an early `return []` in
`validate_fact_keys` in `src/manager_mosaic/fact_keys.py`, then ran the new
regression: result `1 failed`. Restored the file and reran canonical
`python -m pytest tests/test_fact_key_registry.py -q`: collects 20 tests,
`20 passed` (total coverage 66.39% on this single-file run, below the
repo-wide 80% gate, as above). Black: 99 files unchanged.
