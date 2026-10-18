# Raw store validation evidence

- [x] `rg -n "validate_payload" src/manager_mosaic/__init__.py docs/PRODUCT_CONTRACT.md`
  confirms the import, `__all__` export, and CF-1 documentation reference.

The public API follow-up checks the declared export and reports missing `inferred`
and an unknown period together through `manager_mosaic.validate_payload`.
Removing the export from `__all__` in memory makes the strengthened regression fail;
the unchanged package passes all 21 payload cases and all 160 suite tests with
97.34% coverage (`-m "not slow"`).

Follow-up verification adds seven regression cases for validating every entry before
construction and preserving unknown-period diagnostics when currency fields have
non-string values. All 159 tests pass at 97.34% coverage. The required payload
selection passes all 20 cases. [Follow-up deliberate-break proof](96-followup-validation.txt)
records expected failures after disconnecting structural diagnostics, constructor
admission, and currency type checking individually, followed by byte-identical
source restoration and all 37 model tests passing.

All six implementation tasks and five acceptance criteria are verified. Updating
PR #111's checkboxes was rejected because the GitHub tool requires approval while
this run uses approval policy `never`; its reconciled body is prepared at
`/tmp/manager-mosaic-pr-111-body.md` for application by an authorized operator.
Committing the follow-up is also blocked: `.git` is read-only, and `git add`
fails to create `.git/index.lock`. The changes remain in the working tree.
The repository-wide Black gate, Ruff, source mypy and diff checks pass. Running
mypy on the model test file also reports its pre-existing unannotated `bad_sort`
loop variable at line 169; that unrelated code is unchanged.

The previous iteration's original 129 tests reproduce the recorded 91.50% coverage. With 23 additional raw-validation regressions, all 152 tests passed with 97.21% coverage, above the unchanged 80% gate. Targeted coverage of `manager_mosaic.model` was 96.47% (53 tests). At that point, the original 30 model tests and both schema copies were byte-identical to the implementation baseline; this follow-up appends seven model cases without changing those existing tests or the schemas.

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

Serial opener review recovery after native1464b619: all4 native implementation/push attempts directlyterminal, exclusive source96/PR111 claims and temporary future-start pause. Preserved every native test/evidence addition. Schema objects now accept Mapping including nested MappingProxyType; unusable period/document collections suppress only dependent references; four non-Mapping top-level cases produce diagnostics and aggregated ValueError. All5 unchanged Mapping/document-collection regressions fail on native production, exact restoration GREEN. Final169fullPASS/97.64percentcoverage; focused mypy/Black/Ruff/diffPASS.
