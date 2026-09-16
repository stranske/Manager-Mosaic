"""Numeric discrepancy detection tests."""

from __future__ import annotations

import math

import pytest

from manager_mosaic.discrepancy import FactRecord, detect_numeric_discrepancies


def _irr_pair() -> list[FactRecord]:
    return [
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="2024Q4",
            value=12.0,
            evidence_id="ev-irr-a",
        ),
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="2024Q4",
            value=18.0,
            evidence_id="ev-irr-b",
        ),
    ]


def test_detect_numeric_discrepancies_flags_conflicting_irr_values() -> None:
    discrepancies = detect_numeric_discrepancies(_irr_pair(), threshold_percent=5.0)

    assert len(discrepancies) == 1
    record = discrepancies[0]
    assert record.fact_key == "performance.irr"
    assert record.entity_ref == "fund-alpha"
    assert record.period == "2024Q4"
    assert record.kind == "numeric_delta"
    assert set(record.values) == {12.0, 18.0}
    assert set(record.evidence_ids) == {"ev-irr-a", "ev-irr-b"}


def test_threshold_boundary_equality_and_just_over() -> None:
    facts = _irr_pair()

    assert detect_numeric_discrepancies(facts, threshold_percent=50.0) == []
    assert len(detect_numeric_discrepancies(facts, threshold_percent=49.0)) == 1


def test_zero_baseline_flags_unbounded_spread() -> None:
    facts = [
        FactRecord("metric", "entity", "2024", 0.0, "ev-a"),
        FactRecord("metric", "entity", "2024", 1.0, "ev-b"),
    ]

    assert len(detect_numeric_discrepancies(facts, threshold_percent=150.0)) == 1


def test_negative_threshold_rejected() -> None:
    with pytest.raises(ValueError, match="threshold_percent"):
        detect_numeric_discrepancies(_irr_pair(), threshold_percent=-1.0)


def test_non_finite_fact_value_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        FactRecord("metric", "entity", "2024", math.nan, "ev-a")


def test_discrepancy_id_injective_for_colon_entity_refs() -> None:
    left = [
        FactRecord("a", "b:c", "d", 1.0, "ev-1"),
        FactRecord("a", "b:c", "d", 2.0, "ev-2"),
    ]
    right = [
        FactRecord("a:b", "c", "d", 1.0, "ev-3"),
        FactRecord("a:b", "c", "d", 2.0, "ev-4"),
    ]

    left_id = detect_numeric_discrepancies(left)[0].discrepancy_id
    right_id = detect_numeric_discrepancies(right)[0].discrepancy_id
    assert left_id != right_id
