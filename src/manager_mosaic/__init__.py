"""Manager mosaic: evidence-linked facts, discrepancy detection, and thesis monitoring."""

from manager_mosaic.evidence import validate_evidence_object
from manager_mosaic.model import (
    Document,
    Entry,
    Fund,
    Gap,
    Mention,
    Period,
    Pub,
    Store,
    Theme,
    ValidationViolation,
    derive_gaps,
    document,
    entry,
    fund,
    gap,
    load_schema,
    mention,
    period,
    pub,
    theme,
    validate,
)

__version__ = "0.1.0"
__all__ = [
    "Document",
    "Entry",
    "Fund",
    "Gap",
    "Mention",
    "Period",
    "Pub",
    "Store",
    "Theme",
    "ValidationViolation",
    "derive_gaps",
    "document",
    "entry",
    "fund",
    "gap",
    "load_schema",
    "mention",
    "period",
    "pub",
    "theme",
    "validate",
    "validate_evidence_object",
    "greet",
    "add",
]


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
