"""Test utilities and helpers."""
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Type, TypeVar, Union

import yaml

T = TypeVar('T')

def load_test_data(filename: str, data_type: Type[T] = dict) -> T:
    """Load test data from a YAML or JSON file.
    
    Args:
        filename: Name of the file in the test data directory.
        data_type: Expected return type (dict, list, etc.).
        
    Returns:
        The loaded data in the specified type.
    """
    path = Path(__file__).parent / 'data' / filename
    suffix = path.suffix.lower()
    
    with open(path, 'r', encoding='utf-8') as f:
        if suffix in ('.yaml', '.yml'):
            data = yaml.safe_load(f)
        elif suffix == '.json':
            data = json.load(f)
        else:
            raise ValueError(f'Unsupported file type: {suffix}')
    
    if not isinstance(data, data_type):
        raise ValueError(f'Expected {data_type}, got {type(data)}')
    
    return data


def assert_error_message_contains(
    error: Exception,
    expected_messages: Union[str, list[str]],
    partial: bool = True
) -> None:
    """Assert that an error message contains expected text.
    
    Args:
        error: The exception that was raised.
        expected_messages: String or list of strings to look for in the error message.
        partial: If True, check if message contains the text (default).
                If False, check for exact match.
    """
    if isinstance(expected_messages, str):
        expected_messages = [expected_messages]
    
    error_message = str(error)
    
    for msg in expected_messages:
        if partial:
            assert msg in error_message, f'"{msg}" not found in error message: {error_message}'
        else:
            assert msg == error_message, f'Expected "{msg}", got "{error_message}"'


@contextmanager
tempfile_context = tempfile.NamedTemporaryFile


def create_temp_file(
    content: str = '',
    suffix: str = '.txt',
    dir: Optional[Union[str, Path]] = None
) -> Generator[Path, None, None]:
    """Create a temporary file with the given content.
    
    Args:
        content: Content to write to the file.
        suffix: File suffix.
        dir: Directory to create the file in. If None, uses system temp dir.
        
    Yields:
        Path to the created temporary file.
    """
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix=suffix,
        dir=str(dir) if dir else None,
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        yield temp_path
    finally:
        if temp_path.exists():
            temp_path.unlink()


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in a string for comparison."""
    return re.sub(r'\s+', ' ', text).strip()
