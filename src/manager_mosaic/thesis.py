"""Deterministic thesis claim evaluation against normalized facts."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from manager_mosaic.discrepancy import FactRecord

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

    latest = max(matching, key=lambda fact: (fact.period, fact.evidence_id))
    if claim.expected_pattern == "min":
        verdict: ThesisVerdict = "contradicted" if latest.value < claim.threshold else "supported"
    else:
        verdict = "contradicted" if latest.value > claim.threshold else "supported"

    return ThesisCheck(
        claim_id=claim.claim_id,
        verdict=verdict,
        evidence_ids=(latest.evidence_id,),
    )
