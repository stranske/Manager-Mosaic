"""Numeric discrepancy detection tests."""

from __future__ import annotations

import json
import math
import sys
from itertools import permutations

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


def test_detect_numeric_discrepancies_groups_equivalent_period_labels() -> None:
    facts = [
        FactRecord("performance.irr", "fund-alpha", "2024Q4", 12.0, "ev-a"),
        FactRecord("performance.irr", "fund-alpha", "Q4 2024", 18.0, "ev-b"),
    ]

    discrepancies = detect_numeric_discrepancies(facts, threshold_percent=5.0)

    assert len(discrepancies) == 1
    assert discrepancies[0].period == "2024Q4"
    assert discrepancies[0].kind == "numeric_delta"
    assert set(discrepancies[0].values) == {12.0, 18.0}


def test_unparseable_periods_still_group_by_exact_label() -> None:
    facts = [
        FactRecord("performance.irr", "fund-alpha", "FY2025", 12.0, "ev-a"),
        FactRecord("performance.irr", "fund-alpha", "FY2025", 18.0, "ev-b"),
    ]

    discrepancies = detect_numeric_discrepancies(facts, threshold_percent=5.0)

    assert len(discrepancies) == 1
    assert discrepancies[0].period == "FY2025"

    distinct_labels = [
        FactRecord("performance.irr", "fund-alpha", "FY2025", 12.0, "ev-c"),
        FactRecord("performance.irr", "fund-alpha", "FY 2025", 18.0, "ev-d"),
    ]

    assert detect_numeric_discrepancies(distinct_labels, threshold_percent=5.0) == []


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


def test_non_finite_threshold_rejected() -> None:
    with pytest.raises(ValueError, match="threshold_percent"):
        detect_numeric_discrepancies(_irr_pair(), threshold_percent=math.nan)


def test_opposite_max_finite_values_produce_documented_spread() -> None:
    max_value = sys.float_info.max
    facts = [
        FactRecord("metric", "entity", "2024", max_value, "ev-a"),
        FactRecord("metric", "entity", "2024", -max_value, "ev-b"),
    ]

    assert detect_numeric_discrepancies(facts, threshold_percent=200.0) == []


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


def test_discrepancy_id_and_display_are_permutation_stable() -> None:
    facts = [
        FactRecord("performance.irr", "fund:alpha", label, value, f"ev-{i}")
        for i, (label, value) in enumerate(
            zip(["2025Q1", "2025-Q1", "Q1 2025"], [8.0, 12.0, 16.0], strict=True)
        )
    ]
    results = [detect_numeric_discrepancies(list(order))[0] for order in permutations(facts)]
    assert len({r.discrepancy_id for r in results}) == 1
    assert {r.period for r in results} == {"2025-Q1"}
    assert json.loads(results[0].discrepancy_id) == [
        "performance.irr",
        "fund:alpha",
        ["quarter", 2025, 1],
    ]
    for result in results:
        assert set(zip(result.values, result.evidence_ids, strict=True)) == {
            (8.0, "ev-0"),
            (12.0, "ev-1"),
            (16.0, "ev-2"),
        }


@pytest.mark.parametrize("period", ["2025Q1", "2025-Q1", "Q1 2025", " 2025q1 ", "q1 2025"])
def test_discrepancy_id_is_independent_of_aliases_present(period: str) -> None:
    # A source can change its period spelling between runs without changing identity.
    facts = [
        FactRecord("performance.irr", "fund:alpha", period, 8.0, "ev-a"),
        FactRecord("performance.irr", "fund:alpha", period, 12.0, "ev-b"),
    ]

    discrepancies = detect_numeric_discrepancies(facts)

    assert len(discrepancies) == 1
    assert discrepancies[0].discrepancy_id == '["performance.irr","fund:alpha",["quarter",2025,1]]'
    assert discrepancies[0].period == period


def test_discrepancy_canonical_identity_keeps_distinct_dimensions() -> None:
    identities = [
        ("metric", "fund:a", "2025Q1"),
        ("other", "fund:a", "2025Q1"),
        ("metric", "fund:b", "2025Q1"),
        ("metric", "fund:a", "2025Q2"),
        ("metric", "fund:a", "2026Q1"),
        ("metric", "fund:a", "2025 Q1"),
        ("metric", "fund:a", '["quarter",2025,1]'),
        ("metric", "fund:a", "FY2025"),
        ("metric", "fund:a", "FY2025 "),
        ("metric", "fund:a", "FY 2025"),
    ]
    records = [
        detect_numeric_discrepancies(
            [
                FactRecord(key, entity, period, 1.0, "ev-a"),
                FactRecord(key, entity, period, 2.0, "ev-b"),
            ]
        )[0]
        for key, entity, period in identities
    ]
    assert len({r.discrepancy_id for r in records}) == len(identities)
    assert json.loads(records[-1].discrepancy_id)[2] == ["raw", "FY 2025"]
