"""Conftest."""

from __future__ import annotations

import os
import typing

import pytest

from pytest_checkers import checkers

TESTED_TOOL = os.environ.get("TESTED_TOOL")
XFAIL_MSG = "'{tool_name}' expected to fail, tested tool is '{tested_tool}'"

ToolHelp = tuple[str, str]
ToolName = str

pytest_plugins = ["pytester"]


def _tool_help_data() -> list[ToolHelp]:
    out = [("checkers", "Enable all available checks")]
    out.extend((k, v["help_"]) for k, v in checkers.TOOLS_MAP.items())
    return out


def _tool_help_ids(value: tuple[str, str]) -> str:
    tool_name, _ = value
    return f"tool_option:{tool_name}"


# @pytest.fixture(scope="session")
# def tested_tool() -> str | None:
#     """Tested tool."""
#     return os.environ.get("TESTED_TOOL")
#
#
# @pytest.fixture(scope="session")
# def xfail_msg() -> str:
#     """XFAIL message."""
#     return "'{tool_name}' expected to fail, tested tool is '{tested_tool}' "


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Set hook."""
    if not isinstance(item, pytest.Function):
        return
    if "tool_name" in item.fixturenames:
        tool_name = item.funcargs.get("tool_name")
        if TESTED_TOOL not in ["checkers", tool_name]:
            pytest.xfail(XFAIL_MSG.format(tool_name=tool_name, tested_tool=TESTED_TOOL))


@pytest.fixture(params=_tool_help_data(), ids=_tool_help_ids, scope="session")
def tool_help_data(request: pytest.FixtureRequest) -> typing.Any:
    """Tool and help data."""
    return request.param


_tool_names: list[ToolName] = list(checkers.TOOLS_MAP)


@pytest.fixture(params=_tool_names, ids=lambda v: f"tool_option:{v}", scope="session")
def tool_name(request: pytest.FixtureRequest) -> typing.Any:
    """Tool name."""
    return request.param
