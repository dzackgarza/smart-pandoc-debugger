"""Example unit tests for the Smart Pandoc Debugger."""
import pytest

from tests.base import BaseUnitTest


class TestExample(BaseUnitTest):
    """Example test class demonstrating the testing framework."""
    
    def test_example(self):
        """Example test case."""
        assert 1 + 1 == 2
    
    @pytest.mark.parametrize('a,b,expected', [
        (1, 1, 2),
        (2, 3, 5),
        (0, 0, 0),
    ])
    def test_addition(self, a, b, expected):
        """Test addition with multiple test cases."""
        assert a + b == expected
    
    def test_with_fixture(self, tmp_path):
        """Test using a pytest fixture."""
        test_file = tmp_path / 'test.txt'
        test_file.write_text('test content')
        assert test_file.read_text() == 'test content'


@pytest.mark.slow
def test_slow():
    """Marked as a slow test."""
    # This test would be skipped with `pytest -m "not slow"`
    assert True
