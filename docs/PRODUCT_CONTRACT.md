# Product contract

This document is the canonical list of Manager-Mosaic's user-facing core
functions. The repository operates on local files and synthetic or public test
data; it does not require a hosted service or database.

## Core functions

| ID | A user can | Entry point | Observable outcome |
| --- | --- | --- | --- |
| CF-1 | An analyst can load a hand-edited mosaic store and validate it. | `manager_mosaic.model.validate(Store)` | All structural violations are returned in one pass; a valid store returns `[]`. |
| CF-2 | An analyst can derive coverage gaps without changing entry status. | `manager_mosaic.model.derive_gaps(Store)` | Missing mentions in active periods are listed as gaps; silence does not change an entry's status. |
| CF-3 | An analyst can compare evidence for the same fact and see numeric conflicts. | `manager_mosaic.discrepancy.detect_numeric_discrepancies(facts)` | Conflicting values for a normalized `(fact_key, entity_ref, period)` surface as `numeric_delta` discrepancies. |
| CF-4 | An analyst can evaluate an investment-thesis claim against available facts. | `manager_mosaic.thesis.evaluate_claim(claim, facts)` | The latest normalized-period facts produce `supported`, `at_risk`, `contradicted`, or `insufficient_evidence`. |
| CF-5 | An analyst can validate an `evidence-object/v1` payload and see every defect. | `manager_mosaic.validate_evidence_object(payload)` | Schema and excerpt-presence violations are returned in one pass; a valid payload returns `[]`. |
| CF-6 | An operator can validate a consumer ingest fixture offline and see whether it conforms. | `scripts/validate_run_contract.py <fixture> --registry config/backplane_participants.json` | Declared consumer `ingests` are checked; a non-conformant fixture exits non-zero. |

## Primary user journey

1. Load a local mosaic store and run `validate`.
2. Run `derive_gaps` to surface missing coverage without inferring an exit.
3. Build evidence-linked `FactRecord` values from source material.
4. Run `detect_numeric_discrepancies` across comparable facts.
5. Run `evaluate_claim` for each investment-thesis claim.
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

