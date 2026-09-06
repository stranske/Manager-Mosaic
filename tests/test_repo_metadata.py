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
