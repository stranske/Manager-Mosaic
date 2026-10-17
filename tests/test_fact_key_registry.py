"""Tests for the shared fact_key registry and loader."""

import json
import re
from importlib import resources
from pathlib import Path

import pytest

from manager_mosaic import fact_keys
from manager_mosaic.discrepancy import FactRecord
from manager_mosaic.fact_keys import (
    UnregisteredFactKeyError,
    load_fact_key_registry,
    validate_fact_keys,
)
from manager_mosaic.thesis import ThesisClaim, evaluate_claim

_FIXTURE_FACT_KEY_PATTERN = re.compile(r'fact_key\s*=\s*"([^"]+)"')


def _fixture_fact_keys_from_tests() -> frozenset[str]:
    tests_dir = Path(__file__).resolve().parent
    keys: set[str] = set()
    for path in tests_dir.glob("test_*.py"):
        if path.name == "test_fact_key_registry.py":
            continue
        text = path.read_text(encoding="utf-8")
        keys.update(_FIXTURE_FACT_KEY_PATTERN.findall(text))
    return frozenset(keys)


def test_fact_key_registry_contains_core_performance_and_liquidity_keys() -> None:
    registry = load_fact_key_registry()
    assert "fund.net_irr" in registry
    assert "legal.withdrawal_notice_days" in registry
    assert "performance.irr" in registry
    assert "liquidity.redemption_frequency" in registry


def test_fact_key_registry_covers_synthetic_fixture_keys() -> None:
    registry = load_fact_key_registry()
    fixture_keys = _fixture_fact_keys_from_tests()
    assert fixture_keys, "expected synthetic test fixtures to reference fact_key strings"
    missing = sorted(fixture_keys - registry)
    assert not missing, f"fixture fact_keys missing from registry: {missing}"


def test_fact_key_registry_is_readable_through_package_resources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The registry must resolve from the installed package, not only a source path."""
    registry_file = resources.files("manager_mosaic").joinpath("fact_key_registry.json")
    assert registry_file.is_file()
    packaged_keys = frozenset(
        str(key) for key in json.loads(registry_file.read_text(encoding="utf-8"))["keys"]
    )
    # Hide the source-checkout copy so the packaged-resource branch is the one taken.
    monkeypatch.setattr(fact_keys, "_REPO_REGISTRY_PATH", tmp_path / "absent" / "registry.json")
    assert not fact_keys._REPO_REGISTRY_PATH.is_file()
    assert load_fact_key_registry() == packaged_keys


def _claim(claim_id: str, fact_key: str) -> ThesisClaim:
    return ThesisClaim(
        claim_id=claim_id,
        claim_text="test claim",
        entity_ref="fund-alpha",
        fact_key=fact_key,
        expected_pattern="min",
        threshold=10.0,
    )


def _fact(evidence_id: str, fact_key: str) -> FactRecord:
    return FactRecord(
        fact_key=fact_key,
        entity_ref="fund-alpha",
        period="2024Q4",
        value=12.0,
        evidence_id=evidence_id,
    )


def test_opted_in_validation_reports_unregistered_key_instead_of_insufficient_evidence() -> None:
    """A typo'd claim key is an unregistered-key violation when validation is opted in."""
    claim = _claim("irr-floor", "performance.irrr")
    facts = [_fact("ev-irr-ok", "performance.irr")]

    # Legacy caller: no validation requested, previous behaviour is retained.
    legacy = evaluate_claim(claim, facts)
    assert legacy.verdict == "insufficient_evidence"
    assert legacy.evidence_ids == ()

    # Explicit validation call (documented primary-journey pre-step).
    violations = validate_fact_keys(facts, claims=[claim])
    assert [(v.record_id, v.fact_key) for v in violations] == [("irr-floor", "performance.irrr")]
    assert "unregistered" in violations[0].message
    assert "performance.irrr" in violations[0].message

    # Opted-in strict mode on evaluate_claim surfaces the same violation.
    with pytest.raises(UnregisteredFactKeyError) as excinfo:
        evaluate_claim(claim, facts, strict_fact_keys=True)
    assert [(v.record_id, v.fact_key) for v in excinfo.value.violations] == [
        ("irr-floor", "performance.irrr")
    ]
    assert "performance.irrr" in str(excinfo.value)


def test_legacy_caller_with_matching_unregistered_key_retains_previous_behaviour() -> None:
    """Callers omitting validation keep the old verdict even for unregistered keys."""
    claim = _claim("irr-floor", "performance.irrr")
    facts = [_fact("ev-typo", "performance.irrr")]

    assert evaluate_claim(claim, facts).verdict == "supported"

    violations = validate_fact_keys(facts, claims=[claim])
    assert {(v.record_id, v.fact_key) for v in violations} == {
        ("irr-floor", "performance.irrr"),
        ("ev-typo", "performance.irrr"),
    }

    with pytest.raises(UnregisteredFactKeyError):
        evaluate_claim(claim, facts, strict_fact_keys=True)


def test_validate_fact_keys_returns_all_violations_in_one_pass() -> None:
    claims = [_claim("claim-a", "performance.irrr"), _claim("claim-b", "fees.unknown")]
    facts = [
        _fact("ev-1", "performance.irr"),
        _fact("ev-2", "liquidity.unknown"),
        _fact("ev-3", "performance.irrr"),
    ]

    violations = validate_fact_keys(facts, claims=claims)

    assert {(v.record_id, v.fact_key) for v in violations} == {
        ("claim-a", "performance.irrr"),
        ("claim-b", "fees.unknown"),
        ("ev-2", "liquidity.unknown"),
        ("ev-3", "performance.irrr"),
    }
    assert all("unregistered" in v.message for v in violations)


def test_validate_fact_keys_accepts_registered_keys_and_strict_mode_evaluates() -> None:
    claim = _claim("irr-floor", "performance.irr")
    facts = [_fact("ev-irr-ok", "performance.irr")]

    assert validate_fact_keys(facts, claims=[claim]) == []
    check = evaluate_claim(claim, facts, strict_fact_keys=True)
    assert check.verdict == "supported"
    assert check.evidence_ids == ("ev-irr-ok",)


def test_source_and_packaged_fact_key_registries_match() -> None:
    """The editable and installed-package registries must not drift."""
    repo_root = Path(__file__).resolve().parents[1]
    source_payload = json.loads(
        (repo_root / "config" / "fact_key_registry.json").read_text(encoding="utf-8")
    )
    packaged_payload = json.loads(
        (repo_root / "src" / "manager_mosaic" / "fact_key_registry.json").read_text(
            encoding="utf-8"
        )
    )

    assert source_payload == packaged_payload
