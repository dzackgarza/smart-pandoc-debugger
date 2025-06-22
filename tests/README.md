# Test Organization

This directory contains the test suite for the Smart Pandoc Debugger project.

## Directory Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests between components
- `functional/`: End-to-end functional tests
- `data/`: Test data and fixtures
- `error_finder/`: Tests specific to the error finder module

## Running Tests

Run all tests:
```bash
pytest
```

Run unit tests only:
```bash
pytest tests/unit
```

Run with coverage:
```bash
pytest --cov=smart_pandoc_debugger
```

## Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Place functional tests in `tests/functional/`
- Use descriptive test names that start with `test_`
- Group related tests in classes that start with `Test`

## Test Data

- Place test data files in `tests/data/`
- Use YAML for structured test data
- Keep test data files small and focused
