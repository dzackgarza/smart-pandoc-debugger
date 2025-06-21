#!/usr/bin/env bash
# context_viewer.sh — Context Viewer role: show LaTeX source lines around error
#
# Input:
#   - TEXFILE: path to intermediate LaTeX (.tex) file (env var)
#   - ERROR_LINE: line number near which to show context (env var or arg)
#
# Output:
#   Prints a context block of lines with the error line highlighted by prefix ">> "
#
# Exit codes:
#   0 on success, 1 if TEXFILE missing or ERROR_LINE invalid

set -eo pipefail

# Validate TEXFILE
if [[ -z "$TEXFILE" || ! -f "$TEXFILE" ]]; then
  echo "context_viewer.sh: TEXFILE environment variable not set or file not found" >&2
  exit 1
fi

# Accept error line either from env or first arg
ERROR_LINE="${ERROR_LINE:-${1:-}}"
if ! [[ "$ERROR_LINE" =~ ^[0-9]+$ ]]; then
  echo "context_viewer.sh: ERROR_LINE not set or not a valid number" >&2
  exit 1
fi

# Find \begin{document} line number, default to 1 if not found
BEGIN_DOC_LINE=$(awk '/\\begin{document}/ {print NR; exit}' "$TEXFILE")
BEGIN_DOC_LINE="${BEGIN_DOC_LINE:-1}"

# Compute start and end lines for context window
START_LINE=$(( ERROR_LINE > 30 ? ERROR_LINE - 30 : BEGIN_DOC_LINE ))
(( START_LINE < BEGIN_DOC_LINE )) && START_LINE=$BEGIN_DOC_LINE
END_LINE=$(( ERROR_LINE + 5 ))

# Print header
echo "Context (lines $START_LINE to $END_LINE):"

# Print lines with numbering and highlight error line
awk -v start="$START_LINE" -v end="$END_LINE" -v error="$ERROR_LINE" '
  NR >= start && NR <= end {
    prefix = (NR == error) ? ">> " : "   "
    printf "%s%5d\t%s\n", prefix, NR, $0
  }
' "$TEXFILE"

exit 0

