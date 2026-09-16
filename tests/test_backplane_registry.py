"""Consumer-local backplane participant registry."""

import json
from pathlib import Path

EXPECTED_INGESTS = (
    "evidence-object/v1",
    "artifact-manifest/v1",
    "run-contract/v1",
    "identity-map-conventions",
)


def test_manager_mosaic_consumer_entry_present() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "config" / "backplane_participants.json").read_text())
    entry = next(
        (
            participant
            for participant in registry.get("participants", [])
            if participant.get("repo") == "stranske/Manager-Mosaic"
        ),
        None,
    )
    assert entry is not None, "Manager-Mosaic participant entry missing"
    assert entry.get("role") == "consumer"
    assert entry.get("status") == "planned"
    assert entry.get("parent_issue") == "stranske/Manager-Mosaic#3"
    assert entry.get("ingests") == list(EXPECTED_INGESTS)
