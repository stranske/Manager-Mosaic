"""Synthetic ingest fixtures validated against checked-in schemas, offline."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "backplane"
SCHEMAS = ROOT / "docs" / "contracts" / "schemas"


def _fixture(name: str) -> dict[str, Any]:
    document: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return document


def _validator() -> Draft202012Validator:
    schema = json.loads((SCHEMAS / "evidence-object-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_valid_evidence_object_fixture_loads() -> None:
    document = _fixture("valid_evidence_object.json")
    assert document["schema_version"] == "evidence-object/v1"
    _validator().validate(document)


def test_missing_excerpt_fixture_is_rejected() -> None:
    document = _fixture("invalid_evidence_object_missing_excerpt.json")
    valid = _fixture("valid_evidence_object.json")
    assert document == {key: value for key, value in valid.items() if key != "excerpt"}
    errors = list(_validator().iter_errors(document))
    assert len(errors) == 1
    assert errors[0].validator == "required"
    assert "excerpt" in errors[0].message


@pytest.mark.parametrize(
    ("filename", "conformant"),
    [
        ("valid_evidence_object.json", True),
        ("invalid_evidence_object_missing_excerpt.json", False),
    ],
)
def test_consumer_cli_validates_evidence_fixture(
    filename: str, conformant: bool, tmp_path: Path
) -> None:
    report_path = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_run_contract.py"),
            str(FIXTURES / filename),
            "--schema-dir",
            str(SCHEMAS),
            "--registry",
            str(ROOT / "config" / "backplane_participants.json"),
            "--repo",
            "stranske/Manager-Mosaic",
            "--report-json",
            str(report_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == (0 if conformant else 1), result.stdout + result.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["role"] == "consumer"
    assert report["skipped"] is False
    assert report["conformant"] is conformant
    if not conformant:
        assert any("excerpt" in item["message"] for item in report["violations"])
