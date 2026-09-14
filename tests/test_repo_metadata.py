"""Keep published repository links aligned with the distribution identity."""

import subprocess
import sys
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
    try:
        with pytest.raises(AssertionError, match=f"Template placeholder in author {field}"):
            test_project_authors_are_not_template_placeholder()
    finally:
        metadata.write_text(original)
    test_project_authors_are_not_template_placeholder()


@pytest.mark.parametrize("placement", ["replace-owner", "before-owner", "after-owner"])
@pytest.mark.parametrize(
    ("name", "email", "invalid_field"),
    [
        ("Your Name", "your.email@example.com", "name"),
        ("Your Name", "noreply@users.noreply.github.com", "name"),
        ("stranske", "your.email@example.com", "email"),
        ("prefix Your Name suffix", "noreply@users.noreply.github.com", "name"),
        ("stranske", "prefix your.email@example.com suffix", "email"),
    ],
    ids=[
        "full-placeholder",
        "placeholder-name",
        "placeholder-email",
        "embedded-placeholder-name",
        "embedded-placeholder-email",
    ],
)
def test_author_placeholder_block_detects_break_and_revert(
    tmp_path: Path, placement: str, name: str, email: str, invalid_field: str
) -> None:
    """Reject full or partially corrected template authors, then accept the owner."""
    root = Path(__file__).resolve().parents[1]
    original = (root / "pyproject.toml").read_text()
    metadata = tmp_path / "pyproject.toml"
    test_copy = tmp_path / "tests" / "test_repo_metadata.py"
    test_copy.parent.mkdir()
    test_copy.write_text(Path(__file__).read_text())
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "tests/test_repo_metadata.py::test_project_authors_are_not_template_placeholder",
        "-o",
        "addopts=",
        "-m",
        "not slow",
    ]
    owner = '{name = "stranske", email = "noreply@users.noreply.github.com"}'
    placeholder = f'{{name = "{name}", email = "{email}"}}'
    replacement = {
        "replace-owner": placeholder,
        "before-owner": f"{placeholder},\n    {owner}",
        "after-owner": f"{owner},\n    {placeholder}",
    }[placement]
    broken = original.replace(owner, replacement)
    assert broken != original
    metadata.write_text(broken)
    try:
        failed = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=30)
        assert failed.returncode == pytest.ExitCode.TESTS_FAILED, failed.stdout + failed.stderr
        assert (
            "test_repo_metadata.py::test_project_authors_are_not_template_placeholder FAILED"
            in failed.stdout
        ), failed.stdout
        assert f"Template placeholder in author {invalid_field}" in failed.stdout
    finally:
        metadata.write_text(original)
    passed = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert passed.returncode == pytest.ExitCode.OK, passed.stdout + passed.stderr
    assert (
        "test_repo_metadata.py::test_project_authors_are_not_template_placeholder PASSED"
        in passed.stdout
    ), passed.stdout
