"""Test behaviour."""

from __future__ import annotations

import typing

import pytest

from tests.conftest import (
    TESTED_TOOL,
    XFAIL_MSG,
)

if typing.TYPE_CHECKING:

    from tests.conftest import (
        ToolHelp,
        ToolName,
    )


def test_enabled_option(pytester: pytest.Pytester, tool_help_data: ToolHelp) -> None:
    """Test option appears in help output."""
    tool_name, help_ = tool_help_data
    if TESTED_TOOL not in ["checkers", tool_name]:
        pytest.xfail(XFAIL_MSG.format(tool_name=tool_name, tested_tool=TESTED_TOOL))
    result = pytester.runpytest_subprocess("--help")
    result.stdout.fnmatch_lines([f"*--{tool_name}*{help_}"])


def test_tool_header(pytester: pytest.Pytester, tool_name: ToolName) -> None:
    """Test tool header."""
    file_content = '"""Test doc."""\n'
    file_path = pytester.path / "dummy_file.py"
    file_path.write_text(file_content)
    result = pytester.runpytest_subprocess(f"--{tool_name}")
    result.stdout.fnmatch_lines([f"===* tests {tool_name} ===*"])


def test_tool_footer(pytester: pytest.Pytester, tool_name: ToolName) -> None:
    """Test tool footer."""
    file_content = '"""Test doc."""\n'
    file_path = pytester.path / "dummy_file.py"
    file_path.write_text(file_content)
    result = pytester.runpytest_subprocess(f"--{tool_name}")
    result.stdout.fnmatch_lines(["===* 1 passed in *===*"])


def test_tool_summary_passed(pytester: pytest.Pytester, tool_name: ToolName) -> None:
    """Test summary code passed."""
    file_content = '"""Test doc."""\n'
    file_path = pytester.path / "dummy_file.py"
    file_path.write_text(file_content)
    result = pytester.runpytest_subprocess(f"--{tool_name}")
    result.assert_outcomes(passed=1)


def test_tool_summary_failed(pytester: pytest.Pytester, tool_name: ToolName) -> None:
    """Test summary code failed."""
    file_content = "import foo\n\n\nimport bar\n-\n\n"
    file_path = pytester.path / "dummy_file.py"
    file_path.write_text(file_content)
    result = pytester.runpytest_subprocess(f"--{tool_name}")
    result.assert_outcomes(failed=1)
