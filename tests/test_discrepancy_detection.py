"""Numeric discrepancy detection tests."""

from __future__ import annotations

from manager_mosaic.discrepancy import FactRecord, detect_numeric_discrepancies


def test_detect_numeric_discrepancies_flags_conflicting_irr_values() -> None:
    facts = [
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

    discrepancies = detect_numeric_discrepancies(facts, threshold_percent=5.0)

    assert len(discrepancies) == 1
    record = discrepancies[0]
    assert record.fact_key == "performance.irr"
    assert record.entity_ref == "fund-alpha"
    assert record.period == "2024Q4"
    assert record.kind == "numeric_delta"
    assert set(record.values) == {12.0, 18.0}
    assert set(record.evidence_ids) == {"ev-irr-a", "ev-irr-b"}
