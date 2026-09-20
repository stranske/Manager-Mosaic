"""Model validation and silence-invariant gates for Manager-Mosaic."""

from __future__ import annotations

import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

from manager_mosaic.model import (
    Store,
    derive_gaps,
    entry,
    load_schema,
    mention,
    pub,
    validate,
)

FIXTURES = Path(__file__).parent / "fixtures" / "model"


def _load(name: str) -> Store:
    return Store.from_json(FIXTURES / name)


def _validate_schema(name: str) -> None:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    Draft202012Validator(load_schema()).validate(payload)


def test_fixture_validates_against_json_schema() -> None:
    _validate_schema("minimal_store.json")


def test_mistyped_entry_period_reference_is_reported() -> None:
    broken = Store.from_dict(
        {
            **json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8")),
            "entries": [
                {
                    **json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))[
                        "entries"
                    ][0],
                    "first": "2025Q1_typo",
                }
            ],
        }
    )
    violations = validate(broken)
    assert any(v.record_id == "alpha-fund" and "2025Q1_typo" in v.message for v in violations)


def test_inverted_entry_period_range_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["first"] = "2025Q2"
    payload["entries"][0]["last"] = "2025Q1"
    broken = Store.from_dict(payload)

    violations = validate(broken)

    assert [(violation.record_id, violation.message) for violation in violations] == [
        ("alpha-fund", "first period '2025Q2' is after last period '2025Q1'")
    ]
    assert derive_gaps(broken) == ()


def test_truncated_currency_suffix_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["mentions"][0]["size"] = "$B"
    broken = Store.from_dict(payload)
    violations = validate(broken)
    assert any("truncated currency" in v.message for v in violations)


def test_mention_without_src_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["mentions"][0]["src"] = ""
    broken = Store.from_dict(payload)
    violations = validate(broken)
    assert any("mention must carry src" in v.message for v in violations)


def test_mention_with_omitted_src_is_reported() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    del payload["entries"][0]["mentions"][0]["src"]
    broken = Store.from_dict(payload)
    violations = validate(broken)
    assert any(
        "mention[0]" in v.record_id and "mention must carry src" in v.message for v in violations
    )


def test_derive_gaps_leaves_status_unchanged() -> None:
    store = _load("minimal_store.json")
    before_status = store.entries[0].status
    gaps = derive_gaps(store)
    assert store.entries[0].status == before_status
    assert any("2025Q2" in item.title for item in gaps)


def test_validator_returns_all_four_defects() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["entries"][0]["first"] = "missing-period"
    payload["entries"][0]["mentions"][0]["src"] = ""
    payload["entries"][0]["mentions"][0]["size"] = "$B"
    payload["entries"][0]["mentions"][0]["bps"] = math.inf
    broken = Store.from_dict(payload)
    violations = validate(broken)
    messages = {(item.record_id, item.message) for item in violations}
    assert any(
        record_id == "alpha-fund" and "missing-period" in message for record_id, message in messages
    )
    assert any(
        "mention[0]" in record_id and "mention must carry src" in message
        for record_id, message in messages
    )
    assert any("truncated currency" in message for _, message in messages)
    assert any("bps must be finite" in message for _, message in messages)


def test_none_period_sort_does_not_abort_validation() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["periods"][0]["sort"] = None
    payload["entries"][0]["first"] = "missing-period"
    broken = Store.from_dict(payload)
    violations = validate(broken)
    messages = {(v.record_id, v.message) for v in violations}
    assert any("sort must be a finite number" in message for _, message in messages)
    assert any(
        record_id == "alpha-fund" and "missing-period" in message for record_id, message in messages
    )


def test_nonnumeric_period_sorts_are_violations_without_aborting() -> None:
    for bad_sort in ("2025Q1", True, {}, []):
        payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
        payload["periods"][0]["sort"] = bad_sort
        broken = Store.from_dict(payload)

        violations = validate(broken)

        assert any(
            v.record_id == "2025Q1" and "sort must be a finite number" in v.message
            for v in violations
        )
        assert derive_gaps(broken) == ()


def test_nonfinite_period_sorts_are_violations_without_aborting() -> None:
    for bad_sort in (math.nan, math.inf, -math.inf):
        payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
        payload["periods"][0]["sort"] = bad_sort
        broken = Store.from_dict(payload)

        violations = validate(broken)

        assert any(
            v.record_id == "2025Q1" and "sort must be finite" in v.message for v in violations
        )
        assert derive_gaps(broken) == ()


def test_oversized_integer_sort_does_not_abort_validation() -> None:
    payload = json.loads((FIXTURES / "minimal_store.json").read_text(encoding="utf-8"))
    payload["periods"][0]["sort"] = 10**400
    payload["entries"][0]["first"] = "missing-period"
    broken = Store.from_dict(payload)
    violations = validate(broken)
    assert any(
        record_id == "alpha-fund" and "missing-period" in message
        for record_id, message in ((v.record_id, v.message) for v in violations)
    )


def _forbidden_infer_exit_on_gap(store: Store) -> str:
    """Anti-pattern: treating absence as proof of exit (must never ship)."""

    if derive_gaps(store):
        return "EXITED"
    return store.entries[0].status


def test_silence_invariant_deliberate_break_then_revert() -> None:
    """Deliberate-break gate documented in the PR body."""

    store = _load("minimal_store.json")
    assert store.entries[0].status == "ACTIVE"
    assert _forbidden_infer_exit_on_gap(store) == "EXITED"
    gaps = derive_gaps(store)
    assert store.entries[0].status == "ACTIVE"
    assert gaps


def test_builders_create_expected_entry() -> None:
    item = entry(
        id="demo",
        name="Demo",
        ticker="DMO",
        counterparty="Manager",
        kind="position",
        first="2025Q1",
        last="2025Q2",
        status="ACTIVE",
        peak=None,
        flag="",
        thesis="",
        pub=pub("PENDING", "2025-01-01", "", "Q1-2025-Letter"),
        mentions=[
            mention("2025Q1", "note", 10.0, "$1M", "Q1-2025-Letter", False),
        ],
    )
    assert item.mentions[0].inferred is False
