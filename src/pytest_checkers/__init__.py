"""Init."""

from __future__ import annotations

import importlib.metadata
import os
import re
import subprocess
import sys
import typing

if typing.TYPE_CHECKING:
    import pytest
    from _pytest.terminal import TerminalReporter


__version__ = importlib.metadata.version(__name__)


AnsiColours = typing.Literal[
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
]


def pytest_addoption(parser: pytest.Parser) -> None:
    """Set hooks."""
    group = parser.getgroup("checkers-mypy")
    group.addoption(
        "--ruff",
        action="store_true",
        help="Enable `ruff check`.",
    )


print()


class RuffPlugin:
    """Ruff plugin."""

    def __init__(self, config: pytest.Config) -> None:
        """Init."""
        self.config = config

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        """Pytest terminal summary."""
        if not self.config.option.ruff:
            return
        terminalreporter.write_sep(title="tests ruff", sep="=", purple=True)
        project_root = terminalreporter.config.rootpath
        ruff_cmd = [sys.executable, "-m", "ruff", "check", str(project_root)]
        env_vars = os.environ.copy()
        env_vars["FORCE_COLOR"] = "1"
        result = subprocess.run(ruff_cmd, capture_output=True, text=True, check=False, env=env_vars)  # noqa: S603
        ruff_output = result.stdout + result.stderr
        terminalreporter.write(ruff_output)
        if result.returncode != 0:
            error_count = self.parse_error_count(ruff_output)
            _session = terminalreporter._session  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            if _session is not None:
                _session.testsfailed += error_count

    def parse_error_count(self, output: str) -> int:
        """Parse error count."""
        found_err_patt = re.compile(r"Found (\d+?) error")
        found_err_search = found_err_patt.search(output)
        if found_err_search is None:
            err_msg = ""
            raise ValueError(err_msg)
        return int(found_err_search.group(1))

        # # A simple way to get the count without full JSON parsing if you just need the count
        # # Ruff's default output usually has a summary line at the end
        # if "found" in output and "error" in output:
        #     try:
        #         # Naive parsing of a line like "Found 12 errors."
        #         last_line = output.strip().split("\n")[-1]
        #         return int(last_line.split()[1])
        #     except (ValueError, IndexError):
        #         pass
        # return 0

    # def pytest_report_header(self, config):
    #     return ["Your Custom Plugin Status: Enabled"]


def pytest_configure(config: pytest.Config) -> None:
    """Configure."""
    if config.option.ruff:
        config.pluginmanager.register(RuffPlugin(config), name="ruff")


# print()
# print(1 / 0-)
