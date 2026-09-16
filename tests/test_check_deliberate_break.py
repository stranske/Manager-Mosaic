"""Tests for deliberate-break gate helpers."""

from __future__ import annotations

import sys

from scripts.check_deliberate_break import _pytest_command


def test_pytest_command_clears_addopts() -> None:
    command = _pytest_command("tests/test_example.py::test_gate")
    assert "-o" in command
    assert "addopts=" in command
    assert command[0] == sys.executable
    assert command[1:4] == ("-m", "pytest", "tests/test_example.py::test_gate")
