"""Evidence-object/v1 validator tests."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

import pytest

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


def _identity_payload() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(
        (Path(__file__).parent / "fixtures/backplane/valid_evidence_object.json").read_text()
    )
    payload["locator"] = {"page": 0}
    payload["document_ref"] = {
        "sha256": "a" * 64,
        "doc_key": "manager:demo/manager_letter/2024-02-29",
        "doc_type": "manager_letter",
        "page": 0,
        "text_basis": "native",
        "supersedes": "b" * 64,
        "supersession_evidence": {"mechanism": "owner_assertion", "detail": "Earlier bytes"},
    }
    return payload


@pytest.mark.parametrize(
    "defect, expected",
    [
        ("page", "conflicts with locator.page"),
        ("date", "ISO calendar date"),
        ("supersedes", "earlier byte version"),
    ],
)
def test_document_identity_rejects_individual_defects(defect: str, expected: str) -> None:
    payload = _identity_payload()
    if defect == "page":
        payload["document_ref"]["page"] = 7
    elif defect == "date":
        payload["document_ref"]["doc_key"] = "manager:demo/manager_letter/2025-02-31"
    else:
        payload["document_ref"]["supersedes"] = payload["document_ref"]["sha256"]
    assert any(expected in v for v in validate_evidence_object(payload))


def test_document_identity_combined_defects_returns_all_three_violations() -> None:
    """Schema-valid fields can still violate all three identity relationships."""
    payload = _identity_payload()
    payload["document_ref"]["page"] = 7
    payload["document_ref"]["doc_key"] = "manager:demo/manager_letter/2025-02-31"
    payload["document_ref"]["supersedes"] = payload["document_ref"]["sha256"]

    assert sorted(validate_evidence_object(payload)) == sorted(
        [
            "document_ref.page conflicts with locator.page",
            "document_ref.doc_key as_of must be an ISO calendar date or unknown",
            "document_ref.supersedes must name an earlier byte version",
        ]
    )


def test_document_identity_combined_defects_aggregate_with_schema_and_excerpt() -> None:
    payload = _identity_payload()
    payload["document_ref"]["page"] = 7
    payload["document_ref"]["doc_key"] = "manager:demo/manager_letter/2025-02-31"
    payload["document_ref"]["supersedes"] = payload["document_ref"]["sha256"]
    del payload["excerpt"]
    payload["method"] = "telepathy"
    violations = validate_evidence_object(payload)
    for marker in [
        "conflicts with locator.page",
        "ISO calendar date",
        "earlier byte version",
        "excerpt",
        "telepathy",
    ]:
        assert any(marker in v for v in violations)


@pytest.mark.parametrize("as_of", ["2024-02-29", "unknown", "2025-01-01"])
def test_document_identity_accepts_matching_zero_page_and_valid_dates(as_of: str) -> None:
    payload = _identity_payload()
    payload["document_ref"]["doc_key"] = f"manager:demo/manager_letter/{as_of}"
    assert validate_evidence_object(payload) == []


@pytest.mark.parametrize(
    "field, value",
    [("document_ref", None), ("document_ref", []), ("locator", 1), ("locator", None)],
)
def test_document_identity_bad_container_types_are_reported_without_crashing(
    field: str, value: Any
) -> None:
    payload = _identity_payload()
    payload[field] = value
    assert validate_evidence_object(payload)


def test_document_identity_rejects_noncanonical_date() -> None:
    payload = _identity_payload()
    payload["document_ref"]["doc_key"] = "manager:demo/manager_letter/20240229"
    assert any("ISO calendar date" in v for v in validate_evidence_object(payload))
