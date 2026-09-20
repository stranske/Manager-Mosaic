"""Exercise the consumer-owned Gate's reviewed source dependency bootstrap."""

import json
import os
import subprocess
import textwrap
from pathlib import Path

import pytest


@pytest.mark.parametrize("project_file", ["pyproject.toml", "setup.py"])
@pytest.mark.parametrize("failure", ["", "missing-name", "ambiguous-name", "uninstall"])
def test_gate_installs_dependencies_then_removes_head_project(tmp_path, project_file, failure):
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/pr-00-gate.yml").read_text(encoding="utf-8")
    step = workflow.split("      - name: Install test-quality dependencies\n", 1)[1]
    step = step.split("      # Consumer repos intentionally omit", 1)[0]
    assert "        run: |\n" in step
    script = textwrap.dedent(step.split("        run: |\n", 1)[1])
    (tmp_path / project_file).write_text(
        (
            '[project]\nname = "manager-mosaic"\ndependencies = ["jsonschema==4.22.0"]\n'
            if project_file.endswith("toml")
            else "# setup.py fixture\n"
        ),
        encoding="utf-8",
    )
    report = tmp_path / "install-report.json"
    installs = [
        {"requested": False, "metadata": {"name": "jsonschema"}},
        {
            "requested": True,
            "metadata": {} if failure == "missing-name" else {"name": "manager-mosaic"},
        },
    ]
    if failure == "ambiguous-name":
        installs.append({"requested": True, "metadata": {"name": "another-project"}})
    report.write_text(json.dumps({"install": installs}), encoding="utf-8")
    log = tmp_path / "pip-calls.log"
    # Exercise the real workflow shell flow without changing this test environment.
    shim = """
python() {
  if [ "$1" = "-m" ]; then
    printf '%s\\n' "$*" >> "$PIP_TEST_LOG"
    if [ "$3" = "install" ] && [ "$4" = "--report" ]; then
      cp "$PIP_TEST_REPORT" "$5"
    fi
    if [ "$3" = "uninstall" ] && [ "$PIP_TEST_FAILURE" = "uninstall" ]; then
      return 1
    fi
    return 0
  fi
  command python3 "$@"
}
"""
    result = subprocess.run(
        ["bash", "-c", shim + script],
        cwd=tmp_path,
        env={
            **os.environ,
            "PIP_TEST_LOG": str(log),
            "PIP_TEST_REPORT": str(report),
            "PIP_TEST_FAILURE": failure,
        },
        capture_output=True,
        text=True,
    )
    if failure:
        assert result.returncode != 0, "Unsafe base test must not run"
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        calls = log.read_text(encoding="utf-8").splitlines()
        assert any(call.startswith("-m pip install --report ") for call in calls)
        assert "-m pip uninstall -y manager-mosaic" in calls
        assert "-m pip uninstall -y jsonschema" not in calls
