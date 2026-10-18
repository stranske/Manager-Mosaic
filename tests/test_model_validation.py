"""Model validation and silence-invariant gates for Manager-Mosaic."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

import manager_mosaic
from manager_mosaic.model import (
    FactRecord,
    Store,
    derive_gaps,
    entry,
    load_schema,
    mention,
    pub,
    validate,
    validate_payload,
)

FIXTURES = Path(__file__).parent / "fixtures" / "model"


def _load(name: str) -> Store:
    return Store.from_json(FIXTURES / name)


def _validate_schema(name: str) -> None:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    Draft202012Validator(load_schema()).validate(payload)


def test_fixture_validates_against_json_schema() -> None:
    _validate_schema("minimal_store.json")


def test_public_and_packaged_schemas_match() -> None:
    public_schema = Path("schemas/mosaic-store-v1.schema.json")
    assert json.loads(public_schema.read_text(encoding="utf-8")) == load_schema()


def test_mistyped_entry_period_reference_is_reported() -> None:
    broken = Store.from_dict(
        {
            **json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8")),
            "entries": [
                {
                    **json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))[
                        "entries"
                    ][0],
                    "first": "2025Q1_typo",
                }
            ],
        }
    )
    violations = validate(broken)
    assert any(v.record_id == "alpha-fund" and "2025Q1_typo" in v.message for v in violations)


def test_inverted_entry_period_range_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["first"] = "2025Q2"
    payload["entries"][0]["last"] = "2025Q1"
    broken = Store.from_dict(payload)

    violations = validate(broken)

    assert [(violation.record_id, violation.message) for violation in violations] == [
        ("alpha-fund", "first period '2025Q2' is after last period '2025Q1'")
    ]
    assert derive_gaps(broken) == ()


def test_truncated_currency_suffix_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["mentions"][0]["size"] = "$B"
    broken = Store.from_dict(payload)
    violations = validate(broken)
    assert any("truncated currency" in v.message for v in violations)


def test_mention_without_src_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["mentions"][0]["src"] = ""
    broken = _typed_mention(src="")
    violations = validate(broken)
    assert any("mention must carry src" in v.message for v in violations)


def test_mention_with_omitted_src_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    del payload["entries"][0]["mentions"][0]["src"]
    with pytest.raises(ValueError, match=r"entries\[0\].mentions\[0\].src"):
        Store.from_dict(payload)


def test_derive_gaps_leaves_status_unchanged() -> None:
    store = _load("minimal_store.json")
    before_status = store.entries[0].status
    gaps = derive_gaps(store)
    assert store.entries[0].status == before_status
    assert any("2025Q2" in item.title for item in gaps)
    assert any("2025Q2" in item.title and item.sev == "info" for item in gaps)


def test_nonnumeric_mention_bps_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["mentions"][0]["bps"] = "25"
    violations = validate(_typed_mention(bps="25"))
    assert [(v.record_id, v.message) for v in violations] == [
        ("alpha-fund:mention[0]", "bps must be a finite number or null")
    ]


def test_boolean_peak_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["peak"] = True
    violations = validate(
        replace(
            _load("minimal_store.json"),
            entries=(replace(_load("minimal_store.json").entries[0], peak=True),),
        )
    )
    assert [(v.record_id, v.message) for v in violations] == [
        ("alpha-fund", "peak must be a finite number or null")
    ]


def test_validator_returns_all_four_defects() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["first"] = "missing-period"
    payload["entries"][0]["mentions"][0]["src"] = ""
    payload["entries"][0]["mentions"][0]["size"] = "$B"
    payload["entries"][0]["mentions"][0]["bps"] = math.inf
    original = _typed_mention(src="", size="$B", bps=math.inf)
    broken = replace(original, entries=(replace(original.entries[0], first="missing-period"),))
    violations = validate(broken)
    messages = {(item.record_id, item.message) for item in violations}
    assert any(
        record_id == "alpha-fund" and "missing-period" in message for record_id, message in messages
    )
    assert any(
        "mention[0]" in record_id and "mention must carry src" in message
        for record_id, message in messages
    )
    assert any("truncated currency" in message for _, message in messages)
    assert any("bps must be finite" in message for _, message in messages)


def test_none_period_sort_does_not_abort_validation() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["periods"][0]["sort"] = None
    payload["entries"][0]["first"] = "missing-period"
    original = _typed_sort(None)
    broken = replace(original, entries=(replace(original.entries[0], first="missing-period"),))
    violations = validate(broken)
    messages = {(v.record_id, v.message) for v in violations}
    assert any("sort must be a finite number" in message for _, message in messages)
    assert any(
        record_id == "alpha-fund" and "missing-period" in message for record_id, message in messages
    )


def test_nonnumeric_period_sorts_are_violations_without_aborting() -> None:
    for bad_sort in ("2025Q1", True, {}, []):
        payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
        payload["periods"][0]["sort"] = bad_sort
        broken = _typed_sort(bad_sort)

        violations = validate(broken)

        assert any(
            v.record_id == "2025Q1" and "sort must be a finite number" in v.message
            for v in violations
        )
        assert derive_gaps(broken) == ()


def test_nonfinite_period_sorts_are_violations_without_aborting() -> None:
    for bad_sort in (math.nan, math.inf, -math.inf):
        payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
        payload["periods"][0]["sort"] = bad_sort
        broken = _typed_sort(bad_sort)

        violations = validate(broken)

        assert any(
            v.record_id == "2025Q1" and "sort must be finite" in v.message for v in violations
        )
        assert derive_gaps(broken) == ()


def test_oversized_integer_sort_does_not_abort_validation() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["periods"][0]["sort"] = 10**400
    payload["entries"][0]["first"] = "missing-period"
    broken = Store.from_dict(payload)
    violations = validate(broken)
    assert any(
        record_id == "alpha-fund" and "missing-period" in message
        for record_id, message in ((v.record_id, v.message) for v in violations)
    )


def _forbidden_infer_exit_on_gap(store: Store) -> str:
    """Illustrate the forbidden inference; this helper is not a production break gate."""

    if derive_gaps(store):
        return "EXITED"
    return store.entries[0].status


def test_silence_invariant_example() -> None:
    """Keep the original example while a separate regression tests production code."""

    store = _load("minimal_store.json")
    assert store.entries[0].status == "ACTIVE"
    assert _forbidden_infer_exit_on_gap(store) == "EXITED"
    gaps = derive_gaps(store)
    assert store.entries[0].status == "ACTIVE"
    assert gaps


def test_builders_create_expected_entry() -> None:
    item = entry(
        id="demo",
        name="Demo",
        ticker="DMO",
        counterparty="Manager",
        kind="position",
        first="2025Q1",
        last="2025Q2",
        status="ACTIVE",
        peak=None,
        flag="",
        thesis="",
        pub=pub("PENDING", "2025-01-01", "", "Q1-2025-Letter"),
        mentions=[
            mention("2025Q1", "note", 10.0, "$1M", "Q1-2025-Letter", False),
        ],
    )
    assert item.mentions[0].inferred is False


@pytest.mark.parametrize(
    "basis, second_basis",
    [
        ("observed", "observed"),
        ("inferred", "inferred"),
        ("observed", "inferred"),
        ("unknown", "inferred"),
    ],
)
def test_fact_provenance_survives_latest_thesis_and_discrepancy(
    basis: Any, second_basis: Any
) -> None:
    from manager_mosaic.discrepancy import FactRecord, detect_numeric_discrepancies
    from manager_mosaic.thesis import ThesisClaim, evaluate_claim

    old = FactRecord("performance.irr", "fund:a", "2024Q4", 99.0, "old", "observed")
    first = FactRecord("performance.irr", "fund:a", "2025Q1", 8.0, "repeated", basis)
    second = FactRecord("performance.irr", "fund:a", "Q1 2025", 12.0, "repeated", second_basis)
    facts = [old, first, second]
    result = evaluate_claim(
        ThesisClaim("c", "IRR", "fund:a", "performance.irr", "min", 10.0), facts
    )
    assert result.verdict == "at_risk"
    assert result.evidence_ids == ("repeated",)  # Legacy API keeps its original deduplication.
    assert result.contributing_facts == (first, second)
    assert [(f.evidence_id, f.value, f.basis) for f in result.contributing_facts] == [
        ("repeated", 8.0, basis),
        ("repeated", 12.0, second_basis),
    ]
    discrepancy = detect_numeric_discrepancies(facts)[0]
    assert discrepancy.contributing_facts == (first, second)
    assert [(f.value, f.basis) for f in discrepancy.contributing_facts] == [
        (8.0, basis),
        (12.0, second_basis),
    ]


def test_fact_provenance_legacy_constructor_defaults_to_unknown() -> None:
    from manager_mosaic.discrepancy import FactRecord, detect_numeric_discrepancies
    from manager_mosaic.thesis import ThesisClaim, evaluate_claim

    first = FactRecord("metric", "entity", "2025Q1", 1.0, "a")
    second = FactRecord("metric", "entity", "2025Q1", 2.0, "b")
    assert first.basis == "unknown"
    assert {
        f.basis for f in detect_numeric_discrepancies([first, second])[0].contributing_facts
    } == {"unknown"}
    claim = ThesisClaim("c", "Metric", "entity", "metric", "max", 5.0)
    result = evaluate_claim(claim, [first, second])
    assert result.verdict == "supported"
    assert all(f.basis == "unknown" for f in result.contributing_facts)
    assert evaluate_claim(claim, []).contributing_facts == ()


@pytest.mark.parametrize("basis", [None, "parser", "manual", "false", True, [], {}])
def test_fact_provenance_rejects_unsupported_basis(basis: Any) -> None:
    from manager_mosaic.discrepancy import FactRecord

    with pytest.raises(ValueError, match="unsupported fact basis"):
        FactRecord("metric", "entity", "2025Q1", 1.0, "evidence", basis)


def test_model_fact_provenance_preserves_explicit_basis_and_legacy_import() -> None:
    from manager_mosaic.discrepancy import FactRecord as LegacyFactRecord
    from manager_mosaic.thesis import ThesisClaim, evaluate_claim

    assert LegacyFactRecord is FactRecord
    fact = FactRecord("metric", "entity", "2025Q1", 8.0, "evidence", basis="inferred")
    assert fact.basis == "inferred"
    claim = ThesisClaim("c", "Metric", "entity", "metric", "min", 10.0)
    check = evaluate_claim(claim, [fact])
    assert check.verdict == "contradicted"
    assert [(f.value, f.evidence_id, f.basis) for f in check.contributing_facts] == [
        (8.0, "evidence", "inferred")
    ]
    assert LegacyFactRecord("metric", "entity", "2025Q1", 8.0, "evidence").basis == "unknown"


def test_fact_provenance_keeps_equal_values_and_duplicate_associations() -> None:
    from collections import Counter

    from manager_mosaic.discrepancy import detect_numeric_discrepancies
    from manager_mosaic.thesis import ThesisClaim, evaluate_claim

    observed = FactRecord("metric", "entity", "2025Q1", 8.0, "shared", "observed")
    inferred = FactRecord("metric", "entity", "2025Q1", 8.0, "shared", "inferred")
    unknown = FactRecord("metric", "entity", "2025Q1", 12.0, "shared")
    facts = [observed, inferred, unknown, inferred]
    discrepancy = detect_numeric_discrepancies(facts)[0]
    assert discrepancy.contributing_facts == tuple(facts)
    assert discrepancy.values == (8.0, 8.0, 12.0, 8.0)
    assert discrepancy.evidence_ids == ("shared",) * 4

    claim = ThesisClaim("c", "Metric", "entity", "metric", "min", 10.0)
    check = evaluate_claim(claim, facts)
    assert check.verdict == "at_risk"
    assert check.evidence_ids == ("shared",)
    assert Counter((f.value, f.evidence_id, f.basis) for f in check.contributing_facts) == {
        (8.0, "shared", "observed"): 1,
        (8.0, "shared", "inferred"): 2,
        (12.0, "shared", "unknown"): 1,
    }
    assert evaluate_claim(claim, facts[::-1]).contributing_facts == check.contributing_facts


def test_fact_provenance_preserves_legacy_result_constructors() -> None:
    from manager_mosaic.discrepancy import DiscrepancyRecord
    from manager_mosaic.thesis import ThesisCheck

    discrepancy = DiscrepancyRecord(
        "d", "metric", "entity", "2025Q1", (1.0, 2.0), ("a", "b"), "numeric_delta"
    )
    assert discrepancy.contributing_facts == ()
    assert discrepancy.bases == ()
    assert discrepancy.evidence_bases == ()
    check = ThesisCheck("c", "supported", ("a",))
    assert check.contributing_facts == ()
    assert check.bases == ()
    assert check.evidence_bases == ()


def test_result_provenance_accessors_expose_inferred_only_and_mixed_bases() -> None:
    from manager_mosaic.discrepancy import detect_numeric_discrepancies
    from manager_mosaic.thesis import ThesisClaim, evaluate_claim

    claim = ThesisClaim("c", "Metric", "entity", "metric", "min", 10.0)
    inferred = FactRecord("metric", "entity", "2025Q1", 8.0, "shared", basis="inferred")
    inferred_only = evaluate_claim(claim, [inferred])
    assert inferred_only.bases == ("inferred",)
    assert inferred_only.evidence_bases == (("shared", "inferred"),)

    observed = FactRecord("metric", "entity", "2025Q1", 12.0, "shared", basis="observed")
    mixed = evaluate_claim(claim, [observed, inferred])
    assert mixed.bases == ("inferred", "observed")
    assert mixed.evidence_bases == (("shared", "inferred"), ("shared", "observed"))
    # Repeated evidence ID is retained once per contributing fact, not deduplicated.
    assert mixed.evidence_bases.count(("shared", "inferred")) == 1
    assert len(mixed.evidence_bases) == 2

    discrepancy = detect_numeric_discrepancies([observed, inferred])[0]
    assert discrepancy.bases == ("observed", "inferred")
    assert discrepancy.evidence_bases == (("shared", "observed"), ("shared", "inferred"))


def test_result_provenance_accessors_keep_legacy_facts_unknown() -> None:
    from manager_mosaic.thesis import ThesisClaim, evaluate_claim

    legacy = FactRecord("metric", "entity", "2025Q1", 8.0, "ev")
    check = evaluate_claim(ThesisClaim("c", "Metric", "entity", "metric", "min", 10.0), [legacy])
    assert check.bases == ("unknown",)
    assert check.evidence_bases == (("ev", "unknown"),)


def test_top_level_fact_provenance_exports_match_model() -> None:
    from manager_mosaic.model import FactBasis as ModelFactBasis
    from manager_mosaic.model import FactRecord as ModelFactRecord

    assert manager_mosaic.FactRecord is ModelFactRecord
    assert manager_mosaic.FactBasis is ModelFactBasis
    assert "FactRecord" in manager_mosaic.__all__
    assert "FactBasis" in manager_mosaic.__all__
    assert manager_mosaic.FactRecord("m", "e", "2025Q1", 1.0, "ev").basis == "unknown"
    assert manager_mosaic.FactRecord("m", "e", "2025Q1", 1.0, "ev", basis="observed").basis == (
        "observed"
    )
    with pytest.raises(ValueError, match="unsupported fact basis"):
        manager_mosaic.FactRecord("m", "e", "2025Q1", 1.0, "ev", basis="extracted")  # type: ignore[arg-type]


def _typed_mention(**changes: Any) -> Store:
    """Exercise the retained typed API independently of raw-payload admission."""
    store = _load("minimal_store.json")
    item = replace(store.entries[0].mentions[0], **changes)
    return replace(store, entries=(replace(store.entries[0], mentions=(item,)),))


def _typed_sort(value: Any) -> Store:
    store = _load("minimal_store.json")
    return replace(store, periods=(replace(store.periods[0], sort=value), *store.periods[1:]))


def test_payload_collects_structural_and_independent_semantic_defects() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text())
    item = payload["entries"][0]
    del item["id"]
    del payload["periods"][0]["label"]
    mention_data = item["mentions"][0]
    del mention_data["src"]
    mention_data["inferred"] = "false"
    mention_data["bps"] = "25"
    mention_data["size"] = 36
    item["first"] = "unknown-period"
    item["pub"]["src"] = "unknown-document"
    violations = validate_payload(payload)
    paths = {v.record_id for v in violations}
    assert {
        "$.entries[0].id",
        "$.periods[0].label",
        "$.entries[0].mentions[0].src",
        "$.entries[0].mentions[0].inferred",
        "$.entries[0].mentions[0].bps",
        "$.entries[0].mentions[0].size",
        "$.entries[0].first",
        "$.entries[0].pub.src",
    } <= paths
    with pytest.raises(ValueError) as error:
        Store.from_dict(payload)
    assert all(path in str(error.value) for path in paths)


@pytest.mark.parametrize("value", [None, "false", 0, [], {}])
def test_payload_rejects_non_boolean_inferred(value: Any) -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text())
    payload["entries"][0]["mentions"][0]["inferred"] = value
    assert any(v.record_id.endswith(".inferred") for v in validate_payload(payload))
    with pytest.raises(ValueError, match="inferred"):
        Store.from_dict(payload)


def test_payload_missing_inferred_is_aggregated_before_construction() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text())
    del payload["entries"][0]["mentions"][0]["inferred"]
    assert any(v.record_id.endswith(".inferred") for v in validate_payload(payload))
    with pytest.raises(ValueError, match="inferred"):
        Store.from_dict(payload)


@pytest.mark.parametrize("missing_field", ["id", "pub"])
def test_payload_validates_all_entries_before_constructing_any(
    missing_field: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    damaged = dict(payload["entries"][0])
    damaged["id"] = "second-entry"
    damaged["first"] = "unknown-period"
    del damaged[missing_field]
    payload["entries"].append(damaged)

    def unexpected_construction(item: Any) -> None:
        pytest.fail("Entry construction started before the entire payload was validated")

    monkeypatch.setattr("manager_mosaic.model._entry_from_dict", unexpected_construction)

    with pytest.raises(ValueError) as error:
        Store.from_dict(payload)

    assert f"$.entries[1].{missing_field}: required field is missing" in str(error.value)
    assert "$.entries[1].first: period 'unknown-period' referenced but not defined" in str(
        error.value
    )


@pytest.mark.parametrize("value", [36, None, False, [], {}])
def test_payload_currency_type_damage_preserves_independent_period_error(value: Any) -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["flag"] = value
    payload["entries"][0]["mentions"][0]["size"] = value
    payload["entries"][0]["first"] = "unknown-period"

    violations = validate_payload(payload)
    assert {v.record_id for v in violations} == {
        "$.entries[0].flag",
        "$.entries[0].mentions[0].size",
        "$.entries[0].first",
    }

    # The typed API must also skip malformed currency values and finish its checks.
    original = _typed_mention(size=value)
    broken = replace(
        original,
        entries=(replace(original.entries[0], flag=value, first="unknown-period"),),
    )
    assert [(v.record_id, v.message) for v in validate(broken)] == [
        ("alpha-fund", "period 'unknown-period' referenced but not defined")
    ]


@pytest.mark.parametrize("collection", [None, 23, "bad", [{"id": []}], [None]])
def test_payload_wrong_collection_types_do_not_abort_other_checks(collection: Any) -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text())
    payload["periods"] = collection
    payload["entries"][0]["first"] = "unknown"
    payload["entries"][0]["flag"] = "$B"
    violations = validate_payload(payload)
    assert any(v.record_id.startswith("$.periods") for v in violations)
    assert not any("referenced but not defined" in v.message for v in violations)
    assert any(v.record_id == "$.entries[0].flag" for v in violations)


def test_payload_valid_and_public_entrypoint() -> None:
    from manager_mosaic import validate_payload as public_validate

    assert "validate_payload" in manager_mosaic.__all__
    assert public_validate is validate_payload
    payload = json.loads((FIXTURES / "minimal_store.json").read_text())
    assert public_validate(payload) == []
    assert validate(Store.from_dict(payload)) == []


def test_payload_public_entrypoint_reports_structural_and_semantic_defects() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    del payload["entries"][0]["mentions"][0]["inferred"]
    payload["entries"][0]["first"] = "unknown-period"

    violations = manager_mosaic.validate_payload(payload)

    assert all(isinstance(item, manager_mosaic.ValidationViolation) for item in violations)
    assert {item.record_id for item in violations} == {
        "$.entries[0].mentions[0].inferred",
        "$.entries[0].first",
    }
