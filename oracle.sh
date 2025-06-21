#!/usr/bin/env bash
# smart-pandoc-debugger oracle.sh — V1.3: heuristic fix suggestion engine with delegated seer and normalized output
#
# Version: 1.3
# Date: 2025-06-20
# Author: Diagnostic Systems Group
#
# ────────────────────────────────────────────────────────────────────────────────
# Role Overview — THE ORACLE
#
# The Oracle is the primary diagnostic engine that:
#   • Receives LaTeX error logs and metadata
#   • Performs heuristic matching against known error patterns
#   • Delegates complex pattern detection to the Seer sub-module
#   • Aggregates and emits JSON-formatted fix suggestions with contextual hints
#   • Ensures output always includes an "Error: <specific message>" in at least one suggestion if available
#
# Responsibilities:
#   • Match common LaTeX error signatures with concise heuristics
#   • Invoke Seer for delegated complex or lengthy heuristics
#   • Combine all suggestions with confidence and origin metadata
#
# Each suggestion is a JSON object of the form:
#   {
#     "message": "Hint: Unmatched \\left without matching \\right near line 60.",
#     "confidence": 0.9,
#     "origin": "oracle::delimiter_rules"
#   }
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
#   • Suggestions may be empty (output: `[]`)
#
# Exit Codes:
#   0 — Success (even with no suggestions)
#   1 — Internal failure
#
# Requirements:
#   • bash, grep, python3
#   • Designed to be < 100 lines (excluding seer.sh invocation)
#
# ────────────────────────────────────────────────────────────────────────────────

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
# Oracle Heuristic Rules (common straightforward cases)
# ────────────────────────────────────────────────────────────────────────────────

# 1. Unmatched \left without \right
if grep -q -e "Missing \\right" -e "Extra \\left" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Unmatched '\\left' detected — missing matching '\\right'. Check math delimiters near line $ERROR_LINE." \
    0.95 "oracle::delimiter_rules"
fi

# 2. Unterminated inline math (missing closing $)
if grep -qi "Missing \\$ inserted" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Unterminated inline math detected — missing closing '\$' delimiter near line $ERROR_LINE." \
    0.95 "oracle::math_mode"
fi

# 3. Extra or stray closing brace }
if grep -qi "Extra }" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Unexpected '}' detected — possible extra brace or missing '\$' delimiter near line $ERROR_LINE." \
    0.85 "oracle::brace_rules"
fi

# 4. Unbalanced curly braces (missing } or extra {)
if grep -qi "File ended while scanning use of" <<<"$ERROR_SNIPPET" || grep -qi "Runaway argument?" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Unbalanced braces detected — check for missing '}' or extra '{' near line $ERROR_LINE." \
    0.9 "oracle::brace_rules"
fi

# 5. Mismatched brackets in math (e.g. \left[ ... \right) )
if grep -qi "Mismatch" <<<"$ERROR_SNIPPET" || grep -qi "Extra }" <<<"$ERROR_SNIPPET" && grep -qi -e "\\left\\[" -e "\\right)" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Mismatched brackets in math — '\\left[' does not match '\\right)' near line $ERROR_LINE." \
    0.9 "oracle::delimiter_rules"
fi

# 6. Undefined command detected (report command name if possible)
if grep -qi "Undefined control sequence" <<<"$ERROR_SNIPPET"; then
  # Extract command if available
  cmd=$(echo "$ERROR_SNIPPET" | grep -oP '\\\\\w+' | head -1)
  if [[ -n "$cmd" ]]; then
    add_suggestion \
      "Error: Undefined command '$cmd' found — check for typos or missing packages near line $ERROR_LINE." \
      0.85 "oracle::undefined_command"
  else
    add_suggestion \
      "Error: Undefined command detected — check for typos or missing packages near line $ERROR_LINE." \
      0.8 "oracle::undefined_command"
  fi
fi

# 7. Extra closing brace in math expressions (e.g., inside \frac)
if grep -qi "Extra }" <<<"$ERROR_SNIPPET" && grep -qi "\\frac" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Extra '}' detected — brace mismatch in math expression near line $ERROR_LINE." \
    0.9 "oracle::brace_rules"
fi

# 8. Missing environment closure (e.g. missing \end{align})
if grep -qi "Missing \\end" <<<"$ERROR_SNIPPET" || grep -qi "Runaway argument?" <<<"$ERROR_SNIPPET"; then
  # Try to extract env name
  env_name=$(echo "$ERROR_SNIPPET" | grep -oP '(?<=\\end\{)[^}]+' | head -1)
  if [[ -z "$env_name" ]]; then
    env_name="environment"
  fi
  add_suggestion \
    "Error: Environment '$env_name' not properly closed — missing '\\end{$env_name}' near line $ERROR_LINE." \
    0.9 "oracle::env_closure"
fi

# 9. Nested or conflicting $ math delimiters
if grep -qi -e "Extra $" -e "Missing $ inserted" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Conflicting math delimiters detected — nested or extra '\$' found near line $ERROR_LINE." \
    0.85 "oracle::math_mode"
fi

# 10. Unexpected '\' in text (non-math stray backslash)
if grep -qi "Missing $" <<<"$ERROR_SNIPPET" && grep -qi "You can't use" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Unexpected '\\' in text — likely missing escape or math delimiters near line $ERROR_LINE." \
    0.85 "oracle::bare_backslash"
fi

# 11. Non-breaking space (U+00A0) inside math
if grep -q "Unicode char U+00A0" <<<"$ERROR_SNIPPET" || grep -q $'\xC2\xA0' <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Non-breaking space (U+00A0) detected inside math — replace with normal space near line $ERROR_LINE." \
    0.9 "oracle::nbsp_in_math"
fi

# 12. Unicode characters in math
if grep -qi "Unicode character" <<<"$ERROR_SNIPPET"; then
  # Extract first unicode char mentioned if possible
  uch=$(echo "$ERROR_SNIPPET" | grep -oP '(?<=Unicode character)[^ ]+' | head -1 | tr -d "'")
  if [[ -z "$uch" ]]; then
    uch="?"
  fi
  add_suggestion \
    "Error: Unicode character '$uch' detected inside math — may cause compilation issues near line $ERROR_LINE." \
    0.9 "oracle::unicode"
fi

# 13. Unmatched environment ends (e.g. \end{equation} without \begin{equation})
if grep -qi "Extra \\end" <<<"$ERROR_SNIPPET"; then
  env_end=$(echo "$ERROR_SNIPPET" | grep -oP '(?<=\\end\{)[^}]+' | head -1)
  add_suggestion \
    "Error: '\\end{$env_end}' without matching '\\begin{$env_end}' near line $ERROR_LINE." \
    0.9 "oracle::env_mismatch"
fi

# 14. Environment nesting mismatches (e.g., enumerate closed by end{itemize})
if grep -qi "Environment nesting mismatch" <<<"$ERROR_SNIPPET"; then
  # Extract involved envs if possible
  env_open=$(echo "$ERROR_SNIPPET" | grep -oP '(?<=opening environment )\w+' | head -1)
  env_close=$(echo "$ERROR_SNIPPET" | grep -oP '(?<=closing environment )\w+' | head -1)
  if [[ -z "$env_open" || -z "$env_close" ]]; then
    add_suggestion \
      "Error: Environment nesting mismatch detected near line $ERROR_LINE." \
      0.9 "oracle::env_nesting"
  else
    add_suggestion \
      "Error: Environment nesting mismatch — '$env_open' closed by '\\end{$env_close}' near line $ERROR_LINE." \
      0.95 "oracle::env_nesting"
  fi
fi

# 15. Invalid UTF-8 byte sequences
if grep -qi "Invalid UTF-8" <<<"$ERROR_SNIPPET" || grep -qi "UTF-8 decoding error" <<<"$ERROR_SNIPPET"; then
  add_suggestion \
    "Error: Invalid UTF-8 byte sequence detected — check file encoding near line $ERROR_LINE." \
    0.9 "oracle::utf8_error"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Delegate complex heuristics to Seer sub-module (oracle-team/seer.sh)
# ────────────────────────────────────────────────────────────────────────────────

seer_path="$(dirname "$0")/oracle-team/seer.sh"
seer_output="[]"
if [[ -x "$seer_path" ]]; then
  seer_output=$(ERROR_SNIPPET="$ERROR_SNIPPET" ERROR_LINE="$ERROR_LINE" MARKDOWN_CONTEXT="$MARKDOWN_CONTEXT" "$seer_path") || seer_output="[]"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Merge Oracle and Seer suggestions
# ────────────────────────────────────────────────────────────────────────────────

merge_json_arrays() {
  local arr1="$1"
  local arr2="$2"
  local clean1 clean2
  clean1=$(echo "$arr1" | sed -e '1d' -e '$d' | tr -d '\n' | sed 's/^\s*//;s/\s*$//')
  clean2=$(echo "$arr2" | sed -e '1d' -e '$d' | tr -d '\n' | sed 's/^\s*//;s/\s*$//')
  if [[ -z "$clean1" ]]; then
    echo "[$clean2]"
  elif [[ -z "$clean2" ]]; then
    echo "[$clean1]"
  else
    echo "[$clean1,$clean2]"
  fi
}

combined_json=$(merge_json_arrays "$(printf '[%s]\n' "$(IFS=,; echo "${suggestions[*]}")")" "$seer_output")

has_error_prefix=$(echo "$combined_json" | jq '[.[] | select(.message | test("^Error:"))] | length')

if [[ "$has_error_prefix" -eq 0 ]] && [[ $(echo "$combined_json" | jq 'length') -gt 0 ]]; then
  combined_json=$(echo "$combined_json" | jq '.[0].message |= ("Error: " + .) | .')
fi

echo "$combined_json"
exit 0

