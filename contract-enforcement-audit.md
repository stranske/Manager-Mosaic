# Public contract enforcement audit

Audited production snapshot: `2ec5f0998c7792c970c5de0dd863c118fb1377c0`
(the original audit base). The historical audit added tests and audit artifacts
without production edits. Subsequent implementation branches add production behavior.
Historical findings describe that source snapshot,
not the eventual behavior of related implementation PRs. Pending delivery is not
a passing implementation. All probes use local synthetic data.

Integration note (PR115): the canonical `FactRecord` and its validation hook now live in `model.py`; `discrepancy.FactRecord` remains a compatible alias. The machine inventory and corresponding entrypoint rows below follow that defining module and the existing source101 regression probes. Historical findings and their original snapshot remain preserved.

PR117 integration note: the four result-accessor catalog entries are explicitly
`branch-state`, verified at `a5d4d452bbe79d079f3352b835211ce8876f006d`. Their
`already-correct` accessor classifications do not revise the historical parent
result-type defects at the audit base. PR117 extends merged PR115 with ordered
accessors and top-level aliases; both implementations are retained.

## Contract boundaries and rule/path dispositions

The public journey is defined by [docs/PRODUCT_CONTRACT.md](docs/PRODUCT_CONTRACT.md).
CF-1 through CF-6 are inventoried below; CF-7 is also included because the current
contract explicitly makes vocabulary validation opt-in. The original scope's
claim that the registry has no evaluation callers is stale at this snapshot:
`thesis.evaluate_claim` and `discrepancy.detect_numeric_discrepancies` both call
`fact_keys.validate_fact_keys` when either strict-mode spelling is enabled.
Unflagged evaluation deliberately retains the legacy behavior.

| Rule / applicable path | Disposition, issue, and owner | Probing evidence and proposed regression |
| --- | --- | --- |
| CF-1: raw object shapes, required nested keys, scalar types, unknown fields; `Store.from_dict` / `Store.from_json` construct before checking the packaged store schema | confirmed-bug [#96](https://github.com/stranske/Manager-Mosaic/issues/96); consumer | `src/manager_mosaic/model.py:Store.from_dict`; `tests/test_model_validation.py::test_fixture_validates_against_json_schema` checks only the fixture. Proposed: send multiple malformed raw fields through a public payload validator and require all errors without constructor exceptions. Related implementation: [PR #111](https://github.com/stranske/Manager-Mosaic/pull/111). |
| CF-1: finite numeric values, references, chronology, source presence, duplicate IDs, vocabularies and currency truncation on typed stores | already-correct; consumer | `src/manager_mosaic/model.py:validate`; `tests/test_model_validation.py::test_validator_returns_all_four_defects` and `test_none_period_sort_does_not_abort_validation`. Preserve simultaneous-defect probes; raw structural failures are covered by the preceding issue. |
| CF-2: missing mentions produce gaps without inferring exit status; invalid ranges do not produce gaps | already-correct; consumer | `src/manager_mosaic/model.py:derive_gaps`; `tests/test_model_validation.py::test_derive_gaps_leaves_status_unchanged`, `test_inverted_entry_period_range_is_reported`. Preserve before/after status assertions. |
| CF-3: exact key/entity joins, normalized quarter grouping, finite input and nonnegative finite threshold | already-correct; consumer | `src/manager_mosaic/discrepancy.py:detect_numeric_discrepancies`, `src/manager_mosaic/periods.py:period_chronology_key`; `tests/test_discrepancy_detection.py::test_detect_numeric_discrepancies_groups_equivalent_period_labels`, `test_threshold_boundary_equality_and_just_over`. Preserve quarter aliases, raw-label fallback and threshold boundary probes. |
| CF-3: stable ID for normalized coordinates still uses the first raw period spelling | confirmed-bug [#98](https://github.com/stranske/Manager-Mosaic/issues/98); consumer | `src/manager_mosaic/discrepancy.py:detect_numeric_discrepancies`; `tests/test_discrepancy_detection.py::test_discrepancy_id_injective_for_colon_entity_refs` proves tuple injectivity, not alias-stable IDs. Proposed: permute equivalent quarter labels and require an identical discrepancy ID. Related implementation: [PR #113](https://github.com/stranske/Manager-Mosaic/pull/113). |
| CF-4: entity/key filtering, latest normalized quarter, mixed same-period outcomes, evidence IDs and finite thresholds | already-correct; consumer | `src/manager_mosaic/thesis.py:evaluate_claim`; `tests/test_thesis_monitoring.py::test_evaluate_claim_selects_chronologically_latest_across_period_formats`, `test_evaluate_claim_same_period_conflict_is_independent_of_evidence_id_order`. Preserve threshold/verdict and order-invariance probes. |
| `src/manager_mosaic/model.py:FactRecord` (CF-3, CF-4) | already-correct; Manager-Mosaic | Caller-supplied basis with unknown default and unsupported-basis rejection; source [#101](https://github.com/stranske/Manager-Mosaic/issues/101), compatible discrepancy alias. Probe: `tests/test_model_validation.py::test_model_fact_provenance_preserves_explicit_basis_and_legacy_import` |
| CF-5: schema structure, excerpt presence (including explicit null), page bounds, hash syntax, doc_type/text_basis enums, supersession pairing and quote-page requirement | already-correct; consumer enforcement of Workflows-owned schema | `src/manager_mosaic/evidence.py:validate_evidence_object`; `tests/test_evidence_validation.py::test_validate_evidence_object_reports_every_violation`, `test_validate_evidence_object_reports_violations_at_mixed_depths`, `test_packaged_evidence_schema_matches_published_contract`. Proposed: table of document_ref schema negatives as well as the existing mixed-defect probe. |
| CF-5: document/locator page agreement, real calendar date and self-supersession rejection are only implemented in the standalone CLI | confirmed-bug [#97](https://github.com/stranske/Manager-Mosaic/issues/97); consumer package behavior | `src/manager_mosaic/evidence.py:validate_evidence_object` versus `scripts/validate_run_contract.py:_check_document_page`; `tests/test_evidence_validation.py::test_validate_evidence_object_reports_violations_at_mixed_depths` does not cover these comparisons. Proposed: one payload with page mismatch, February 31 and self-supersession must return all three violations. Related implementation: [PR #112](https://github.com/stranske/Manager-Mosaic/pull/112). |
| CF-5: require document_ref on every legacy quote, resolve original bytes, prove reference existence across artifacts | intentionally-opt-in / outside this single-object validator; consumer corpus/importer policy | `docs/contracts/document-identity-conventions.md` permits legacy records. `tests/test_evidence_validation.py::test_validate_evidence_object_accepts_valid_payload` preserves that compatibility. Proposed: keep the legacy quote probe and require explicit attribution only when adopting a versioned policy. |
| CF-6: declared consumer ingests, schema validation and nonzero exit for invalid input | already-correct for the declared evidence journey; Workflows owns synced script/specs, consumer owns registry and fixtures | `scripts/validate_run_contract.py:main`, `_validate_consumer`; `tests/test_backplane_fixtures.py::test_consumer_cli_validates_evidence_fixture` executes valid and invalid fixtures from outside the checkout. Proposed: retain both exit-code and report assertions. |
| CF-6: full mosaic-core / tracked-variable wire shapes (see mapping below) | intentionally-opt-in interchange policy; Workflows | `config/backplane_participants.json` does not declare either schema in this consumer's ingests. Explicit CLI modes support them, but CF-6 does not promise these undeclared paths. Proposed: upon adoption, add valid/invalid subprocess fixtures for each declared wire type. |
| CF-3/CF-4/CF-7: registry vocabulary, every violation with claim/evidence identity, strict-mode failure, legacy compatibility | intentionally-opt-in, already wired; consumer | `src/manager_mosaic/fact_keys.py:load_fact_key_registry`, `validate_fact_keys`; `src/manager_mosaic/thesis.py:evaluate_claim`; `src/manager_mosaic/discrepancy.py:detect_numeric_discrepancies`; `tests/test_fact_key_registry.py::test_public_validators_consult_default_fact_key_registry` checks a newly added key and removal of a normally valid key through both strict-mode spellings. `test_opted_in_validation_reports_claim_and_facts_rather_than_insufficient_evidence` checks claim and fact identity together. Regression implemented; no current registry-disconnection defect at this snapshot. |

All local package implementation findings belong to **Manager-Mosaic (consumer)**.
Shared schema/specification or standalone-validator changes belong first in
**stranske/Workflows**, then sync here. This audit changes no synced automation.
The issue links above are inherited from the existing audit; GitHub API access is
unavailable in this run, so current issue/PR state has not been reverified.
No additional uncovered instance was established, so no `gh issue create` is
needed. New findings would require a separate issue per uncovered instance under
the task's explicit authorization; do not silently reclassify one as passing.

## Normative resource mapping

| Resource | Rule family and applicable public path | Local versus interchange boundary |
| --- | --- | --- |
| `src/manager_mosaic/schemas/mosaic-store-v1.schema.json` | CF-1 `model.load_schema`, `Store.from_dict`, `Store.from_json`, `validate`; shapes, required properties, types, additional-property rejection and pub-state enum | Mandatory raw-store structure has the issue #96 gap above. Typed builders are explicit programmer inputs; their existence is not schema enforcement. Semantic rules and CF-2 silence behavior come from `docs/PRODUCT_CONTRACT.md` and `model.py`. |
| `src/manager_mosaic/schemas/evidence-object-v1.schema.json` | CF-5 `evidence.load_evidence_schema` / `validate_evidence_object`; schema_version, required identity/method/excerpt, ranges and optional identity extension | Mandatory schema enforcement on every public evidence-validation call; matches `docs/contracts/schemas/evidence-object-v1.schema.json`. |
| [document-identity-conventions.md](docs/contracts/document-identity-conventions.md) | CF-5 evidence validation; CF-6 `_check_document_page`; byte-hash identity, doc_key/type, calendar dates, supersession evidence, text_basis, quote pages and coverage evidence | Extension adoption is optional; once present its rules apply. A supplied digest is syntax-checked, not independently verified against absent source bytes. Corpus resolution is not an exported package function. |
| [mosaic-core-v1.md](docs/contracts/mosaic-core-v1.md) and `docs/contracts/schemas/mosaic-core-v1.schema.json` | CF-3 local numeric joins/stable IDs, CF-4 verdict/period semantics; CF-6 wire dispatch if declared | Wire-only fields include schema_version/record_type, fact_id/status/primary_evidence_id, discrepancy fact_ids/severity/resolution_note, thesis_id/fact_keys/evidence_policy, checked_at/trigger_source_id. Numeric ranges, min<=max, unique IDs and cross-artifact evidence closure belong to interchange producers/importers. Local numeric dataclasses are not claimed to be interchange serializers. Thresholds and supported patterns are consumer policy. |
| [tracked-variable-v1.md](docs/contracts/tracked-variable-v1.md) and `docs/contracts/schemas/tracked-variable-v1.schema.json` | CF-6 explicit tracked-variable mode; potential upstream input to CF-3/CF-4 | Wire schema_version, embedded evidence, dual document/mirror provenance, ontology_key and vocabulary-family aliases are Workflows policy. No local tracked-variable importer is promised by CF-1 to CF-6. An eventual importer must copy ontology_key exactly and check evidence/reference closure before constructing local FactRecord values. |
| `src/manager_mosaic/fact_key_registry.json` and `config/fact_key_registry.json` | CF-7 explicit validator and CF-3/CF-4 strict modes | Consumer-owned optional vocabulary, not a blanket rejection policy on all typed constructors or legacy evaluators. `tests/test_fact_key_registry.py::test_source_and_packaged_fact_key_registries_match` checks copy parity. |

## Complete entry-point inventory

The machine-readable companion is
[docs/audits/contract-enforcement-catalog.json](docs/audits/contract-enforcement-catalog.json).
It records CF identifiers, source contract paths, classifications, owners, issue
numbers and exact probing tests. The test guards top-level public classes and
functions (including async definitions), public methods/properties, explicitly
defined construction hooks and submodule __all__ aliases. Generated dataclass
methods, private helpers, type aliases/constants and duplicate root re-exports
are not separate inputs. Root compatibility helpers are explicitly outside the
contract. A cited test proves the behavior it asserts; proposals above identify
the behavior existing probes do not cover.

| Source / core functions | Disposition / owner | Rule and probing test |
| --- | --- | --- |
| `src/manager_mosaic/model.py:Fund` (CF-1) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:Period` (CF-1, CF-2) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:Pub` (CF-1) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_builders_create_expected_entry` |
| `src/manager_mosaic/model.py:Mention` (CF-1, CF-2) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_builders_create_expected_entry` |
| `src/manager_mosaic/model.py:Entry` (CF-1, CF-2) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_builders_create_expected_entry` |
| `src/manager_mosaic/model.py:Theme` (CF-1) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:Document` (CF-1) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:Gap` (CF-2) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_derive_gaps_leaves_status_unchanged` |
| `src/manager_mosaic/model.py:Store` (CF-1, CF-2) | confirmed-bug [#96](https://github.com/stranske/Manager-Mosaic/issues/96); Manager-Mosaic | Raw structure is constructed before validation; existing PR111 repairs this. Pending delivery is not a current-main pass. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:Store.__post_init__` (CF-1, CF-2) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:Store.from_dict` (CF-1) | confirmed-bug [#96](https://github.com/stranske/Manager-Mosaic/issues/96); Manager-Mosaic | Raw structure is constructed before validation; existing PR111 repairs this. Pending delivery is not a current-main pass. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:Store.from_json` (CF-1) | confirmed-bug [#96](https://github.com/stranske/Manager-Mosaic/issues/96); Manager-Mosaic | Raw structure is constructed before validation; existing PR111 repairs this. Pending delivery is not a current-main pass. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:ValidationViolation` (CF-1) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_validator_returns_all_four_defects` |
| `src/manager_mosaic/model.py:fund` (CF-1) | intentionally-opt-in; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:period` (CF-1, CF-2) | intentionally-opt-in; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:pub` (CF-1) | intentionally-opt-in; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py::test_builders_create_expected_entry` |
| `src/manager_mosaic/model.py:mention` (CF-1, CF-2) | intentionally-opt-in; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py::test_builders_create_expected_entry` |
| `src/manager_mosaic/model.py:entry` (CF-1, CF-2) | intentionally-opt-in; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py::test_builders_create_expected_entry` |
| `src/manager_mosaic/model.py:theme` (CF-1) | intentionally-opt-in; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:document` (CF-1) | intentionally-opt-in; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/model.py:gap` (CF-2) | intentionally-opt-in; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py::test_derive_gaps_leaves_status_unchanged` |
| `src/manager_mosaic/model.py:validate` (CF-1) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_validator_returns_all_four_defects` |
| `src/manager_mosaic/model.py:derive_gaps` (CF-2) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_derive_gaps_leaves_status_unchanged` |
| `src/manager_mosaic/model.py:load_schema` (CF-1, CF-5) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py::test_public_and_packaged_schemas_match` |
| `src/manager_mosaic/evidence.py:load_evidence_schema` (CF-5) | already-correct; Manager-Mosaic | Packaged evidence-object/v1 loader used by the public validator. Probe: `tests/test_evidence_validation.py::test_evidence_schema_is_readable_through_package_resources` |
| `src/manager_mosaic/evidence.py:validate_evidence_object` (CF-5) | confirmed-bug [#97](https://github.com/stranske/Manager-Mosaic/issues/97); Manager-Mosaic | Schema and excerpt presence are enforced; cross-field page agreement, calendar dates and self-supersession are missing (#97). Probe: `tests/test_evidence_validation.py::test_validate_evidence_object_reports_every_violation` |
| `src/manager_mosaic/fact_keys.py:load_fact_key_registry` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py::test_fact_key_registry_is_readable_through_package_resources` |
| `src/manager_mosaic/fact_keys.py:FactKeyViolation` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py::test_validate_fact_keys_returns_all_violations_in_one_pass` |
| `src/manager_mosaic/fact_keys.py:UnregisteredFactKeyError` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py::test_ensure_registered_fact_keys_returns_none_for_valid_and_exposes_all_violations` |
| `src/manager_mosaic/fact_keys.py:validate_fact_keys` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py::test_public_validators_consult_default_fact_key_registry` |
| `src/manager_mosaic/fact_keys.py:validate_claim_and_facts` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py::test_public_validation_helper_aliases_delegate_with_claim_and_fact_identity` |
| `src/manager_mosaic/fact_keys.py:validate_facts_and_claims` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py::test_public_validation_helper_aliases_delegate_with_claim_and_fact_identity` |
| `src/manager_mosaic/fact_keys.py:ensure_registered_fact_keys` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py::test_ensure_registered_fact_keys_returns_none_for_valid_and_exposes_all_violations` |
| `src/manager_mosaic/model.py:FactRecord` (CF-3, CF-4) | already-correct; Manager-Mosaic | Caller-supplied basis with unknown default and unsupported-basis rejection; source [#101](https://github.com/stranske/Manager-Mosaic/issues/101), compatible discrepancy alias. Probe: `tests/test_model_validation.py::test_model_fact_provenance_preserves_explicit_basis_and_legacy_import` |
| `src/manager_mosaic/model.py:FactRecord.__post_init__` (CF-3, CF-4) | already-correct; Manager-Mosaic | Caller-supplied basis with unknown default and unsupported-basis rejection; source [#101](https://github.com/stranske/Manager-Mosaic/issues/101), compatible discrepancy alias. Probe: `tests/test_model_validation.py::test_fact_provenance_rejects_unsupported_basis` |
| `src/manager_mosaic/discrepancy.py:DiscrepancyRecord` (CF-3) | confirmed-bug [#101](https://github.com/stranske/Manager-Mosaic/issues/101); Manager-Mosaic | Existing accepted101 owns caller-supplied basis propagation; verdict/threshold/latest-period rules pass existing tests. Probe: `tests/test_discrepancy_detection.py::test_detect_numeric_discrepancies_groups_equivalent_period_labels` |
| `src/manager_mosaic/discrepancy.py:DiscrepancyRecord.bases` (CF-3) | already-correct; Manager-Mosaic | Result provenance accessors expose each contributing fact's basis in contributing order without deduplication. Probe: `tests/test_model_validation.py::test_result_provenance_accessors_expose_inferred_only_and_mixed_bases` |
| `src/manager_mosaic/discrepancy.py:DiscrepancyRecord.evidence_bases` (CF-3) | already-correct; Manager-Mosaic | Result provenance accessors expose each contributing fact's (evidence_id, basis) pair in contributing order without deduplication. Probe: `tests/test_model_validation.py::test_result_provenance_accessors_expose_inferred_only_and_mixed_bases` |
| `src/manager_mosaic/thesis.py:ThesisCheck.bases` (CF-4) | already-correct; Manager-Mosaic | Result provenance accessors expose each contributing fact's basis in contributing order without deduplication. Probe: `tests/test_model_validation.py::test_result_provenance_accessors_expose_inferred_only_and_mixed_bases` |
| `src/manager_mosaic/thesis.py:ThesisCheck.evidence_bases` (CF-4) | already-correct; Manager-Mosaic | Result provenance accessors expose each contributing fact's (evidence_id, basis) pair in contributing order without deduplication. Probe: `tests/test_model_validation.py::test_result_provenance_accessors_expose_inferred_only_and_mixed_bases` |
| `src/manager_mosaic/discrepancy.py:detect_numeric_discrepancies` (CF-3) | confirmed-bug [#98](https://github.com/stranske/Manager-Mosaic/issues/98) [#101](https://github.com/stranske/Manager-Mosaic/issues/101); Manager-Mosaic | Grouping normalizes periods; identity still uses the first raw label on this main. PR113 fixes identity. Caller provenance belongs to accepted101. Probe: `tests/test_discrepancy_detection.py::test_detect_numeric_discrepancies_groups_equivalent_period_labels` |
| `src/manager_mosaic/thesis.py:ThesisClaim` (CF-4) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_thesis_monitoring.py::test_thesis_claim_rejects_non_finite_threshold` |
| `src/manager_mosaic/thesis.py:ThesisClaim.__post_init__` (CF-4) | already-correct; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_thesis_monitoring.py::test_thesis_claim_rejects_non_finite_threshold` |
| `src/manager_mosaic/thesis.py:ThesisCheck` (CF-4) | confirmed-bug [#101](https://github.com/stranske/Manager-Mosaic/issues/101); Manager-Mosaic | Existing accepted101 owns caller-supplied basis propagation; verdict/threshold/latest-period rules pass existing tests. Probe: `tests/test_thesis_monitoring.py::test_evaluate_claim_selects_chronologically_latest_across_period_formats` |
| `src/manager_mosaic/thesis.py:evaluate_claim` (CF-4) | confirmed-bug [#101](https://github.com/stranske/Manager-Mosaic/issues/101); Manager-Mosaic | Existing accepted101 owns caller-supplied basis propagation; verdict/threshold/latest-period rules pass existing tests. Probe: `tests/test_thesis_monitoring.py::test_evaluate_claim_selects_chronologically_latest_across_period_formats` |
| `src/manager_mosaic/periods.py:period_chronology_key` (CF-3, CF-4) | already-correct; Manager-Mosaic | One shared quarter parser; unsupported labels fail explicitly for chronology; discrepancy raw labels remain exact. Probe: `tests/test_thesis_monitoring.py::test_evaluate_claim_selects_chronologically_latest_across_period_formats` |
| `src/manager_mosaic/__init__.py:greet` (outside CF-1 to CF-6) | intentionally-opt-in; Manager-Mosaic | Compatibility scaffold outside mosaic core contracts; direct unit probes only. Probe: `tests/test_main.py::test_greet` |
| `src/manager_mosaic/__init__.py:add` (outside CF-1 to CF-6) | intentionally-opt-in; Manager-Mosaic | Compatibility scaffold outside mosaic core contracts; direct unit probes only. Probe: `tests/test_main.py::test_add` |
| `src/manager_mosaic/model.py:validate_payload` (CF-1) | confirmed-bug [#96](https://github.com/stranske/Manager-Mosaic/issues/96); Manager-Mosaic | Existing issue96/PR111 introduces raw structure plus prerequisite-safe semantic diagnostics. Pending delivery, not yet a current-main symbol. **Planned API, absent at the audited snapshot.** Probe: `tests/test_model_validation.py::test_mistyped_entry_period_reference_is_reported` |
| `src/manager_mosaic/fact_keys.py:FactKeyViolation.kind` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Read-only unregistered_fact_key diagnostic discriminator (CF7). Probe: `tests/test_fact_key_registry.py::test_validate_fact_keys_reports_identity_for_generic_records` |
| `src/manager_mosaic/fact_keys.py:UnregisteredFactKeyError.__init__` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Strict-mode exception preserves all identity-qualified violations (CF7). Probe: `tests/test_fact_key_registry.py::test_ensure_registered_fact_keys_returns_none_for_valid_and_exposes_all_violations` |
| `src/manager_mosaic/fact_keys.py:ValidationViolation` (CF-3, CF-4, CF-7) | already-correct; Manager-Mosaic | Public compatibility alias of FactKeyViolation, not a second validator. Probe: `tests/test_fact_key_registry.py::test_validate_fact_keys_reports_identity_for_generic_records` |
| `scripts/validate_run_contract.py:main` (CF-6) | already-correct; Workflows | CF-6 dispatch checks declared consumer ingests and returns nonzero for invalid evidence fixtures. Other interchange forms are conditional on registry adoption or explicit CLI flags. Probe: `tests/test_backplane_fixtures.py::test_consumer_cli_validates_evidence_fixture` |

## Regression prevention and verification

`tests/test_repo_hygiene.py::test_public_contract_entrypoints_have_audited_dispositions`
fails for unreported public inputs, duplicates, stale current symbols, missing CF
mappings, missing contract resources or nonexistent named probes.
`test_packaged_contract_resources_have_audited_consumers` fails for unlisted
packaged schemas/registry or removed loader calls; the raw-store schema has the
explicit issue #96 exception. These inventory checks cannot prove that an
otherwise unused call enforces the right behavior. The registry test above is a
behavioral complement, exercising actual public validation and evaluation.

The source-diff criterion and the deliberate-break criterion are reconciled by
mutating only for the probe and restoring the exact original bytes; no package
implementation change is committed. The registry wiring being disconnected is
already present in the audited baseline. Verification results are recorded below
after running the tests; historical evidence in `docs/evidence/issue-99/99-red.txt`
is a static call-presence check, not the newly requested behavioral break gate.

Verified in this run:

- [x] Inventory the six scoped modules against CF-1 through CF-6, also recording CF-7's current opt-in boundary and the CF-6 CLI dispatch.
- [x] Map entry points to the product contract, shared normative contracts and packaged schemas/registry.
- [x] Classify rule/path pairs and cite exact existing tests; distinguish proposed gap probes from passing behavior.
- [x] Update this report with consumer/Workflows ownership and a regression proposal for every finding.
- [x] Link the existing issues; no new uncovered instance requires issue creation. Remote issue state remains unverified because GitHub access failed.
- [x] Implement inventory/resource regression checks and a behavioral registry probe.

Validation: `python -m pytest -q -m "not slow"` passed **121 tests** with the
repository's configured coverage gate. The focused hygiene check passed all five
tests with `python -m pytest -q --no-cov -m "not slow" tests/test_repo_hygiene.py`.
`ruff check tests/test_repo_hygiene.py tests/test_fact_key_registry.py` and
`git diff --check` passed. Black formatting and the repository-wide
`black --check --line-length 100 --exclude '(\.workflows-lib|node_modules)' .`
passed for all 99 Python files. Because sandbox restrictions prevented Black's
worker notifications, every file was first checked individually into a writable
`BLACK_CACHE_DIR`; the unchanged repository-wide check then completed normally.

Behavioral deliberate-break evidence:
[disconnected: two expected failures](docs/evidence/issue-99/registry-behavior-red.txt)
and [restored: two passes](docs/evidence/issue-99/registry-behavior-green.txt).
The mutation replaced registry resolution in `validate_fact_keys` with an early
`return []`; the new test failed on the missing identity-qualified violation.
Exact source bytes were restored in a `finally` block before rerunning; the green
transcript records the restored SHA-256. Both strict-mode spellings are covered.

`git diff --stat origin/main...HEAD -- src/manager_mosaic` and the working-tree
package diff both print nothing. This checkout has no local `main` ref, so
`origin/main` is the corresponding base for the source-diff check. No production
fix for the linked findings is included in this audit PR.

Delivery blocker: committing these verified changes was attempted, but Git failed
with `Unable to create .git/index.lock: Read-only file system`. The environment
mounts `.git` read-only and does not allow permission escalation. The changes and
new behavioral transcripts remain in the working tree; no new commit or push was
created in this run.
