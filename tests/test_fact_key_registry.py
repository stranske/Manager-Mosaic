"""Tests for the shared fact_key registry and loader."""

import json
import re
from importlib import resources
from pathlib import Path

import pytest

from manager_mosaic import fact_keys
from manager_mosaic.discrepancy import FactRecord, detect_numeric_discrepancies
from manager_mosaic.fact_keys import (
    UnregisteredFactKeyError,
    ensure_registered_fact_keys,
    load_fact_key_registry,
    validate_claim_and_facts,
    validate_fact_keys,
    validate_facts_and_claims,
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


@pytest.mark.parametrize("alias", [False, True], ids=["strict", "alias"])
def test_public_validators_consult_default_fact_key_registry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, alias: bool
) -> None:
    """The real registry controls validation, including keys added or removed locally."""
    registry_file = tmp_path / "registry.json"
    registry_file.write_text(json.dumps({"keys": ["audit.registered_metric"]}), encoding="utf-8")
    monkeypatch.setattr(fact_keys, "_REPO_REGISTRY_PATH", registry_file)
    claim = _claim("claim-custom", "audit.registered_metric")
    registered = _fact("ev-custom", "audit.registered_metric")
    removed = _fact("ev-removed", "performance.irr")

    assert validate_fact_keys([registered], claims=[claim]) == []
    assert [
        (v.record_id, v.fact_key, v.record_kind)
        for v in validate_fact_keys([registered, removed], claims=[claim])
    ] == [("ev-removed", "performance.irr", "fact")]

    assert (
        evaluate_claim(
            claim, [registered], strict_fact_keys=not alias, validate_fact_keys_opt_in=alias
        ).verdict
        == "supported"
    )
    assert (
        detect_numeric_discrepancies(
            [registered], strict_fact_keys=not alias, validate_fact_keys_opt_in=alias
        )
        == []
    )
    with pytest.raises(UnregisteredFactKeyError) as excinfo:
        evaluate_claim(
            claim,
            [registered, removed],
            strict_fact_keys=not alias,
            validate_fact_keys_opt_in=alias,
        )
    assert [(v.record_id, v.fact_key, v.record_kind) for v in excinfo.value.violations] == [
        ("ev-removed", "performance.irr", "fact")
    ]
    with pytest.raises(UnregisteredFactKeyError) as excinfo:
        detect_numeric_discrepancies(
            [registered, removed], strict_fact_keys=not alias, validate_fact_keys_opt_in=alias
        )
    assert [(v.record_id, v.fact_key, v.record_kind) for v in excinfo.value.violations] == [
        ("ev-removed", "performance.irr", "fact")
    ]
    # Unflagged callers still evaluate the matching custom fact without validation.
    assert evaluate_claim(claim, [registered, removed]).verdict == "supported"
    assert detect_numeric_discrepancies([registered, removed]) == []


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


def test_opted_in_validation_reports_claim_and_facts_rather_than_insufficient_evidence() -> None:
    """Both a claim and its facts using unregistered keys: violation, not insufficient_evidence.

    The claim and facts carry *different* unregistered keys, so a legacy
    caller finds no matching fact and returns ``insufficient_evidence`` —
    indistinguishable from a genuinely absent fact. Opted-in validation
    must instead report every unregistered key with record identity.
    """
    claim = _claim("irr-floor", "performance.irrr")
    facts = [_fact("ev-liquidity-typo", "liquidity.unknownn")]

    # Legacy caller omitting validation retains the previous behaviour.
    legacy = evaluate_claim(claim, facts)
    assert legacy.verdict == "insufficient_evidence"
    assert legacy.evidence_ids == ()

    # Explicit pre-step (documented primary-journey step 3) reports both.
    violations = validate_fact_keys(facts, claims=[claim])
    assert [(v.record_id, v.fact_key, v.record_kind, v.kind) for v in violations] == [
        ("irr-floor", "performance.irrr", "claim", "unregistered_fact_key"),
        ("ev-liquidity-typo", "liquidity.unknownn", "fact", "unregistered_fact_key"),
    ]
    assert all("unregistered" in v.message for v in violations)

    # Opted-in strict mode raises the same violations instead of evaluating.
    with pytest.raises(UnregisteredFactKeyError) as excinfo:
        evaluate_claim(claim, facts, strict_fact_keys=True)
    assert [(v.record_id, v.fact_key) for v in excinfo.value.violations] == [
        ("irr-floor", "performance.irrr"),
        ("ev-liquidity-typo", "liquidity.unknownn"),
    ]
    assert "performance.irrr" in str(excinfo.value)
    assert "liquidity.unknownn" in str(excinfo.value)


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


def test_public_validation_helper_aliases_delegate_with_claim_and_fact_identity() -> None:
    claim = _claim("claim-typo", "performance.irrr")
    facts = [_fact("fact-typo", "liquidity.unknown")]

    expected = [("claim-typo", "performance.irrr"), ("fact-typo", "liquidity.unknown")]
    assert [
        (violation.record_id, violation.fact_key)
        for violation in validate_claim_and_facts(claim, facts)
    ] == expected
    assert [
        (violation.record_id, violation.fact_key)
        for violation in validate_facts_and_claims(facts, [claim])
    ] == expected


def test_package_top_level_exports_fact_claim_validator_helpers() -> None:
    """The validator is reachable from `manager_mosaic`, not only its submodule."""
    import manager_mosaic

    for name in (
        "ensure_registered_fact_keys",
        "validate_claim_and_facts",
        "validate_fact_keys",
        "validate_facts_and_claims",
    ):
        assert name in manager_mosaic.__all__
        assert getattr(manager_mosaic, name) is getattr(fact_keys, name)

    claim = _claim("claim-typo", "performance.irrr")
    facts = [_fact("fact-typo", "liquidity.unknown")]
    assert [
        (v.record_id, v.fact_key) for v in manager_mosaic.validate_claim_and_facts(claim, facts)
    ] == [("claim-typo", "performance.irrr"), ("fact-typo", "liquidity.unknown")]
    with pytest.raises(UnregisteredFactKeyError):
        manager_mosaic.ensure_registered_fact_keys(facts, [claim])


def test_ensure_registered_fact_keys_returns_none_for_valid_and_exposes_all_violations() -> None:
    registered_claim = _claim("irr-floor", "performance.irr")
    registered_facts = [_fact("ev-irr-ok", "performance.irr")]
    assert ensure_registered_fact_keys(registered_facts, [registered_claim]) is None

    bad_claim = _claim("claim-typo", "performance.irrr")
    bad_facts = [_fact("fact-typo", "liquidity.unknown")]
    with pytest.raises(UnregisteredFactKeyError) as excinfo:
        ensure_registered_fact_keys(bad_facts, [bad_claim])
    assert [
        (violation.record_id, violation.fact_key) for violation in excinfo.value.violations
    ] == [
        ("claim-typo", "performance.irrr"),
        ("fact-typo", "liquidity.unknown"),
    ]


def test_discrepancy_opted_in_validation_reports_unregistered_key() -> None:
    """Typo'd keys are unrelated groups for legacy callers, violations when opted in."""
    facts = [
        _fact("ev-irr-ok", "performance.irr"),
        FactRecord(
            fact_key="performance.irrr",
            entity_ref="fund-alpha",
            period="2024Q4",
            value=20.0,
            evidence_id="ev-irr-typo",
        ),
    ]

    # Legacy caller: the typo'd key forms its own singleton group, no discrepancy.
    assert detect_numeric_discrepancies(facts) == []

    violations = validate_fact_keys(facts)
    assert [(v.record_id, v.fact_key) for v in violations] == [("ev-irr-typo", "performance.irrr")]

    with pytest.raises(UnregisteredFactKeyError) as excinfo:
        detect_numeric_discrepancies(facts, strict_fact_keys=True)
    assert [(v.record_id, v.fact_key) for v in excinfo.value.violations] == [
        ("ev-irr-typo", "performance.irrr")
    ]


def test_discrepancy_strict_mode_reports_all_violations_and_still_detects_valid() -> None:
    bad = [
        _fact("ev-bad-1", "performance.irrr"),
        _fact("ev-bad-2", "liquidity.unknown"),
    ]
    with pytest.raises(UnregisteredFactKeyError) as excinfo:
        detect_numeric_discrepancies(bad, strict_fact_keys=True)
    assert {(v.record_id, v.fact_key) for v in excinfo.value.violations} == {
        ("ev-bad-1", "performance.irrr"),
        ("ev-bad-2", "liquidity.unknown"),
    }

    valid = [
        _fact("ev-1", "performance.irr"),
        FactRecord(
            fact_key="performance.irr",
            entity_ref="fund-alpha",
            period="2024Q4",
            value=20.0,
            evidence_id="ev-2",
        ),
    ]
    discrepancies = detect_numeric_discrepancies(valid, strict_fact_keys=True)
    assert [d.evidence_ids for d in discrepancies] == [("ev-1", "ev-2")]


def test_primary_journey_pre_step_then_strict_steps_report_typo_end_to_end() -> None:
    """Journey steps 3-5: pre-step validation, then strict discrepancy/evaluate."""
    claim = _claim("irr-floor", "performance.irrr")
    facts = [_fact("ev-irr-ok", "performance.irr"), _fact("ev-irr-typo", "performance.irrr")]

    # Step 3 documented pre-step reports the typo with record identity.
    violations = validate_fact_keys(facts, claims=[claim])
    assert {(v.record_id, v.fact_key) for v in violations} == {
        ("irr-floor", "performance.irrr"),
        ("ev-irr-typo", "performance.irrr"),
    }
    # Steps 4-5 strict modes surface the same violation instead of grouping/evaluating.
    with pytest.raises(UnregisteredFactKeyError):
        detect_numeric_discrepancies(facts, strict_fact_keys=True)
    with pytest.raises(UnregisteredFactKeyError):
        evaluate_claim(claim, facts, strict_fact_keys=True)
    # The discrepancy step accepts the same opt-in alias spelling as evaluate_claim.
    with pytest.raises(UnregisteredFactKeyError):
        detect_numeric_discrepancies(facts, validate_fact_keys_opt_in=True)
    # Legacy callers omitting every opt-in retain previous behaviour.
    assert detect_numeric_discrepancies(facts) == []
    assert evaluate_claim(claim, facts).verdict == "supported"


def test_discrepancy_strict_mode_preserves_threshold_error_precedence() -> None:
    """An invalid threshold stays a ValueError even when strict validation is on."""
    with pytest.raises(ValueError, match="threshold_percent"):
        detect_numeric_discrepancies(
            [_fact("ev-bad", "performance.irrr")],
            threshold_percent=-1.0,
            strict_fact_keys=True,
        )


def test_evaluate_claim_opt_in_alias_reports_fact_only_unregistered_key() -> None:
    """Step 5 alias: a fact-only typo raises instead of insufficient_evidence."""
    claim = _claim("irr-floor", "performance.irr")
    facts = [_fact("ev-irr-typo", "performance.irrr")]

    # Legacy caller: no flag, the typo'd fact simply does not match.
    assert evaluate_claim(claim, facts).verdict == "insufficient_evidence"

    # Both opt-in spellings on evaluate_claim report the fact's identity.
    with pytest.raises(UnregisteredFactKeyError) as excinfo:
        evaluate_claim(claim, facts, strict_fact_keys=True)
    assert [(v.record_id, v.fact_key, v.record_kind) for v in excinfo.value.violations] == [
        ("ev-irr-typo", "performance.irrr", "fact")
    ]
    with pytest.raises(UnregisteredFactKeyError) as excinfo:
        evaluate_claim(claim, facts, validate_fact_keys_opt_in=True)
    assert [(v.record_id, v.fact_key, v.record_kind) for v in excinfo.value.violations] == [
        ("ev-irr-typo", "performance.irrr", "fact")
    ]


def test_evaluate_claim_opt_in_alias_evaluates_registered_keys() -> None:
    claim = _claim("irr-floor", "performance.irr")
    facts = [_fact("ev-irr-ok", "performance.irr")]

    check = evaluate_claim(claim, facts, validate_fact_keys_opt_in=True)
    assert check.verdict == "supported"
    assert check.evidence_ids == ("ev-irr-ok",)


def test_validate_fact_keys_reports_identity_for_generic_records() -> None:
    """Records without claim/evidence ids still report a stable identity."""

    class _Record:
        def __init__(self, fact_key: str, **ids: str) -> None:
            self.fact_key = fact_key
            for name, value in ids.items():
                setattr(self, name, value)

    by_record_id = validate_fact_keys([_Record("fees.unknown", record_id="rec-1")])
    assert [(v.record_id, v.fact_key, v.record_kind, v.kind) for v in by_record_id] == [
        ("rec-1", "fees.unknown", "record", "unregistered_fact_key")
    ]

    by_id = validate_fact_keys([_Record("fees.unknown", id="rec-2")])
    assert [(v.record_id, v.record_kind) for v in by_id] == [("rec-2", "record")]

    anonymous = _Record("fees.unknown")
    by_repr = validate_fact_keys([anonymous])
    assert [(v.record_id, v.fact_key) for v in by_repr] == [(repr(anonymous), "fees.unknown")]


def test_validate_fact_keys_accepts_single_records_bare_keys_and_custom_registries(
    tmp_path: Path,
) -> None:
    claim = _claim("irr-floor", "performance.irrr")
    fact = _fact("ev-typo", "performance.irrr")

    # Single records (not sequences) and bare key strings are validated in one pass.
    assert [(v.record_id, v.fact_key) for v in validate_fact_keys(fact, claims=claim)] == [
        ("irr-floor", "performance.irrr"),
        ("ev-typo", "performance.irrr"),
    ]
    assert [
        (v.record_id, v.fact_key, v.record_kind) for v in validate_fact_keys("fees.unknown")
    ] == [("fees.unknown", "fees.unknown", "fact_key")]
    assert validate_fact_keys() == []

    # An explicit in-memory or on-disk registry replaces the default vocabulary.
    assert validate_fact_keys(facts=[fact], registry={"performance.irrr"}) == []
    registry_file = tmp_path / "registry.json"
    registry_file.write_text(json.dumps({"keys": ["performance.irrr"]}), encoding="utf-8")
    assert validate_fact_keys(facts=[fact], registry=registry_file) == []
    assert validate_fact_keys(facts=[fact], registry_path=str(registry_file)) == []
    assert [(v.record_id, v.fact_key) for v in validate_fact_keys(facts=[fact], registry=[])] == [
        ("ev-typo", "performance.irrr")
    ]


def test_validate_fact_keys_rejects_records_without_fact_key_and_bad_registries(
    tmp_path: Path,
) -> None:
    with pytest.raises(TypeError, match="no fact_key"):
        validate_fact_keys([object()])

    empty_registry = tmp_path / "empty.json"
    empty_registry.write_text(json.dumps({"keys": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty 'keys' list"):
        load_fact_key_registry(empty_registry)

    missing_keys = tmp_path / "missing.json"
    missing_keys.write_text(json.dumps({"other": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty 'keys' list"):
        validate_fact_keys([_fact("ev-1", "performance.irr")], registry=missing_keys)


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
