# Manager-Mosaic

Every source of manager communication says something about the same investment. This repo holds the model that lets those statements be compared: a **fact** that carries the **evidence** it came from, contradictions that surface on their own, and a written **investment thesis** monitored against what the documents actually say.

Created 2026-09-04 on the owner's decision, after an inventory of the work environment found the nearest existing tool to be phase one only: a hand-edited data file rendered to a single page, with no comparable synthesis view yet.

## What it is and is not

- **It is** the fact, evidence, entity, period, theme, thesis and gap model, its validator, discrepancy detection, and thesis monitoring.
- **It is not** a document reader. Document identity and text extraction with page pointers belong to `stranske/Doc-Lineage`.
- **It is not** a renderer. Hubs, decks and memos belong to `stranske/Deliverable-Render`.

That split is deliberate: the same three concerns are currently solved three times over in the work environment, once per tracker.

The canonical list of user-facing capabilities, entry points, and probes is in
the [product contract](docs/PRODUCT_CONTRACT.md).

## Invariants taken from real failures, not from theory

1. **Silence is weak evidence, never proof.** A position missing from a document is a gap, not an exit. Inferring a removal from an absence has already produced a wrong finding.
2. **Valid is not undamaged.** A structured file can parse cleanly and still be corrupt: a text substitution once turned a dollar figure into a bare suffix, and a single mistyped identifier once made a whole record vanish from a rendered view with no error. `manager_mosaic.validate_payload(raw_mapping)` checks structure and applicable semantics before constructing a Store, reporting path-qualified violations in one pass. `Store.from_dict` rejects malformed structure with one aggregated ValueError; `validate(Store)` remains the typed semantic API.
3. **An inference is labelled as one.** Every fact carries its source, and anything derived rather than observed is marked, so the two can never be read as the same thing.
4. **One-click back to the document.** A fact whose evidence cannot be opened is not usable for a decision.

## Data and hosting

Synthetic and public inputs only in this repository; no proprietary manager material is ever committed or used in tests. Nothing server-hosted or database-backed runs in the target environment today, so the model works as files and a local command. That is a current constraint rather than a permanent one: where a hosted or database-backed component would genuinely serve a goal that files cannot, the design records the goal, why a local shape cannot reach it, and the accommodation the work IT team would need to grant.

## Interoperability

Field names come from the tool already in use rather than being invented here, and the store aligns with the fleet contracts in `docs/contracts/` (run records, artifact manifests, evidence objects, identity conventions).

### Fact provenance in local results

Pass an explicit `basis` to `manager_mosaic.model.FactRecord` when its source supports
observed/inferred classification; legacy facts remain unknown. The existing
`manager_mosaic.discrepancy.FactRecord` import and constructors remain compatible.
Discrepancy and thesis outputs keep
all contributing fact/value/evidence/basis associations, including mixed bases and
repeated evidence IDs, without changing evaluation policy. Both result types also
expose `bases`, `evidence_bases`, and `value_bases` (the `(value, evidence_id,
basis)` association per contributing fact) directly, and `FactRecord`/`FactBasis` are
importable from the top-level `manager_mosaic` package. The product contract
documents this caller boundary. Verified offline: 66 model tests, 103 focused
model/discrepancy/thesis tests, and 228 full-suite tests passed. Temporarily erasing
the caller's explicit basis in `model.py` failed the named regression; restoring
the source passed. Commands and captured outcomes are in the
[delivery evidence](docs/evidence/issue-101/README.md).

This scope excludes extraction, hosting, and method-to-basis inference. Mention
boolean validation is covered by the merged store-validation candidate; shared
interchange contracts retain their existing owners.
