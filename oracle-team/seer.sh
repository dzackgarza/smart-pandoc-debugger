#!/usr/bin/env bash
# smart-pandoc-debugger oracle-team/seer.sh — V1.1: focused LaTeX error pattern interpreter
#
# Version: 1.1
# Date: 2025-06-20
# Author: Diagnostic Systems Group
#
# ────────────────────────────────────────────────────────────────────────────────
# Role Overview — THE SEER
#
# The Seer is a specialized sub-role under the Oracle’s management.
# It focuses on detailed interpretation of cryptic LaTeX error snippets,
# detecting specific complex patterns that the Oracle delegates due to
# complexity or length constraints.
#
# Responsibilities:
#   • Identify advanced or subtle LaTeX error patterns (e.g. environment mismatches,
#     nested math delimiters, encoding issues)
#   • Emit well-formed JSON fix suggestions with messages, confidences, and origins
#   • Operate within a ~100 lines script limit; offload large or ML-based tasks externally
#
# The Seer’s output is consumed by the Oracle, which aggregates and normalizes
# all fix suggestions before presenting to the user.
#
# ────────────────────────────────────────────────────────────────────────────────
# Interface Contract
#
# Inputs:
#   • ERROR_SNIPPET    (env): LaTeX error excerpt (stdin fallback)
#   • ERROR_LINE       (env): Line number in TEXFILE (default: "unknown")
#   • MARKDOWN_CONTEXT (env): Markdown near error (currently unused)
#
# Output:
#   • JSON array to stdout (valid UTF-8)
#   • May emit empty array `[]` if no matches found
#
# Exit Codes:
#   0 — Success (even if no suggestions)
#   1 — Internal failure
#
# Requirements:
#   • bash, grep, python3
#
# ────────────────────────────────────────────────────────────────────────────────
# Versioning and Documentation Note:
#
# When updating Seer:
#   • Increment minor version (e.g., 1.1 → 1.2)
#   • Update date and version in header
#   • Maintain clear and current role overview and interface docs
#
# This ensures clean delegation and traceability within the oracle-team.
#

set -eo pipefail

ERROR_SNIPPET="${ERROR_SNIPPET:-$(cat)}"
ERROR_LINE="${ERROR_LINE:-unknown}"
MARKDOWN_CONTEXT="${MARKDOWN_CONTEXT:-}"

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()), end="")'
}

declare -a suggestions=()

add_suggestion() {
  local msg="$1" conf="$2" tag="$3"
  suggestions+=("{
    \"message\": $(printf '%s' "$msg" | json_escape),
    \"confidence\": $conf,
    \"origin\": $(printf '%s' "$tag" | json_escape)
  }")
}

# ────────────────────────────────────────────────────────────────────────────────
# Heuristic Rules — Complex / delegated patterns
# ────────────────────────────────────────────────────────────────────────────────

# Rule: Mismatched brackets (e.g. \left[ vs \right))
if grep -q "Mismatch between \\left" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Mismatched brackets detected (e.g. '\\left[' vs '\\right)'). Verify paired delimiters near line $ERROR_LINE." \
    0.9 "seer::brackets"
fi

# Rule: Unclosed environment (\begin without \end)
if grep -q "Runaway argument?" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Possible unclosed environment detected — missing '\\end{...}' near line $ERROR_LINE." \
    0.9 "seer::env_unclosed"
fi

# Rule: Nested or unclosed inline math delimiters ($...$)
if grep -q "Extra $" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Nested or unclosed inline math delimiters ('$') found — check math environments near line $ERROR_LINE." \
    0.85 "seer::dollar_nesting"
fi

# Rule: Bare backslash in text
if grep -q -i "Missing \\" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Stray or bare backslash detected in text — verify escapes near line $ERROR_LINE." \
    0.8 "seer::bare_backslash"
fi

# Rule: Non-breaking space (U+00A0) inside math
if grep -q "Non-breaking space" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Non-breaking space (U+00A0) detected inside math mode — may cause issues near line $ERROR_LINE." \
    0.85 "seer::nbsp_in_math"
fi

# Rule: Environment mismatch (wrong \end{})
if grep -q "Environment" <<<"$ERROR_SNIPPET" && grep -q "ended by \\end" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Environment mismatch detected — improper '\\end{...}' statement near line $ERROR_LINE." \
    0.9 "seer::env_mismatch"
fi

# Rule: Invalid UTF-8 byte sequence
if grep -q -i "Invalid UTF-8" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Invalid UTF-8 byte sequence detected in source — check encoding near line $ERROR_LINE." \
    0.9 "seer::utf8_error"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Output all matching suggestions as JSON array
# ────────────────────────────────────────────────────────────────────────────────

if [[ ${#suggestions[@]} -eq 0 ]]; then
  echo "[]"
  exit 0
fi

{
  echo "["
  local i
  for i in "${!suggestions[@]}"; do
    (( i > 0 )) && echo ","
    echo "${suggestions[$i]}"
  done
  echo "]"
}

exit 0

