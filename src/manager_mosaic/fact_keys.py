"""Load the shared fact_key vocabulary registry and validate keys against it.

Validation is explicit and opt-in: callers that never call
:func:`validate_fact_keys` (and never pass ``strict_fact_keys=True`` to
``evaluate_claim``) retain their previous behaviour.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, cast

_REPO_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "config" / "fact_key_registry.json"
_PACKAGED_REGISTRY_NAME = "fact_key_registry.json"


def _load_registry_payload(registry_path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(registry_path.read_text(encoding="utf-8")))


def _default_registry_payload() -> dict[str, object]:
    if _REPO_REGISTRY_PATH.is_file():
        return _load_registry_payload(_REPO_REGISTRY_PATH)
    packaged = resources.files("manager_mosaic").joinpath(_PACKAGED_REGISTRY_NAME)
    return cast(dict[str, object], json.loads(packaged.read_text(encoding="utf-8")))


def load_fact_key_registry(path: Path | None = None) -> frozenset[str]:
    """Return the registered fact_key strings from the JSON registry."""
    registry_path = path or _REPO_REGISTRY_PATH
    payload = _load_registry_payload(path) if path is not None else _default_registry_payload()
    keys = payload.get("keys")
    if not isinstance(keys, list) or not keys:
        raise ValueError(f"{registry_path} must contain a non-empty 'keys' list")
    return frozenset(str(key) for key in keys)


@dataclass(frozen=True)
class FactKeyViolation:
    """One unregistered fact_key, identified by the record that carried it."""

    record_id: str
    fact_key: str
    message: str
    record_kind: str = "fact"

    @property
    def kind(self) -> str:
        return "unregistered_fact_key"


# Backwards-/forward-compatible alias matching the model validator's naming.
ValidationViolation = FactKeyViolation


class UnregisteredFactKeyError(ValueError):
    """Raised by opted-in strict validation when any fact_key is unregistered."""

    def __init__(self, violations: Sequence[FactKeyViolation]) -> None:
        self.violations: tuple[FactKeyViolation, ...] = tuple(violations)
        detail = "; ".join(v.message for v in self.violations)
        super().__init__(f"unregistered fact_key violation(s): {detail}")


def _resolve_registry(
    registry: frozenset[str] | set[str] | Sequence[str] | Path | str | None,
) -> frozenset[str]:
    if registry is None:
        return load_fact_key_registry()
    if isinstance(registry, (Path, str)):
        return load_fact_key_registry(Path(registry))
    return frozenset(str(key) for key in registry)


def _as_records(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "fact_key"):
        return [value]
    if isinstance(value, (str, bytes)):
        return [value]
    return list(value)


def _record_identity(record: Any) -> tuple[str, str]:
    if hasattr(record, "claim_id"):
        return str(record.claim_id), "claim"
    if hasattr(record, "evidence_id"):
        return str(record.evidence_id), "fact"
    if hasattr(record, "record_id"):
        return str(record.record_id), "record"
    if hasattr(record, "id"):
        return str(record.id), "record"
    return repr(record), "record"


def _check_record(record: Any, registered: frozenset[str]) -> FactKeyViolation | None:
    fact_key = record if isinstance(record, str) else getattr(record, "fact_key", None)
    if fact_key is None:
        raise TypeError(f"record {record!r} has no fact_key attribute")
    key = str(fact_key)
    if key in registered:
        return None
    record_id, record_kind = (
        (key, "fact_key") if isinstance(record, str) else _record_identity(record)
    )
    return FactKeyViolation(
        record_id=record_id,
        fact_key=key,
        message=(
            f"unregistered fact_key {key!r} for {record_kind} {record_id!r}: "
            "not in fact_key registry"
        ),
        record_kind=record_kind,
    )


def validate_fact_keys(
    facts: Any = (),
    claims: Any = (),
    *,
    registry: frozenset[str] | set[str] | Sequence[str] | Path | str | None = None,
    registry_path: Path | str | None = None,
) -> list[FactKeyViolation]:
    """Return every unregistered fact_key across ``facts`` and ``claims`` in one pass.

    This is the explicit, opted-in validation call for the primary journey.
    Each violation carries record identity: a claim's ``claim_id`` or a
    fact's ``evidence_id``. Registered keys produce no violations, so a
    valid input returns ``[]``. Callers that omit this call (and omit
    ``strict_fact_keys=True`` on ``evaluate_claim``) are unaffected.
    """
    registered = _resolve_registry(registry_path if registry is None else registry)
    violations: list[FactKeyViolation] = []
    for record in [*_as_records(claims), *_as_records(facts)]:
        violation = _check_record(record, registered)
        if violation is not None:
            violations.append(violation)
    return violations


def validate_claim_and_facts(
    claim: Any,
    facts: Any = (),
    *,
    registry: frozenset[str] | set[str] | Sequence[str] | Path | str | None = None,
) -> list[FactKeyViolation]:
    """Return unregistered-key violations for one claim and its facts."""
    return validate_fact_keys(facts, claims=[claim] if claim is not None else [], registry=registry)


def validate_facts_and_claims(
    facts: Any = (),
    claims: Any = (),
    *,
    registry: frozenset[str] | set[str] | Sequence[str] | Path | str | None = None,
) -> list[FactKeyViolation]:
    """Alias for :func:`validate_fact_keys`."""
    return validate_fact_keys(facts, claims=claims, registry=registry)


def ensure_registered_fact_keys(
    facts: Any = (),
    claims: Any = (),
    *,
    registry: frozenset[str] | set[str] | Sequence[str] | Path | str | None = None,
) -> None:
    """Raise :class:`UnregisteredFactKeyError` if any fact_key is unregistered."""
    violations = validate_fact_keys(facts, claims=claims, registry=registry)
    if violations:
        raise UnregisteredFactKeyError(violations)


__all__ = [
    "FactKeyViolation",
    "UnregisteredFactKeyError",
    "ValidationViolation",
    "ensure_registered_fact_keys",
    "load_fact_key_registry",
    "validate_claim_and_facts",
    "validate_fact_keys",
    "validate_facts_and_claims",
]
