#!/usr/bin/env bash
# investigator.sh — V3: Structured log investigator for LaTeX build failures
#
# Version: 3.0
# Date: 2025-06-20
# Author: Diagnostic Systems Group
#
# ────────────────────────────────────────────────────────────────────────────────
# Role Overview — THE INVESTIGATOR
#
# Responsibilities:
#   • Parse raw pdflatex logs from Miner to locate the first critical LaTeX error.
#   • Extract and normalize error blocks to clean diagnostic excerpts.
#   • Extract approximate LaTeX source line number associated with the error.
#
# The Investigator owns all filtering, normalization, and line attribution logic.
#
# ────────────────────────────────────────────────────────────────────────────────
# Interface Contract (V3)
#
# Subcommands:
#   extract_latex_error_line
#       → Echo approximate TEXFILE line number (integer), or blank if none found.
#
#   filter_latex_log_excerpt
#       → Print a cleaned excerpt (≤ 40 lines) of the first LaTeX error block.
#
# Environment Variables:
#   Required:
#     LOGFILE  — path to raw pdflatex log file
#   Optional:
#     TEXFILE  — path to LaTeX source file (for fallback line extraction)
#     TMPDIR   — scratch directory (reserved, unused here)
#
# Output:
#   All output is UTF-8 plaintext on stdout.
#
# Exit Codes:
#   0 on success (including no errors found)
#   2 on usage error (e.g., missing LOGFILE)
#
# Dependencies:
#   Uses standard UNIX utilities: awk, grep, sed
#
# ────────────────────────────────────────────────────────────────────────────────

set -eo pipefail
export LC_ALL=C.UTF-8

usage() {
  cat <<EOF
Usage: $0 <subcommand>

Subcommands:
  extract_latex_error_line   # Echo first LaTeX error line number (int) or blank
  filter_latex_log_excerpt   # Print filtered excerpt of first LaTeX error block (≤ 40 lines)

Required environment:
  LOGFILE   - path to raw pdflatex log file

Optional:
  TEXFILE   - LaTeX source file (for fallback line extraction)
  TMPDIR    - (unused)

Exit codes:
  0 - success (even if no errors)
  2 - usage error (e.g. missing LOGFILE)
EOF
}

if [[ -z "$LOGFILE" ]]; then
  echo "Error: Environment variable LOGFILE is required." >&2
  usage >&2
  exit 2
fi

extract_latex_error_line() {
  # Primary extraction: Look for lines beginning with '!' (LaTeX error),
  # then next line matching "l.<number>", per pdflatex convention.
  local line
  line=$(awk '
    BEGIN { found=0 }
    /^! / { found=1; next }
    found && match($0, /^l\.([0-9]+)/, m) {
      print m[1]; exit
    }
  ' "$LOGFILE")

  if [[ -n "$line" ]]; then
    echo "$line"
    return 0
  fi

  # Fallback extraction: look for "<filename>:<line>:" patterns in log,
  # using basename of TEXFILE if available.
  if [[ -n "$TEXFILE" ]]; then
    local base
    base=$(basename "$TEXFILE")
    line=$(grep -Eo "(${base}):[0-9]+:" "$LOGFILE" | sed -E "s/.*${base}:([0-9]+):.*/\1/" | head -n1)
    if [[ -n "$line" ]]; then
      echo "$line"
      return 0
    fi
  fi

  # No line found: produce no output but exit 0 gracefully.
  return 0
}

filter_latex_log_excerpt() {
  # Extract the first LaTeX error block from the log:
  # Starts at line beginning with '!' and includes following lines until
  # two consecutive blank lines or known log markers appear.
  awk '
    BEGIN { in_error=0; blank=0 }
    /^!/ {
      in_error=1; blank=0
      print; next
    }
    in_error {
      if (/^\s*$/) {
        blank++
        if (blank > 1) { exit }
      } else {
        blank=0
      }
      print
    }
  ' "$LOGFILE" | sed -E '
    /^Transcript written on /d
    /^Output written on /d
    /^Here is how much /d
    /^\\.*Warning:/d
  ' | head -n 40
}

case "$1" in
  extract_latex_error_line) extract_latex_error_line ;;
  filter_latex_log_excerpt) filter_latex_log_excerpt ;;
  *)
    usage
    exit 2
    ;;
esac

