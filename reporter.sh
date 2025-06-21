#!/usr/bin/env bash
# smart-pandoc-debugger reporter.sh — V1.6.1: structured diagnostic output layer with enhanced Proofreader error handling
#
# Version: 1.6.1
# Date: 2025-06-22 # MODIFIED
# Author: Diagnostic Systems Group
#
# ────────────────────────────────────────────────────────────────────────────────
# Role Overview — THE REPORTER
#
# The Reporter formats and emits plain-text diagnostics.
# It handles errors from two main sources:
#   1. LaTeX build failures (via Investigator, Oracle, Librarian).
#   2. Static analysis checks from Proofreader (which may include checks on Markdown or TeX files).
#
# Responsibilities:
#   • Emit top-level summary error message, always prefixed by "Error: <specific message>"
#   • For build failures (from LaTeX compilation):
#     • Include indented log excerpt from Investigator.
#     • Display LaTeX source context from around the error line.
#     • Render Oracle hints as "Hint: ..." lines.
#     • Robustly handle empty or malformed Oracle JSON hints.
#     • Provide fallback error message if no hints from Oracle.
#   • For Proofreader errors (Markdown or TeX static checks):
#     • Parse structured error data from Proofreader.
#     • Generate specific, user-centric error messages and hints based on Proofreader's findings.
#     • If the error is from a TeX check, display LaTeX source context.
#     • If the error is from a Markdown check, the "context" is the line content itself;
#       `reporter_show_context_block` might show TeX context if available, but the primary
#       focus for Markdown errors is the reported line content and snippet.
#
# Invocation Assumptions:
#   • Script is sourced; entrypoints are `reporter_emit` (for build failures)
#     and `reporter_emit_proofreader_error` (for Proofreader issues).
#   • `TEXFILE` environment variable is set (path to generated TeX file).
#   • `MDFILE` environment variable is set (path to original Markdown file). # Added assumption
#   • `jq` is available in PATH (for `reporter_emit`).
#
# ────────────────────────────────────────────────────────────────────────────────
# Interface Contract
#
# Call signature for build failures (`reporter_emit`):
#   source reporter.sh && reporter_emit "$LINE" "$EXCERPT" "$HINT_JSON" "$CONTEXT_BLOCK"
# Arguments:
#   $1 - LINE          : Line number (in TeX file)
#   $2 - EXCERPT       : Log excerpt (from LaTeX build)
#   $3 - HINT_JSON     : JSON array of fix suggestions from Oracle
#   $4 - CONTEXT_BLOCK : Pre-formatted source context from Librarian (TeX context)
#
# Call signature for Proofreader errors (`reporter_emit_proofreader_error`):
#   source reporter.sh && reporter_emit_proofreader_error "$PROOFREADER_DATA" "$TEXFILE_PATH_ARG"
# Arguments:
#   $1 - PROOFREADER_DATA : Structured error data from Proofreader.
#                          (Fields like LINE_NUMBER, LINE_CONTENT, PROBLEM_SNIPPET refer to the
#                           file the specific Proofreader checker analyzed, which could be MD or TeX).
#   $2 - TEXFILE_PATH_ARG : Path to the TeX file (primarily uses TEXFILE env var for context display).
#
# Output:
#   • UTF-8 plain text to stdout (no colors or formatting codes)
#   • First line always starts with "Error: ..."
#
# Exit:
#   • These functions print diagnostics but do not exit the calling script.
#
# ────────────────────────────────────────────────────────────────────────────────
# CONTRIBUTOR NOTES:
#   If you modify this file, you MUST:
#     1. Keep or update all of the header documentation (version, date,
#        responsibilities, invocation, and output contracts).
#     2. Increment the minor version number for any functional change.
#     3. Ensure any parsing of structured data (e.g., from Proofreader)
#        is robust and explicitly handles all expected fields for each ERROR_TYPE.
#     4. When adding a handler for a new ERROR_TYPE from Proofreader:
#        a. Ensure the main error message is user-centric and actionable.
#        b. Include relevant details from the structured data (LINE_NUMBER, PROBLEM_SNIPPET, counts).
#        c. Provide a clear, helpful hint.
#        d. Consider if `reporter_show_context_block` is appropriate (usually for TeX errors).
#           For Markdown errors, the `LINE_CONTENT` and `PROBLEM_SNIPPET` are the primary context.
#     5. Test thoroughly with the main test suite to ensure no regressions and
#        that new messages match V3 expectations.
# ────────────────────────────────────────────────────────────────────────────────

set -eo pipefail
export LC_ALL=C.UTF-8

# Function to handle errors reported by Proofreader
reporter_emit_proofreader_error() {
  local proofreader_data_string="$1"
  # TEXFILE_PATH_ARG ($2) is not explicitly used; function relies on TEXFILE env var for context.

  # --- Declare local variables to store parsed data ---
  local error_type=""
  local line_number="unknown" # This line number is relative to the file checked by the proofreader tool
  local line_content_raw=""   # Full line from the file checked
  local problem_snippet=""    # Specific snippet from the file checked
  local left_count="" right_count=""
  local open_delim_count="" close_delim_count="" 
  local open_count="" close_count=""

  local IFS_orig="$IFS"
  IFS=$'\n' 
  for line_item in $proofreader_data_string; do
    local temp_key="${line_item%%=*}"
    local temp_value="${line_item#*=}"
    case "$temp_key" in
      ERROR_TYPE) error_type="$temp_value" ;;
      LINE_NUMBER) line_number="$temp_value" ;;
      LINE_CONTENT) line_content_raw="$temp_value" ;;
      PROBLEM_SNIPPET) problem_snippet="$temp_value" ;;
      LEFT_COUNT) left_count="$temp_value" ;;
      RIGHT_COUNT) right_count="$temp_value" ;;
      OPEN_DELIM_COUNT) open_delim_count="$temp_value" ;;
      CLOSE_DELIM_COUNT) close_delim_count="$temp_value" ;;
      OPEN_COUNT) open_count="$temp_value" ;;
      CLOSE_COUNT) close_count="$temp_value" ;;
    esac
  done
  IFS="$IFS_orig" 

  if [[ -z "$line_number" || ! "$line_number" =~ ^[0-9]+$ ]]; then
    line_number="unknown"
  fi
  if [[ -z "$problem_snippet" && -n "$line_content_raw" ]]; then
    problem_snippet="$line_content_raw"
  fi

  # --- Generate diagnostic output based on ERROR_TYPE ---
  if [[ "$error_type" == "UnmatchedDelimiters" ]]; then # TeX check
    local missing_part="a corresponding delimiter"
    local found_part="'$problem_snippet'"
    if [[ "$left_count" -gt "$right_count" ]]; then
      missing_part="a matching '\\right)'" 
      if [[ "$problem_snippet" == *"\\left("*  ]]; then found_part="'\\left(...'";
      elif [[ "$problem_snippet" == *"\\left["* ]]; then found_part="'\\left[...'";
      fi
    elif [[ "$right_count" -gt "$left_count" ]]; then
      missing_part="a matching '\\left('"
      if [[ "$problem_snippet" == *"\\right)"* ]]; then found_part="'\\right)...'";
      elif [[ "$problem_snippet" == *"\\right]"* ]]; then found_part="'\\right]...'";
      fi
    fi
    echo "Error: Unmatched $found_part — missing $missing_part. Review your math expression in the TeX source."
    echo

    echo "Details (from TeX file analysis):"
    echo "  Line number (TeX): $line_number"
    echo "  Problem snippet (TeX): $problem_snippet"
    echo "  Full line content (TeX): $line_content_raw"
    echo "  Counts: $left_count \\left vs $right_count \\right"
    echo

    reporter_show_context_block "$line_number" # Show context from TeX file
    echo
    echo "Hint: Ensure every \\left has a corresponding \\right (and vice-versa) within the same mathematical expression in your TeX source."
    echo "      This usually originates from your Markdown math."
    echo

  # Task 6: Handle UnterminatedInlineMathMarkdown
  elif [[ "$error_type" == "UnterminatedInlineMathMarkdown" ]]; then # Markdown check
    # V3 Expectation: "Error: Unterminated math mode — started with '$' but no closing '$' found for 'x + y + z'. Add a closing '$'."
    # problem_snippet from python script is "x + y + z"
    echo "Error: Unterminated math mode — started with '\$' but no closing '\$' found for '$problem_snippet'. Add a closing '\$'."
    echo

    echo "Details (from Markdown file analysis):"
    echo "  Line number (Markdown): $line_number"
    echo "  Problematic content (Markdown): $problem_snippet" # This is the content after the first $
    echo "  Full line content (Markdown): $line_content_raw"
    # OPEN_DELIM_COUNT and CLOSE_DELIM_COUNT from Python script are placeholders (1 and 0)
    # echo "  Markdown '$' count on line: Odd" # Or use the counts if they become more meaningful
    echo

    # Context for Markdown errors: The line itself is the primary context.
    # We can show the Markdown line. `reporter_show_context_block` shows TeX.
    echo "Problematic Markdown line content:"
    echo "  L$line_number (MD): $line_content_raw"
    echo
    # If TEXFILE is available, showing its context might still be useful if pandoc attempted conversion
    # reporter_show_context_block "$line_number_in_tex_if_mappable"
    # For now, let's keep it simple and focus on Markdown context.

    echo "Hint: Check line $line_number in your Markdown file ('${MDFILE:-unknown file}') for a missing closing '\$' that matches an opening '\$'."
    echo

  elif [[ "$error_type" == "UnterminatedInlineMath" ]]; then # TeX check (fallback if old \(\) check is used)
    echo "Error: Unterminated math mode (TeX) — started with '\\(' but no closing '\\)' found for '$problem_snippet'. Add a closing '\\)'."
    echo
    echo "Details (from TeX file analysis):"
    echo "  Line number (TeX): $line_number"
    echo "  Problem snippet (from TeX): $problem_snippet" 
    echo "  Full line content (from TeX): $line_content_raw"
    echo "  Counts (TeX delimiters): ${open_delim_count:-N/A} open vs ${close_delim_count:-N/A} close"
    echo
    reporter_show_context_block "$line_number"
    echo
    echo "Hint: Check the TeX source for unmatched '\\(' and '\\)'. This often results from unclosed '\$' in Markdown."
    echo

  elif [[ "$error_type" == "UnbalancedBraces" ]]; then # TeX check
    local brace_issue_desc=""
    local hint_text="Check for missing or extra braces '{' or '}' in your TeX math expression."
    if [[ "$open_count" -gt "$close_count" ]]; then
      brace_issue_desc="a '{' is opened but not closed. Add a matching '}'."
    elif [[ "$close_count" -gt "$open_count" ]]; then 
      if [[ "$problem_snippet" == *"}"* && "$open_count" -lt "$close_count" ]]; then 
         echo "Error: Unexpected closing brace '}' found in TeX snippet '$problem_snippet'. Check for an extra '}' or a missing opening '\$' in your Markdown."
         hint_text="Verify brace balancing in your TeX source. If math delimiters are also suspect, ensure they are correctly paired in Markdown."
         brace_issue_desc="" 
      else
        brace_issue_desc="a '}' is present without a matching open '{'. Check for an extra '}' or a missing '{'."
      fi
    else 
      brace_issue_desc="brace counts are mismatched. Open: $open_count, Closed: $close_count."
    fi

    if [[ -n "$brace_issue_desc" ]]; then
        echo "Error: Unbalanced brace in TeX snippet '$problem_snippet' — $brace_issue_desc"
    fi
    echo

    echo "Details (from TeX file analysis):"
    echo "  Line number (TeX): $line_number"
    echo "  Problem snippet (TeX): $problem_snippet"
    echo "  Full line content (TeX): $line_content_raw"
    echo "  Brace counts: ${open_count:-N/A} open '{' vs ${close_count:-N/A} close '}'"
    echo
    reporter_show_context_block "$line_number"
    echo
    echo "Hint: $hint_text Usually this means a similar issue exists in your Markdown math."
    echo

  else
    # --- Fallback for other/unknown error types from Proofreader ---
    echo "Error: An issue was detected by static analysis (Proofreader) near line $line_number."
    echo
    echo "Details:"
    echo "  Error Type code: ${error_type:-N/A}"
    echo "  Line number: $line_number (in ${MDFILE:-the checked file if MD, or TEXFILE if TeX})"
    if [[ -n "$problem_snippet" ]]; then
        echo "  Problem snippet: $problem_snippet"
    fi
    if [[ -n "$line_content_raw" ]]; then
      echo "  Full line content: $line_content_raw"
    fi
    echo
    reporter_show_context_block "$line_number" # Shows TeX context by default
    echo
    echo "Hint: Please review the source file (Markdown or TeX) around the reported line for potential static errors."
    echo
  fi
}

# Original function for handling compilation errors
reporter_emit() {
  local line_number="${1:-unknown}"
  local excerpt="${2:-}"
  local hint_json="${3:-[]}"
  local context_block="${4:-}" 

  if [[ -z "$line_number" || "$line_number" == "unknown" ]]; then
    line_number="unknown"
  fi

  if ! echo "$hint_json" | jq empty >/dev/null 2>&1; then
    hint_json="[]"
  fi

  local primary_hint
  primary_hint=$(echo "$hint_json" | jq -r '.[0].message // empty' | sed -E 's/^Error: //')

  if [[ -n "$primary_hint" ]]; then
    echo "Error: $primary_hint"
  else
    echo "Error: Problem detected during LaTeX compilation near line $line_number."
  fi
  echo

  if [[ -n "$excerpt" ]]; then
    echo "$excerpt" | sed 's/^/  /'
    echo
  fi

  if [[ -n "$context_block" ]]; then
    echo "$context_block"
  else
    reporter_show_context_block "$line_number" 
  fi
  echo

  reporter_format_hints "$hint_json"
  echo
}

reporter_show_context_block() {
  local line="${1:-unknown}" # This line number is assumed to be for TEXFILE

  if [[ "$line" == "unknown" ]]; then
    echo "  [LaTeX source line unknown — no context to show.]"
    return
  fi

  if [[ ! -f "${TEXFILE:-}" ]]; then
    echo "  [No LaTeX source available (TEXFILE='${TEXFILE:-not set}') to show context.]"
    return
  fi

  local begin_doc_line
  begin_doc_line=$(grep -n '\\begin{document}' "$TEXFILE" | head -n1 | cut -d: -f1)
  [[ -z "$begin_doc_line" ]] && begin_doc_line=1 

  local start_offset=3 
  local end_offset=4   

  local start_line=$(( line - start_offset ))
  (( start_line < begin_doc_line )) && start_line=$begin_doc_line
  (( start_line < 1 )) && start_line=1

  local end_line=$(( line + end_offset ))

  echo "Context (lines $start_line to $end_line of TeX file '${TEXFILE##*/}'):" # Show only filename
  nl -w6 -ba "$TEXFILE" | sed -n "${start_line},${end_line}p" | \
    sed -E "s/^ *([0-9]+)/\1 /" | \
    sed -E "s/^($line)\s/>> \1 /" | sed 's/^/  /' 
}

reporter_format_hints() {
  local json="$1"
  [[ -z "$json" || "$json" == "[]" ]] && return 0

  echo "$json" | jq -r '.[1:] | .[] | select(.message != null and .message != "") | "Hint: " + .message'
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Usage: This script should be sourced." >&2
  echo "Available functions: reporter_emit, reporter_emit_proofreader_error" >&2
  exit 2
fi
