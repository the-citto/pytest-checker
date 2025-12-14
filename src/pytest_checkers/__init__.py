"""Init."""

from __future__ import annotations

import importlib.metadata

__version__ = importlib.metadata.version(__name__)


# Tool = typing.Literal["black", "flake8", "isort", "mypy", "pyright", "ruff", "ty"]
# EscTable = typing.Literal[
#     "black",
#     "red",
#     "green",
#     "yellow",
#     "blue",
#     "purple",
#     "cyan",
#     "white",
#     "Black",
#     "Red",
#     "Green",
#     "Yellow",
#     "Blue",
#     "Purple",
#     "Cyan",
#     "White",
#     "bold",
#     "light",
#     "blink",
#     "invert",
# ]
#
#
# def _conditional_addoption(
#     group: pytest.OptionGroup,
#     /,
#     *,
#     tool: Tool,
#     help_: str,
#     action: str = "store_true",
# ) -> None:
#     with contextlib.suppress(importlib.metadata.PackageNotFoundError):
#         _ = importlib.metadata.version(tool)
#         group.addoption(f"--{tool}", action=action, help=help_)
#
#
# def pytest_addoption(parser: pytest.Parser) -> None:
#     """Set hooks."""
#     group = parser.getgroup("checkers")
#     _conditional_addoption(group, tool="ruff", help_="Enable `ruff check`.")
#     _conditional_addoption(group, tool="black", help_="Enable `black --diff`.")
#
#
# def pytest_configure(config: pytest.Config) -> None:
#     """Configure."""
#     if getattr(config.option, "ruff", False):
#         config.pluginmanager.register(RuffPlugin(config), name="ruff")
#     if getattr(config.option, "black", False):
#         config.pluginmanager.register(BlackPlugin(config), name="black")
#
#
# class CheckersPlugin(abc.ABC):
#     """Abstract checkers plugin."""
#
#     tool: Tool
#     header_markup: EscTable
#     cmd_output: str = ""
#     cmd_returncode: int = 0
#
#     def __init__(self, config: pytest.Config) -> None:
#         """Init."""
#         self.config = config
#
#     @property
#     @abc.abstractmethod
#     def cmd_flags(self) -> list[str]:
#         """Command flags."""
#
#     @property
#     @abc.abstractmethod
#     def env_vars(self) -> dict[str, str]:
#         """Environment variables."""
#         return os.environ.copy()
#
#     @property
#     @abc.abstractmethod
#     def is_error(self) -> bool:
#         """Tool-specific error logic."""
#         return self.cmd_returncode != 0
#
#     def append_error(self, session: pytest.Session) -> None:
#         """Append error."""
#         project_root = session.config.rootpath
#         nodeid = f"{self.tool} check"
#         report = TestReport(
#             nodeid=nodeid,
#             location=(str(project_root), 0, nodeid),
#             keywords={nodeid: 1},
#             when="call",
#             longrepr=(f"{self.tool.title()} Failure", 0, "Code quality checks failed. See output above."),
#             sections=[(f"{self.tool.title()} Output", self.cmd_output)],
#             outcome="failed",
#         )
#         reporter = session.config.pluginmanager.get_plugin("terminalreporter")
#         if reporter:
#             reporter.stats.setdefault("failed", []).append(report)
#
#     def pytest_sessionfinish(self, session: pytest.Session) -> None:
#         """Pytest session finish."""
#         if not getattr(self.config.option, self.tool, False):
#             return
#         project_root = session.config.rootpath
#         cmd = [sys.executable, "-m", self.tool, *self.cmd_flags, str(project_root)]
#         result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=self.env_vars)
#         self.cmd_output = result.stdout + result.stderr
#         self.cmd_returncode = result.returncode
#         if self.is_error:
#             self.append_error(session)
#
#     def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
#         """Pytest terminal summary."""
#         if not getattr(self.config.option, self.tool, False):
#             return
#         # circumventing mypy quirk - https://github.com/python/mypy/issues/10023
#         header_markup_kwarg = {typing.cast("str", self.header_markup): True}
#         terminalreporter.write_sep(title=f"tests {self.tool}", sep="=", **header_markup_kwarg)
#         terminalreporter.write(self.cmd_output)
#
#
# class BlackPlugin(CheckersPlugin):
#     """Black plugin."""
#
#     tool = "black"
#     header_markup = "cyan"
#
#     @property
#     def cmd_flags(self) -> list[str]:
#         """Command flags."""
#         return ["--diff", "."]
#
#     @property
#     def env_vars(self) -> dict[str, str]:
#         """Environment variables."""
#         return super().env_vars
#
#     @property
#     def is_error(self) -> bool:
#         """Tool-specific error logic."""
#         return "+++" in self.cmd_output
#
#
# class RuffPlugin(CheckersPlugin):
#     """Ruff plugin."""
#
#     tool = "ruff"
#     header_markup = "purple"
#
#     @property
#     def cmd_flags(self) -> list[str]:
#         """Command flags."""
#         return ["check", "."]
#
#     @property
#     def env_vars(self) -> dict[str, str]:
#         """Environment variables."""
#         env_vars = super().env_vars
#         env_vars["FORCE_COLOR"] = "1"
#         return env_vars
#
#     @property
#     def is_error(self) -> bool:
#         """Tool-specific error logic."""
#         return super().is_error
