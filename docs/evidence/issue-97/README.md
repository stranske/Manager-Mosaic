# Public evidence identity proof

131tests PASS with94.03percent coverage. Focused mypy/Black/Ruff/diff pass. Three unchanged individual identity regressions and the combined schema/excerpt/identity regression fail after removing only the public helper call; exact-byte restoration returns the whole suite green. Tests also preserve page0, leap day, unknown dates, earlier-byte supersession, legacy payloads and safe malformed-container reporting. Three real standalone CLI subprocesses agree with the public package validator. Schema files and the standalone validator are unchanged.
