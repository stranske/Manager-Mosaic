"""Load the shared fact_key vocabulary registry."""

from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "config" / "fact_key_registry.json"


def load_fact_key_registry(path: Path | None = None) -> frozenset[str]:
    """Return the registered fact_key strings from the JSON registry."""
    registry_path = path or _DEFAULT_REGISTRY_PATH
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    keys = payload.get("keys")
    if not isinstance(keys, list) or not keys:
        raise ValueError(f"{registry_path} must contain a non-empty 'keys' list")
    return frozenset(str(key) for key in keys)
