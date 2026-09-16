"""Deterministic numeric discrepancy detection for normalized facts."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FactRecord:
    fact_key: str
    entity_ref: str
    period: str
    value: float
    evidence_id: str

    def __post_init__(self) -> None:
        if not math.isfinite(self.value):
            raise ValueError(f"fact value must be finite, got {self.value!r}")


@dataclass(frozen=True)
class DiscrepancyRecord:
    discrepancy_id: str
    fact_key: str
    entity_ref: str
    period: str
    values: tuple[float, ...]
    evidence_ids: tuple[str, ...]
    kind: Literal["numeric_delta"]


def _discrepancy_id(fact_key: str, entity_ref: str, period: str) -> str:
    """Return an injective ID for the canonical (fact_key, entity_ref, period) tuple."""
    return json.dumps([fact_key, entity_ref, period], separators=(",", ":"))


def _relative_spread_percent(values: Sequence[float]) -> float:
    """Return the maximum pairwise relative spread across ``values`` in percent."""
    if len(values) < 2:
        return 0.0
    spread = 0.0
    for left in values:
        for right in values:
            if left == right:
                continue
            baseline = min(abs(left), abs(right))
            if baseline == 0.0:
                return math.inf
            spread = max(spread, abs(left - right) / baseline * 100.0)
    return spread


def detect_numeric_discrepancies(
    facts: Sequence[FactRecord],
    *,
    threshold_percent: float = 5.0,
) -> list[DiscrepancyRecord]:
    """Flag fact groups that disagree beyond ``threshold_percent`` relative spread."""
    if not math.isfinite(threshold_percent) or threshold_percent < 0:
        raise ValueError(
            "threshold_percent must be a non-negative finite number, " f"got {threshold_percent!r}"
        )

    grouped: dict[tuple[str, str, str], list[FactRecord]] = defaultdict(list)
    for fact in facts:
        grouped[(fact.fact_key, fact.entity_ref, fact.period)].append(fact)

    discrepancies: list[DiscrepancyRecord] = []
    for (fact_key, entity_ref, period), group in sorted(grouped.items()):
        if len(group) < 2:
            continue
        values = tuple(fact.value for fact in group)
        spread = _relative_spread_percent(values)
        if not math.isinf(spread) and spread <= threshold_percent:
            continue
        evidence_ids = tuple(fact.evidence_id for fact in group)
        discrepancies.append(
            DiscrepancyRecord(
                discrepancy_id=_discrepancy_id(fact_key, entity_ref, period),
                fact_key=fact_key,
                entity_ref=entity_ref,
                period=period,
                values=values,
                evidence_ids=evidence_ids,
                kind="numeric_delta",
            )
        )
    return discrepancies
