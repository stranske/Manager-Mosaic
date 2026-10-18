# Product contract

This document is the canonical list of Manager-Mosaic's user-facing core
functions. The repository operates on local files and synthetic or public test
data; it does not require a hosted service or database.

## Core functions

| ID | A user can | Entry point | Observable outcome |
| --- | --- | --- | --- |
| CF-1 | An analyst can load a hand-edited mosaic store and validate it. | `manager_mosaic.validate_payload(raw_mapping)` then `Store.from_dict`; `validate(Store)` for typed models | Raw structure and applicable semantic violations are returned together with source paths; malformed structure raises one aggregated ValueError before construction. Valid payloads return `[]`. |
| CF-2 | An analyst can derive coverage gaps without changing entry status. | `manager_mosaic.model.derive_gaps(Store)` | Missing mentions in active periods are listed as gaps; silence does not change an entry's status. |
| CF-3 | An analyst can compare evidence for the same fact and see numeric conflicts. | `manager_mosaic.discrepancy.detect_numeric_discrepancies(facts)` | Conflicting values for a normalized `(fact_key, entity_ref, period)` surface as `numeric_delta` discrepancies. |
| CF-4 | An analyst can evaluate an investment-thesis claim against available facts. | `manager_mosaic.thesis.evaluate_claim(claim, facts)` | The latest normalized-period facts produce `supported`, `at_risk`, `contradicted`, or `insufficient_evidence`. |
| CF-7 | An analyst can check fact and claim keys against the registered vocabulary before evaluation. | `manager_mosaic.fact_keys.validate_fact_keys(facts, claims)` or `evaluate_claim(claim, facts, strict_fact_keys=True)` | Every unregistered `fact_key` is returned in one pass as a `FactKeyViolation` with record identity (`claim_id` for claims, `evidence_id` for facts); strict mode raises `UnregisteredFactKeyError`. A valid input returns `[]`. Opt-in only: callers omitting validation retain previous behaviour. |
| CF-5 | An analyst can validate an `evidence-object/v1` payload and see every defect. | `manager_mosaic.validate_evidence_object(payload)` | Schema and excerpt-presence violations are returned in one pass; a valid payload returns `[]`. |
| CF-6 | An operator can validate a consumer ingest fixture offline and see whether it conforms. | `scripts/validate_run_contract.py <fixture> --registry config/backplane_participants.json` | Declared consumer `ingests` are checked; a non-conformant fixture exits non-zero. |

## Primary user journey

1. Parse the local JSON and run `validate_payload(raw_mapping)` to report all structural and applicable semantic defects. `Store.from_dict` checks raw structure before construction and raises one aggregated `ValueError`; use `validate(Store)` for typed semantic checks. Invalid prerequisite fields skip only dependent checks; malformed values are never coerced.
2. Run `derive_gaps` to surface missing coverage without inferring an exit.
3. Build evidence-linked `FactRecord` values from source material, then explicitly validate fact keys (opt-in): run `manager_mosaic.fact_keys.validate_fact_keys(facts, claims=[claim])` for one claim (or `claims=claims` for a prepared collection), which checks every key against `load_fact_key_registry()` and returns all unregistered-key violations with record identity in one pass. Alternatively pass `strict_fact_keys=True` to `evaluate_claim` (step 5) to raise `UnregisteredFactKeyError` instead of returning `insufficient_evidence` for a typo'd key. Callers that omit both retain the previous behaviour.
4. Run `detect_numeric_discrepancies` across comparable facts (or `detect_numeric_discrepancies(..., strict_fact_keys=True)` per the opt-in in step 3 — the `validate_fact_keys_opt_in=True` alias spelling from step 5 is also accepted — so a typo'd key raises `UnregisteredFactKeyError` instead of silently forming an unrelated group).
5. Run `evaluate_claim` for each investment-thesis claim (or `evaluate_claim(..., strict_fact_keys=True)` per the opt-in in step 3 — the `validate_fact_keys_opt_in=True` alias spelling is also accepted, and a fact-only typo raises with the fact's `evidence_id` instead of returning `insufficient_evidence`).
6. Validate every linked evidence payload with `validate_evidence_object`.

## Probe commands

Run the core-function probes from the repository root:

```bash
python3 -m pytest -q --no-cov tests/test_model_validation.py tests/test_discrepancy_detection.py tests/test_thesis_monitoring.py tests/test_evidence_validation.py tests/test_backplane_fixtures.py
```

Run the contract-presence gate independently:

```bash
python3 -m pytest -q --no-cov tests/test_repo_hygiene.py::test_product_contract_documents_core_functions
```

## Caller-supplied fact provenance

Local `manager_mosaic.model.FactRecord(..., basis="observed" | "inferred" | "unknown")`
preserves a caller's explicit basis. The existing import from
`manager_mosaic.discrepancy` remains an alias of the same class. `observed` labels
an observation supported directly by source evidence; `inferred` labels a derived
assertion. `unknown` means the basis has not been established, not that a fact is
observed. The default is `unknown`, so the old five-argument
constructor stays valid without inventing observed status. Unsupported bases
including explicit `None` raise `ValueError`; use `unknown` or omit the argument
for an unset basis. Extraction `method` records production/extraction, not this
classification, and is never mapped to a basis implicitly.
The caller must establish this label from separately validated source evidence.

`DiscrepancyRecord.contributing_facts` retains every competing FactRecord with
its value, evidence ID and basis. `ThesisCheck.contributing_facts` retains every
matching latest-period fact; mixed bases and repeated evidence IDs remain
separate associations. Both result types also expose that provenance directly:
`bases` returns the basis of each contributing fact in `contributing_facts`
order, and `evidence_bases` returns the `(evidence_id, basis)` pair for each
contributing fact without deduplicating repeated evidence IDs. Legacy result
constructors leave both empty. `FactRecord` and `FactBasis` are also importable
from the top-level `manager_mosaic` package, identical to the `model` classes. Legacy result constructors still accept their original arguments (the added tuple defaults empty). ThesisCheck equality retains its
legacy claim/verdict/evidence-ID semantics; the supplemental contributing-fact
associations remain inspectable and are excluded from that comparison. Existing `evidence_ids` conventions,
thresholds, chronological selection and verdicts remain unchanged. Unknown or
inferred facts are not excluded from evaluation. Mention.inferred and shared
interchange schemas remain under their existing validation owners. Mention boolean
validation is covered by the merged store-validation candidate and is excluded
from this fact-provenance change.
