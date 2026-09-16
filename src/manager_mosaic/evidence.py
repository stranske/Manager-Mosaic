"""Evidence-object/v1 validation for the manager mosaic package."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from manager_mosaic.model import load_schema


def load_evidence_schema() -> dict[str, Any]:
    """Load the packaged evidence-object/v1 JSON Schema.

    The schema ships inside the package (``manager_mosaic/schemas``) and is read
    through package resources, so validation works from an installed wheel and
    not only from a source checkout.
    """
    return load_schema("evidence-object-v1")


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
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
        violations.append(error.message)
    return violations
