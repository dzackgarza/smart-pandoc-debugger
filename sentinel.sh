#!/usr/bin/env bash
# sentinel.sh — Static LaTeX delimiter checker (Sentinel)
#
# Role:
#   Scans LaTeX source for mismatched \left and \right delimiters.
#   Reports detailed diagnostics and exits nonzero if problems found.
#
# Usage:
#   sentinel.sh <texfile>
#
# Output:
#   On error: prints multi-line diagnostic, exits 1
#   On success: no output, exits 0
#
# Exit codes:
#   0 - no delimiter mismatch detected
#   1 - delimiter mismatch detected with diagnostic output
#   2 - misuse (missing or invalid texfile argument)
#
set -eo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <texfile>" >&2
  exit 2
fi

texfile="$1"
if [[ ! -f "$texfile" ]]; then
  echo "Error: TEXFILE '$texfile' not found." >&2
  exit 2
fi

problem_lines=$(awk '
  {
    left_count = gsub(/\\left/, "")
    right_count = gsub(/\\right/, "")
    if (left_count != right_count) print NR, "Unmatched \\left and \\right counts differ (" left_count " vs " right_count ")"
  }
' "$texfile")

if [[ -n "$problem_lines" ]]; then
  echo "Error: Detected unmatched \\left and \\right delimiters in LaTeX source."
  echo
  echo "Details:"
  while IFS=: read -r lineno msg; do
    echo "  Line $lineno: $msg"
    sed -n "${lineno}p" "$texfile" | sed 's/^/    /'
  done <<< "$problem_lines"
  echo
  echo "Hint: Check that every \\left has a matching \\right in the same context."
  exit 1
fi

exit 0

