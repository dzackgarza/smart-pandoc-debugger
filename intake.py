#!/usr/bin/env python3
# intake.py — SDE V5.1: Diagnostic Job Intake and Coordinator Invoker
#
# Version: 5.1.0 (corresponds to SDE V5.1 Design)
# Date: 2025-06-25 (Placeholder, based on design doc)
# Author: Smart Diagnostic Engine Team
#
# Philosophy for this version (aligned with SDE V5.1):
#   - Acts as the primary user-facing entry point for the Smart Diagnostic Engine (SDE).
#   - Captures user input (Markdown document via stdin).
#   - Initializes a "DiagnosticJob" JSON object, which is the central evolving payload
#     for the entire diagnostic pipeline. This object includes the Markdown content,
#     a unique case ID, and a creation timestamp, among other fields.
#   - Invokes the Python-based `Coordinator.py` script (the main orchestrator).
#   - Pipes the initial DiagnosticJob JSON to `Coordinator.py`'s stdin.
#   - Ensures `PYTHONPATH` includes the project root for `Coordinator.py` to resolve
#     its modules (like `data_models.py`, `service_runner.py`, etc.).
#   - Relays the final diagnostic report summary (from `Coordinator.py`'s stdout) to the user.
#   - Exits with the status code provided by `Coordinator.py`.
#
# ────────────────────────────────────────────────────────────────────────────────
# Role: THE INTAKE CLERK & LAUNCHER (SDE V5.1)
#
# This script is the main user-facing entry point. Its responsibilities are primarily
# logistical:
#   1. Read Markdown content from stdin.
#   2. Generate a unique case ID and timestamp.
#   3. Construct the initial `DiagnosticJob` JSON object as defined by the SDE V5.1
#      data model (see `data_models.py`).
#   4. Prepare the environment for `Coordinator.py` (e.g., `PYTHONPATH`, `DEBUG` flag).
#   5. Invoke `Coordinator.py`, passing the `DiagnosticJob` JSON.
#   6. Forward `Coordinator.py`'s stdout (the final report summary) to this script's stdout.
#   7. Exit with `Coordinator.py`'s exit status.
#
# It does not perform any diagnostic analysis itself; that is the responsibility of
# `Coordinator.py` and the services it orchestrates.
#
# ────────────────────────────────────────────────────────────────────────────────
# Guidelines:
#
#   • This script should remain simple, focused on setup and delegation to `Coordinator.py`.
#   • It defines the initial state of the `DiagnosticJob` and how `Coordinator.py` is invoked.
#
# ────────────────────────────────────────────────────────────────────────────────
# Component Interaction:
#
#   `intake.py` -> (pipes DiagnosticJob JSON via stdin, sets PYTHONPATH & DEBUG env var) -> `Coordinator.py`
#   `Coordinator.py` then orchestrates other services (MdTexConverterService, TexCompilerService, etc.)
#   by passing and receiving updated DiagnosticJob JSON objects.
#
# ────────────────────────────────────────────────────────────────────────────────
# Interface Contract (for this intake.py script)
#
# Invocation:
#   [DEBUG=true] printf "markdown content" | ./intake.py
#
# Input:
#   - Markdown document content via stdin.
#   - Optional `DEBUG` environment variable (e.g., `DEBUG=true ./intake.py`), which it
#     will then pass to `Coordinator.py`.
#
# Output (to stdout):
#   - Relays the exact stdout from `Coordinator.py`. As per SDE V5.1, this is expected
#     to be the `final_user_report_summary` from the `DiagnosticJob`.
#
# Output (to stderr, if DEBUG=true):
#   - Debug messages from this script regarding `DEBUG` flag and the initial `DiagnosticJob`.
#
# Exit codes:
#   - Mirrors the exit code of `Coordinator.py`. Typically:
#     - 0: If `Coordinator.py` indicates successful compilation or successful generation of diagnostics for a user document error that leads to a clear report.
#     - Non-zero: `Coordinator.py` (or a service it called) encountered an issue, or `Coordinator.py` itself indicated an error state (e.g., unhandled error, no actionable leads found where expected).
#   - 2: If this `intake.py` script itself has a usage error (e.g., no Markdown content received on stdin).
#
# Environment Variables SET by this script for `Coordinator.py`:
#   - `PYTHONPATH`: Prepended with the project root directory to ensure `Coordinator.py`
#                   can import other project modules.
#   - `DEBUG`: Passed through from `intake.py`'s environment.
#
# Note: Unlike older shell-based entry points, this script does NOT set environment
# variables for individual service paths (e.g., COMPILER_BIN). Service discovery or
# path management is handled by `Coordinator.py` and its `service_runner.py` utility
# as per SDE V5.1 design.
#
# ────────────────────────────────────────────────────────────────────────────────

import sys
import os
import json
import uuid
import subprocess
import pathlib
import datetime

# --- Configuration ---
ROOT_DIR = pathlib.Path(__file__).resolve().parent
Coordinator_PY_SCRIPT = ROOT_DIR / "Coordinator.py"

# --- Helper Functions ---
def eprint(*args, **kwargs):
    """Prints to stderr."""
    print(*args, file=sys.stderr, **kwargs)

# --- Main Logic ---
def main():
    """Main function for intake.py."""
    is_debug_mode = os.environ.get("DEBUG", "false").lower() == "true"

    if is_debug_mode:
        eprint(f"DEBUG INTAKE.PY (SDE V5.1): DEBUG mode ENABLED.")
        eprint(f"DEBUG INTAKE.PY: Project ROOT_DIR resolved to '{ROOT_DIR}'.")
        eprint(f"DEBUG INTAKE.PY: Expecting Coordinator script at '{Coordinator_PY_SCRIPT}'.")

    # 1. Read Markdown from stdin
    markdown_content = sys.stdin.read()
    if not markdown_content:
        eprint("Error (intake.py): No Markdown content received on stdin.")
        sys.exit(2)

    if is_debug_mode:
        eprint(f"DEBUG INTAKE.PY: Read {len(markdown_content)} chars of Markdown content.")

    # 2. Generate case ID and timestamp
    case_id = str(uuid.uuid4())
    timestamp_created = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"

    if is_debug_mode:
        eprint(f"DEBUG INTAKE.PY: Generated case_id: {case_id}")
        eprint(f"DEBUG INTAKE.PY: Generated timestamp_created: {timestamp_created}")

    # 3. Construct Initial DiagnosticJob JSON
    #    This structure aligns with the SDE V5.1 `DiagnosticJob` Pydantic model.
    initial_diagnostic_job = {
        "case_id": case_id,
        "timestamp_created": timestamp_created,
        "original_markdown_content": markdown_content,
        "md_to_tex_conversion_attempted": False,
        "md_to_tex_conversion_successful": False,
        "md_to_tex_raw_log": None,
        "generated_tex_content": None,
        "tex_to_pdf_compilation_attempted": False,
        "tex_to_pdf_compilation_successful": False,
        "tex_compiler_raw_log": None,
        "actionable_leads": [],
        "markdown_remedies": [],
        "current_pipeline_stage": "pending_coordination", # Stage after intake, before Coordinator starts
        "final_job_outcome": None,
        "final_user_report_summary": None,
        "internal_tool_outputs_verbatim": {}
    }
    initial_diagnostic_job_json = json.dumps(initial_diagnostic_job) # indent=2 for debug, but not for piping

    if is_debug_mode:
        eprint("DEBUG INTAKE.PY: Initial DiagnosticJob JSON for Coordinator.py (first 300 chars):")
        eprint(json.dumps(initial_diagnostic_job, indent=2)[:300] + "...") # Pretty print for debug log

    # 4. Prepare environment for Coordinator.py
    #    PYTHONPATH needs to include the project root for module imports.
    #    Pass through the DEBUG status.
    Coordinator_env = os.environ.copy()
    project_root_str = str(ROOT_DIR)
    
    if "PYTHONPATH" in Coordinator_env:
        Coordinator_env["PYTHONPATH"] = project_root_str + os.pathsep + Coordinator_env["PYTHONPATH"]
    else:
        Coordinator_env["PYTHONPATH"] = project_root_str
    
    if is_debug_mode:
        Coordinator_env["DEBUG"] = "true" # Ensure Coordinator sees it if intake is in debug
        eprint(f"DEBUG INTAKE.PY: Setting PYTHONPATH to '{Coordinator_env['PYTHONPATH']}' for Coordinator.py call.")
        eprint(f"DEBUG INTAKE.PY: DEBUG flag for Coordinator.py will be '{Coordinator_env['DEBUG']}'.")
    else:
        Coordinator_env["DEBUG"] = "false"


    # 5. Invoke Python Coordinator
    if not Coordinator_PY_SCRIPT.is_file():
        eprint(f"Error (intake.py): Coordinator script not found at '{Coordinator_PY_SCRIPT}'.")
        sys.exit(3) # Specific exit code for missing Coordinator

    try:
        process = subprocess.run(
            [sys.executable, str(Coordinator_PY_SCRIPT)],
            input=initial_diagnostic_job_json,
            capture_output=True,
            text=True,
            check=False, # We will check returncode manually
            env=Coordinator_env
        )
    except Exception as e:
        eprint(f"Error (intake.py): Failed to execute Coordinator.py: {e}")
        sys.exit(4) # Specific exit code for subprocess execution failure

    # 6. Relay Coordinator.py's stdout (final report summary) to this script's stdout
    sys.stdout.write(process.stdout)

    # 7. Relay Coordinator.py's stderr (if any) to this script's stderr, especially in debug mode
    if process.stderr:
        # In non-debug mode, Coordinator's stderr might still be important for tool errors
        eprint("--- Coordinator.py stderr ---")
        eprint(process.stderr.strip())
        eprint("--- End Coordinator.py stderr ---")

    if is_debug_mode:
        eprint(f"DEBUG INTAKE.PY: Coordinator.py exited with code {process.returncode}.")

    # 8. Exit with Coordinator.py's exit status
    sys.exit(process.returncode)

if __name__ == "__main__":
    main()
