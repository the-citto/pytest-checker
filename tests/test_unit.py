"""Test unit."""

from __future__ import annotations

import importlib.metadata
import typing
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest

if typing.TYPE_CHECKING:
    import pytest_mock


# Import the code from your plugin file (adjust 'your_plugin_file' as needed)
from pytest_checkers import checkers


def test_pytest_addoption(mocker: pytest_mock.MockerFixture) -> None:
    """Test that options are added only for installed packages."""
    mocker.patch.object(checkers, "added_options", [])

    with patch("importlib.metadata.version") as mock_version:

        def side_effect(tool_name: str) -> str:
            if tool_name == "flake8":
                return "1.0.0"
            # Simulate 'ruff' also being installed
            if tool_name == "ruff":
                return "1.0.0"
            raise importlib.metadata.PackageNotFoundError

        mock_version.side_effect = side_effect

        # Mock the Parser object. We rely on the mock to capture calls to getgroup/addoption
        mock_parser = MagicMock(spec=pytest.Parser)
        mock_group = MagicMock()
        mock_parser.getgroup.return_value = mock_group

        # Call the function under test
        checkers.pytest_addoption(mock_parser)  # ty: ignore[invalid-argument-type]

        # --- FIX: Assert on exact string values, not typing.Any ---
        # The function calls addoption with static strings/actions defined in the code
        expected_flake8_call = mocker.call("--flake8", action="store_true", help="Enable `flake8`")
        expected_ruff_call = mocker.call("--ruff", action="store_true", help="Enable `ruff check`")

        mock_group.addoption.assert_has_calls([expected_flake8_call, expected_ruff_call], any_order=True)

        # Check that 'flake8' and 'ruff' were added to the added_options list
        assert "flake8" in checkers.added_options
        assert "ruff" in checkers.added_options
        # Ensure tools that threw PackageNotFoundError are not in the list
        assert "black" not in checkers.added_options


def test_pytest_configure_checkers_all(mocker: pytest_mock.MockerFixture) -> None:
    """Test that --checkers enables all available options."""
    mock_config = mocker.Mock()

    # We must ensure the nested 'pluginmanager.register' path works
    mock_register = mock_config.pluginmanager.register

    mock_config.option = mocker.Mock()
    # Simulate that the user provided --checkers=True on the CLI
    mock_config.option.checkers = True

    # Simulate that 'flake8' and 'isort' were the added_options
    mocker.patch.object(checkers, "added_options", ["flake8", "isort"])

    # Call the function under test
    checkers.pytest_configure(mock_config)

    # Verify that both plugins were activated because --checkers was set
    assert mock_config.option.flake8 is True
    assert mock_config.option.isort is True

    # Verify registration happened
    assert mock_register.call_count == 2
    mock_register.assert_any_call(mocker.ANY, name="flake8")
    mock_register.assert_any_call(mocker.ANY, name="isort")


def test_checkers_plugin_properties() -> None:
    """Test abstract base class properties."""
    # Create a mock config object
    mock_config = MagicMock(spec=pytest.Config)

    # Create a concrete mock class inheriting from CheckersPlugin to test abstract methods
    class MockCheckPlugin(checkers.CheckersPlugin):
        tool: checkers.Tool = "black"
        header_markup: checkers.EscTable = "cyan"

        @property
        def cmd_flags(self) -> list[str]:
            return ["--mock-flag"]

    plugin_instance = MockCheckPlugin(mock_config)  # ty: ignore[invalid-argument-type]
    # Test cmd_flags abstract property implementation
    assert plugin_instance.cmd_flags == ["--mock-flag"]
    # Test default is_error implementation (based on returncode)
    plugin_instance.cmd_returncode = 0
    assert plugin_instance.is_error is False
    plugin_instance.cmd_returncode = 1
    assert plugin_instance.is_error is True
    # Test env_vars property
    env = plugin_instance.env_vars
    assert "FORCE_COLOR" in env
    assert env["FORCE_COLOR"] == "1"
    assert "MYPY_FORCE_COLOR" in env
    assert env["MYPY_FORCE_COLOR"] == "1"


def test_black_plugin_is_error_logic() -> None:
    """Test Black specific error logic based on output content."""
    mock_config = MagicMock(spec=pytest.Config)
    plugin = checkers.BlackPlugin(mock_config)  # ty: ignore[invalid-argument-type]
    plugin.cmd_output = ""
    plugin.cmd_returncode = 0  # Default logic would say no error
    assert plugin.is_error is False  # Black logic overrides to check output
    plugin.cmd_output = "@@ code change @@"
    assert plugin.is_error is True
    plugin.cmd_output = "black fail to reformat a file"
    assert plugin.is_error is True


def test_isort_plugin_is_error_logic() -> None:
    """Test Isort specific error logic based on output content."""
    mock_config = MagicMock(spec=pytest.Config)
    plugin = checkers.IsortPlugin(mock_config)  # ty: ignore[invalid-argument-type]
    plugin.cmd_output = ""
    assert plugin.is_error is False
    plugin.cmd_output = "@@ import change @@"
    assert plugin.is_error is True
