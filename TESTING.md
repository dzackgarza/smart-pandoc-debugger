# Testing the Smart Diagnostic Engine

This document outlines the structure of the test suite and how to add new tests.

## Test Suite Structure

The test suite uses `pytest` as its primary framework and runner. Tests are organized within the `tests/` directory at the root of the project.

The main categories for tests are:

*   **`tests/e2e/`**: End-to-end tests.
    *   These tests are designed to check the complete workflow of the Smart Diagnostic Engine (SDE) by invoking its main entry point (e.g., the `smart-pandoc-debugger` executable or `run_intake.sh` script) with various Markdown inputs.
    *   They verify the final output or behavior of the system as a whole.
    *   Input Markdown files for E2E tests can be stored in `tests/e2e/test_cases/`.
*   **`tests/integration/`**: Integration tests.
    *   These tests focus on the interaction between different components or modules of the SDE (e.g., how `Coordinator.py` orchestrates the `Manager` modules).
    *   They mock fewer parts than unit tests but don't necessarily run the entire application from the command line.
*   **`tests/unit/`**: Unit tests.
    *   These tests are for testing individual Python modules, classes, or functions in isolation.
    *   Subdirectories exist for different parts of the application:
        *   `tests/unit/managers/`: For core Manager modules (`Miner.py`, `Investigator.py`, etc.) and their specialist teams (`investigator_team/`, `miner_team/`, etc.).
        *   `tests/unit/scripts/`: For top-level scripts like `intake.py` and `coordinator.py`.
        *   `tests/unit/utils/`: For shared utility modules (`data_model.py`, `process_runner.py`, etc.).

## Running Tests

1.  **Install Dependencies:**
    Ensure `pytest` and other testing-related dependencies (like `pytest-mock`, `pydantic`, `pyyaml`) are installed. These can typically be installed via pip:
    ```bash
    pip install pytest pytest-mock pydantic pyyaml
    ```
    (Refer to `requirements.txt` or `pyproject.toml` if they exist for a full list of project dependencies).

2.  **Run All Tests:**
    Navigate to the root directory of the project and run:
    ```bash
    pytest
    ```
    For more verbose output:
    ```bash
    pytest -v
    ```

3.  **Run Specific Tests:**
    *   Run tests in a specific file: `pytest tests/unit/utils/test_data_model.py`
    *   Run a specific test class: `pytest tests/unit/utils/test_data_model.py::TestDiagnosticJob` (if classes were used)
    *   Run a specific test function: `pytest tests/unit/utils/test_data_model.py::test_diagnosticjob_creation_minimal`
    *   **Run tests by level/marker:** Tests can be marked with levels (e.g., `@pytest.mark.level1`, `@pytest.mark.level2`). To run all tests of a specific level:
        ```bash
        pytest -m level1
        ```
        If any `level1` tests (or tests of any specified marker) fail, `pytest` will provide a detailed error summary and exit with a non-zero status code, clearly indicating the failure of these critical tests.

## Adding New Tests

1.  **Determine Test Type:** Decide if your test is E2E, integration, or unit.
2.  **Choose/Create File:**
    *   Place your test in an existing relevant file (e.g., unit tests for `Miner.py` go into `tests/unit/managers/test_miner.py`).
    *   If testing a new module or a new category of interaction, create a new file named `test_*.py` (e.g., `test_new_feature.py`) in the appropriate directory.
3.  **Write Test Functions:**
    *   Test function names **must** start with `test_`.
    *   Use standard `pytest` conventions (e.g., `assert` statements for checks).
    *   Use fixtures (defined in the test file itself or in `conftest.py`) for setting up test data or mock objects. Example:
        ```python
        import pytest
        from utils.data_model import YourModel # Example import

        @pytest.fixture
        def sample_model_instance():
            return YourModel(param1="value1", param2=123) # Ensure all required fields for YourModel are provided

        @pytest.mark.level1 # Example marker
        def test_your_functionality(sample_model_instance):
            # result = your_module.your_function(sample_model_instance)
            # assert result == "expected_value"
            pass # Placeholder for actual test logic
        ```
4.  **Naming Conventions:**
    *   Test files: `test_*.py` or `*_test.py`.
    *   Test functions: `test_*`.
    *   Test classes (if used): `Test*` or `*Tests`.
5.  **Markers:**
    *   Use markers like `@pytest.mark.level1`, `@pytest.mark.level2`, etc., to categorize tests by importance or type, as discussed with the team.
    *   Register custom markers in `pytest.ini` to avoid warnings:
        ```ini
        [pytest]
        markers =
            level1: Critical pipeline tests (e.g., no crash on simple valid doc)
            level2: Basic error feedback tests
            # Add other markers as needed
        ```

## Configuration

*   `pytest.ini`: Located in the project root, this file configures `pytest` discovery paths, file/class/function matching patterns, and custom markers.
*   `conftest.py`: Also in the project root, this file is used for project-wide fixtures and hook implementations. Currently, it adds the project root to `sys.path` to ensure application modules are importable by tests.

## Existing Test Scripts

The older bash-based test scripts (`test` and `h1_tests.sh`) still exist but the goal is to gradually migrate their functionality or cover their scenarios within the `pytest` framework, especially under `tests/e2e/`.
