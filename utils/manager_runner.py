#!/usr/bin/env python3
# utils/manager_runner.py
"""
Manager Runner Utility - "Crash Violently" Development Version

This module provides the `run_manager` function, designed for early
development of the SDE. It prioritizes immediate and loud failure (via
Assertions or direct Python errors) when contracts are violated,
rather than graceful error handling.

Design Philosophy:
  - All preconditions and postconditions are checked with `assert`.
  - No `try/except` blocks for operational errors (e.g., file not found,
    JSON errors, subprocess failures). Let Python raise raw errors.
  - If `DiagnosticJob` or other critical imports fail, the script fails at import.
  - Modifies `PYTHONPATH` for the subprocess to ensure Manager scripts can
    find the `utils` package.

Manager Script Contract (assumed by this runner):
  - Invoked with `python3 <manager_script_path> --process-job`.
  - Reads a single JSON string (a `DiagnosticJob`) from stdin.
  - Writes a single JSON string (the updated `DiagnosticJob`) to stdout.
  - Exits 0 on success.
  - Exits non-zero on failure (this runner will assert returncode is 0).
  - Can import modules from the project's `utils` package (e.g., `from utils.data_model import ...`)
    due to `PYTHONPATH` adjustment by this runner.
"""

import subprocess
import json
import logging
import os
import sys # Often useful in utils, though not strictly required by current functionality

# --- Critical Imports: Fail loudly at import time if these are missing ---
# This assumes manager_runner.py is part of the 'utils' package,
# and data_model.py is a sibling module within 'utils'.
from .data_model import DiagnosticJob # If this fails, the whole module is unusable.

# Standard Python logger. Configuration is expected from the calling environment.
logger = logging.getLogger(__name__)


def run_manager(manager_script_path: str, diagnostic_job_model: DiagnosticJob) -> DiagnosticJob:
    """
    Runs a specified SDE Manager script, relying on assertions for contract checks.

    Serializes `DiagnosticJob` to JSON, executes the Manager script as a subprocess
    (passing JSON via stdin), captures output, and deserializes stdout JSON back
    into an updated `DiagnosticJob`. Crashes via AssertionError or direct Python
    errors if any part of the contract is violated.

    Crucially, this function calculates the project's root directory and prepends it
    to the `PYTHONPATH` for the executed subprocess. This allows the Manager
    scripts (e.g., those in the `managers/` directory) to reliably import modules
    from the project's `utils/` package (e.g., `from utils.data_model import DiagnosticJob`).

    Args:
        manager_script_path: Path to the Python Manager script.
        diagnostic_job_model: The Pydantic `DiagnosticJob` model instance.

    Returns:
        An updated `DiagnosticJob` Pydantic model instance from the Manager.

    Raises:
        AssertionError: If any explicitly checked contract/assumption fails.
        FileNotFoundError: If `python3` or `manager_script_path` is not found by subprocess.
        json.JSONDecodeError: If Manager output is not valid JSON.
        pydantic.ValidationError: If Manager output JSON does not match `DiagnosticJob` model.
        (Other standard Python errors may also propagate directly).
    """
    assert os.path.isfile(manager_script_path), \
        f"Assertion Failed: Manager script not found or is not a file: {manager_script_path}"

    command = ["python3", manager_script_path, "--process-job"]

    # If model_dump_json fails (e.g., Pydantic error), let it crash.
    job_json_input = diagnostic_job_model.model_dump_json()

    logger.debug(f"Running Manager: {' '.join(command)}")
    log_input_snippet = job_json_input[:500] + ("..." if len(job_json_input) > 500 else "")
    logger.debug(f"Input DiagnosticJob JSON (snippet for {manager_script_path}):\n{log_input_snippet}")

    # --- Add Project Root to PYTHONPATH for the subprocess ---
    # Calculate project root: directory containing the 'utils' directory (parent of this script's dir)
    # Assumes this script (manager_runner.py) is in $PROJECT_ROOT/utils/
    current_script_dir = os.path.dirname(os.path.abspath(__file__)) # $PROJECT_ROOT/utils
    project_root = os.path.dirname(current_script_dir) # $PROJECT_ROOT
    
    # Get current environment, make a copy to modify
    env = os.environ.copy()
    
    # Prepend project_root to PYTHONPATH, or set it if it doesn't exist
    # This allows Manager scripts in (e.g.) managers/ to find the utils/ package
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = project_root + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = project_root
    
    logger.debug(f"Manager subprocess PYTHONPATH for '{manager_script_path}' will be: {env.get('PYTHONPATH')}")
    # --- End PYTHONPATH modification ---

    # If subprocess.run fails at OS level (e.g., python3 not found), let it crash.
    process = subprocess.run(
        command,
        input=job_json_input.encode('utf-8'),
        capture_output=True,
        check=False,  # We will assert the returncode explicitly.
        env=env       # Pass the modified environment to the subprocess
    )

    stdout_str = process.stdout.decode('utf-8').strip()
    stderr_str = process.stderr.decode('utf-8').strip()

    logger.debug(f"Manager {manager_script_path} exited with RC: {process.returncode}")
    if stdout_str:
        log_output_snippet = stdout_str[:500] + ("..." if len(stdout_str) > 500 else "")
        logger.debug(f"Manager {manager_script_path} STDOUT (snippet):\n{log_output_snippet}")
    if stderr_str: # Still log stderr as it's useful for debugging assertion failures.
        logger.info(f"Manager {manager_script_path} STDERR:\n{stderr_str}")

    assert process.returncode == 0, \
        f"Assertion Failed: Manager script '{manager_script_path}' crashed or reported an error. " \
        f"RC: {process.returncode}\nStderr:\n{stderr_str}"

    assert stdout_str, \
        f"Assertion Failed: Manager script '{manager_script_path}' returned empty stdout. " \
        f"Expected a JSON DiagnosticJob string."

    # If JSON decoding or Pydantic validation fails, let them crash.
    updated_job_model = DiagnosticJob.model_validate_json(stdout_str)
    
    logger.debug(f"Successfully deserialized and validated DiagnosticJob from {manager_script_path} stdout.")
    return updated_job_model

# No __main__ block for tests in this version.
# This file is intended to be used as a module only.
