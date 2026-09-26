# Deliberate-break evidence: `evaluate_claim` min threshold (#32 / #13)

Issue `stranske/Manager-Mosaic#32` requires RED/GREEN output for temporarily inverting the `min`
comparison in `src/manager_mosaic/thesis.py::evaluate_claim`.

## Named gate (GREEN on `main`)

```text
pytest tests/test_thesis_monitoring.py::test_evaluate_claim_marks_contradicted_when_irr_below_min_threshold -q --no-cov
```

```
============================== 1 passed in 11.73s ==============================
```

## Deliberate break

In `evaluate_claim`, for `expected_pattern == "min"`, replace:

`contradicted = [fact.value < claim.threshold for fact in latest_facts]`

with:

`contradicted = [fact.value >= claim.threshold for fact in latest_facts]`

Re-run the named gate:

```
FAILED tests/test_thesis_monitoring.py::test_evaluate_claim_marks_contradicted_when_irr_below_min_threshold
AssertionError: assert 'supported' == 'contradicted'
============================== 1 failed in 6.03s ===============================
```

## Revert

Restore the original `<` comparison and re-run the named gate (same command as GREEN above).

```
============================== 1 passed in 11.73s ==============================
```
