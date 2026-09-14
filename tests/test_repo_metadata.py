"""Keep published repository links aligned with the distribution identity."""

import tomllib
from pathlib import Path


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
