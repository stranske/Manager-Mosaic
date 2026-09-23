"""Deterministic thesis claim evaluation against normalized facts."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from manager_mosaic.discrepancy import FactRecord
from manager_mosaic.periods import period_chronology_key

ThesisVerdict = Literal[
    "supported",
    "at_risk",
    "contradicted",
    "insufficient_evidence",
]
ExpectedPattern = Literal["min", "max"]


@dataclass(frozen=True)
class ThesisClaim:
    claim_id: str
    claim_text: str
    entity_ref: str
    fact_key: str
    expected_pattern: ExpectedPattern
    threshold: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.threshold):
            raise ValueError(f"threshold must be finite, got {self.threshold!r}")


@dataclass(frozen=True)
class ThesisCheck:
    claim_id: str
    verdict: ThesisVerdict
    evidence_ids: tuple[str, ...]


def evaluate_claim(claim: ThesisClaim, facts: Sequence[FactRecord]) -> ThesisCheck:
    """Evaluate one thesis claim against matching facts for the same entity and key."""
    matching = [
        fact
        for fact in facts
        if fact.entity_ref == claim.entity_ref and fact.fact_key == claim.fact_key
    ]
    if not matching:
        return ThesisCheck(
            claim_id=claim.claim_id,
            verdict="insufficient_evidence",
            evidence_ids=(),
        )

    latest_period = max(period_chronology_key(fact.period) for fact in matching)
    latest_facts = [
        fact for fact in matching if period_chronology_key(fact.period) == latest_period
    ]
    if claim.expected_pattern == "min":
        contradicted = [fact.value < claim.threshold for fact in latest_facts]
    elif claim.expected_pattern == "max":
        contradicted = [fact.value > claim.threshold for fact in latest_facts]
    else:
        raise ValueError(f"unsupported expected_pattern: {claim.expected_pattern!r}")

    verdict: ThesisVerdict
    if any(contradicted) and not all(contradicted):
        verdict = "at_risk"
    elif any(contradicted):
        verdict = "contradicted"
    else:
        verdict = "supported"

    return ThesisCheck(
        claim_id=claim.claim_id,
        verdict=verdict,
        evidence_ids=tuple(sorted({fact.evidence_id for fact in latest_facts})),
    )
