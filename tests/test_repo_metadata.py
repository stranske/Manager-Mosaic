"""Keep published repository links aligned with the distribution identity."""

import tomllib
from pathlib import Path

import pytest


def test_project_urls_reference_manager_mosaic_repo() -> None:
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as source:
        urls = tomllib.load(source)["project"]["urls"]
    expected = "https://github.com/stranske/Manager-Mosaic"
    assert urls["Homepage"] == expected
    assert urls["Repository"] == expected


def test_project_authors_are_not_template_placeholder() -> None:
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as source:
        authors = tomllib.load(source)["project"]["authors"]
    assert authors, "Project metadata must declare an author"
    for author in authors:
        for field in ("name", "email"):
            value = author.get(field, "")
            for placeholder in ("Your Name", "your.email@example.com"):
                assert placeholder not in value, f"Template placeholder in author {field}: {value}"


def test_project_authors_include_repository_owner() -> None:
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as source:
        authors = tomllib.load(source)["project"]["authors"]
    assert {"name": "stranske", "email": "noreply@users.noreply.github.com"} in authors


@pytest.mark.parametrize("field", ["name", "email"])
@pytest.mark.parametrize("placeholder", ["Your Name", "your.email@example.com"])
def test_author_placeholder_guard_detects_break_and_revert(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, placeholder: str
) -> None:
    """Exercise the named guard against contaminated metadata, then restore it."""
    root = Path(__file__).resolve().parents[1]
    original = (root / "pyproject.toml").read_text()
    metadata = tmp_path / "pyproject.toml"
    monkeypatch.setitem(globals(), "__file__", str(tmp_path / "tests" / "test_repo_metadata.py"))
    owner_value = {"name": "stranske", "email": "noreply@users.noreply.github.com"}[field]
    broken = original.replace(
        f'{field} = "{owner_value}"', f'{field} = "prefix {placeholder} suffix"'
    )
    assert broken != original
    metadata.write_text(broken)
    with pytest.raises(AssertionError, match=f"Template placeholder in author {field}"):
        test_project_authors_are_not_template_placeholder()
    metadata.write_text(original)
    test_project_authors_are_not_template_placeholder()


def test_author_placeholder_block_detects_break_and_revert(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject the original template author block and accept the restored owner."""
    root = Path(__file__).resolve().parents[1]
    original = (root / "pyproject.toml").read_text()
    metadata = tmp_path / "pyproject.toml"
    monkeypatch.setitem(globals(), "__file__", str(tmp_path / "tests" / "test_repo_metadata.py"))
    broken = original.replace(
        '{name = "stranske", email = "noreply@users.noreply.github.com"}',
        '{name = "Your Name", email = "your.email@example.com"}',
    )
    assert broken != original
    metadata.write_text(broken)
    with pytest.raises(AssertionError, match="Template placeholder in author name"):
        test_project_authors_are_not_template_placeholder()
    metadata.write_text(original)
    test_project_authors_are_not_template_placeholder()
