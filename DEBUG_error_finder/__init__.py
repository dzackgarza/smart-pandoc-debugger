"""
DEBUG_error_finder - A consolidated testing framework for error_finder.py

This package contains tests and utilities for testing LaTeX error detection.
"""

# Make the main function available at package level
from .error_finder import find_primary_error, main

__version__ = "0.1.0"
__all__ = ['find_primary_error', 'main']
