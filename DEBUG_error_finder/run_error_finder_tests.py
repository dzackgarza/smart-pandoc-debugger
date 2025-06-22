#!/usr/bin/env python3
"""
Direct test runner for error_finder.py
"""

import sys
import os
import unittest
from unittest.mock import patch, mock_open

# Add the project root to the Python path so we can import the managers
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from managers.investigator_team.error_finder import find_primary_error


class TestErrorFinder(unittest.TestCase):
    def test_missing_math_delimiters_simple(self):
        """Test detection of missing math delimiters in simple equations."""
        log = "! Missing $ inserted."
        result = find_primary_error(log)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISSING_DOLLAR')
        self.assertIn('Missing $ inserted', result.get('raw_error_message', ''))
    
    def test_undefined_control_sequence(self):
        """Test detection of undefined control sequences."""
        log = "! Undefined control sequence.\\nl.6 \\nonexistentcommand"
        result = find_primary_error(log)
        self.assertEqual(result.get('error_signature'), 'LATEX_UNDEFINED_CONTROL_SEQUENCE')
    
    def test_mismatched_delimiters_basic(self):
        """Test detection of basic mismatched delimiters."""
        log = "! Missing $ inserted.\\nl.6 \\left(\\frac{a}{b}\\right]"
        result = find_primary_error(log)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISMATCHED_DELIMITERS')
    
    def test_unbalanced_braces_simple(self):
        """Test detection of simple unbalanced braces."""
        log = "! Missing } inserted.\\nl.6 f(x) = \\frac{1}{1 + e^{-x}}"
        result = find_primary_error(log)
        self.assertEqual(result.get('error_signature'), 'LATEX_UNBALANCED_BRACES')
    
    def test_compilation_success(self):
        """Test successful compilation detection."""
        log = "Output written on test.pdf (1 page, 12345 bytes)."
        result = find_primary_error(log)
        self.assertEqual(result.get('error_signature'), 'LATEX_COMPILATION_SUCCESSFUL')

if __name__ == '__main__':
    unittest.main(verbosity=2)
