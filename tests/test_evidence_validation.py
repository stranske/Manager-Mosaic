"""Evidence-object/v1 validator tests."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from manager_mosaic import validate_evidence_object
from manager_mosaic.evidence import load_evidence_schema


def test_validate_evidence_object_reports_missing_excerpt_key() -> None:
    payload = {
        "schema_version": "evidence-object/v1",
        "evidence_id": "ev-1",
        "fact_ref": "strategy.asset_class",
        "source_id": "doc-1",
        "method": "parser",
    }
    violations = validate_evidence_object(payload)
    assert violations
    assert any("excerpt" in message for message in violations)


def test_validate_evidence_object_accepts_explicit_null_excerpt() -> None:
    payload = {
        "schema_version": "evidence-object/v1",
        "evidence_id": "ev-1",
        "fact_ref": "strategy.asset_class",
        "source_id": "doc-1",
        "method": "parser",
        "excerpt": None,
    }
    assert validate_evidence_object(payload) == []


def test_validate_evidence_object_accepts_valid_payload() -> None:
    payload = {
        "schema_version": "evidence-object/v1",
        "evidence_id": "ev-1",
        "fact_ref": "strategy.asset_class",
        "source_id": "doc-1",
        "method": "parser",
        "excerpt": "Quoted source text supporting the fact.",
    }
    assert validate_evidence_object(payload) == []


def test_validate_evidence_object_reports_every_violation() -> None:
    """A validator that returns only the first error must fail this test."""
    violations = validate_evidence_object({})

    # The missing-excerpt pre-check plus one `required` error per schema key.
    assert len(violations) == 7
    for key in (
        "schema_version",
        "evidence_id",
        "fact_ref",
        "source_id",
        "method",
        "excerpt",
    ):
        assert any(key in message for message in violations), key


def test_validate_evidence_object_reports_violations_at_mixed_depths() -> None:
    """Violations nested at different paths are all returned, in path order."""
    payload = {
        "schema_version": "evidence-object/v1",
        "evidence_id": "",
        "fact_ref": "strategy.asset_class",
        "source_id": "doc-1",
        "method": "telepathy",
        "excerpt": "Quoted source text supporting the fact.",
        "locator": {"page": -1, "bbox": [1.0, 2.0]},
        "confidence": 5,
    }
    violations = validate_evidence_object(payload)

    assert len(violations) == 5
    assert any("non-empty" in message for message in violations)
    assert any("telepathy" in message for message in violations)
    assert any("too short" in message for message in violations)
    assert any("minimum of 0" in message for message in violations)
    assert any("maximum of 1" in message for message in violations)


def test_evidence_schema_is_readable_through_package_resources() -> None:
    """The schema must resolve from the installed package, not a source path."""
    schema_file = resources.files("manager_mosaic").joinpath(
        "schemas", "evidence-object-v1.schema.json"
    )
    assert schema_file.is_file()
    assert load_evidence_schema() == json.loads(schema_file.read_text(encoding="utf-8"))


def test_packaged_evidence_schema_matches_published_contract() -> None:
    """The packaged copy must not drift from the published contract."""
    published = Path("docs/contracts/schemas/evidence-object-v1.schema.json")
    if not published.is_file():  # pragma: no cover - installed-package runs
        return
    packaged = resources.files("manager_mosaic").joinpath(
        "schemas", "evidence-object-v1.schema.json"
    )
    assert json.loads(packaged.read_text(encoding="utf-8")) == json.loads(
        published.read_text(encoding="utf-8")
    )
