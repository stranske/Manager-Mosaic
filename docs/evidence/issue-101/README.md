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

## Direct result provenance accessors (follow-up)

`DiscrepancyRecord` and `ThesisCheck` now also expose `bases` and
`evidence_bases` derived from `contributing_facts` (no deduplication of
repeated evidence IDs; legacy constructors leave them empty), and
`FactRecord`/`FactBasis` are importable from the top-level `manager_mosaic`
package. New regressions in `tests/test_model_validation.py`:
`test_result_provenance_accessors_expose_inferred_only_and_mixed_bases`,
`test_result_provenance_accessors_keep_legacy_facts_unknown`, and
`test_top_level_fact_provenance_exports_match_model`.
Observed this session: `python -m pytest tests/test_model_validation.py -q`
collected 56 tests, all passed (whole-package coverage gate is only met by
the full suite); focused model/discrepancy/thesis run passed 93 tests;
full suite passed 218 tests. Deliberate break: forcing `basis` to
`unknown` in `src/manager_mosaic/model.py` made the named accessor
regression fail with `('unknown',) == ('inferred',)` (exit 1); restoring
`model.py` byte-for-byte made it pass (exit 0). Both outputs are in
[model-provenance-accessors-break.txt](model-provenance-accessors-break.txt).

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

## Observed-only and discrepancy legacy-unknown accessors (follow-up)

New regression `test_result_provenance_accessors_observed_only_and_discrepancy_legacy_unknown`
in `tests/test_model_validation.py` covers the accessor matrix not previously
asserted directly: observed-only `ThesisCheck.bases`/`evidence_bases`, a mixed
observed/inferred `DiscrepancyRecord`, and legacy discrepancy facts staying
`unknown` with a repeated evidence ID retained twice.

Observed this session:

- `python -m pytest tests/test_model_validation.py -q` — collected 57 tests,
  **57 passed**; the process exits 1 only on the whole-package coverage gate
  (73.02% < 80% when a single test file runs against all of `src/`). The full
  suite below meets that gate.
- `python -m pytest tests/test_model_validation.py tests/test_discrepancy_detection.py tests/test_thesis_monitoring.py --no-cov -q -m 'not slow'`
  — **94 passed**, exit 0.
- `python -m pytest -q -m 'not slow'` — **219 passed**, exit 0, coverage 97.68%.
- Deliberate break: forcing `basis` to `unknown` in
  `src/manager_mosaic/model.py` made the new regression fail with
  `('unknown',) == ('observed',)` (exit 1); restoring `model.py` byte-for-byte
  (`cmp` identical) made it pass (exit 0). Both outputs are in
  [model-provenance-observed-only-break.txt](model-provenance-observed-only-break.txt).

## Value-associated provenance accessors (follow-up)

`DiscrepancyRecord` and `ThesisCheck` now also expose `value_bases`: the
`(value, evidence_id, basis)` association for each contributing fact, in
contributing order and without deduplication. This keeps a basis tied to its
value when values are equal or an evidence ID repeats, which
`bases`/`evidence_bases` alone cannot show. Legacy result constructors leave
it empty. The audit catalog and `contract-enforcement-audit.md` gained
matching `value_bases` rows, as the repo hygiene gate requires.

New regression
`test_result_value_bases_retain_basis_to_value_evidence_association` in
`tests/test_model_validation.py` covers an equal-value mixed-basis thesis
result sharing one evidence ID, an observed-only discrepancy, and a mixed
discrepancy; `test_fact_provenance_preserves_legacy_result_constructors` now
also asserts `value_bases == ()` for both legacy constructors.

Observed this session:

- `python -m pytest tests/test_model_validation.py -q` — collected 58 tests,
  **58 passed**; the process exits 1 only on the whole-package coverage gate
  (73.21% < 80% when a single test file runs against all of `src/`). The full
  suite below meets that gate.
- `python -m pytest tests/test_model_validation.py tests/test_discrepancy_detection.py tests/test_thesis_monitoring.py --no-cov -q -m 'not slow'`
  — **95 passed**, exit 0.
- `python -m pytest -q -m 'not slow'` — **220 passed**, exit 0, coverage 97.70%.
- `BLACK_CACHE_DIR=/tmp/mm-black-cache BLACK_NUM_WORKERS=1 black --check --line-length 100 --exclude '(\.workflows-lib|node_modules)' .`
  — passed, **102 files unchanged**, exit 0 (single-worker/cache env only
  avoids the sandbox socket restriction on Black's process runner).
- Deliberate break: forcing `basis` to `unknown` in
  `src/manager_mosaic/model.py` made the new regression fail with
  `(8.0, 'shared', 'unknown') != (8.0, 'shared', 'inferred')` (exit 1);
  restoring `model.py` byte-for-byte (`sha256sum -c` OK, `cmp` identical)
  made it pass (exit 0). Both outputs are in
  [model-provenance-value-bases-break.txt](model-provenance-value-bases-break.txt).

## Inferred-only discrepancy and legacy value_bases (follow-up)

New regression `test_result_value_bases_inferred_only_discrepancy_and_legacy_results`
in `tests/test_model_validation.py` covers the accessor combinations not
previously asserted directly: an inferred-only `DiscrepancyRecord`
(`bases`/`evidence_bases`/`value_bases` all inferred, repeated evidence ID
retained), a legacy thesis fact staying `unknown` in `value_bases`, and legacy
discrepancy facts staying `unknown` in `value_bases` with a repeated evidence
ID retained twice.

Observed this session:

- `python -m pytest tests/test_model_validation.py -q` — collected 59 tests,
  **59 passed**; the process exits 1 only on the whole-package coverage gate
  (73.21% < 80% when a single test file runs against all of `src/`). The full
  suite below meets that gate.
- `python -m pytest tests/test_model_validation.py tests/test_discrepancy_detection.py tests/test_thesis_monitoring.py --no-cov -q -m 'not slow'`
  — **96 passed**, exit 0.
- `python -m pytest -q -m 'not slow'` — **221 passed**, exit 0, coverage 97.70%.
- `BLACK_CACHE_DIR=/tmp/mm-black-cache BLACK_NUM_WORKERS=1 black --check --line-length 100 --exclude '(\.workflows-lib|node_modules)' .`
  — passed, **102 files unchanged**, exit 0 (single-worker/cache env only
  avoids the sandbox socket restriction on Black's process runner).
- Deliberate break: forcing `basis` to `unknown` in
  `src/manager_mosaic/model.py` made the new regression fail with
  `('unknown', 'unknown') == ('inferred', 'inferred')` (exit 1); restoring
  `model.py` byte-for-byte (`sha256sum -c` OK, `cmp` identical) made it pass
  (exit 0). Both outputs are in
  [model-provenance-value-bases-inferred-legacy-break.txt](model-provenance-value-bases-inferred-legacy-break.txt).

## Direct-construction accessors and invalid-basis message (follow-up)

`FactRecord` now lists the supported bases in its rejection
(`unsupported fact basis: ...; expected one of 'observed', 'inferred', 'unknown'`),
and new regressions cover directly constructed `DiscrepancyRecord`/`ThesisCheck`
provenance accessors, empty accessors for `insufficient_evidence`, and
case/whitespace basis variants (`OBSERVED`, `""`, `" inferred"`, …).

Observed this session:

- `python -m pytest tests/test_model_validation.py -q --no-cov` — **66 passed**.
- Focused model/discrepancy/thesis run — **103 passed**; full suite — **228 passed**, coverage 97.70%.
- `black --workers 1 --check --line-length 100 --exclude '(\.workflows-lib|node_modules)' .` — **102 files unchanged**.
- Deliberate break: removing the basis-validation raise in `model.py` made
  12 invalid-basis tests fail (`DID NOT RAISE ValueError`); byte-for-byte
  restore (`cmp` identical) made all 66 pass. See
  [model-provenance-invalid-basis-break.txt](model-provenance-invalid-basis-break.txt).

## FACT_BASES source of truth and latest-period accessors (follow-up)

`manager_mosaic.model.FACT_BASES` is now the canonical supported-basis tuple;
`FactRecord` validation and its rejection message derive from it instead of a
duplicated literal, and it is exported as `manager_mosaic.FACT_BASES`. New
regressions in `tests/test_model_validation.py`:
`test_fact_bases_constant_is_the_validation_source` and
`test_thesis_provenance_accessors_only_include_latest_period_facts` (an older
observed fact leaks no basis into a latest-period mixed inferred/observed check).

Observed this session:

- `python -m pytest tests/test_model_validation.py -q` — collected 68 tests,
  **68 passed**; the process exits 1 only on the whole-package coverage gate
  (73.24% < 80% for a single file), as in prior follow-ups. The full suite
  below meets that gate.
- `python -m pytest tests/test_model_validation.py tests/test_discrepancy_detection.py tests/test_thesis_monitoring.py --no-cov -q -m 'not slow'`
  — **105 passed**, exit 0.
- `python -m pytest -q -m 'not slow'` — **230 passed**, exit 0, coverage 97.70%.
- Deliberate break: removing `'inferred'` from `FACT_BASES` in
  `src/manager_mosaic/model.py` made both new regressions fail (exit 1);
  restoring `model.py` byte-for-byte (`cmp` identical, sha256
  `d15539bad40c28f79a71d372d06455a0c11ce87a15656ea8b0cc3453413fb9cd`) made them
  pass (exit 0). Both outputs are in
  [model-provenance-fact-bases-break.txt](model-provenance-fact-bases-break.txt).

## Explicit-unknown accessor provenance (follow-up)

New regression `test_result_provenance_accessors_treat_explicit_unknown_as_unset`
in `tests/test_model_validation.py`: an explicit `basis="unknown"` exposes the
same `bases`/`evidence_bases`/`value_bases` unknown provenance as a legacy
omitted basis on `ThesisCheck`, and stays unknown beside an inferred fact with a
repeated evidence ID in both `ThesisCheck` and `DiscrepancyRecord`.

Observed this session:

- `python -m pytest tests/test_model_validation.py -q` — **69 passed**
  (single-file coverage gate 73% < 80% exits 1 as before; full suite below).
- Deliberate break: removing `'unknown'` from `FACT_BASES` in
  `src/manager_mosaic/model.py` made the new regression fail with
  `ValueError: unsupported fact basis: 'unknown'`; byte-for-byte restore
  (`cmp` identical, sha256
  `d15539bad40c28f79a71d372d06455a0c11ce87a15656ea8b0cc3453413fb9cd`) made it
  pass. See
  [model-provenance-explicit-unknown-break.txt](model-provenance-explicit-unknown-break.txt).

## Non-string invalid-basis rejection (follow-up)

New regression `test_fact_provenance_rejects_nonstring_basis_values` in
`tests/test_model_validation.py` covers non-string bases not previously
asserted directly (`1`, `1.5`, `b"observed"`, `("observed",)`, `["observed"]`)
on both the canonical `manager_mosaic.model.FactRecord` and the legacy
`manager_mosaic.discrepancy.FactRecord` import: each is rejected with
`unsupported fact basis ... 'observed', 'inferred', 'unknown'`, with no
coercion of bytes or sequence-wrapped values.

Observed this session:

- `python -m pytest tests/test_model_validation.py -q` — **74 passed**
  (single-file coverage gate 73.24% < 80% exits 1 as before; full suite below).
- `python -m pytest tests/test_model_validation.py tests/test_discrepancy_detection.py tests/test_thesis_monitoring.py --no-cov -q -m 'not slow'`
  — **111 passed**, exit 0.
- `python -m pytest -q -m 'not slow'` — **236 passed**, exit 0, coverage 97.70%.
- `BLACK_CACHE_DIR=/tmp/mm-black-cache BLACK_NUM_WORKERS=1 black --check --line-length 100 --exclude '(\.workflows-lib|node_modules)' .`
  — passed, **102 files unchanged**, exit 0.
- Deliberate break: replacing the `if self.basis not in FACT_BASES:` guard in
  `src/manager_mosaic/model.py` with `if False:` made all 5 new cases fail
  with `DID NOT RAISE ValueError`; byte-for-byte restore (`cmp` identical,
  sha256 `d15539bad40c28f79a71d372d06455a0c11ce87a15656ea8b0cc3453413fb9cd`)
  made them pass (5 passed). See
  [model-provenance-nonstring-basis-break.txt](model-provenance-nonstring-basis-break.txt).
