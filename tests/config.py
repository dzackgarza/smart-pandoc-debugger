"""Test configuration and constants."""
from pathlib import Path

# Test directories
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / 'data'

# Test file paths
SAMPLE_CONFIG_FILE = TEST_DATA_DIR / 'config.yaml'
SAMPLE_INPUT_FILE = TEST_DATA_DIR / 'input.md'
SAMPLE_OUTPUT_FILE = TEST_DATA_DIR / 'output.html'

# Test constants
TEST_TIMEOUT = 30  # seconds
MAX_TEST_RETRIES = 3

# Test markers
SLOW_TEST = 'slow'
INTEGRATION_TEST = 'integration'
FUNCTIONAL_TEST = 'functional'

# Test categories
TEST_CATEGORIES = {
    'unit': 'Unit tests',
    'integration': 'Integration tests',
    'functional': 'Functional tests',
    'all': 'All tests'
}

def get_test_category(category: str) -> str:
    """Get the display name for a test category."""
    return TEST_CATEGORIES.get(category.lower(), f'Unknown category: {category}')
