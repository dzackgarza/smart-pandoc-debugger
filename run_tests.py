#!/usr/bin/env python3
"""Test runner for the Smart Pandoc Debugger project."""
import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

import pytest

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_tests(
    test_type: str = 'all',
    verbose: bool = False,
    coverage: bool = False,
    parallel: bool = False,
    markers: Optional[List[str]] = None,
    test_path: Optional[str] = None
) -> int:
    """Run tests with the specified options.
    
    Args:
        test_type: Type of tests to run (unit, integration, functional, all)
        verbose: Enable verbose output
        coverage: Generate coverage report
        parallel: Run tests in parallel
        markers: List of pytest markers to include
        test_path: Specific test path to run
        
    Returns:
        int: Exit code from pytest
    """
    test_paths = {
        'unit': 'tests/unit',
        'integration': 'tests/integration',
        'functional': 'tests/functional',
        'all': 'tests'
    }
    
    if test_type not in test_paths:
        print(f"Error: Unknown test type '{test_type}'. "
              f"Must be one of: {', '.join(test_paths.keys())}")
        return 1
    
    # Build the pytest arguments
    args = []
    
    if verbose:
        args.append('-v')
    
    if coverage:
        args.extend([
            '--cov=smart_pandoc_debugger',
            '--cov-report=term-missing',
            '--cov-report=xml:coverage.xml'
        ])
    
    if parallel:
        args.extend(['-n', 'auto'])
    
    if markers:
        args.extend(['-m', ' or '.join(markers)])
    
    # Add the test path
    path = test_path or test_paths[test_type]
    args.append(str(path))
    
    print(f"Running {test_type} tests...")
    return pytest.main(args)

def main() -> int:
    """Parse command line arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run tests for Smart Pandoc Debugger')
    
    parser.add_argument(
        'test_type',
        nargs='?',
        default='all',
        help='Type of tests to run (unit, integration, functional, all)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '-c', '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '-p', '--parallel',
        action='store_true',
        help='Run tests in parallel'
    )
    
    parser.add_argument(
        '-m', '--marker',
        action='append',
        help='Only run tests matching the given marker'
    )
    
    parser.add_argument(
        'test_path',
        nargs='?',
        help='Specific test file or directory to run'
    )
    
    args = parser.parse_args()
    
    return run_tests(
        test_type=args.test_type,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel,
        markers=args.marker,
        test_path=args.test_path
    )

if __name__ == '__main__':
    sys.exit(main())
