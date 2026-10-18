"""Core mosaic store model and semantic validator.

The store is meant to be edited by hand. Editing a rendered output instead of the
store is a discarded edit — always change the store and re-validate.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

from jsonschema import Draft202012Validator, validators

PUB_STATES = frozenset({"PENDING", "COMPLETED", "TERMINATED"})
_TRUNCATED_CURRENCY = re.compile(r"^[$€£¥][A-Za-z]+$")
_NUMERIC_FIELDS = frozenset({"sort", "bps", "peak"})
FactBasis = Literal["observed", "inferred", "unknown"]


@dataclass(frozen=True)
class FactRecord:
    """A numeric assertion with a caller-supplied basis, independent of evidence method.

    Omitted basis is unknown, never an implicit observation. The evidence ID
    references separately validated evidence; this model does not classify it.
    """

    fact_key: str
    entity_ref: str
    period: str
    value: float
    evidence_id: str
    basis: FactBasis = "unknown"

    def __post_init__(self) -> None:
        if self.basis not in ("observed", "inferred", "unknown"):
            raise ValueError(f"unsupported fact basis: {self.basis!r}")
        if not math.isfinite(self.value):
            raise ValueError(f"fact value must be finite, got {self.value!r}")


@dataclass(frozen=True, slots=True)
class Fund:
    name: str
    manager: str
    strategy: str
    archetype: str
    note: str


@dataclass(frozen=True, slots=True)
class Period:
    id: str
    sort: int
    label: str
    kind: str
    title: str
    author: str
    attendees: str
    verdict: str
    note: str


@dataclass(frozen=True, slots=True)
class Pub:
    state: str
    as_of: str
    detail: str
    src: str


@dataclass(frozen=True, slots=True)
class Mention:
    period: str
    text: str
    bps: float | None
    size: str
    src: str
    inferred: bool


@dataclass(frozen=True, slots=True)
class Entry:
    id: str
    name: str
    ticker: str
    counterparty: str
    kind: str
    first: str
    last: str
    status: str
    peak: float | None
    flag: str
    thesis: str
    pub: Pub
    mentions: tuple[Mention, ...]


@dataclass(frozen=True, slots=True)
class Theme:
    id: str
    name: str
    desc: str
    periods: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Document:
    name: str
    date: str
    verdict: str
    note: str


@dataclass(frozen=True, slots=True)
class Gap:
    sev: str
    title: str
    desc: str


@dataclass(frozen=True, slots=True)
class Store:
    funds: tuple[Fund, ...]
    periods: tuple[Period, ...]
    entries: tuple[Entry, ...]
    themes: tuple[Theme, ...]
    documents: tuple[Document, ...]
    gaps: tuple[Gap, ...]
    status_vocabularies: Mapping[str, frozenset[str]]

    def __post_init__(self) -> None:
        immutable_vocabularies = MappingProxyType(
            {kind: frozenset(values) for kind, values in self.status_vocabularies.items()}
        )
        object.__setattr__(self, "status_vocabularies", immutable_vocabularies)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Store:
        if _payload_structure_violations(payload):
            violations = validate_payload(payload)
            raise ValueError(
                "Invalid store payload: "
                + "; ".join(f"{v.record_id}: {v.message}" for v in violations)
            )
        status_vocabularies = {
            kind: frozenset(values)
            for kind, values in payload.get("status_vocabularies", {}).items()
        }
        return cls(
            funds=tuple(fund(**item) for item in payload.get("funds", [])),
            periods=tuple(period(**item) for item in payload.get("periods", [])),
            entries=tuple(_entry_from_dict(item) for item in payload.get("entries", [])),
            themes=tuple(
                theme(
                    id=item["id"],
                    name=item["name"],
                    desc=item["desc"],
                    periods=tuple(item.get("periods", [])),
                )
                for item in payload.get("themes", [])
            ),
            documents=tuple(document(**item) for item in payload.get("documents", [])),
            gaps=tuple(gap(**item) for item in payload.get("gaps", [])),
            status_vocabularies=status_vocabularies,
        )

    @classmethod
    def from_json(cls, path: Path) -> Store:
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


@dataclass(frozen=True, slots=True)
class ValidationViolation:
    record_id: str
    message: str


def fund(
    name: str,
    manager: str,
    strategy: str,
    archetype: str,
    note: str,
) -> Fund:
    return Fund(name, manager, strategy, archetype, note)


def period(
    id: str,
    sort: int,
    label: str,
    kind: str,
    title: str,
    author: str,
    attendees: str,
    verdict: str,
    note: str,
) -> Period:
    return Period(id, sort, label, kind, title, author, attendees, verdict, note)


def pub(state: str, as_of: str, detail: str, src: str) -> Pub:
    return Pub(state, as_of, detail, src)


def mention(
    period: str,
    text: str,
    bps: float | None,
    size: str,
    src: str,
    inferred: bool,
) -> Mention:
    return Mention(period, text, bps, size, src, inferred)


def entry(
    id: str,
    name: str,
    ticker: str,
    counterparty: str,
    kind: str,
    first: str,
    last: str,
    status: str,
    peak: float | None,
    flag: str,
    thesis: str,
    pub: Pub,
    mentions: Sequence[Mention],
) -> Entry:
    return Entry(
        id,
        name,
        ticker,
        counterparty,
        kind,
        first,
        last,
        status,
        peak,
        flag,
        thesis,
        pub,
        tuple(mentions),
    )


def theme(id: str, name: str, desc: str, periods: Sequence[str]) -> Theme:
    return Theme(id, name, desc, tuple(periods))


def document(name: str, date: str, verdict: str, note: str) -> Document:
    return Document(name, date, verdict, note)


def gap(sev: str, title: str, desc: str) -> Gap:
    return Gap(sev, title, desc)


def _entry_from_dict(item: Mapping[str, Any]) -> Entry:
    pub_data = item["pub"]
    mentions = tuple(
        mention(
            period=m["period"],
            text=m["text"],
            bps=m.get("bps"),
            size=m.get("size", ""),
            src=m.get("src", ""),
            inferred=m["inferred"],
        )
        for m in item.get("mentions", [])
    )
    return entry(
        id=item["id"],
        name=item["name"],
        ticker=item.get("ticker", ""),
        counterparty=item.get("counterparty", ""),
        kind=item.get("kind", "position"),
        first=item["first"],
        last=item["last"],
        status=item["status"],
        peak=item.get("peak"),
        flag=item.get("flag", ""),
        thesis=item.get("thesis", ""),
        pub=pub(
            state=pub_data["state"],
            as_of=pub_data.get("as_of", ""),
            detail=pub_data.get("detail", ""),
            src=pub_data.get("src", ""),
        ),
        mentions=mentions,
    )


def _append_duplicate(
    violations: list[ValidationViolation],
    seen: dict[str, str],
    record_id: str,
    collection: str,
) -> None:
    if record_id in seen:
        violations.append(
            ValidationViolation(
                record_id,
                f"identifier {record_id!r} defined twice in {collection}",
            )
        )
    seen[record_id] = collection


def _check_finite(
    violations: list[ValidationViolation],
    record_id: str,
    field: str,
    value: Any,
) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        violations.append(
            ValidationViolation(record_id, f"{field} must be a finite number or null")
        )
        return
    if isinstance(value, float) and not math.isfinite(value):
        violations.append(ValidationViolation(record_id, f"{field} must be finite, got {value!r}"))


def _check_period_sort(
    violations: list[ValidationViolation],
    record_id: str,
    value: Any,
) -> bool:
    """Return True when sort is safe to compare."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        violations.append(ValidationViolation(record_id, "sort must be a finite number"))
        return False
    if isinstance(value, float) and not math.isfinite(value):
        violations.append(ValidationViolation(record_id, f"sort must be finite, got {value!r}"))
        return False
    return True


def _check_truncated_currency(
    violations: list[ValidationViolation],
    record_id: str,
    field: str,
    value: str,
) -> None:
    if isinstance(value, str) and value and _TRUNCATED_CURRENCY.match(value.strip()):
        violations.append(
            ValidationViolation(
                record_id,
                f"{field} looks like a truncated currency amount: {value!r}",
            )
        )


def validate(store: Store) -> list[ValidationViolation]:
    """Return every semantic violation in one pass."""
    violations: list[ValidationViolation] = []
    seen_ids: dict[str, str] = {}

    periods_by_id = {item.id: item for item in store.periods}
    period_ids = set(periods_by_id)
    document_names = {item.name for item in store.documents}

    valid_period_sorts: dict[str, bool] = {}
    for period_item in store.periods:
        _append_duplicate(violations, seen_ids, period_item.id, "periods")
        valid_period_sorts[period_item.id] = _check_period_sort(
            violations, period_item.id, period_item.sort
        )

    for theme_item in store.themes:
        _append_duplicate(violations, seen_ids, theme_item.id, "themes")
        for period_ref in theme_item.periods:
            if period_ref not in period_ids:
                violations.append(
                    ValidationViolation(
                        theme_item.id,
                        f"period {period_ref!r} referenced but not defined",
                    )
                )

    for document_item in store.documents:
        if document_item.name in seen_ids:
            violations.append(
                ValidationViolation(
                    document_item.name,
                    f"identifier {document_item.name!r} defined twice in documents",
                )
            )
        seen_ids[document_item.name] = "documents"

    for entry_item in store.entries:
        _append_duplicate(violations, seen_ids, entry_item.id, "entries")
        if entry_item.first not in period_ids:
            violations.append(
                ValidationViolation(
                    entry_item.id,
                    f"period {entry_item.first!r} referenced but not defined",
                )
            )
        if entry_item.last not in period_ids:
            violations.append(
                ValidationViolation(
                    entry_item.id,
                    f"period {entry_item.last!r} referenced but not defined",
                )
            )
        first_period = periods_by_id.get(entry_item.first)
        last_period = periods_by_id.get(entry_item.last)
        if (
            first_period is not None
            and last_period is not None
            and valid_period_sorts.get(entry_item.first, False)
            and valid_period_sorts.get(entry_item.last, False)
            and first_period.sort > last_period.sort
        ):
            violations.append(
                ValidationViolation(
                    entry_item.id,
                    f"first period {entry_item.first!r} is after last period {entry_item.last!r}",
                )
            )
        _check_finite(violations, entry_item.id, "peak", entry_item.peak)
        _check_truncated_currency(violations, entry_item.id, "flag", entry_item.flag)

        vocabulary = store.status_vocabularies.get(entry_item.kind, frozenset())
        if vocabulary and entry_item.status not in vocabulary:
            violations.append(
                ValidationViolation(
                    entry_item.id,
                    f"status {entry_item.status!r} is not allowed for "
                    f"{entry_item.kind!r} entries",
                )
            )

        if entry_item.pub.state not in PUB_STATES:
            violations.append(
                ValidationViolation(
                    entry_item.id,
                    f"pub.state must be one of {sorted(PUB_STATES)}, got {entry_item.pub.state!r}",
                )
            )
        if entry_item.pub.src not in document_names:
            violations.append(
                ValidationViolation(
                    entry_item.id,
                    f"document {entry_item.pub.src!r} referenced but not defined",
                )
            )

        for index, mention_item in enumerate(entry_item.mentions):
            mention_id = f"{entry_item.id}:mention[{index}]"
            if not mention_item.src:
                violations.append(ValidationViolation(mention_id, "mention must carry src"))
            elif mention_item.src not in document_names:
                violations.append(
                    ValidationViolation(
                        mention_id,
                        f"document {mention_item.src!r} referenced but not defined",
                    )
                )
            if mention_item.period not in period_ids:
                violations.append(
                    ValidationViolation(
                        mention_id,
                        f"period {mention_item.period!r} referenced but not defined",
                    )
                )
            _check_finite(violations, mention_id, "bps", mention_item.bps)
            _check_truncated_currency(violations, mention_id, "size", mention_item.size)

    return violations


def derive_gaps(store: Store) -> tuple[Gap, ...]:
    """Compute coverage gaps without mutating entry status."""
    period_ids = {item.id: item for item in store.periods}
    gaps: list[Gap] = []
    for entry_item in store.entries:
        mentioned_periods = {mention.period for mention in entry_item.mentions}
        active_periods = [
            period_item
            for period_item in store.periods
            if _period_in_range(period_item, entry_item, period_ids)
        ]
        for period_item in active_periods:
            if period_item.id not in mentioned_periods:
                gaps.append(
                    gap(
                        sev="info",
                        title=f"Missing mention for {entry_item.id} in {period_item.id}",
                        desc=(
                            f"Entry {entry_item.id!r} is active in period {period_item.id!r} "
                            "but has no mention; silence is not a status change."
                        ),
                    )
                )
    return tuple(gaps)


def _period_in_range(
    period_item: Period,
    entry_item: Entry,
    period_ids: Mapping[str, Period],
) -> bool:
    first = period_ids.get(entry_item.first)
    last = period_ids.get(entry_item.last)
    if first is None or last is None:
        return False
    bounds = (first.sort, last.sort, period_item.sort)
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or (isinstance(value, float) and not math.isfinite(value))
        for value in bounds
    ):
        return False
    return first.sort <= period_item.sort <= last.sort


def load_schema(name: str = "mosaic-store-v1") -> dict[str, Any]:
    schema_file = resources.files("manager_mosaic").joinpath("schemas", f"{name}.schema.json")
    payload: dict[str, Any] = json.loads(schema_file.read_text(encoding="utf-8"))
    return payload


def _payload_path(parts: Sequence[str | int]) -> str:
    path = "$"
    for part in parts:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def _payload_structure_violations(payload: Mapping[str, Any]) -> list[ValidationViolation]:
    violations = []
    validator_type = validators.extend(
        Draft202012Validator,
        type_checker=Draft202012Validator.TYPE_CHECKER.redefine(
            "object", lambda checker, value: isinstance(value, Mapping)
        ),
    )
    for error in validator_type(load_schema()).iter_errors(payload):
        path = list(error.absolute_path)
        if error.validator == "required" and isinstance(error.instance, Mapping):
            missing = [key for key in error.validator_value if key not in error.instance]
            # jsonschema emits one error per absent property, so select this one.
            for key in missing:
                item = ValidationViolation(_payload_path([*path, key]), "required field is missing")
                if item not in violations:
                    violations.append(item)
        else:
            violations.append(ValidationViolation(_payload_path(path), error.message))
    return violations


def validate_payload(payload: Mapping[str, Any]) -> list[ValidationViolation]:
    """Collect raw structure and every semantic check with well-typed prerequisites.

    Diagnostics use source paths even when a record has no usable ID. No values
    are coerced or supplied to make malformed records constructible.
    """
    violations = _payload_structure_violations(payload)
    if not isinstance(payload, Mapping):
        return violations

    def records(key: str) -> list[tuple[str, Mapping[str, Any]]]:
        collection = payload.get(key)
        if not isinstance(collection, list):
            return []
        return [
            (f"$.{key}[{i}]", value)
            for i, value in enumerate(collection)
            if isinstance(value, Mapping)
        ]

    periods = {
        item["id"]: item for _, item in records("periods") if isinstance(item.get("id"), str)
    }

    def reference_ids(key: str, field: str) -> set[str] | None:
        collection = payload.get(key, [])
        if not isinstance(collection, list) or any(
            not isinstance(item, Mapping) or not isinstance(item.get(field), str)
            for item in collection
        ):
            return None
        return {item[field] for item in collection}

    period_reference_ids = reference_ids("periods", "id")
    documents = reference_ids("documents", "name")
    seen: set[str] = set()
    for collection in ("periods", "themes", "documents", "entries"):
        field = "name" if collection == "documents" else "id"
        for path, item in records(collection):
            identity = item.get(field)
            if isinstance(identity, str):
                if identity in seen:
                    violations.append(
                        ValidationViolation(
                            f"{path}.{field}", f"identifier {identity!r} defined twice"
                        )
                    )
                seen.add(identity)

    def reference(value: Any, path: str, known: set[str] | None, kind: str) -> None:
        if known is not None and isinstance(value, str) and value not in known:
            violations.append(
                ValidationViolation(path, f"{kind} {value!r} referenced but not defined")
            )

    valid_sorts: dict[str, bool] = {}
    for path, item in records("periods"):
        if "sort" in item:
            safe = _check_period_sort(violations, f"{path}.sort", item["sort"])
            if isinstance(item.get("id"), str):
                valid_sorts[item["id"]] = safe
    for path, item in records("themes"):
        refs = item.get("periods")
        if isinstance(refs, list):
            for i, value in enumerate(refs):
                reference(value, f"{path}.periods[{i}]", period_reference_ids, "period")
    vocabularies = payload.get("status_vocabularies")
    for path, item in records("entries"):
        for field in ("first", "last"):
            reference(item.get(field), f"{path}.{field}", period_reference_ids, "period")
        first, last = item.get("first"), item.get("last")
        if (
            period_reference_ids is not None
            and isinstance(first, str)
            and isinstance(last, str)
            and valid_sorts.get(first, False)
            and valid_sorts.get(last, False)
            and periods[first]["sort"] > periods[last]["sort"]
        ):
            violations.append(
                ValidationViolation(path, f"first period {first!r} is after last period {last!r}")
            )
        if "peak" in item:
            _check_finite(violations, f"{path}.peak", "peak", item["peak"])
        if isinstance(item.get("flag"), str):
            _check_truncated_currency(violations, f"{path}.flag", "flag", item["flag"])
        kind, status = item.get("kind"), item.get("status")
        if isinstance(vocabularies, Mapping) and isinstance(kind, str) and isinstance(status, str):
            vocabulary = vocabularies.get(kind)
            if (
                isinstance(vocabulary, list)
                and all(isinstance(value, str) for value in vocabulary)
                and vocabulary
                and status not in vocabulary
            ):
                violations.append(
                    ValidationViolation(
                        f"{path}.status", f"status {status!r} is not allowed for {kind!r} entries"
                    )
                )
        publication = item.get("pub")
        if isinstance(publication, Mapping):
            reference(publication.get("src"), f"{path}.pub.src", documents, "document")
        mentions = item.get("mentions")
        if not isinstance(mentions, list):
            continue
        for i, value in enumerate(mentions):
            if not isinstance(value, Mapping):
                continue
            mention_path = f"{path}.mentions[{i}]"
            reference(value.get("period"), f"{mention_path}.period", period_reference_ids, "period")
            reference(value.get("src"), f"{mention_path}.src", documents, "document")
            if "bps" in value:
                _check_finite(violations, f"{mention_path}.bps", "bps", value["bps"])
            if isinstance(value.get("size"), str):
                _check_truncated_currency(violations, f"{mention_path}.size", "size", value["size"])
    return violations
