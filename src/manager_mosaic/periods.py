"""Shared period-label normalization helpers."""

from __future__ import annotations

import re

_YEAR_FIRST_QUARTER = re.compile(
    r"^(?P<year>\d{4})(?:Q|-Q)(?P<quarter>[1-4])$",
    re.IGNORECASE,
)
_QUARTER_FIRST_YEAR = re.compile(
    r"^Q(?P<quarter>[1-4])\s+(?P<year>\d{4})$",
    re.IGNORECASE,
)


def period_chronology_key(period: str) -> tuple[int, int, str]:
    """Normalize ``YYYYQn``, ``YYYY-Qn``, and ``Qn YYYY`` for comparison."""
    normalized = period.strip()
    for pattern in (_YEAR_FIRST_QUARTER, _QUARTER_FIRST_YEAR):
        match = pattern.match(normalized)
        if match:
            return (int(match.group("year")), int(match.group("quarter")), "")
    raise ValueError(f"unsupported period label: {period!r}")
