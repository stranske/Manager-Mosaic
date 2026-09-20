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


def test_evaluate_claim_returns_insufficient_evidence_for_different_fact_key() -> None:
    claim = _irr_min_claim()
    facts = [
        FactRecord(
            fact_key="performance.moic",
            entity_ref="fund-alpha",
            period="2024Q4",
            value=12.0,
            evidence_id="ev-moic",
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


def test_evaluate_claim_selects_chronologically_latest_across_period_formats() -> None:
    claim = _irr_min_claim()
    facts = [
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="Q4 2024",
            value=8.0,
            evidence_id="ev-q4-2024",
        ),
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="2025Q1",
            value=12.0,
            evidence_id="ev-2025q1",
        ),
    ]

    check = evaluate_claim(claim, facts)

    assert check.verdict == "supported"
    assert check.evidence_ids == ("ev-2025q1",)


@pytest.mark.parametrize("claim", [_irr_min_claim(), _irr_max_claim()])
def test_evaluate_claim_same_period_conflict_is_independent_of_evidence_id_order(
    claim: ThesisClaim,
) -> None:
    """Relabeling equivalent conflicting facts must not change the thesis check."""
    values = (8.0, 18.0)
    equivalent_latest_periods = ("2025Q1", "Q1 2025")
    checks = []
    for assigned_ids in (("ev-a", "ev-z"), ("ev-z", "ev-a")):
        facts = [
            FactRecord("performance.irr", "fund-alpha", "2024Q4", 12.0, "ev-old"),
            *(
                FactRecord("performance.irr", "fund-alpha", period, value, evidence_id)
                for period, value, evidence_id in zip(
                    equivalent_latest_periods, values, assigned_ids, strict=True
                )
            ),
        ]

        check = evaluate_claim(claim, facts)
        checks.append(check)

        assert check.verdict == "at_risk"
        assert check.evidence_ids == ("ev-a", "ev-z")

    assert checks[0] == checks[1]


@pytest.mark.parametrize(
    ("claim", "values", "expected_verdict"),
    [
        pytest.param(_irr_min_claim(), (10.0, 12.0), "supported", id="min-supported"),
        pytest.param(_irr_min_claim(), (8.0, 9.0), "contradicted", id="min-contradicted"),
        pytest.param(_irr_max_claim(), (13.0, 15.0), "supported", id="max-supported"),
        pytest.param(_irr_max_claim(), (16.0, 18.0), "contradicted", id="max-contradicted"),
    ],
)
def test_evaluate_claim_same_period_consistent_facts_retain_all_evidence(
    claim: ThesisClaim,
    values: tuple[float, float],
    expected_verdict: str,
) -> None:
    facts = [
        FactRecord("performance.irr", "fund-alpha", "2025Q1", values[0], "ev-b"),
        FactRecord("performance.irr", "fund-alpha", "2025Q1", values[1], "ev-a"),
    ]

    check = evaluate_claim(claim, facts)

    assert check.verdict == expected_verdict
    assert check.evidence_ids == ("ev-a", "ev-b")


@pytest.mark.parametrize(
    "threshold",
    [math.nan, math.inf, -math.inf],
    ids=["nan", "inf", "neg_inf"],
)
def test_thesis_claim_rejects_non_finite_threshold(threshold: float) -> None:
    with pytest.raises(ValueError, match="threshold must be finite"):
        _irr_min_claim(threshold=threshold)
