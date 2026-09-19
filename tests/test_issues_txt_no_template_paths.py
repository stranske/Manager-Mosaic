"""Keep the agent queue aligned with the installed package identity."""

from pathlib import Path


def test_issues_txt_does_not_reference_my_project() -> None:
    queue = Path(__file__).resolve().parents[1] / "Issues.txt"
    assert "my_project" not in queue.read_text(encoding="utf-8")
