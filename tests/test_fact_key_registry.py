"""Tests for the shared fact_key registry and loader."""

import re
from pathlib import Path

from manager_mosaic.fact_keys import load_fact_key_registry

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
