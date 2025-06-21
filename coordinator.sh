#!/usr/bin/env bash
# smart-pandoc-debugger coordinator.sh — V3.6.1: structured diagnostic orchestrator with unified reporting and component debug info
#
# Version: 3.6.1
# Date: 2025-06-22 # Updated
# Author: Diagnostic Systems Group
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
#   • Manage control flow and error handling,
#   • Route intermediate results and environment variables appropriately,
#   • Produce minimal, clear output indicating success or failure.
#
# Key changes in V3.6:
#   • Proofreader errors are now routed through the Reporter for consistent messaging.
#     Proofreader is expected to output structured data on failure, which is then
#     passed to the Reporter.
# Key changes in V3.6.1:
#   • Added "# DEBUG: SourceComponent: Proofreader" output when Proofreader detects an error.
#
# ────────────────────────────────────────────────────────────────────────────────
# Guidelines:
#
#   • Roles exceeding ~100 lines of code should internally manage their own
#     delegation and sub-tasks rather than offloading everything to the coordinator.
#   • Coordinator remains thin, focused on sequencing and environment orchestration.
#
# ────────────────────────────────────────────────────────────────────────────────
# Component Pipeline — V3.6 Diagnostic Roles # (Using V3.6 component roles as base)
#
# 📦  Miner
#     - Executes Markdown to TeX and PDF builds
#     - Produces raw logs without filtering or analysis
#
# 📝  Proofreader
#     - Runs quick static checks on LaTeX source (e.g., unmatched delimiters)
#     - Emits structured error data on failure for processing by the Reporter.
#
# 🪓  Investigator
#     - Parses raw Miner logs to locate a single critical build-blocking error
#     - Extracts error line number and filtered log snippet
#
# 📜  Librarian
#     - Retrieves source code excerpts around reported error lines
#
# 🔮  Oracle
#     - Provides minimal, precise fix suggestions based on error snippet
#
# 🔍  Inspector
#     - Validates that final PDF is non-empty and valid
#
# 🗒  Reporter
#     - Composes final user-facing plain-text diagnostic output.
#     - Now also processes structured error data from Proofreader.
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
#   PROOFREADER_BIN, REPORTER_BIN, LIBRARIAN_BIN, INSPECTOR_BIN
#
# Output:
#   - Success: Exactly "PDF generated successfully."
#   - Failure: Multi-line diagnostic starting with "Error:", may include "# DEBUG:" lines.
#
# Exit codes:
#   0 = success
#   1 = failure with diagnostics
#   2 = misuse or missing environment variables
#
# Example diagnostic output: (This remains the target format)
#   Error: LaTeX compilation failed
#   Line: 42
#   Log:  ! LaTeX Error: Missing \end{document}.
#   Fix:  Add \end{document} before EOF
#
# ────────────────────────────────────────────────────────────────────────────────

set -eo pipefail
export LC_ALL=C.UTF-8

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MINER_BIN="${MINER_BIN:-$ROOT/miner.sh}"
INVESTIGATOR_BIN="${INVESTIGATOR_BIN:-$ROOT/investigator.sh}"
ORACLE_BIN="${ORACLE_BIN:-$ROOT/oracle.sh}"
PROOFREADER_BIN="${PROOFREADER_BIN:-$ROOT/proofreader.sh}"
REPORTER_BIN="${REPORTER_BIN:-$ROOT/reporter.sh}"
LIBRARIAN_BIN="${LIBRARIAN_BIN:-$ROOT/librarian.sh}"
INSPECTOR_BIN="${INSPECTOR_BIN:-$ROOT/inspector.sh}"

_validate_env() {
  local var
  for var in MDFILE TMPDIR TEXFILE LOGFILE PDFOUT \
             MINER_BIN INVESTIGATOR_BIN ORACLE_BIN \
             PROOFREADER_BIN REPORTER_BIN LIBRARIAN_BIN INSPECTOR_BIN; do
    if [[ -z "${!var}" ]]; then
      echo "Error: Required environment variable '$var' is not set." >&2
      exit 2
    fi
  done
}

# run_diagnostics can now be triggered by:
# 1. Proofreader failure (called with proofreader_output as $1)
# 2. Compilation failure or PDF invalidation (called with no arguments)
run_diagnostics() {
  local proofreader_error_data="${1:-}" # Optional: structured data from Proofreader

  local err_line err_excerpt hints_json context_block

  # Source Reporter once, as it's needed for both paths.
  # TEXFILE must be in the environment for Reporter.
  source "$REPORTER_BIN"

  if [[ -n "$proofreader_error_data" ]]; then
    # Path 1: Error detected by Proofreader
    # Print debug information about the source component
    echo "# DEBUG: SourceComponent: Proofreader" # TASK 1 IMPLEMENTED HERE

    # Reporter needs a function to handle this, e.g., reporter_emit_proofreader_error
    # This function is responsible for parsing proofreader_error_data and TEXFILE
    # to produce the final user-facing diagnostic.
    if type -t reporter_emit_proofreader_error >/dev/null; then
      reporter_emit_proofreader_error "$proofreader_error_data" "$TEXFILE"
    else
      # Fallback if Reporter is not yet updated to handle Proofreader errors.
      # This provides some debugging information but won't match desired output.
      echo "Error: Reporter function 'reporter_emit_proofreader_error' not found." >&2
      echo "Raw Proofreader data received:" >&2
      echo "$proofreader_error_data" >&2
      echo "Please update reporter.sh to handle direct Proofreader errors." >&2
    fi
    return # Diagnostics complete for Proofreader error
  fi

  # Path 2: Error from compilation (Miner/pdflatex) or PDF invalidation - original logic
  # Determine primary source of error for compilation path (e.g. Oracle or Investigator)
  # For now, let's assume if Oracle provides hints, it's the key source.
  # This debug line might be refined later.
  echo "# DEBUG: SourceComponent: Oracle" # Default for compilation path, can be refined

  # Investigator: find first critical error line number in TEXFILE
  err_line=$("$INVESTIGATOR_BIN" extract_latex_error_line || true)
  if ! [[ "$err_line" =~ ^[0-9]+$ ]]; then
    err_line=1 # Default to line 1 if no specific line found
  fi

  # Investigator: extract filtered error log excerpt
  err_excerpt=$("$INVESTIGATOR_BIN" filter_latex_log_excerpt || true)

  # Oracle: generate fix suggestions from error snippet
  hints_json="[]"
  if [[ -n "$err_excerpt" ]]; then
    ERROR_LINE="$err_line" ERROR_SNIPPET="$err_excerpt" \
      hints_json=$("$ORACLE_BIN") || hints_json="[]"
  fi

  # Librarian: fetch source context around error line
  # Librarian is sourced here as it's only relevant for compilation error path.
  TEXFILE="$TEXFILE" source "$LIBRARIAN_BIN"
  context_block=""
  if type -t librarian_show_context >/dev/null; then
    context_block=$(librarian_show_context "$err_line" || echo "")
  fi

  # Reporter: output final human-readable diagnostic for compilation errors
  if type -t reporter_emit >/dev/null; then
    # Pass context_block to reporter_emit
    reporter_emit "$err_line" "$err_excerpt" "$hints_json" "$context_block"
  else
    echo "Error: Failed to invoke reporter_emit for compilation error." >&2
  fi
}

coordinator_collect_reports() {
  _validate_env

  # Step 1: Generate LaTeX source from Markdown (fast path)
  if ! "$MINER_BIN" run_pandoc_tex; then
    echo "Error: Failed to generate LaTeX source from Markdown." >&2
    # Potentially add a # DEBUG: SourceComponent: Miner line here too
    return 1
  fi

  # Step 2: Run static LaTeX syntax checks (e.g., delimiters)
  # Proofreader now outputs structured data on failure, which is passed to Reporter.
  local proofreader_output
  local proofreader_data_file # Using a temporary file for potentially multi-line output
  proofreader_data_file=$(mktemp "${TMPDIR:-/tmp}/proofreader_data.XXXXXX")
  
  # Execute Proofreader, redirecting its stdout (structured data) to the temp file.
  # The exit code of Proofreader determines if an error was found.
  if ! "$PROOFREADER_BIN" check_delimiters "$TEXFILE" > "$proofreader_data_file"; then
    proofreader_output=$(<"$proofreader_data_file") # Read the captured structured data
    rm -f "$proofreader_data_file"                 # Clean up temp file

    # Proofreader found an error. Pass its structured output to run_diagnostics.
    run_diagnostics "$proofreader_output"
    return 1 # Exit with failure status
  fi
  rm -f "$proofreader_data_file" # Clean up temp file if Proofreader succeeded (no output)


  # Step 3: Attempt direct Markdown → PDF build
  if "$MINER_BIN" run_pandoc_pdf; then
    # Step 3a: Validate PDF
    if "$INSPECTOR_BIN" check_pdf_valid; then
      echo "PDF generated successfully."
      return 0
    else
      # PDF invalid despite successful build — force diagnostics (compilation error path)
      run_diagnostics
      return 1
    fi
  fi

  # Step 4: Fallback manual pdflatex build
  if ! "$MINER_BIN" run_pdflatex; then
    run_diagnostics # Build failed, run diagnostics (compilation error path)
    return 1
  fi

  # Step 5: Validate PDF after manual pdflatex build
  if "$INSPECTOR_BIN" check_pdf_valid; then
    echo "PDF generated successfully."
    return 0
  else
    # PDF invalid despite manual build success — force diagnostics (compilation error path)
    run_diagnostics
    return 1
  fi
}

if [[ "${1:-}" == "coordinator_collect_reports" ]]; then
  coordinator_collect_reports
else
  echo "Usage: $0 coordinator_collect_reports" >&2
  exit 2
fi
