"""Shared pytest configuration and fixtures."""
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest

# Add the project root to the Python path to allow for absolute imports.
# This ensures that tests can import modules from `managers`, `utils`, etc.,
# as if they were being run from the project's top-level directory.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure the source directory is in the Python path
SRC_DIR = PROJECT_ROOT / 'smart_pandoc_debugger'
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
def temp_dir() -> Generator[Path, None, None]:
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


# Add any project-wide fixtures here
# Example:
# @pytest.fixture(scope="session")
# def db_connection():
#     # Setup db connection
#     yield connection
#     # Teardown db connection

# --- Tiered Testing System ---
# Test results tracking for tier dependencies
_tier_results = {}

def pytest_runtest_setup(item):
    """Hook to enforce tier dependencies before running tests."""
    # Get the tier marker from the test
    tier_marker = None
    for marker in item.iter_markers():
        if marker.name.startswith('tier'):
            tier_marker = marker
            break
    
    if tier_marker is None:
        return  # No tier marker, run normally
    
    tier_num = int(tier_marker.name.replace('tier', ''))
    
    # Check if all lower tiers have passed
    for lower_tier in range(1, tier_num):
        tier_key = f'tier{lower_tier}'
        if tier_key not in _tier_results or not _tier_results[tier_key]:
            pytest.skip(f"Skipping Tier {tier_num} test - Tier {lower_tier} tests have not all passed")

def pytest_runtest_teardown(item, nextitem):
    """Hook to track test results for tier enforcement."""
    # Get the tier marker from the test
    tier_marker = None
    for marker in item.iter_markers():
        if marker.name.startswith('tier'):
            tier_marker = marker
            break
    
    if tier_marker is None:
        return  # No tier marker, ignore
    
    tier_key = tier_marker.name
    
    # Initialize tier tracking if not exists
    if tier_key not in _tier_results:
        _tier_results[tier_key] = True
    
    # If this test failed, mark the tier as failed
    if item.session.testsfailed > _tier_results.get('_last_failure_count', 0):
        _tier_results[tier_key] = False
        _tier_results['_last_failure_count'] = item.session.testsfailed
