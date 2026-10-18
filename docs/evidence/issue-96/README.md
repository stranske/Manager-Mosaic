# Raw store validation evidence

The original 129 tests reproduce the recorded 91.50% coverage. With 23 additional raw-validation regressions, all 152 tests pass with 97.21% coverage, above the unchanged 80% gate. Targeted coverage of `manager_mosaic.model` is 96.47% (53 tests). The original 30 model tests and both schema copies remain byte-identical to the implementation baseline.

Removing only the structural-violation collection from `validate_payload` makes both unchanged combined-defect and missing-inferred regressions fail. Byte-identical restoration returns all 30 model tests green. No malformed value is coerced; independent semantic checks run only when their prerequisite inputs have usable types. `Store.from_dict` rejects malformed structure with one aggregate `ValueError` and retains structurally valid semantic inspection through `validate(Store)`.

Verified task checklist:

- [x] All original 129 tests pass; coverage exceeds the recorded 91.50% and existing 80% threshold. The expanded suite passes all 152 tests at 97.21%.
- [x] Combined defects include missing entry, period and mention fields, non-boolean `inferred`, string `bps`, numeric `size` and unknown references without construction exceptions.
- [x] Both unchanged regressions fail when structural collection is disconnected; exact restoration returns all 30 original model tests green.
- [x] Focused mypy, Black, Ruff and diff checks pass; both schema copies are unchanged.

Current raw proof (commands and exit codes are included):

- [Full suite and coverage](96-current-full-coverage.txt)
- [Targeted model coverage](96-current-targeted-coverage.txt)
- [Structural collection disconnected](96-current-red.txt)
- [Exact restoration](96-current-green.txt)
- [Mypy, Ruff, diff and schema identity](96-current-quality.txt)
- [Repository Black gate](96-current-black.txt)

Black's default workers cannot start inside this sandbox. Each of the 100 included Python files passed an individual check with a writable cache directory; the required repository-wide command then passed using that cache and `BLACK_NUM_WORKERS=1`. The original evidence logs are retained alongside these current results.
