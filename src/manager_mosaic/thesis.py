"""Deterministic thesis claim evaluation against normalized facts."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from manager_mosaic.discrepancy import FactRecord

_QUARTER_YEAR = re.compile(r"^(\d{4})Q([1-4])$", re.IGNORECASE)
_YEAR_QUARTER = re.compile(r"^Q([1-4])\s+(\d{4})$", re.IGNORECASE)

ThesisVerdict = Literal[
    "supported",
    "at_risk",
    "contradicted",
    "insufficient_evidence",
]
ExpectedPattern = Literal["min", "max"]


def _period_chronology_key(period: str) -> tuple[int, int, str]:
    """Return a sortable key for common quarter period labels."""
    normalized = period.strip()
    match = _QUARTER_YEAR.match(normalized)
    if match:
        return (int(match.group(1)), int(match.group(2)), normalized)
    match = _YEAR_QUARTER.match(normalized)
    if match:
        return (int(match.group(2)), int(match.group(1)), normalized)
    return (0, 0, normalized)


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

    latest = max(
        matching,
        key=lambda fact: (_period_chronology_key(fact.period), fact.evidence_id),
    )
    if claim.expected_pattern == "min":
        verdict: ThesisVerdict = "contradicted" if latest.value < claim.threshold else "supported"
    else:
        verdict = "contradicted" if latest.value > claim.threshold else "supported"

    return ThesisCheck(
        claim_id=claim.claim_id,
        verdict=verdict,
        evidence_ids=(latest.evidence_id,),
    )
