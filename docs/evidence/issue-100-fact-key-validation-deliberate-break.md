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
