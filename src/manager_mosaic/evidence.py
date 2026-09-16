"""Evidence-object/v1 validation for the manager mosaic package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

_EVIDENCE_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "docs/contracts/schemas/evidence-object-v1.schema.json"
)


def load_evidence_schema() -> dict[str, Any]:
    """Load the checked-in evidence-object/v1 JSON Schema."""
    return cast(
        dict[str, Any],
        json.loads(_EVIDENCE_SCHEMA_PATH.read_text(encoding="utf-8")),
    )


def validate_evidence_object(payload: dict[str, Any]) -> list[str]:
    """Return all schema violations for an evidence-object/v1 payload.

    An empty list means the payload is valid. The ``excerpt`` key must be
    present even when its value is ``null``; a wholly absent key is rejected.
    """
    violations: list[str] = []
    if "excerpt" not in payload:
        violations.append(
            "excerpt key must be present (string or explicit null); positional anchors alone are insufficient"
        )

    validator = Draft202012Validator(load_evidence_schema())
    for error in sorted(validator.iter_errors(payload), key=lambda item: item.path):
        violations.append(error.message)
    return violations
