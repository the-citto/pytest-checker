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
    finish_msg: str = ""

    def __init__(self, config: pytest.Config) -> None:
        """Init."""
        self.config = config
        self.cmd_output = ""
        self.cmd_returncode = 0

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
    # @abc.abstractmethod
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return self.cmd_returncode != 0

    def generate_report(self, session: pytest.Session, *, outcome: typing.Literal["passed", "failed"]) -> None:
        """Generate report."""
        project_root = session.config.rootpath
        nodeid = f"{self.tool} check"
        location = (str(project_root), 0, nodeid)
        longrepr: tuple[str, int, str] | None = None
        sections: list[tuple[str, str]] = []
        if outcome == "failed":
            longrepr = (f"{self.tool} failure", 0, "code quality checks failed, see output above.")
            sections = [(f"{self.tool} output", self.cmd_output)]
        report = TestReport(
            nodeid=nodeid,
            location=location,
            keywords={nodeid: 1},
            when="call",
            longrepr=longrepr,
            sections=sections,
            outcome=outcome,
        )
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.stats.setdefault(outcome, []).append(report)

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
            self.generate_report(session, outcome="failed")
        else:
            self.cmd_output += self.finish_msg
            self.generate_report(session, outcome="passed")

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


class TyPlugin(CheckersPlugin):
    """Ty plugin."""

    tool = "ty"
    header_markup = "green"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["check"]


class MypyPlugin(CheckersPlugin):
    """Mypy plugin."""

    tool = "mypy"
    header_markup = "green"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return []


class RuffPlugin(CheckersPlugin):
    """Ruff plugin."""

    tool = "ruff"
    header_markup = "purple"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["check"]


class Flake8Plugin(CheckersPlugin):
    """Flake8 plugin."""

    tool = "flake8"
    header_markup = "purple"
    finish_msg = "All done.\n"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["--color=always"]


class BlackPlugin(CheckersPlugin):
    """Black plugin."""

    tool = "black"
    header_markup = "cyan"

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return "@@" in self.cmd_output

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["--diff", "--color"]


class IsortPlugin(CheckersPlugin):
    """Isort plugin."""

    tool = "isort"
    header_markup = "cyan"
    finish_msg = "All done.\n"

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return "@@" in self.cmd_output

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["--diff", "--color"]


class ToolMapDictValues(typing.TypedDict):
    """ToolMapDictValues."""

    tool_cls: type[CheckersPlugin]
    help_: str


tools_map: dict[Tool, ToolMapDictValues] = {
    "black": {"tool_cls": BlackPlugin, "help_": "Enable `black --diff`"},
    "isort": {"tool_cls": IsortPlugin, "help_": "Enable `isort --diff`"},
    "flake8": {"tool_cls": Flake8Plugin, "help_": "Enable `flake8`"},
    "ruff": {"tool_cls": RuffPlugin, "help_": "Enable `ruff check`"},
    "mypy": {"tool_cls": MypyPlugin, "help_": "Enable `mypy`"},
    "ty": {"tool_cls": TyPlugin, "help_": "Enable `ty check`"},
    "pyright": {"tool_cls": PyrightPlugin, "help_": "Enable `pyright`"},
}
added_options: list[Tool] = []


def pytest_addoption(parser: pytest.Parser) -> None:
    """Set hooks."""
    group = parser.getgroup("checkers")
    group.addoption("--checkers", action="store_true", help="Enable all available checks")
    for tool, v in tools_map.items():
        with contextlib.suppress(importlib.metadata.PackageNotFoundError):
            _ = importlib.metadata.version(tool)
            help_ = v["help_"]
            group.addoption(f"--{tool}", action="store_true", help=help_)
            added_options.append(tool)


def pytest_configure(config: pytest.Config) -> None:
    """Configure."""
    for tool in added_options:
        if config.option.checkers:
            setattr(config.option, tool, True)
        if getattr(config.option, tool, False):
            tool_cls = tools_map[tool]["tool_cls"]
            config.pluginmanager.register(tool_cls(config), name=tool)
