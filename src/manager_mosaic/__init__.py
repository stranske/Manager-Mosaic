"""Manager mosaic: evidence-linked facts, discrepancy detection, and thesis monitoring."""

from manager_mosaic.evidence import validate_evidence_object
from manager_mosaic.fact_keys import (
    FactKeyViolation,
    UnregisteredFactKeyError,
    ensure_registered_fact_keys,
    load_fact_key_registry,
    validate_claim_and_facts,
    validate_fact_keys,
    validate_facts_and_claims,
)
from manager_mosaic.model import (
    FACT_BASES,
    Document,
    Entry,
    FactBasis,
    FactRecord,
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
    validate_payload,
)

__version__ = "0.1.0"
__all__ = [
    "FACT_BASES",
    "Document",
    "Entry",
    "FactBasis",
    "FactRecord",
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
    "FactKeyViolation",
    "UnregisteredFactKeyError",
    "ensure_registered_fact_keys",
    "load_fact_key_registry",
    "validate",
    "validate_payload",
    "validate_claim_and_facts",
    "validate_evidence_object",
    "validate_fact_keys",
    "validate_facts_and_claims",
    "greet",
    "add",
]


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
