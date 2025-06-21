#!/usr/bin/env python3
# utils/process_runner.py - V1.3.1 (Simplified, Assertion-Driven, PYTHONPATH-Aware, Logging Fix)
#
# Purpose:
#   Provides a utility for running subprocesses, primarily for SDE components
#   (services/managers or specialist tools). It relies on Python's default
#   error handling (propagating exceptions like CalledProcessError, JSONDecodeError)
#   to align with a "crash violently" development philosophy.
#   It also handles setting PYTHONPATH for the subprocess to ensure project-internal
#   imports (e.g., from `utils` by scripts in `managers` or `services`) work correctly.
#
# Design Philosophy:
#   - Uses `subprocess.run(check=True)`: Crashes (raises CalledProcessError) if the
#     called script exits with a non-zero status.
#   - `expect_json_output=True`: If set, parses stdout as JSON and returns the dict.
#     Crashes (raises JSONDecodeError or ValueError) if stdout is not valid/empty JSON.
#   - `PYTHONPATH` Modification: Calculates the project root and prepends it to the
#     `PYTHONPATH` of the subprocess, facilitating imports like `from utils.data_model import ...`
#     from scripts located in subdirectories (e.g., `managers/`, `services/`).
#   - Logging: Uses the SDE's standard logger (expected to be configured by the entry point).
#
# Usage by SDE components (e.g., Coordinator calling a Service, or a Manager calling a Specialist):
#   - `service_runner.py` (for Service-to-Service or Coordinator-to-Service):
#     This `process_runner.run_script` can be used as the underlying mechanism if
#     `service_runner.run_script` needs to call a *service* that expects/returns
#     `DiagnosticJob` JSON. `service_runner` would then handle the `DiagnosticJob`
#     Pydantic model validation.
#   - Managers calling Specialist Tools (e.g., Investigator.py calling error_finder.py):
#     This `process_runner.run_script` is ideal. The Manager would pass
#     `expect_json_output=True` if the specialist tool returns JSON.
#
# --------------------------------------------------------------------------------

import os
import sys
import json
import subprocess
import pathlib
import logging # <<< --- ADDED MISSING IMPORT ---
from typing import List, Optional, Dict, Union

# --- Logger Setup ---
# Assumes logger_utils.py or a similar mechanism has configured a logger.
# The logger instance is fetched here. If no configuration has happened upstream,
# logging might not produce visible output or use default settings.
# This is preferable to this utility trying to configure logging itself,
# as configuration should ideally happen once at the application entry point.
logger = logging.getLogger(__name__) # Uses "utils.process_runner" as logger name

# --- Project Root Calculation ---
# Assumes this script (process_runner.py) is in $PROJECT_ROOT/utils/
# This is used to set PYTHONPATH for subprocesses.
try:
    UTILS_DIR = pathlib.Path(__file__).resolve().parent
    PROJECT_ROOT_PATH = UTILS_DIR.parent
    assert PROJECT_ROOT_PATH.is_dir(), "Calculated project root is not a directory."
except Exception as e:
    logger.error(f"CRITICAL ProcessRunner Error: Could not determine project root. Subprocess PYTHONPATH may be incorrect. Error: {e}")
    PROJECT_ROOT_PATH = None


def run_script(
    command_parts: List[str],
    input_json_obj: Optional[dict] = None,
    expect_json_output: bool = False,
    timeout: Optional[int] = None,
    env_additions: Optional[Dict[str, str]] = None,
    log_prefix_for_caller: Optional[str] = None,
    set_project_pythonpath: bool = True
) -> Union[subprocess.CompletedProcess, dict]:
    """
    Runs an external script, manages JSON I/O, and sets PYTHONPATH for the subprocess.

    - If `input_json_obj` is provided, it's serialized to JSON and passed to the script's stdin.
    - Uses `subprocess.run(check=True)`, so it raises `subprocess.CalledProcessError`
      if the called script exits with a non-zero status.
    - If `expect_json_output` is `True`:
        - Parses the script's stdout as JSON.
        - Returns the parsed dictionary.
        - Raises `ValueError` if stdout is empty (but script exited 0).
        - Raises `json.JSONDecodeError` if stdout is not valid JSON.
    - If `expect_json_output` is `False` (default):
        - Returns the `subprocess.CompletedProcess` object.
    - If `set_project_pythonpath` is `True` (default) and `PROJECT_ROOT_PATH` was determined:
        - Prepends the project root directory to the `PYTHONPATH` for the subprocess.
        This allows scripts in subdirectories (e.g., `managers/`, `services/`) to
        import modules from other top-level project packages (e.g., `from utils.data_model import ...`).
    - Logs debug information based on the SDE's standard logging configuration.

    Args:
        command_parts: List of strings forming the command and its arguments
                       (e.g., `['python3', 'script.py', '--arg']`).
        input_json_obj: Optional dictionary to be serialized to JSON and passed to stdin.
        expect_json_output: If True, expects stdout to be JSON and returns a parsed dict.
                            Otherwise, returns the CompletedProcess object.
        timeout: Optional timeout in seconds for the subprocess.
        env_additions: Optional dictionary of environment variables to add/override for the subprocess.
        log_prefix_for_caller: Optional prefix for log messages to identify the caller.
        set_project_pythonpath: If True, modifies PYTHONPATH for the subprocess.

    Returns:
        If `expect_json_output` is True, a `dict` parsed from the script's stdout.
        Otherwise, a `subprocess.CompletedProcess` object.

    Raises:
        subprocess.CalledProcessError: If the script exits with a non-zero status.
        json.JSONDecodeError: If `expect_json_output` is True and stdout is not valid JSON.
        ValueError: If `expect_json_output` is True and stdout is empty after successful run.
        FileNotFoundError: If the command in `command_parts` is not found.
        subprocess.TimeoutExpired: If the timeout is reached.
        TypeError: If `input_json_obj` is not JSON-serializable.
    """
    caller_name = log_prefix_for_caller or \
                  (os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "ProcessRunnerCaller")
    
    input_str_for_subprocess: Optional[str] = None
    if input_json_obj is not None:
        input_str_for_subprocess = json.dumps(input_json_obj)

    effective_env = os.environ.copy()
    if env_additions:
        effective_env.update(env_additions)

    if set_project_pythonpath and PROJECT_ROOT_PATH:
        project_root_str = str(PROJECT_ROOT_PATH)
        if "PYTHONPATH" in effective_env:
            effective_env["PYTHONPATH"] = project_root_str + os.pathsep + effective_env["PYTHONPATH"]
        else:
            effective_env["PYTHONPATH"] = project_root_str
        logger.debug(f"[{caller_name}] Setting PYTHONPATH for '{command_parts[0]}' to: {effective_env['PYTHONPATH']}")
    elif set_project_pythonpath and not PROJECT_ROOT_PATH:
        logger.warning(f"[{caller_name}] Wanted to set project PYTHONPATH for '{command_parts[0]}' but project root could not be determined.")


    logger.debug(f"[{caller_name}] Running command: {' '.join(command_parts)}")
    if input_str_for_subprocess:
        logger.debug(f"[{caller_name}]   Input JSON (first 100 chars): {input_str_for_subprocess[:100]}"
                     f"{'...' if len(input_str_for_subprocess) > 100 else ''}")

    proc = subprocess.run(
        command_parts,
        input=input_str_for_subprocess,
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=True,
        env=effective_env,
        timeout=timeout
    )

    logger.debug(f"[{caller_name}]   Command '{os.path.basename(command_parts[0])}' SUCCEEDED (rc=0)")
    
    if proc.stdout and proc.stdout.strip():
        logger.debug(f"[{caller_name}]   Stdout (first 100 chars): {proc.stdout.strip()[:100]}"
                     f"{'...' if len(proc.stdout.strip()) > 100 else ''}")
    else:
        logger.debug(f"[{caller_name}]   Stdout: (empty or whitespace only)")
        
    if proc.stderr and proc.stderr.strip():
        logger.info(f"[{caller_name}]   Stderr from '{os.path.basename(command_parts[0])}' (rc=0) "
                    f"(first 200 chars): {proc.stderr.strip()[:200]}"
                    f"{'...' if len(proc.stderr.strip()) > 200 else ''}")

    if expect_json_output:
        if not proc.stdout or not proc.stdout.strip():
            error_msg = (f"Component '{' '.join(command_parts)}' contract violation: "
                         f"expected JSON output from stdout, but got empty or whitespace-only stdout (script exited 0).")
            logger.error(f"[{caller_name}] {error_msg}")
            raise ValueError(error_msg)
        
        try:
            parsed_output: dict = json.loads(proc.stdout)
            logger.debug(f"[{caller_name}]   Successfully parsed JSON output from '{os.path.basename(command_parts[0])}'.")
            return parsed_output
        except json.JSONDecodeError as e:
            error_msg = (f"Component '{' '.join(command_parts)}' contract violation: "
                         f"failed to decode JSON from stdout. Error: {e}. "
                         f"Stdout (first 500 chars): {proc.stdout.strip()[:500]}...")
            logger.error(f"[{caller_name}] {error_msg}")
            raise
    
    return proc

# No if __name__ == "__main__": block.
