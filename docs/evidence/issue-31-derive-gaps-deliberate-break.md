# Deliberate-break evidence: `derive_gaps` silence invariant (#31 / #3)

Command: `pytest tests/test_model_validation.py::test_derive_gaps_leaves_status_unchanged -q --no-cov`

## RED (temporary mutation in `derive_gaps`)

After inserting `object.__setattr__(entry_item, "status", "EXITED")` when a coverage gap is detected:

```
FAILED tests/test_model_validation.py::test_derive_gaps_leaves_status_unchanged
AssertionError: assert 'EXITED' == 'ACTIVE'
  - ACTIVE
  + EXITED
```

## GREEN (production `derive_gaps` restored)

```
1 passed
```

Production code is unchanged on this branch; only this evidence file is added.
