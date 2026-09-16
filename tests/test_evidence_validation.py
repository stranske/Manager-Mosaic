"""Evidence-object/v1 validator tests."""

from __future__ import annotations

from manager_mosaic.evidence import validate_evidence_object


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
