"""Repository-level checks for generated and deliberately vendored trees."""

import ast
import json
import re
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


def test_public_contract_entrypoints_have_audited_dispositions() -> None:
    catalog = json.loads((REPO_ROOT / "docs/audits/contract-enforcement-catalog.json").read_text())
    rows = catalog["entrypoints"]
    audited = {row["source"] for row in rows}
    assert len(audited) == len(rows), "Duplicate entry points hide conflicting dispositions"
    report = (REPO_ROOT / "contract-enforcement-audit.md").read_text()
    available: set[str] = set()
    for path in (REPO_ROOT / "src/manager_mosaic").glob("*.py"):
        tree = ast.parse(path.read_text())
        names: set[str] = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_"):
                    continue
                names.add(node.name)
                if isinstance(node, ast.ClassDef):
                    names.update(
                        f"{node.name}.{member.name}"
                        for member in node.body
                        if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and (
                            not member.name.startswith("_")
                            or member.name in {"__init__", "__post_init__"}
                        )
                    )
            # Submodule exports include aliases such as fact_keys.ValidationViolation.
            # Root re-exports are covered at their canonical defining module.
            if (
                path.name != "__init__.py"
                and isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "__all__"
                    for target in node.targets
                )
            ):
                names.update(ast.literal_eval(node.value))
        available.update(f"{path.relative_to(REPO_ROOT)}:{name}" for name in names)
    assert available <= audited, f"Unmapped public inputs: {sorted(available - audited)}"
    contract = (REPO_ROOT / "docs/PRODUCT_CONTRACT.md").read_text()
    valid_functions = {f"CF-{number}" for number in range(1, 8)}
    for row in rows:
        assert row["source"] in report
        probe_path = REPO_ROOT / row["probe"]
        assert probe_path.is_file()
        probe_names = {
            node.name
            for node in ast.parse(probe_path.read_text()).body
            if isinstance(node, ast.FunctionDef)
        }
        assert row["probe_name"] in probe_names, f"Missing probing test: {row}"
        assert f"{row['probe']}::{row['probe_name']}" in report
        assert row["contracts"], row
        assert all((REPO_ROOT / contract_path).is_file() for contract_path in row["contracts"])
        assert row["owner"]
        assert set(row["core_functions"]) <= valid_functions, row
        assert all(function in contract for function in row["core_functions"]), row
        assert row["core_functions"] or row.get("outside_contract"), row
        if row["source"].startswith("src/") and row.get("availability") != "planned":
            assert row["source"] in available, f"Stale inventory entry: {row['source']}"
        if row["classification"] in {"confirmed-bug", "needs-investigation"}:
            assert row["issues"], row
    for line in report.splitlines():
        if "confirmed-bug" in line or "needs-investigation" in line:
            assert re.search(
                r"\[#([1-9]\d*)\]\(https://github\.com/stranske/Manager-Mosaic/issues/\1\)", line
            ), f"Unfiled audit finding: {line}"


def test_packaged_contract_resources_have_audited_consumers() -> None:
    catalog = json.loads((REPO_ROOT / "docs/audits/contract-enforcement-catalog.json").read_text())
    packaged = {
        str(p.relative_to(REPO_ROOT))
        for p in (REPO_ROOT / "src/manager_mosaic/schemas").glob("*.json")
    }
    packaged.add("src/manager_mosaic/fact_key_registry.json")
    assert packaged == set(
        catalog["resources"]
    ), "New or missing packaged contract needs an audited consumer"
    for path in packaged:
        assert (REPO_ROOT / path).is_file()
    for module, required_call in [
        ("fact_keys", "load_fact_key_registry"),
        ("evidence", "load_schema"),
    ]:
        tree = ast.parse((REPO_ROOT / f"src/manager_mosaic/{module}.py").read_text())
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert required_call in calls, f"Orphaned contract consumer: {module}:{required_call}"


def test_audit_marks_raw_store_exception_and_optional_vocabulary_truthfully() -> None:
    catalog = json.loads((REPO_ROOT / "docs/audits/contract-enforcement-catalog.json").read_text())
    assert (
        catalog["resources"]["src/manager_mosaic/schemas/mosaic-store-v1.schema.json"][
            "exception_issue"
        ]
        == 96
    )
    assert catalog["additional_findings"] == []
    report = (REPO_ROOT / "contract-enforcement-audit.md").read_text()
    assert "intentionally-opt-in" in report
    assert "Pending delivery" in report
    for issue in (96, 97, 98, 101):
        assert f"issues/{issue}" in report
