#!/usr/bin/env bash
# smart-pandoc-debugger proofreader.sh — V1.5: delegates checks to specialized scripts (Python/Awk for TeX, Python for MD)
#
# Version: 1.5
# Date: 2025-06-22 # MODIFIED
# Author: Diagnostic Systems Group
#
# ────────────────────────────────────────────────────────────────────────────────
# Role Overview — THE PROOFREADER (TEAM LEADER)
#
#   The Proofreader leads a team of specialized "checkers" to meticulously review
#   both the raw Markdown (for early syntax issues) and the generated LaTeX
#   typescript (for TeX-specific structural problems).
#
#   The Proofreader ensures proactive problem flagging before typesetting begins,
#   acting as a coordinator for its specialist team.
#
# Responsibilities:
#   • Coordinate the execution of various checker scripts (from the 'proofreader-team'
#     subdirectory). Some checkers operate on the MDFILE (Markdown), others on TEXFILE (LaTeX).
#     Examples: Python script for unclosed Markdown dollars, Python script for unbalanced TeX braces,
#     Awk script for unmatched TeX \left/\right.
#   • Process the first reported error from any checker.
#   • If any checker finds an issue:
#       • Output structured key-value data based on the checker's findings.
#       • Exit 1.
#   • If all checkers report no issues: exits 0, prints nothing.
#
# Invocation:
#   ./proofreader.sh check_delimiters /path/to/input.tex
#   (Note: 'check_delimiters' is a legacy argument; script now runs all its checks)
#   Assumes MDFILE and TEXFILE are available in the environment or passed appropriately.
#   For this version, MDFILE is expected from the environment (set by main.sh).
#
# Output (on error):
#   - stdout only, key-value pairs, one per line (example fields from checkers):
#     ERROR_TYPE="<SpecificErrorType>" (e.g., UnmatchedDelimiters, UnterminatedInlineMathMarkdown, UnbalancedBraces)
#     LINE_NUMBER="<num>" (relative to the file checked, MD or TeX)
#     LINE_CONTENT="<full content of the line>"
#     PROBLEM_SNIPPET="<more specific problematic text segment>"
#     (plus other type-specific counts)
#   - Exits 1.
# Output (on success):
#   - No stdout.
#   - Exits 0.
#
# Misuse:
#   - Prints usage to stderr, exits 2.
#
# ────────────────────────────────────────────────────────────────────────────────
# CONTRIBUTOR NOTES:
#   If you modify this file, you MUST:
#     1. Keep or update all of the header documentation (version, date,
#        responsibilities, invocation, and output contracts).
#     2. Increment the minor version number for any functional change.
#     3. Checker scripts go in 'proofreader-team'. They should:
#        a) Detect one specific error type.
#        b) Take the relevant file path (MDFILE or TEXFILE) as an argument.
#        c) Output a single colon-delimited line on error to stdout:
#           ERROR_TYPE:LINE_NUM:VAL1:VAL2:SNIPPET:CONTENT
#           (SNIPPET is the focused problematic text, CONTENT is the full line.)
#        d) Exit (within the script) immediately after printing the error.
#        e) Print nothing and exit silently on no error.
#        f) Python scripts should be `python3`. Awk scripts aim for POSIX.
#     4. Update `markdown_checkers` or `tex_checkers` arrays if adding/modifying checkers,
#        and ensure the script execution logic handles them (e.g., python3 vs awk).
#     5. Test thoroughly.
# ────────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# --- Argument and File Validation ---
# TEXFILE is passed as an argument. MDFILE is expected from the environment.
if [[ "${1:-}" != "check_delimiters" || $# -ne 2 ]]; then
  echo "Usage: $0 check_delimiters path/to/generated.tex (MDFILE env var must be set for Markdown checks)" >&2
  exit 2
fi

TEXFILE="$2" # Path to the generated TeX file

if [[ -z "$MDFILE" ]]; then
    echo "Error: MDFILE environment variable is not set. Cannot perform Markdown checks." >&2
    exit 2
fi
if [[ ! -f "$MDFILE" ]]; then
  echo "Error: Markdown source file not found: $MDFILE" >&2
  exit 2
fi
# TEXFILE existence is checked before running tex_checkers loop.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECKER_TEAM_DIR="$SCRIPT_DIR/proofreader-team"

# --- Helper function for processing checker output ---
_process_checker_output() {
    local checker_output_line="$1"
    
    local IFS_orig="$IFS"
    IFS=':' read -r error_type line_num val1 val2 problem_snippet_val line_content_val <<< "$checker_output_line"
    
    echo "ERROR_TYPE=$error_type"
    echo "LINE_NUMBER=$line_num" 
    
    if [[ "$error_type" == "UnmatchedDelimiters" ]]; then 
        echo "LEFT_COUNT=$val1"
        echo "RIGHT_COUNT=$val2"
    elif [[ "$error_type" == "UnterminatedInlineMathMarkdown" ]]; then 
        echo "OPEN_DELIM_COUNT=$val1" 
        echo "CLOSE_DELIM_COUNT=$val2" 
    elif [[ "$error_type" == "UnbalancedBraces" ]]; then # Can be from TeX (Python) or TeX (awk - legacy)
        echo "OPEN_COUNT=$val1"
        echo "CLOSE_COUNT=$val2"
    else
        echo "CHECKER_VAL1=$val1" 
        echo "CHECKER_VAL2=$val2"
    fi
    echo "PROBLEM_SNIPPET=${problem_snippet_val:-$line_content_val}" 
    echo "LINE_CONTENT=$line_content_val"

    IFS="$IFS_orig"
    exit 1 
}

# --- Define Markdown Checkers ---
markdown_checkers=(
  "check_markdown_unclosed_dollar.py" 
)

# --- Define TeX Checkers ---
tex_checkers=(
  "check_unmatched_left_right.awk"    
  "check_tex_unbalanced_braces.py"   # MODIFIED: Replaced awk with Python script for TeX brace check
)

# --- Run Markdown Checkers First ---
for checker_script_name in "${markdown_checkers[@]}"; do
  checker_script_path="$CHECKER_TEAM_DIR/$checker_script_name"
  if [[ ! -f "$checker_script_path" ]]; then
    echo "Error: Proofreader's checker script not found: $checker_script_path" >&2; exit 2; fi

  checker_output=""
  if [[ "$checker_script_name" == *".py" ]]; then
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 command not found, cannot run Python checker: $checker_script_name" >&2; exit 2; fi
    # Pass MDFILE to Markdown checkers
    checker_output=$(python3 "$checker_script_path" "$MDFILE")
  else
    echo "Warning: Unknown Markdown checker type (expected .py): $checker_script_name" >&2; continue; fi

  if [[ -n "$checker_output" ]]; then _process_checker_output "$checker_output"; fi
done

# --- If Markdown checks pass, proceed to TeX checks ---
if [[ ! -f "$TEXFILE" ]] && [[ ${#tex_checkers[@]} -gt 0 ]]; then
  echo "Error: TEXFILE '$TEXFILE' not found before running TeX-based checks. Markdown checks may have passed, but TeX generation failed or was skipped." >&2
  # This might indicate an issue in main.sh or miner.sh if Proofreader is called after failed TeX generation
  exit 2
fi

for checker_script_name in "${tex_checkers[@]}"; do
  checker_script_path="$CHECKER_TEAM_DIR/$checker_script_name"
  if [[ ! -f "$checker_script_path" ]]; then
    echo "Error: Proofreader's checker script not found: $checker_script_path" >&2; exit 2; fi

  checker_output=""
  # Determine how to run the checker based on its extension
  if [[ "$checker_script_name" == *".py" ]]; then
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 command not found, cannot run Python checker: $checker_script_name" >&2; exit 2; fi
    # Pass TEXFILE to TeX checkers (Python or other script types)
    checker_output=$(python3 "$checker_script_path" "$TEXFILE")
  elif [[ "$checker_script_name" == *".awk" ]]; then
    # Pass TEXFILE to Awk TeX checkers
    checker_output=$(awk -f "$checker_script_path" "$TEXFILE")
  else
    echo "Warning: Unknown TeX checker type (expected .py or .awk): $checker_script_name" >&2; continue; fi

  if [[ -n "$checker_output" ]]; then _process_checker_output "$checker_output"; fi
done

# No issues found by any checker
exit 0
