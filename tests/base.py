"""Base test classes and utilities for all test types."""
import unittest
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

class BaseTestCase(unittest.TestCase):
    """Base test case with common assertions and utilities."""
    
    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level test fixtures."""
        cls.test_data_dir = Path(__file__).parent / 'data'
    
    def assertDictContainsSubset(
        self, 
        subset: Dict[Any, Any], 
        dictionary: Dict[Any, Any],
        msg: Optional[str] = None
    ) -> None:
        """Assert that all key-value pairs in subset exist in dictionary."""
        if not msg:
            msg = f"{subset} not found in {dictionary}"
        self.assertTrue(
            all(item in dictionary.items() for item in subset.items()),
            msg=msg
        )


class BaseUnitTest(BaseTestCase):
    """Base class for unit tests."""
    
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        """Setup for all unit tests."""
        self.tmp_path = tmp_path


class BaseIntegrationTest(BaseTestCase):
    """Base class for integration tests."""
    
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path_factory):
        """Setup for all integration tests."""
        self.tmp_path = tmp_path_factory.mktemp("integration")


class BaseFunctionalTest(BaseTestCase):
    """Base class for functional tests."""
    
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path_factory):
        """Setup for all functional tests."""
        self.tmp_path = tmp_path_factory.mktemp("functional")
