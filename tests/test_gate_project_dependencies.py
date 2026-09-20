"""Keep the consumer-owned Gate aligned with Workflows' dependency bootstrap."""

import os
import subprocess
import textwrap
from pathlib import Path


def test_gate_installs_dependencies_without_leaving_head_project(tmp_path):
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/pr-00-gate.yml").read_text(encoding="utf-8")
    step = workflow.split("      - name: Install test-quality dependencies\n", 1)[1]
    step = step.split("      # Consumer repos intentionally omit", 1)[0]
    assert "        run: |\n" in step
    script = textwrap.dedent(step.split("        run: |\n", 1)[1])
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "manager-mosaic"\ndependencies = ["jsonschema==4.22.0"]\n',
        encoding="utf-8",
    )
    log = tmp_path / "pip-calls.log"
    # Exercise the actual shell control flow without changing the test environment.
    shim = """python() {
  if [ "$1" = "-m" ]; then
    printf '%s\\n' "$*" >> "$PIP_TEST_LOG"
    return 0
  fi
  command python3 "$@"
}
"""
    result = subprocess.run(
        ["bash", "-c", shim + script],
        cwd=tmp_path,
        env={**os.environ, "PIP_TEST_LOG": str(log)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = log.read_text(encoding="utf-8").splitlines()
    assert "-m pip install ." in calls
    assert "-m pip uninstall -y manager-mosaic" in calls
    assert calls.index("-m pip install .") < calls.index("-m pip uninstall -y manager-mosaic")
