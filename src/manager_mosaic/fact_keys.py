"""Load the shared fact_key vocabulary registry."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

_REPO_REGISTRY_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "fact_key_registry.json"
)
_PACKAGED_REGISTRY_NAME = "fact_key_registry.json"


def _load_registry_payload(registry_path: Path) -> dict[str, object]:
    return json.loads(registry_path.read_text(encoding="utf-8"))


def _default_registry_payload() -> dict[str, object]:
    if _REPO_REGISTRY_PATH.is_file():
        return _load_registry_payload(_REPO_REGISTRY_PATH)
    packaged = resources.files("manager_mosaic").joinpath(_PACKAGED_REGISTRY_NAME)
    return json.loads(packaged.read_text(encoding="utf-8"))


def load_fact_key_registry(path: Path | None = None) -> frozenset[str]:
    """Return the registered fact_key strings from the JSON registry."""
    registry_path = path or _REPO_REGISTRY_PATH
    payload = _load_registry_payload(path) if path is not None else _default_registry_payload()
    keys = payload.get("keys")
    if not isinstance(keys, list) or not keys:
        raise ValueError(f"{registry_path} must contain a non-empty 'keys' list")
    return frozenset(str(key) for key in keys)
