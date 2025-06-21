#!/usr/bin/env bash
# smart-pandoc-debugger coordinator.sh — V3.13.4: Consolidated Docs & Minimal Orchestration
#
# Version: 3.13.4
# Date: 2025-06-24 
# Author: Diagnostic Systems Group
#
# Philosophy for this version:
#   - Assumes a tightly controlled local development environment.
#   - All component scripts are assumed to exist, be executable, and function correctly.
#   - Relies on "set -euo pipefail" to crash if a *tool component* (e.g., Reporter) fails.
#   - User document build/conversion "failures" (non-zero exits from Miner, Proofreader, Inspector)
#     are caught to trigger diagnostic solution paths.
#   - Internal debug output is controlled by a single 'DEBUG' environment variable.
#
# ────────────────────────────────────────────────────────────────────────────────
# Role: THE COORDINATOR
#
# This script orchestrates the entire Markdown → PDF diagnostic pipeline by
# delegating tasks to specialized components. It does not perform any log parsing,
# error analysis, or fix generation itself.
#
# The coordinator’s sole responsibility is to:
#   • Execute each pipeline stage in order,
#   • Manage control flow (relying on set -euo pipefail for tool component crashes),
#   • Route intermediate results and environment variables appropriately,
#   • Produce minimal, clear output indicating success or failure.
#
# Current Features:
#   - Integrated Python-based Reporter (reporter.py), called as an executable.
#   - Proofreader errors are routed through the Reporter.
#   - Internal debug messages (e.g., "# DEBUG: SourceComponent:") are conditional
#     on the 'DEBUG' environment variable and sent to stderr.
#   - Relies on `set -u` for unset variables and `set -e` for command/tool component failures.
#   - Calls to Python scripts (like reporter.py) are prefixed with PYTHONPATH="$ROOT"
#     to aid module resolution.
#
# ────────────────────────────────────────────────────────────────────────────────
# Guidelines:
#
#   • Roles exceeding ~100 lines of code should internally manage their own
#     delegation and sub-tasks rather than offloading everything to the coordinator.
#   • Coordinator remains thin, focused on sequencing and environment orchestration.
#
# ────────────────────────────────────────────────────────────────────────────────
# Component Pipeline — (Behavior as of this version)
#
# 📦  Miner
#     - Executes Markdown to TeX and PDF builds. Its non-zero exit for user doc issues
#       (e.g., pandoc failing MD->TeX, or LaTeX failing TeX->PDF) is caught by
#       Coordinator to trigger diagnostics. Crashes if Miner script itself has a bug.
# 📝  Proofreader
#     - Runs static checks. Its non-zero exit (indicating found issues in user doc,
#       with data to stdout) is caught by Coordinator to trigger diagnostics.
#       Crashes if Proofreader script itself has a bug.
# 🪓  Investigator, 📜  Librarian, 🔮  Oracle
#     - These are diagnostic tool components. If they have internal bugs and crash
#       during diagnostic generation, the Coordinator will crash.
# 🔍  Inspector
#     - Validates PDF. Its non-zero exit (indicating an invalid PDF from user doc processing)
#       is caught by Coordinator to trigger diagnostics. Crashes if Inspector script
#       itself has a bug.
# 🗒  Reporter (Python script: reporter.py)
#     - Composes final diagnostic report. If the Reporter script itself has a bug
#       and crashes, the Coordinator will crash.
#
# ────────────────────────────────────────────────────────────────────────────────
# Interface Contract
#
# Entry Point:
#   coordinator_collect_reports
#
# Required environment variables (set externally, e.g., main.sh):
#   MDFILE, TMPDIR, TEXFILE, LOGFILE, PDFOUT
#   MINER_BIN, INVESTIGATOR_BIN, ORACLE_BIN
#   PROOFREADER_BIN, REPORTER_PY_BIN, LIBRARIAN_BIN, INSPECTOR_BIN
#   DEBUG (optional, if "true", enables debug output from this script and its Python children like reporter.py)
#
# Output:
#   - Success (stdout): Exactly "PDF generated successfully."
#   - Failure (stdout): Multi-line diagnostic from Reporter, starting with "Error:".
#   - Debug trace (stderr, if DEBUG=true): "# DEBUG: SourceComponent: ..." lines from this script,
#     and any "COORDINATOR_TRACE:" lines.
#
# Exit codes:
#   - 0 = success ("PDF generated successfully.")
#   - 1 = failure, diagnostics provided for user document error.
#   - 2 = misuse of this script (e.g., wrong arguments).
#   - Other non-zero: A tool component crashed, or a setup issue occurred (e.g., unset var due to `set -u`).
#
# Example diagnostic output (on stdout):
#   Error: LaTeX compilation failed
#   Line: 42
#   Log:  ! LaTeX Error: Missing \end{document}.
#   Fix:  Add \end{document} before EOF
#
# ────────────────────────────────────────────────────────────────────────────────

set -euo pipefail 
export LC_ALL=C.UTF-8

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # Project root

MINER_BIN="${MINER_BIN:-$ROOT/miner.sh}"
INVESTIGATOR_BIN="${INVESTIGATOR_BIN:-$ROOT/investigator.sh}"
ORACLE_BIN="${ORACLE_BIN:-$ROOT/oracle.sh}"
PROOFREADER_BIN="${PROOFREADER_BIN:-$ROOT/proofreader.sh}"
REPORTER_PY_BIN="${REPORTER_PY_BIN:-$ROOT/reporter.py}"
LIBRARIAN_BIN="${LIBRARIAN_BIN:-$ROOT/librarian.sh}"
INSPECTOR_BIN="${INSPECTOR_BIN:-$ROOT/inspector.sh}"

_debug_echo_coordinator() {
  if [[ "${DEBUG,,}" == "true" ]]; then
    echo "COORDINATOR_TRACE: $1" >&2 
  fi
}
_source_component_echo() {
  if [[ "${DEBUG,,}" == "true" ]]; then
    echo "# DEBUG: SourceComponent: $1" >&2
  fi
}

_trigger_solution_path() { # $1: proofreader_error_data (optional)
  local proofreader_error_data="${1:-}"
  if [[ -n "$proofreader_error_data" ]]; then
    _source_component_echo "Proofreader"
    PYTHONPATH="$ROOT" python3 "$REPORTER_PY_BIN" emit_proofreader_error "$proofreader_error_data"
    return
  fi

  _source_component_echo "Oracle" 
  local err_line err_excerpt hints_json context_block

  err_line=$("$INVESTIGATOR_BIN" extract_latex_error_line)
    [[ -z "$err_line" || ! "$err_line" =~ ^[0-9]+$ || "$err_line" -le 0 ]] && err_line="1"
  err_excerpt=$("$INVESTIGATOR_BIN" filter_latex_log_excerpt)
    [[ -z "$err_excerpt" ]] && err_excerpt="" 

  hints_json="[]" 
  if [[ -n "$err_excerpt" ]]; then
    hints_json=$(ERROR_LINE="$err_line" ERROR_SNIPPET="$err_excerpt" "$ORACLE_BIN")
    [[ -z "$hints_json" ]] && hints_json="[]" 
    echo "$hints_json" | python3 -c "import sys,json;json.load(sys.stdin)" # Crash if Oracle output bad JSON
  fi
  
  source "$LIBRARIAN_BIN" 
  context_block=$(librarian_show_context "$err_line" 2>/dev/null) 
  [[ -z "$context_block" ]] && context_block="  [Librarian: No context/error for line $err_line]"
  
  PYTHONPATH="$ROOT" python3 "$REPORTER_PY_BIN" emit "$err_line" "$err_excerpt" "$hints_json" "$context_block"
}

coordinator_collect_reports() {
  _debug_echo_coordinator "coordinator_collect_reports started."

  _debug_echo_coordinator "Attempting Step 1: Miner run_pandoc_tex."
  set +e 
  "$MINER_BIN" run_pandoc_tex
  local pandoc_tex_status=$?
  set -e
  if [[ $pandoc_tex_status -ne 0 ]]; then
    _source_component_echo "Miner (pandoc_tex_failed)"
    _trigger_solution_path 
    exit 1 
  fi
  _debug_echo_coordinator "Step 1 (Miner run_pandoc_tex) finished successfully."

  _debug_echo_coordinator "Attempting Step 2: Proofreader check_delimiters."
  local proofreader_data_file; proofreader_data_file=$(mktemp "${TMPDIR:-/tmp}/proofreader_data.XXXXXX")
  trap '_debug_echo_coordinator "Cleaning up $proofreader_data_file via trap"; rm -f "$proofreader_data_file"' RETURN EXIT
  set +e
  "$PROOFREADER_BIN" check_delimiters "$TEXFILE" > "$proofreader_data_file"
  local proofreader_status=$?
  set -e
  if [[ $proofreader_status -ne 0 ]]; then
    _debug_echo_coordinator "Proofreader found errors. Data captured."
    _trigger_solution_path "$(<"$proofreader_data_file")"
    _debug_echo_coordinator "Exiting after proofreader solution path."
    exit 1
  fi
  _debug_echo_coordinator "Step 2 (Proofreader) finished, no errors found."

  _debug_echo_coordinator "Attempting Step 3: Miner run_pandoc_pdf."
  set +e
  "$MINER_BIN" run_pandoc_pdf 
  local pandoc_pdf_status=$?
  set -e
  if [[ $pandoc_pdf_status -ne 0 ]]; then
    _source_component_echo "Miner (pandoc_pdf_failed_latex_error)"
    _trigger_solution_path
    _debug_echo_coordinator "Exiting after Miner run_pandoc_pdf solution path."
    exit 1
  fi
  _debug_echo_coordinator "Step 3 (Miner run_pandoc_pdf) apparently succeeded. Proceeding to inspect."

  _debug_echo_coordinator "Attempting Step 4: Inspector check_pdf_valid."
  set +e
  "$INSPECTOR_BIN" check_pdf_valid
  local inspector_status=$?
  set -e
  if [[ $inspector_status -ne 0 ]]; then
    _source_component_echo "Inspector (pdf_invalid)"
    _trigger_solution_path
    _debug_echo_coordinator "Exiting after Inspector pdf_invalid solution path."
    exit 1
  fi

  _debug_echo_coordinator "PDF generated and validated successfully."
  echo "PDF generated successfully." # To stdout
  exit 0
}

if [[ "${1:-}" == "coordinator_collect_reports" ]]; then
  _debug_echo_coordinator "Entry point matched. Calling coordinator_collect_reports."
  coordinator_collect_reports
else
  echo "Usage: $0 coordinator_collect_reports" >&2 
  exit 2
fi
