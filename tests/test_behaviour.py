"""Test behaviour."""

from __future__ import annotations

import pytest

from pytest_checkers.checkers import TOOLS_MAP

param_tool_help_ = [(k, v["help_"]) for k, v in TOOLS_MAP.items()]


@pytest.mark.parametrize(("tool", "help_"), param_tool_help_)
def test_enabled_option(pytester: pytest.Pytester, tool: str, help_: str) -> None:
    """Test option appears in help output."""
    result = pytester.runpytest_subprocess("--help")
    result.stdout.fnmatch_lines([f"*--{tool}*{help_}"])


@pytest.mark.parametrize("tool", TOOLS_MAP)
def test_header(pytester: pytest.Pytester, tool: str) -> None:
    """Test header."""
    file_content = '"""Test doc."""\n'
    file_path = pytester.path / "dummy_file.py"
    file_path.write_text(file_content)
    result = pytester.runpytest_subprocess(f"--{tool}")
    result.stdout.fnmatch_lines([f"===* tests {tool} ===*"])


@pytest.mark.parametrize("tool", TOOLS_MAP)
def test_footer(pytester: pytest.Pytester, tool: str) -> None:
    """Test footer."""
    file_content = '"""Test doc."""\n'
    file_path = pytester.path / "dummy_file.py"
    file_path.write_text(file_content)
    result = pytester.runpytest_subprocess(f"--{tool}")
    result.stdout.fnmatch_lines(["===* 1 passed in *===*"])


@pytest.mark.parametrize("tool", TOOLS_MAP)
def test_code_passed(pytester: pytest.Pytester, tool: str) -> None:
    """Test code passed."""
    file_content = '"""Test doc."""\n'
    file_path = pytester.path / "dummy_file.py"
    file_path.write_text(file_content)
    result = pytester.runpytest_subprocess(f"--{tool}")
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize("tool", TOOLS_MAP)
def test_code_failed(pytester: pytest.Pytester, tool: str) -> None:
    """Test code failed."""
    file_content = "import foo\n\n\nimport bar\n-\n\n"
    file_path = pytester.path / "dummy_file.py"
    file_path.write_text(file_content)
    result = pytester.runpytest_subprocess(f"--{tool}")
    result.assert_outcomes(failed=1)
