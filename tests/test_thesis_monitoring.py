"""Thesis monitoring evaluator tests."""

from __future__ import annotations

from manager_mosaic.discrepancy import FactRecord
from manager_mosaic.thesis import ThesisClaim, evaluate_claim


def test_evaluate_claim_marks_contradicted_when_irr_below_min_threshold() -> None:
    claim = ThesisClaim(
        claim_id="irr-floor",
        claim_text="Fund IRR should remain above 10%",
        entity_ref="fund-alpha",
        fact_key="performance.irr",
        expected_pattern="min",
        threshold=10.0,
    )
    facts = [
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="2024Q4",
            value=8.5,
            evidence_id="ev-irr-low",
        )
    ]

    check = evaluate_claim(claim, facts)

    assert check.claim_id == "irr-floor"
    assert check.verdict == "contradicted"
    assert check.evidence_ids == ("ev-irr-low",)
