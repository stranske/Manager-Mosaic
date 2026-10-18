"""Deterministic thesis claim evaluation against normalized facts."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from manager_mosaic.fact_keys import (
    FactKeyViolation,
    UnregisteredFactKeyError,
    validate_fact_keys,
)
from manager_mosaic.model import FactBasis, FactRecord
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
    contributing_facts: tuple[FactRecord, ...] = field(default=(), compare=False)

    @property
    def bases(self) -> tuple[FactBasis, ...]:
        """Basis of each contributing fact, aligned with ``contributing_facts``."""
        return tuple(fact.basis for fact in self.contributing_facts)

    @property
    def evidence_bases(self) -> tuple[tuple[str, FactBasis], ...]:
        """``(evidence_id, basis)`` per contributing fact, preserving repeats."""
        return tuple((fact.evidence_id, fact.basis) for fact in self.contributing_facts)


def evaluate_claim(
    claim: ThesisClaim,
    facts: Sequence[FactRecord],
    *,
    strict_fact_keys: bool = False,
    validate_fact_keys_opt_in: bool = False,
    fact_key_registry: frozenset[str] | None = None,
) -> ThesisCheck:
    """Evaluate one thesis claim against matching facts for the same entity and key.

    Fact-key validation is opt-in. With ``strict_fact_keys=True`` (alias:
    ``validate_fact_keys_opt_in=True``) every fact_key on the claim and on
    all supplied facts is checked against ``load_fact_key_registry()`` and
    any unregistered key raises :class:`UnregisteredFactKeyError` carrying
    every violation, instead of silently returning
    ``insufficient_evidence`` for a typo'd key. Callers omitting the flag
    retain the previous behaviour exactly.
    """
    if strict_fact_keys or validate_fact_keys_opt_in:
        violations: list[FactKeyViolation] = validate_fact_keys(
            facts, claims=[claim], registry=fact_key_registry
        )
        if violations:
            raise UnregisteredFactKeyError(violations)
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
        contributing_facts=tuple(
            sorted(
                latest_facts,
                key=lambda fact: (
                    fact.fact_key,
                    fact.entity_ref,
                    fact.period,
                    fact.value,
                    fact.evidence_id,
                    fact.basis,
                ),
            )
        ),
    )
