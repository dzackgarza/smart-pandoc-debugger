#!/usr/bin/env bash
# smart-pandoc-debugger librarian.sh — V1.1: context viewer for LaTeX diagnostics
#
# Version: 1.1
# Date: 2025-06-20
# Author: Diagnostic Systems Group
#
# ────────────────────────────────────────────────────────────────────────────────
# Role Overview — The LIBRARIAN
#
# The Librarian displays a window of context lines from a LaTeX source file
# around a specified line number to aid debugging.
#
# Responsibilities:
#   • Show ~8 lines total: typically 3 lines before, target line (highlighted),
#     and 4 lines after.
#   • Include line numbers and mark the exact target line with a ">>" prefix.
#   • Ensure the context window includes \begin{document} line if it precedes
#     the context start.
#   • Handle errors near file start or end gracefully.
#   • Print a clear message if TEXFILE is missing or unreadable.
#
# ────────────────────────────────────────────────────────────────────────────────
# Interface Contract with Coordinator
#
# Environment variables:
#   TEXFILE        — path to the LaTeX source file (required)
#
# Invocation:
#   source librarian.sh && librarian_show_context <line>
#
# Input:
#   <line>         — positive integer line number to highlight
#
# Output:
#   - Plain UTF-8 text, no colors or formatting
#   - Context lines with line numbers
#   - Target line prefixed with ">>"
#   - Prints "Context (lines X to Y):" header
#
# Exit codes:
#   0 — success
#   1 — misuse (missing TEXFILE, invalid line argument, or unreadable file)
#
# ────────────────────────────────────────────────────────────────────────────────
# Script Length Guideline:
#
# To maintain readability and modularity, roles whose scripts exceed ~100 lines
# should delegate internal tasks to sub-scripts or helper functions.
#
# This script is intentionally concise (<70 lines).
#
# ────────────────────────────────────────────────────────────────────────────────

set -eo pipefail

librarian_show_context() {
  local line="$1"

  # Validate TEXFILE
  if [[ -z "$TEXFILE" ]]; then
    echo "Error: librarian_show_context requires TEXFILE environment variable to be set." >&2
    return 1
  fi
  if [[ ! -f "$TEXFILE" ]]; then
    echo "Error: TEXFILE '$TEXFILE' does not exist or is not a regular file." >&2
    return 1
  fi

  # Validate line argument
  if [[ -z "$line" ]]; then
    echo "Error: librarian_show_context requires a line number argument." >&2
    return 1
  fi
  if ! [[ "$line" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: librarian_show_context line argument must be a positive integer." >&2
    return 1
  fi

  # Find \begin{document} line number (default 1 if missing)
  local begin_line
  begin_line=$(grep -n '\\begin{document}' "$TEXFILE" | head -n1 | cut -d: -f1)
  [[ -z "$begin_line" ]] && begin_line=1

  # Determine context window: 3 lines before, target line, 4 lines after
  # Ensure start line ≥ begin_line
  local start=$(( line > 3 ? line - 3 : begin_line ))
  (( start < begin_line )) && start=$begin_line
  local end=$(( line + 4 ))

  # Include \begin{document} line if it is before start
  if (( begin_line < start )); then
    start=$begin_line
  fi

  # Determine total lines in TEXFILE to avoid overshoot
  local total_lines
  total_lines=$(wc -l < "$TEXFILE")
  (( end > total_lines )) && end=$total_lines

  # Output header
  echo "Context (lines $start to $end):"

  # Print numbered lines with target line highlighted by ">>"
  nl -ba "$TEXFILE" | sed -n "${start},${end}p" | sed -E "s/^ *$line\b/>> &/"
}

# Optional direct invocation
if [[ "${1:-}" == "librarian_show_context" ]]; then
  shift
  librarian_show_context "$@"
fi

