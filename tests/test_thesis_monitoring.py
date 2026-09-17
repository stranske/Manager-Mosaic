"""Thesis monitoring evaluator tests."""

from __future__ import annotations

import math
import pytest

from manager_mosaic.discrepancy import FactRecord
from manager_mosaic.thesis import ThesisClaim, evaluate_claim


def _irr_min_claim(*, threshold: float = 10.0) -> ThesisClaim:
    return ThesisClaim(
        claim_id="irr-floor",
        claim_text="Fund IRR should remain above 10%",
        entity_ref="fund-alpha",
        fact_key="performance.irr",
        expected_pattern="min",
        threshold=threshold,
    )


def _irr_max_claim(*, threshold: float = 15.0) -> ThesisClaim:
    return ThesisClaim(
        claim_id="irr-ceiling",
        claim_text="Fund IRR should stay below 15%",
        entity_ref="fund-alpha",
        fact_key="performance.irr",
        expected_pattern="max",
        threshold=threshold,
    )


def test_evaluate_claim_marks_contradicted_when_irr_below_min_threshold() -> None:
    claim = _irr_min_claim()
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


def test_evaluate_claim_marks_supported_when_min_threshold_met() -> None:
    claim = _irr_min_claim()
    facts = [
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="2024Q4",
            value=12.0,
            evidence_id="ev-irr-ok",
        )
    ]

    check = evaluate_claim(claim, facts)

    assert check.verdict == "supported"
    assert check.evidence_ids == ("ev-irr-ok",)


def test_evaluate_claim_marks_contradicted_when_max_threshold_exceeded() -> None:
    claim = _irr_max_claim()
    facts = [
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="2024Q4",
            value=16.0,
            evidence_id="ev-irr-high",
        )
    ]

    check = evaluate_claim(claim, facts)

    assert check.verdict == "contradicted"
    assert check.evidence_ids == ("ev-irr-high",)


def test_evaluate_claim_marks_supported_when_max_threshold_not_exceeded() -> None:
    claim = _irr_max_claim()
    facts = [
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="2024Q4",
            value=14.0,
            evidence_id="ev-irr-ok",
        )
    ]

    check = evaluate_claim(claim, facts)

    assert check.verdict == "supported"
    assert check.evidence_ids == ("ev-irr-ok",)


def test_evaluate_claim_returns_insufficient_evidence_when_no_matching_facts() -> None:
    claim = _irr_min_claim()
    facts = [
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-beta",
            period="2024Q4",
            value=12.0,
            evidence_id="ev-other-fund",
        )
    ]

    check = evaluate_claim(claim, facts)

    assert check.verdict == "insufficient_evidence"
    assert check.evidence_ids == ()


def test_evaluate_claim_selects_latest_matching_fact_by_period() -> None:
    claim = _irr_min_claim()
    facts = [
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="Q4 2024",
            value=8.0,
            evidence_id="ev-old",
        ),
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="Q1 2025",
            value=12.0,
            evidence_id="ev-new",
        ),
    ]

    check = evaluate_claim(claim, facts)

    assert check.verdict == "supported"
    assert check.evidence_ids == ("ev-new",)


def test_thesis_claim_rejects_non_finite_threshold() -> None:
    with pytest.raises(ValueError, match="threshold must be finite"):
        _irr_min_claim(threshold=math.nan)
