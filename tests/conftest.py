"""Shared pytest fixtures.

This file contains fixtures available to all tests.
Add project-wide fixtures here.
"""

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir() -> Path:
    """Return the test data/fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Return a sample valid configuration dict.

    Use this as a starting point for tests that need configuration.
    Modify specific keys as needed in your tests.
    """
    return {
        "input_path": "/path/to/input",
        "output_path": "/path/to/output",
        "verbose": True,
    }
