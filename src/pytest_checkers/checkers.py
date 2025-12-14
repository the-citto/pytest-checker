"""Checkers."""

from __future__ import annotations

import abc
import contextlib
import importlib.metadata
import os
import subprocess
import sys
import typing

from _pytest.reports import TestReport

if typing.TYPE_CHECKING:
    import pytest
    from _pytest.terminal import TerminalReporter


Tool = typing.Literal["black", "flake8", "isort", "mypy", "pyright", "ruff", "ty"]
EscTable = typing.Literal[
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "purple",
    "cyan",
    "white",
    "Black",
    "Red",
    "Green",
    "Yellow",
    "Blue",
    "Purple",
    "Cyan",
    "White",
    "bold",
    "light",
    "blink",
    "invert",
]


class CheckersPlugin(abc.ABC):
    """Abstract checkers plugin."""

    tool: Tool
    header_markup: EscTable
    cmd_output: str = ""
    cmd_returncode: int = 0
    finish_msg: str = ""

    def __init__(self, config: pytest.Config) -> None:
        """Init."""
        self.config = config

    @property
    @abc.abstractmethod
    def cmd_flags(self) -> list[str]:
        """Command flags."""

    @property
    def env_vars(self) -> dict[str, str]:
        """Environment variables."""
        env_vars = os.environ.copy()
        env_vars["FORCE_COLOR"] = "1"
        env_vars["MYPY_FORCE_COLOR"] = "1"
        return env_vars

    @property
    @abc.abstractmethod
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return self.cmd_returncode != 0

    def append_error(self, session: pytest.Session) -> None:
        """Append error."""
        project_root = session.config.rootpath
        nodeid = f"{self.tool} check"
        report = TestReport(
            nodeid=nodeid,
            location=(str(project_root), 0, nodeid),
            keywords={nodeid: 1},
            when="call",
            longrepr=(f"{self.tool.title()} Failure", 0, "Code quality checks failed. See output above."),
            sections=[(f"{self.tool.title()} Output", self.cmd_output)],
            outcome="failed",
        )
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.stats.setdefault("failed", []).append(report)

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        """Pytest session finish."""
        if not getattr(self.config.option, self.tool, False):
            return
        project_root = session.config.rootpath
        cmd = [sys.executable, "-m", self.tool, *self.cmd_flags, str(project_root)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=self.env_vars)  # noqa: S603
        self.cmd_output = result.stdout + result.stderr
        self.cmd_returncode = result.returncode
        if self.is_error:
            self.append_error(session)
        else:
            self.cmd_output += self.finish_msg

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        """Pytest terminal summary."""
        if not getattr(self.config.option, self.tool, False):
            return
        # circumventing mypy quirk - https://github.com/python/mypy/issues/10023
        header_markup_kwarg = {typing.cast("str", self.header_markup): True}
        terminalreporter.write_sep(title=f"tests {self.tool}", sep="=", **header_markup_kwarg)
        terminalreporter.write(self.cmd_output)


class PyrightPlugin(CheckersPlugin):
    """Pyright plugin."""

    tool = "pyright"
    header_markup = "green"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return []

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return super().is_error


class TyPlugin(CheckersPlugin):
    """Ty plugin."""

    tool = "ty"
    header_markup = "green"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["check"]

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return super().is_error


class MypyPlugin(CheckersPlugin):
    """Mypy plugin."""

    tool = "mypy"
    header_markup = "green"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return []

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return super().is_error


class RuffPlugin(CheckersPlugin):
    """Ruff plugin."""

    tool = "ruff"
    header_markup = "purple"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["check"]

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return super().is_error


class Flake8Plugin(CheckersPlugin):
    """Flake8 plugin."""

    tool = "flake8"
    header_markup = "purple"
    finish_msg = "All done.\n"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["--color=always"]

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return super().is_error


class BlackPlugin(CheckersPlugin):
    """Black plugin."""

    tool = "black"
    header_markup = "cyan"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["--diff", "--color"]

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return "@@" in self.cmd_output


class IsortPlugin(CheckersPlugin):
    """Isort plugin."""

    tool = "isort"
    header_markup = "cyan"
    finish_msg = "All done.\n"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["--diff", "--color"]

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return "@@" in self.cmd_output


tools_map: dict[Tool, type[CheckersPlugin]] = {
    "black": BlackPlugin,
    "isort": IsortPlugin,
    "flake8": Flake8Plugin,
    "ruff": RuffPlugin,
    "mypy": MypyPlugin,
    "ty": TyPlugin,
    "pyright": PyrightPlugin,
}
added_options: list[Tool] = []


def _conditional_addoption(group: pytest.OptionGroup, /, *, tool: Tool, help_: str, action: str = "store_true") -> None:
    with contextlib.suppress(importlib.metadata.PackageNotFoundError):
        _ = importlib.metadata.version(tool)
        group.addoption(f"--{tool}", action=action, help=help_)
        added_options.append(tool)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Set hooks."""
    group = parser.getgroup("checkers")
    group.addoption("--checkers", action="store_true", help="Enable all available checks")
    _conditional_addoption(group, tool="black", help_="Enable `black --diff`")
    _conditional_addoption(group, tool="isort", help_="Enable `isort --diff`")
    _conditional_addoption(group, tool="flake8", help_="Enable `flake8`")
    _conditional_addoption(group, tool="ruff", help_="Enable `ruff check`")
    _conditional_addoption(group, tool="mypy", help_="Enable `mypy`")
    _conditional_addoption(group, tool="ty", help_="Enable `ty check`")
    _conditional_addoption(group, tool="pyright", help_="Enable `pyright`")


def pytest_configure(config: pytest.Config) -> None:
    """Configure."""
    for tool in added_options:
        if config.option.checkers:
            setattr(config.option, tool, True)
        if getattr(config.option, tool, False):
            tool_cls = tools_map[tool]
            config.pluginmanager.register(tool_cls(config), name=tool)
