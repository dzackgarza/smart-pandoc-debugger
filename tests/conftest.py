"""Shared pytest configuration and fixtures."""
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / 'smart_pandoc_debugger'

# Ensure the source directory is in the Python path
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# --- Fixtures ---

@pytest.fixture(scope='session')
def test_data_dir() -> Path:
    """Return the path to the test data directory."""
    return PROJECT_ROOT / 'tests' / 'data'


@pytest.fixture(scope='session')
def sample_data() -> Dict[str, Any]:
    """Load sample test data."""
    # This can be extended to load specific test data files
    return {}


@pytest.fixture
temp_dir() -> Generator[Path, None, None]:
    """Create and return a temporary directory that's cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_environment(monkeypatch):
    """Fixture to mock environment variables."""
    env_vars = {}
    
    def set_env(name: str, value: str) -> None:
        env_vars[name] = value
        monkeypatch.setenv(name, value)
    
    def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
        return env_vars.get(name, default)
    
    return set_env, get_env


@pytest.fixture(autouse=True)
def _setup_logging():
    """Setup logging for tests."""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    # Disable logging for tests by default
    logging.disable(logging.CRITICAL)


# Import any common fixtures from the error_finder test directory
try:
    from tests.error_finder.conftest import *  # noqa: F403, F401
except ImportError:
    pass
