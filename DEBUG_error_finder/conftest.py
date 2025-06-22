"""Pytest configuration and fixtures for error_finder tests."""

import pytest
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging for tests
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common fixtures can be defined here and will be automatically discovered by pytest
