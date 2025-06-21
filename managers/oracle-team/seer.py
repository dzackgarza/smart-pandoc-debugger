#!/usr/bin/env bash
# smart-pandoc-debugger oracle-team/seer.sh — V1.3: YAML-Rule Driven LaTeX Error Interpreter
#
# Version: 1.3
# Date: 2025-06-25 (Updated from V1.2)
# Author: Diagnostic Systems Group
#
# ────────────────────────────────────────────────────────────────────────────────
# Role Overview — THE SEER
#
# Interprets LaTeX error snippets based on rules defined in an external YAML file.
# Detects specific complex patterns and emits JSON suggestions.
#
# Responsibilities:
#   • Load error patterns and suggestion templates from 'seer_rules.yaml'.
#   • Match patterns against the provided error snippet.
#   • For each match, format a suggestion using the template and provided context.
#   • Emit all generated suggestions as a JSON array to stdout.
#
# The Seer’s output is consumed by Oracle.py.
#
# ────────────────────────────────────────────────────────────────────────────────
# Interface Contract (V1.3)
#
# Invocation (by Oracle.py via process_runner.run_script):
#   bash seer.sh --error-snippet "LaTeX log excerpt" --error-line "123" \
#                [--rules-file /path/to/seer_rules.yaml]
#
# Command-line Arguments:
#   --error-snippet <string> : (Required) The LaTeX error excerpt to analyze.
#   --error-line <string>    : (Optional) The line number in the TeX source. Defaults to "unknown".
#   --rules-file <path>      : (Optional) Path to the YAML rules file.
#                              Defaults to 'seer_rules.yaml' in the same directory as this script.
#
# Environment Variables (Optional):
#   • MARKDOWN_CONTEXT : Markdown near error (currently unused by this script).
#
# Output (to stdout):
#   • A JSON array of "suggestion" objects (valid UTF-8).
#   • Example suggestion: {"message": "...", "confidence": 0.9, "origin_tag": "seer::rule_name"}
#     (Note: 'origin_tag' from YAML is used directly for 'origin' in JSON output)
#   • Emits `[]` if no rules match.
#
# Exit Codes:
#   0 — Success (analysis complete, JSON array printed).
#   1 — Internal script failure (e.g., Python error, YAML parsing error).
#   2 — Usage error (e.g., missing arguments, rules file not found).
#
# Requirements:
#   • bash, grep, python3 (with PyYAML library: `pip install PyYAML`)
#
# ────────────────────────────────────────────────────────────────────────────────

set -eo pipefail

# --- Argument Parsing ---
ERROR_SNIPPET=""
ERROR_LINE="unknown"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_FILE="${SCRIPT_DIR}/seer_rules.yaml" # Default rules file path

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --error-snippet)
      ERROR_SNIPPET="$2"
      shift 2
      ;;
    --error-line)
      ERROR_LINE="$2"
      shift 2
      ;;
    --rules-file)
      RULES_FILE="$2"
      shift 2
      ;;
    *)
      echo "Error: Unknown option or missing value for $1" >&2
      echo "Usage: $0 --error-snippet \"<snippet>\" [--error-line \"<line_num>\"] [--rules-file <path_to_rules.yaml>]" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$ERROR_SNIPPET" ]]; then
  echo "Error: --error-snippet argument is required." >&2
  echo "Usage: $0 --error-snippet \"<snippet>\" [--error-line \"<line_num>\"] [--rules-file <path_to_rules.yaml>]" >&2
  exit 2
fi

if [[ ! -f "$RULES_FILE" ]]; then
  echo "Error: Rules file not found at '$RULES_FILE'" >&2
  exit 2
fi

# MARKDOWN_CONTEXT remains an optional environment variable, currently unused by rules.
MARKDOWN_CONTEXT="${MARKDOWN_CONTEXT:-}"

# --- Helper Functions ---
json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()), end="")'
}

# --- Python script to parse YAML and process rules ---
# This embedded Python script avoids dependency on 'yq'
# Requires PyYAML: pip install PyYAML

read -r -d '' PYTHON_SCRIPT_TO_PROCESS_RULES <<EOF
import yaml
import json
import sys
import re
import os

def process_rules(rules_file_path, error_snippet, error_line):
    try:
        with open(rules_file_path, 'r') as f:
            rules = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading/parsing YAML rules file '{rules_file_path}': {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(rules, list):
        print(f"Error: Rules file '{rules_file_path}' does not contain a list of rules at the top level.", file=sys.stderr)
        sys.exit(1)

    matched_suggestions = []

    for rule in rules:
        if not isinstance(rule, dict):
            print(f"Warning: Skipping invalid rule entry (not a dictionary): {rule}", file=sys.stderr)
            continue

        pattern = rule.get("pattern")
        message_template = rule.get("message")
        confidence = rule.get("confidence", 0.5) # Default confidence
        origin_tag = rule.get("origin_tag", f"seer::unknown_rule_{rule.get('name', 'unnamed')}")
        match_type = rule.get("match_type", "string") # Default to string match

        if not pattern or not message_template:
            print(f"Warning: Skipping rule due to missing pattern or message: {rule.get('name', rule)}", file=sys.stderr)
            continue

        match_found = False
        try:
            if match_type == "regex":
                # For grep -E (ERE), pattern might need to be as is.
                # For Python re.search, ensure pattern is valid Python regex.
                # The YAML patterns should be written for grep -E if we stick to grep,
                # or Python re if we use Python for matching.
                # Let's assume Python re.search here for consistency.
                if re.search(pattern, error_snippet, re.IGNORECASE): # Added re.IGNORECASE
                    match_found = True
            elif match_type == "string": # Case-insensitive fixed string search
                if pattern.lower() in error_snippet.lower():
                    match_found = True
            else:
                print(f"Warning: Unknown match_type '{match_type}' for rule {rule.get('name')}. Skipping.", file=sys.stderr)
                continue
        except re.error as e_re:
            print(f"Warning: Invalid regex pattern '{pattern}' for rule {rule.get('name')}. Error: {e_re}. Skipping.", file=sys.stderr)
            continue


        if match_found:
            # Substitute placeholders in the message
            formatted_message = message_template.replace("%%ERROR_LINE%%", str(error_line))
            
            suggestion = {
                "message": formatted_message,
                "confidence": float(confidence),
                "origin": origin_tag 
            }
            matched_suggestions.append(suggestion)

    # Output the list of suggestion objects as a JSON array string
    print(json.dumps(matched_suggestions))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Python script usage: script.py <rules_file_path> <error_snippet_stdin_surrogate> <error_line>", file=sys.stderr)
        # <error_snippet_stdin_surrogate> is just a placeholder because snippet is piped to stdin for this python script
        sys.exit(1)
    
    # Read error_snippet from stdin for the Python script
    # The bash script will pipe ERROR_SNIPPET to this Python script's stdin
    actual_error_snippet = sys.stdin.read()

    rules_f_path = sys.argv[1]
    # sys.argv[2] is a placeholder for error_snippet when calling python, actual snippet via stdin
    err_line = sys.argv[3]
    
    process_rules(rules_f_path, actual_error_snippet, err_line)
EOF

# --- Execute Rule Processing ---
# Pass ERROR_SNIPPET via stdin to the Python script for safe handling of multiline/special chars
# Pass other arguments as command-line args to the Python script
# The "stdin_placeholder" is just to satisfy sys.argv count in the Python script,
# as the actual snippet is piped.
output_json=$(printf "%s" "$ERROR_SNIPPET" | python3 -c "$PYTHON_SCRIPT_TO_PROCESS_RULES" "$RULES_FILE" "stdin_placeholder" "$ERROR_LINE")

# Check if python3 script execution failed (e.g. yaml parsing error, bad rule format)
# The python script itself exits 1 on such errors and prints to its stderr.
# The $() captures stdout. We rely on set -e to catch python3 non-zero exit.
# If python3 has an unhandled exception, it also exits non-zero.

echo "$output_json"
exit 0
