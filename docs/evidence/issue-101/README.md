# Fact provenance proof

The local fact representation lives in `src/manager_mosaic/model.py`;
`manager_mosaic.discrepancy.FactRecord` and `FactBasis` remain compatibility
aliases. Basis is caller-supplied `observed`, `inferred`, or `unknown` (default).
Evidence extraction method does not establish a basis. Result tuples preserve
individual contributing facts, including equal values, repeated evidence IDs,
and exact duplicates. Existing comparison and thesis policies are unchanged.

## Verified tasks

- [x] Define and document observed/inferred/unknown provenance with compatible constructors.
- [x] Preserve contributing fact/evidence associations in discrepancy and thesis results.
- [x] Test inferred-only, observed-only, mixed, legacy-unknown, and invalid bases in `tests/test_model_validation.py`; document the caller boundary.
- [x] Record scope, compatibility, exclusions, and observable results in README.md.

## Verified acceptance criteria

- [x] Inferred latest-period facts expose inferred provenance; mixed latest facts retain both associations.
- [x] Discrepancies preserve each value/evidence/basis association, including repeated IDs and exact duplicates.
- [x] Legacy facts default to unknown; unsupported explicit bases raise a clear ValueError.
- [x] Existing thresholds, latest-period selection, same-period conflicts, and verdict tests pass.
- [x] PRODUCT_CONTRACT.md defines the field, default, and caller responsibility without method-to-basis inference.
- [x] `python -m pytest tests/test_model_validation.py -q` collected and passed 32 tests (environment options below).
- [x] The named regression fails after disconnecting basis preservation in `model.py` and passes after byte-for-byte restoration.

## Commands and captured results

- `PYTEST_ADDOPTS="--no-cov -m 'not slow'" python -m pytest tests/test_model_validation.py -q`
  — **32 passed**, exit 0. [Full model transcript](model-provenance-verification.txt).
  The environment options skip slow tests and disable whole-package coverage for
  this focused behavior probe; the full suite separately enforces coverage.
- `python -m pytest tests/test_model_validation.py tests/test_discrepancy_detection.py tests/test_thesis_monitoring.py --no-cov -q -m 'not slow'`
  — **61 passed**, exit 0.
- `python -m pytest -q -m 'not slow'` — **131 passed**, exit 0, including the
  repository's coverage gate. [Full-suite transcript](model-provenance-full-suite.txt).
- `mypy src/manager_mosaic` and
  `ruff check src/manager_mosaic tests/test_model_validation.py` — passed.
  An additional mypy check including the test file found the pre-existing
  unannotated `bad_sort` loop variable; this change leaves that unrelated test intact.
- `BLACK_CACHE_DIR=/tmp/manager-mosaic-black-cache BLACK_NUM_WORKERS=1 black --check --line-length 100 --exclude '(\.workflows-lib|node_modules)' .`
  — passed, **99 files unchanged**, exit 0. Relevant files were first formatted
  with Black at line length 100. Because this sandbox blocks Black's process
  runner and its default cache is not writable, individual file checks primed
  the writable temporary cache before the required repository-wide command.

The regressions `test_fact_provenance_survives_latest_thesis_and_discrepancy`,
`test_fact_provenance_legacy_constructor_defaults_to_unknown`, and
`test_fact_provenance_rejects_unsupported_basis` cover the basis matrix.
`test_model_fact_provenance_preserves_explicit_basis_and_legacy_import` checks
the shared model and legacy import through an inferred-only thesis result.
`test_fact_provenance_keeps_equal_values_and_duplicate_associations` checks
association multiplicity, and `test_fact_provenance_preserves_legacy_result_constructors`
checks the original result constructor signatures.

For the deliberate break, temporarily replace the basis validation in
`model.py` with `object.__setattr__(self, "basis", "unknown")`.
The unchanged named model regression fails with `'unknown' == 'inferred'`
(exit 1); restore the original bytes and the same command passes (exit 0).
[Both command outputs](model-provenance-deliberate-break.txt) are retained.
The temporary mutation is absent from the delivered source.

Mention boolean validation belongs to the merged store-validation candidate.
This scope adds no extraction adapter, hosting layer, evidence-method mapping,
or shared interchange schema changes. The original implementation's historical
builder-level break and test logs remain in `101-final-red.txt` and
`101-full-final.txt`; the model-level proof above supplements them.

## Delivery blocker

The requested commit was attempted after verification, but the sandbox mounts
`.git` read-only. `git add` failed with
`fatal: Unable to create '.git/index.lock': Read-only file system`.
The verified changes remain in the working tree; a runner with a writable Git
metadata directory must stage and commit them.
