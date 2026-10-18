# Public contract enforcement audit

Snapshot: main2ec5f09. Scope is package public inputs/validators plus the CF6 consumer CLI. All data/probes are synthetic and offline. Existing repairs are linked; their open PRs are not represented as merged behavior. No new uncovered instance was confirmed outside already assigned96/97/98/101, and no follow-up issue was filed.

## Rules and ownership

| Contract | Rule / path | Disposition and existing owner | Evidence |
| --- | --- | --- | --- |
| CF1 | Raw JSON shape before Store construction; finite values, unique IDs, references, status vocabularies, chronology, currency truncation | confirmed-bug #96, PR111 pending; consumer-owned | model.py:Store.from_dict, validate; test_model_validation.py; packaged mosaic-store schema |
| CF2 | Missing mentions create gaps and never infer exits | already-correct; consumer-owned | model.py:derive_gaps; unchanged silence/range tests |
| CF3 | Canonical grouping and injective stable identity; spread threshold | confirmed-bug #98, PR113 pending; consumer-owned | discrepancy.py; alias/injectivity/threshold tests. Provenance accepted #101 |
| CF4 | Entity/key match, latest normalized quarter, mixed same-period verdict | already-correct evaluation; provenance confirmed-bug #101 under existing accepted scope | thesis.py:evaluate_claim; test_thesis_monitoring.py |
| CF5 | Schema, mandatory excerpt key, optional legacy identity; page agreement, calendar date, earlier-byte supersession | confirmed-bug #97, PR112 pending; consumer owns package behavior | evidence.py; test_evidence_validation.py and standalone CLI parity |
| CF6 | Interchange evidence/consumer fixture validation | already-correct; Workflows owns synced schema/script, consumer owns fixtures | scripts/validate_run_contract.py; test_backplane_fixtures.py |
| CF7 | Fact/claim key vocabulary and identity-qualified diagnostics | intentionally-opt-in, already wired; consumer-owned | fact_keys.py; strict_fact_keys and validate_fact_keys_opt_in;21 registry tests |

Local dataclass construction remains a typed programmer API. This audit does not impose interchange-only schema policy on every typed constructor, make strict vocabulary flags mandatory, infer provenance from extraction method, or validate remote document contents. Legacy evidence without document_ref remains accepted, with incomplete attribution rather than fabricated identity. Shared tracked-variable/document identity contracts are Workflows-owned; no package extraction/ingest/renderer is claimed.

## Complete entry-point inventory

| Source and symbol | Disposition / owner | Applicable rule and evidence |
| --- | --- | --- |
| `src/manager_mosaic/model.py:Fund` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Period` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Pub` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Mention` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Entry` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Theme` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Document` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Gap` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Store` | confirmed-bug [#96](https://github.com/stranske/Manager-Mosaic/issues/96); Manager-Mosaic | Raw structure is constructed before validation; existing PR111 repairs this. Pending delivery is not a current-main pass. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Store.__post_init__` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Store.from_dict` | confirmed-bug [#96](https://github.com/stranske/Manager-Mosaic/issues/96); Manager-Mosaic | Raw structure is constructed before validation; existing PR111 repairs this. Pending delivery is not a current-main pass. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:Store.from_json` | confirmed-bug [#96](https://github.com/stranske/Manager-Mosaic/issues/96); Manager-Mosaic | Raw structure is constructed before validation; existing PR111 repairs this. Pending delivery is not a current-main pass. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:ValidationViolation` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:fund` | intentionally-opt-in ; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:period` | intentionally-opt-in ; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:pub` | intentionally-opt-in ; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:mention` | intentionally-opt-in ; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:entry` | intentionally-opt-in ; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:theme` | intentionally-opt-in ; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:document` | intentionally-opt-in ; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:gap` | intentionally-opt-in ; Manager-Mosaic | Typed constructors are building blocks; validate(Store) performs semantic checks, not implicit coercion. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:validate` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:derive_gaps` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/model.py:load_schema` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_model_validation.py` |
| `src/manager_mosaic/evidence.py:load_evidence_schema` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_evidence_validation.py` |
| `src/manager_mosaic/evidence.py:validate_evidence_object` | confirmed-bug [#97](https://github.com/stranske/Manager-Mosaic/issues/97); Manager-Mosaic | Identity page/date/supersession rules missing on this public path; existing PR112 repairs them. Probe: `tests/test_evidence_validation.py` |
| `src/manager_mosaic/fact_keys.py:load_fact_key_registry` | already-correct ; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py` |
| `src/manager_mosaic/fact_keys.py:FactKeyViolation` | already-correct ; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py` |
| `src/manager_mosaic/fact_keys.py:UnregisteredFactKeyError` | already-correct ; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py` |
| `src/manager_mosaic/fact_keys.py:validate_fact_keys` | already-correct ; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py` |
| `src/manager_mosaic/fact_keys.py:validate_claim_and_facts` | already-correct ; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py` |
| `src/manager_mosaic/fact_keys.py:validate_facts_and_claims` | already-correct ; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py` |
| `src/manager_mosaic/fact_keys.py:ensure_registered_fact_keys` | already-correct ; Manager-Mosaic | Registry validates keys/identities through explicit validators; discrepancy/thesis strict flags are intentionally opt-in (CF7). Probe: `tests/test_fact_key_registry.py` |
| `src/manager_mosaic/discrepancy.py:FactRecord` | confirmed-bug [#101](https://github.com/stranske/Manager-Mosaic/issues/101); Manager-Mosaic | Existing accepted101 owns caller-supplied basis propagation; verdict/threshold/latest-period rules pass existing tests. Probe: `tests/test_discrepancy_detection.py` |
| `src/manager_mosaic/discrepancy.py:FactRecord.__post_init__` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_discrepancy_detection.py` |
| `src/manager_mosaic/discrepancy.py:DiscrepancyRecord` | confirmed-bug [#101](https://github.com/stranske/Manager-Mosaic/issues/101); Manager-Mosaic | Existing accepted101 owns caller-supplied basis propagation; verdict/threshold/latest-period rules pass existing tests. Probe: `tests/test_discrepancy_detection.py` |
| `src/manager_mosaic/discrepancy.py:detect_numeric_discrepancies` | confirmed-bug [#98](https://github.com/stranske/Manager-Mosaic/issues/98) [#101](https://github.com/stranske/Manager-Mosaic/issues/101); Manager-Mosaic | Grouping normalizes periods; identity still uses the first raw label on this main. PR113 fixes identity. Caller provenance belongs to accepted101. Probe: `tests/test_discrepancy_detection.py` |
| `src/manager_mosaic/thesis.py:ThesisClaim` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_thesis_monitoring.py` |
| `src/manager_mosaic/thesis.py:ThesisClaim.__post_init__` | already-correct ; Manager-Mosaic | Typed local values; explicit semantic validation where applicable. Probe: `tests/test_thesis_monitoring.py` |
| `src/manager_mosaic/thesis.py:ThesisCheck` | confirmed-bug [#101](https://github.com/stranske/Manager-Mosaic/issues/101); Manager-Mosaic | Existing accepted101 owns caller-supplied basis propagation; verdict/threshold/latest-period rules pass existing tests. Probe: `tests/test_thesis_monitoring.py` |
| `src/manager_mosaic/thesis.py:evaluate_claim` | confirmed-bug [#101](https://github.com/stranske/Manager-Mosaic/issues/101); Manager-Mosaic | Existing accepted101 owns caller-supplied basis propagation; verdict/threshold/latest-period rules pass existing tests. Probe: `tests/test_thesis_monitoring.py` |
| `src/manager_mosaic/periods.py:period_chronology_key` | already-correct ; Manager-Mosaic | One shared quarter parser; unsupported labels fail explicitly for chronology; discrepancy raw labels remain exact. Probe: `tests/test_thesis_monitoring.py` |
| `src/manager_mosaic/__init__.py:greet` | intentionally-opt-in ; Manager-Mosaic | Compatibility scaffold outside mosaic core contracts; direct unit probes only. Probe: `tests/test_main.py` |
| `src/manager_mosaic/__init__.py:add` | intentionally-opt-in ; Manager-Mosaic | Compatibility scaffold outside mosaic core contracts; direct unit probes only. Probe: `tests/test_main.py` |
| `src/manager_mosaic/model.py:validate_payload` | confirmed-bug [#96](https://github.com/stranske/Manager-Mosaic/issues/96); Manager-Mosaic | Existing issue96/PR111 introduces raw structure plus prerequisite-safe semantic diagnostics. Pending delivery, not yet a current-main symbol. Probe: `tests/test_model_validation.py` |

## Regression prevention and limits

`tests/test_repo_hygiene.py` enumerates public package definitions and packaged schemas/registry against the machine-readable catalog. An unreported public entry point or newly orphaned packaged resource fails. It also checks real non-test calls to load_fact_key_registry and load_schema; presence is an audit coverage check, not proof of semantics. Current semantic probes remain the behavioral authority. The known raw-store gap has an explicit issue96 exception until delivery.

A deliberate removal of both fact-key loader calls must fail the resource-consumer guard; exact restoration returns it green. This test-only/report PR leaves src/manager_mosaic byte-for-byte unchanged. Future new findings return as scoped proposals for human review; no automatic issue filing is authorized.
