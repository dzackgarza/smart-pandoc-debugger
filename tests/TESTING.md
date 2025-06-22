# Testing the LaTeX Error Finder

This document provides instructions for running tests and interpreting results for the LaTeX Error Finder.

## Table of Contents
- [Running Tests](#running-tests)
- [Test Types](#test-types)
- [Interpreting Results](#interpreting-results)
- [Test Maintenance](#test-maintenance)
- [Best Practices](#best-practices)

## Running Tests

### Prerequisites
- Python 3.7+
- Dependencies installed: `pip install -e .`

### Basic Test Commands

Run all tests:
```bash
pytest -v
```

Run a specific test class:
```bash
pytest -v test_error_finder_consolidated.py::TestSpecificErrorTypes
```

Run a single test:
```bash
pytest -v test_error_finder_consolidated.py::TestSpecificErrorTypes::test_undefined_reference
```

### Useful Options

Show test coverage:
```bash
pytest --cov=DEBUG_error_finder --cov-report=term-missing
```

Run tests in parallel (faster):
```bash
pytest -n auto
```

Stop on first failure:
```bash
pytest -x
```

## Test Types

1. **Basic Functionality Tests**: Verify core functionality
2. **Error Detection Tests**: Test specific error conditions
3. **Performance Tests**: Check performance characteristics
4. **Integration Tests**: Test with real-world scenarios
5. **Torture Tests**: Stress tests with complex inputs

## Interpreting Results

### Test Output
- `.` - Test passed
- `F` - Test failed
- `E` - Test raised an unexpected exception
- `s` - Test was skipped
- `x` - Test was expected to fail and did

### Common Issues

#### Test Failures
If a test fails:
1. **DO NOT** modify the test to make it pass
2. Check the error message to understand what went wrong
3. Fix the implementation in `error_finder.py`
4. Run the test again to verify the fix

#### Test File Modified Warning
If you see a warning about the test file being modified:
```
Test file has been modified. If this was intentional, update EXPECTED_TEST_FILE_HASH
```

This is a safety check to prevent accidental test modifications. If you intentionally modified tests:
1. Run: `python -c "import hashlib; print(hashlib.sha256(open('test_error_finder_consolidated.py', 'rb').read()).hexdigst())"`
2. Update the `EXPECTED_TEST_FILE_HASH` in the test file

## Test Maintenance

### Adding New Tests
1. Add new test methods to the appropriate test class
2. Update the expected test count in `test_test_count()`
3. Update the test file hash if needed

### Modifying Tests
Tests should only be modified in rare cases. If you must modify a test:
1. Get approval from the team
2. Include `[test-modification-allowed]` in your commit message
3. Update the test file hash after making changes

### Pre-commit Hook
A pre-commit hook is installed to prevent accidental test modifications. To bypass it (when necessary):
```bash
git commit -m "Your message [test-modification-allowed]"
```

## Best Practices

1. **Don't Modify Tests to Fix Failures**: Tests define expected behavior - fix the implementation instead
2. **One Assertion Per Test**: Each test should verify one specific behavior
3. **Descriptive Test Names**: Test names should clearly describe what they're testing
4. **Keep Tests Fast**: Tests should run quickly to encourage frequent testing
5. **Test Edge Cases**: Include tests for boundary conditions and error cases

## Getting Help

If you encounter issues with tests:
1. Check the test output for specific error messages
2. Run tests with `-v` for more verbose output
3. If needed, run a single test with `pdb` for debugging:
   ```bash
   pytest --pdb test_error_finder_consolidated.py::TestSpecificErrorTypes::test_name -v
   ```

Remember: The tests are the source of truth for expected behavior. When in doubt, trust the tests.
