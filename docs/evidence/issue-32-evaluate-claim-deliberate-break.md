# Deliberate-break evidence: `evaluate_claim` min comparison (#32 / #13)

Command: `pytest tests/test_thesis_monitoring.py::test_evaluate_claim_marks_contradicted_when_irr_below_min_threshold -q --no-cov`

## RED (temporary mutation in `evaluate_claim`)

After inverting the `min` pattern check from `fact.value < claim.threshold` to `fact.value > claim.threshold`:

```
FAILED tests/test_thesis_monitoring.py::test_evaluate_claim_marks_contradicted_when_irr_below_min_threshold
AssertionError: assert 'supported' == 'contradicted'
  - contradicted
  + supported
```

## GREEN (production `evaluate_claim` restored)

```
1 passed
```

Production code is unchanged on this branch; only this evidence file is added.
