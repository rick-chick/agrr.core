"""
Basic tests for agrr.core package.
"""
import pytest
from agrr.core import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_import():
    """Test that package can be imported."""
    import agrr.core
    assert hasattr(agrr.core, "__version__")


@pytest.mark.parametrize("test_input,expected", [
    (1, 1),
    (2, 2),
    (3, 3),
])
def test_parametrized(test_input, expected):
    """Example parametrized test."""
    assert test_input == expected


@pytest.mark.slow
def test_slow_operation():
    """Example slow test that can be skipped."""
    import time
    time.sleep(0.1)  # Simulate slow operation
    assert True
