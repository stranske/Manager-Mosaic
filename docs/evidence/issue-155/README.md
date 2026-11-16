# Issue #155 — relative-spread boundary float fix

## Deliberate break

Temporarily restored the division-based spread at `discrepancy.py:64`:

```python
normalized_difference = abs(left / baseline - right / baseline)
spread = max(spread, normalized_difference * 100.0)
```

[RED output](155-named-red.txt): `test_exact_threshold_boundaries_are_not_flagged` — **8 failed**, 2 passed (adjacent controls only).

## Restore

Replaced with `abs(Fraction(left) - Fraction(right)) / Fraction(baseline)` so exact 5%/10% boundaries stay at or below the threshold under `<=` comparison.

[GREEN output](155-named-green.txt): **10 passed**.