"""Test utilities for the test suite."""
import os
import unittest
from pathlib import Path


class TestBase(unittest.TestCase):
    """Base test class with common setup and teardown."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            for f in self.test_dir.glob("*"):
                f.unlink()
            self.test_dir.rmdir()

    def assertFileExists(self, path):
        """Assert that a file exists."""
        self.assertTrue(Path(path).exists(), f"File {path} does not exist")

    def assertFileNotExists(self, path):
        """Assert that a file does not exist."""
        self.assertFalse(Path(path).exists(), f"File {path} exists but should not")
