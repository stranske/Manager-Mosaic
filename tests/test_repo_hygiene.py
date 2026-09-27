"""Repository-level checks for generated and deliberately vendored trees."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_generated_dirs_untracked_and_vendored_preserved() -> None:
    root_modules = _git("ls-files", "node_modules")
    assert root_modules.returncode == 0
    assert not root_modules.stdout.strip(), "root node_modules must not be tracked"

    vendored_modules = _git(
        "ls-files",
        "--error-unmatch",
        "--",
        ".github/scripts/node_modules/minimatch/package.json",
    )
    assert vendored_modules.returncode == 0
    assert vendored_modules.stdout.strip(), "vendored minimatch tree must remain tracked"

    root_ignore = _git("check-ignore", "-q", "node_modules/probe.js")
    assert root_ignore.returncode == 0, "root node_modules must be ignored"

    vendored_ignore = _git(
        "check-ignore",
        "-q",
        "--no-index",
        ".github/scripts/node_modules/minimatch/package.json",
    )
    assert vendored_ignore.returncode == 1, "vendored minimatch tree must not be ignored"


def test_product_contract_documents_core_functions() -> None:
    contract = REPO_ROOT / "docs" / "PRODUCT_CONTRACT.md"

    assert contract.is_file(), "docs/PRODUCT_CONTRACT.md must document the core functions"
    contents = contract.read_text(encoding="utf-8")
    for core_function in range(1, 7):
        assert f"CF-{core_function}" in contents
