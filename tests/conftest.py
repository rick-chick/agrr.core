"""
pytest configuration and shared fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {"key": "value", "number": 42}


@pytest.fixture
def temp_directory(tmp_path):
    """Temporary directory for testing."""
    return tmp_path
