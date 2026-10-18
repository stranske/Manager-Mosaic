"""Raw validation preserves independent checks and the typed semantic API."""

from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from manager_mosaic import Store, validate, validate_payload

FIXTURE = Path(__file__).parent / "fixtures" / "model" / "minimal_store.json"


@pytest.fixture
def payload() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return loaded


@pytest.mark.parametrize(
    ("parts", "value", "message"),
    [
        (("entries", 0, "first"), "unknown", "referenced but not defined"),
        (("entries", 0, "last"), "2025Q1", "after last period"),
        (("entries", 0, "peak"), math.inf, "peak must be finite"),
        (("entries", 0, "flag"), "$B", "truncated currency"),
        (("entries", 0, "status"), "INVALID", "is not allowed"),
        (("entries", 0, "pub", "src"), "unknown", "referenced but not defined"),
        (("entries", 0, "mentions", 0, "src"), "unknown", "referenced but not defined"),
        (("entries", 0, "mentions", 0, "period"), "unknown", "referenced but not defined"),
        (("entries", 0, "mentions", 0, "bps"), math.inf, "bps must be finite"),
        (("entries", 0, "mentions", 0, "size"), "$B", "truncated currency"),
        (("themes", 0, "periods", 0), "unknown", "referenced but not defined"),
    ],
)
def test_raw_and_typed_apis_report_independent_semantics(
    payload: dict[str, Any], parts: tuple[str | int, ...], value: Any, message: str
) -> None:
    payload["themes"] = [{"id": "theme", "name": "Theme", "desc": "", "periods": ["2025Q1"]}]
    payload["entries"][0]["first"] = "2025Q2"
    target: Any = payload
    path = "$"
    for part in parts[:-1]:
        target = target[part]
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    target[parts[-1]] = value
    path += f"[{parts[-1]}]" if isinstance(parts[-1], int) else f".{parts[-1]}"
    if message == "after last period":
        path = "$.entries[0]"

    raw_violations = validate_payload(payload)
    typed_violations = validate(Store.from_dict(payload))

    assert len(raw_violations) == len(typed_violations) == 1
    assert raw_violations[0].record_id == path
    assert message in raw_violations[0].message
    assert message in typed_violations[0].message


@pytest.mark.parametrize("collection", ["periods", "themes", "documents", "entries"])
def test_duplicate_identifiers_have_source_paths(payload: dict[str, Any], collection: str) -> None:
    payload["themes"] = [{"id": "theme", "name": "Theme", "desc": "", "periods": []}]
    duplicate = deepcopy(payload[collection][0])
    payload[collection].append(duplicate)
    field = "name" if collection == "documents" else "id"
    index = len(payload[collection]) - 1

    raw_violations = validate_payload(payload)
    typed_violations = validate(Store.from_dict(payload))

    assert len(raw_violations) == len(typed_violations) == 1
    assert raw_violations[0].record_id == f"$.{collection}[{index}].{field}"
    assert "defined twice" in raw_violations[0].message
    assert "defined twice" in typed_violations[0].message


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("pub", None),
        ("mentions", None),
        ("mentions", [None]),
        ("mentions", [{"period": [], "src": {}, "size": 36}]),
        ("kind", []),
        ("first", {}),
    ],
)
def test_malformed_prerequisites_preserve_other_semantic_checks(
    payload: dict[str, Any], field: str, value: Any
) -> None:
    payload["entries"][0][field] = value
    payload["entries"][0]["last"] = "unknown"
    payload["entries"][0]["flag"] = "$B"
    original = deepcopy(payload)

    violations = validate_payload(payload)

    assert any(v.record_id.startswith(f"$.entries[0].{field}") for v in violations)
    assert any(
        v.record_id == "$.entries[0].last" and "referenced but not defined" in v.message
        for v in violations
    )
    assert any(
        v.record_id == "$.entries[0].flag" and "truncated currency" in v.message for v in violations
    )
    with pytest.raises(ValueError) as error:
        Store.from_dict(payload)
    assert all(v.record_id in str(error.value) for v in violations)
    assert payload == original


def test_missing_fields_are_each_reported_once(payload: dict[str, Any]) -> None:
    del payload["entries"][0]["id"]
    del payload["entries"][0]["name"]
    del payload["entries"][0]["mentions"][0]["src"]
    del payload["entries"][0]["mentions"][0]["inferred"]

    violations = validate_payload(payload)

    assert sorted(v.record_id for v in violations) == [
        "$.entries[0].id",
        "$.entries[0].mentions[0].inferred",
        "$.entries[0].mentions[0].src",
        "$.entries[0].name",
    ]


def test_bad_sort_skips_only_range_check(payload: dict[str, Any]) -> None:
    payload["periods"][0]["sort"] = None
    payload["entries"][0]["first"] = "2025Q2"
    payload["entries"][0]["last"] = "2025Q1"
    payload["entries"][0]["status"] = "INVALID"

    violations = validate_payload(payload)

    assert any(v.record_id == "$.periods[0].sort" for v in violations)
    assert any(v.record_id == "$.entries[0].status" for v in violations)
    assert all("after last period" not in v.message for v in violations)


@pytest.mark.parametrize("bad", [None, [], "text", 3])
def test_non_mapping_payload_is_reported(bad: Any) -> None:
    assert validate_payload(bad)
    with pytest.raises(ValueError):
        Store.from_dict(bad)


def test_read_only_mapping_payload_preserves_input_contract(payload: dict[str, Any]) -> None:
    payload["entries"][0]["pub"] = MappingProxyType(payload["entries"][0]["pub"])
    readonly = MappingProxyType(payload)
    assert validate_payload(readonly) == []
    assert validate(Store.from_dict(readonly)) == []


@pytest.mark.parametrize("bad", [None, 3, [None], [{"name": []}]])
def test_unusable_documents_skip_only_dependent_references(
    payload: dict[str, Any], bad: Any
) -> None:
    payload["documents"] = bad
    payload["entries"][0]["first"] = "unknown-period"
    violations = validate_payload(payload)
    assert any(v.record_id.startswith("$.documents") for v in violations)
    assert any(v.record_id == "$.entries[0].first" for v in violations)
    assert not any(
        "document " in v.message and "referenced but not defined" in v.message for v in violations
    )
