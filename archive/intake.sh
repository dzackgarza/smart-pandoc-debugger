#!/usr/bin/env bash
# smart-pandoc-debugger main.sh — V1.5.1: Python Coordinator Invoker with Standardized Docs
#
# Version: 1.5.1
# Date: 2025-06-24
# Author: Diagnostic Systems Group
#
# Philosophy for this version:
#   - Acts as the primary entry point for the Smart Diagnostic Engine (SDE).
#   - Captures user input (Markdown document).
#   - Sets up a pristine environment for the diagnostic pipeline, including temporary
#     workspace and critical environment variables (paths to service scripts, DEBUG flag).
#   - Constructs an InitialJobPayload JSON containing the Markdown content and a case ID.
#   - Invokes the Python-based `coordinator.py` service, piping the InitialJobPayload JSON
#     to its stdin and ensuring `PYTHONPATH` includes the project root for module resolution.
#   - Relays the final diagnostic report (from `coordinator.py`'s stdout) to the user.
#   - Exits with the status code provided by `coordinator.py`.
#
# ────────────────────────────────────────────────────────────────────────────────
# Role: THE INTAKE CLERK & LAUNCHER
#
# This script is the main user-facing entry point. Its responsibilities are purely
# logistical: prepare the "case file" (as JSON) and hand it off to the
# `Coordinator` service (`coordinator.py`). It does not perform any analysis itself.
#
# The `main.sh` script's sole responsibility is to:
#   • Accept Markdown content from stdin.
#   • Create a temporary workspace and generate a unique case ID.
#   • Export environment variables required by `coordinator.py` and the services it calls
#     (e.g., paths to service scripts, global `DEBUG` flag).
#   • Construct and pipe the `InitialJobPayload` JSON to `coordinator.py`.
#   • Forward `coordinator.py`'s stdout directly to its own stdout.
#   • Exit with `coordinator.py`'s exit status.
#
# ────────────────────────────────────────────────────────────────────────────────
# Guidelines:
#
#   • This script should remain extremely simple, focused on setup and delegation.
#   • It defines the initial contract for how the `Coordinator` service is invoked.
#
# ────────────────────────────────────────────────────────────────────────────────
# Component Service Interaction:
#
#   `main.sh` -> (pipes InitialJobPayload JSON via stdin, sets env vars) -> `coordinator.py`
#   `coordinator.py` then orchestrates other services (InitialProcessor, Compiler, etc.)
#
# ────────────────────────────────────────────────────────────────────────────────
# Interface Contract (for this main.sh script)
#
# Invocation:
#   [DEBUG=true] printf "markdown content" | ./main.sh
#
# Input:
#   - Markdown document content via stdin.
#   - Optional `DEBUG` environment variable (e.g., `DEBUG=true ./main.sh`) which it
#     will then export for all child processes.
#
# Output (to stdout):
#   - Relays the exact stdout from `coordinator.py`, which is expected to be either:
#     * "PDF generated successfully." (rare for this tool's purpose) OR
#     * A multi-line, human-readable diagnostic report.
# Output (to stderr, if DEBUG=true):
#   - Debug messages from this script regarding `DEBUG` flag and `InitialJobPayload`.
#
# Exit codes:
#   - Mirrors the exit code of `coordinator.py`. Typically:
#     - 1: Diagnostics were successfully generated for a user document error.
#     - Other non-zero: `coordinator.py` (or a service it called) crashed due to a tool bug or setup issue.
#     - 2: If this `main.sh` script itself has a usage error (e.g., no stdin).
#
# Environment Variables SET by this script for children:
#   TMPDIR, INITIAL_PROCESSOR_BIN, COMPILER_BIN, LOG_INVESTIGATOR_BIN,
#   ORACLE_SOLUTION_GENERATOR_BIN, FINAL_REPORTER_BIN, LIBRARIAN_BIN, DEBUG.
#   PYTHONPATH (set specifically for the coordinator.py call).
#
# ────────────────────────────────────────────────────────────────────────────────

set -eo pipefail

# Resolve root directory (where this script lives)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Service Script Paths (these are exported for coordinator.py and potentially other services)
COORDINATOR_PY_BIN="$ROOT/coordinator.py" 
INITIAL_PROCESSOR_BIN_PATH="$ROOT/initial_processor.py" 
COMPILER_BIN_PATH="$ROOT/compiler.py"
LOG_INVESTIGATOR_BIN_PATH="$ROOT/log_investigator.py"
ORACLE_SOLUTION_GENERATOR_BIN_PATH="$ROOT/oracle_solution_generator.py"
FINAL_REPORTER_BIN_PATH="$ROOT/reporter.py" 
LIBRARIAN_SCRIPT_PATH="$ROOT/librarian.sh" # May be called by Oracle service

# Create temporary workspace and generate a case ID
tmpdir=$(mktemp -d) # Crash if mktemp fails (e.g., no permissions)
case_id=$(basename "$tmpdir") 

# Read Markdown from stdin into a variable
markdown_content=$(cat)
if [[ -z "$markdown_content" ]]; then # Check if stdin was empty
    echo "Error (main.sh): No Markdown content received on stdin." >&2
    exit 2
fi

# Export environment variables needed by coordinator.py and the services it calls
export TMPDIR="$tmpdir"
export INITIAL_PROCESSOR_BIN="$INITIAL_PROCESSOR_BIN_PATH"
export COMPILER_BIN="$COMPILER_BIN_PATH"
export LOG_INVESTIGATOR_BIN="$LOG_INVESTIGATOR_BIN_PATH"
export ORACLE_SOLUTION_GENERATOR_BIN="$ORACLE_SOLUTION_GENERATOR_BIN_PATH"
export FINAL_REPORTER_BIN="$FINAL_REPORTER_BIN_PATH"
export LIBRARIAN_BIN="$LIBRARIAN_SCRIPT_PATH" 

# Handle and export a single 'DEBUG' variable for all child processes
if [[ "${DEBUG,,}" == "true" ]]; then # Check case-insensitively
    export DEBUG="true"
    echo "DEBUG MAIN.SH (V1.5.1): DEBUG mode ENABLED by caller, DEBUG='true' is being exported." >&2
else
    export DEBUG="false" # Ensure children see a definitive "false"
    # No debug print here if DEBUG is false, to keep stderr clean for non-debug runs.
fi

# Construct InitialJobPayload JSON for coordinator.py
# This payload includes fields coordinator.py V2.1.x expects to be initialized.
# jq is used for safe JSON string escaping of markdown_content.
initial_job_payload_json=$(cat <<EOF
{
  "case_id": "$case_id",
  "original_document": {
    "content": $(echo "$markdown_content" | jq -R -s .),
    "type": "markdown"
  },
  "collected_solutions": [],
  "latex_document_content": null,
  "items_for_oracle_processing": [] 
}
EOF
)

# Conditional debug print for the payload being sent
if [[ "${DEBUG,,}" == "true" ]]; then
    echo "DEBUG MAIN.SH (V1.5.1): InitialJobPayload JSON for coordinator.py (first 200 chars):" >&2
    echo "${initial_job_payload_json:0:200}..." >&2
    echo "DEBUG MAIN.SH (V1.5.1): Setting PYTHONPATH to '$ROOT' for coordinator.py call." >&2
fi

###############
# Main driver
###############
main() {
  # Invoke Python Coordinator, piping the JSON payload to its stdin.
  # PYTHONPATH="$ROOT" ensures Python looks in the project root for packages like manager_utils.
  # The exit code of this pipeline (effectively coordinator.py's exit code) will be main.sh's exit code.
  echo "$initial_job_payload_json" | PYTHONPATH="$ROOT" python3 "$COORDINATOR_PY_BIN"
}

main
# `set -eo pipefail` ensures that if the pipeline above (especially python3 coordinator.py)
# exits non-zero, main.sh will also exit with that status.
