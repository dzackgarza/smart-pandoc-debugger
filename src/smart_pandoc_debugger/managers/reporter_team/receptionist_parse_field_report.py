#!/usr/bin/env python3
# receptionist_parse_field_report.py
#
# Role: RECEPTIONIST (Proofreader Data Standardizer)
#
# This script acts as the "Receptionist" for the Reporter component.
# It receives raw, multi-line "KEY=VALUE" formatted data from various
# Proofreader checker scripts via stdin.
#
# Its primary responsibilities are:
#   1. Parse the KEY=VALUE input string.
#   2. Standardize the keys into a consistent `snake_case` format.
#   3. Standardize the *value* of the `error_type` key to `snake_case`
#      to ensure consistent dispatching by the Reporter.
#   4. Add potentially useful contextual information (like file paths from
#      environment variables) to the payload.
#   5. Output a single, standardized JSON object to stdout, which is then
#      consumed by the main Reporter script (reporter.py).
#
# Input:
#   - Multi-line string from stdin, where each line is expected to be
#     in "KEY=VALUE" format (e.g., "ERROR_TYPE=SomeError\nLINE_NUMBER=10").
#
# Output:
#   - A single JSON string to stdout representing the parsed and standardized report.
#   - In case of critical JSON serialization failure, an error JSON is printed
#     to stderr, and the script exits with status 1.
#
# Environment Variables Used:
#   - MDFILE: Path to the primary Markdown file (used for hints).
#   - TEXFILE: Path to the primary TeX file (used for hints).
#
# Key Standardization:
#   - A `KEY_MAP` dictionary is used to translate known keys from Proofreader
#     checkers (which might be in UPPER_CASE or other formats) to a
#     consistent `snake_case` format for the JSON output.
#   - Unknown keys are prefixed with "unknown_" and converted to lowercase.
#
# Error Type Value Standardization:
#   - The *value* associated with the "error_type" key (after key mapping)
#     is explicitly converted to `snake_case`. For example, if a checker outputs
#     "ERROR_TYPE=UnclosedMarkdownEnvironment", the final JSON will have
#     `"error_type": "unclosed_markdown_environment"`. This is critical for
#     reliable dispatching in `reporter.py`.

import sys
import json
import os
import re

def to_snake_case(name: str) -> str:
    """
    Converts a string from CamelCase or PascalCase to snake_case.
    Example: "UnclosedMarkdownEnvironment" -> "unclosed_markdown_environment"
             "SomeError" -> "some_error"
             "ERROR_TYPE" -> "error_type" (if passed directly, though key_map handles this)
    """
    if not name:
        return ""
    # Handle full UPPERCASE_WITH_UNDERSCORES by just lowercasing
    if name.isupper() and '_' in name:
        return name.lower()
    
    # Insert underscore before uppercase letters (except if it's the first char)
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insert underscore between lowercase/digit and uppercase
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()

def main():
    """
    Reads KEY=VALUE data from stdin, standardizes it, and prints JSON to stdout.
    """
    raw_data_string = sys.stdin.read()
    
    report_dict = {}

    # KEY_MAP: Defines the authoritative snake_case keys for the output JSON.
    # Input keys from Proofreader checkers are mapped to these.
    key_map = {
        # General
        "ERROR_TYPE": "error_type",
        "LINE_NUMBER": "line_number",
        "LINE_CONTENT": "line_content_raw", # Raw content from the file
        "PROBLEM_SNIPPET": "problem_snippet", # Specific part causing the error

        # For TeX unmatched \left/\right errors
        "LEFT_COUNT": "left_count",
        "RIGHT_COUNT": "right_count",

        # For TeX unbalanced braces errors
        "OPEN_COUNT": "open_count",
        "CLOSE_COUNT": "close_count",

        # For TeX mismatched paired delimiters
        "OPENING_DELIM_CHAR": "opening_delim_char",
        "CLOSING_DELIM_CHAR": "closing_delim_char",

        # For Markdown unclosed dollar (inline math)
        # Note: These keys might be from a Python checker, ensure they match.
        "OPEN_DELIM_COUNT": "open_delim_count",
        "CLOSE_DELIM_COUNT": "close_delim_count",

        # For Markdown environment issues (e.g., unclosed, mismatched)
        "ENV_NAME": "env_name",                   # Name of the environment in question
        "EXPECTED_ENV_NAME": "expected_env_name", # For mismatched errors
        "FOUND_ENV_NAME": "found_env_name",       # For mismatched errors
        
        # Add more mappings here as new Proofreader checkers are developed
        # or existing ones output new KEY=VALUE pairs.
    }

    # Parse the input KEY=VALUE string
    for line_item in raw_data_string.strip().split('\n'):
        if not line_item.strip(): # Skip empty lines
            continue
        if '=' in line_item:
            key, value = line_item.split('=', 1)
            original_key_stripped = key.strip()
            value_stripped = value.strip()

            # Use the mapped key if available, otherwise create a generic one
            mapped_key = key_map.get(original_key_stripped)
            if mapped_key:
                report_dict[mapped_key] = value_stripped
            else:
                # For unknown keys, store them with a prefix and in snake_case
                # This helps in identifying new/unexpected data from checkers.
                report_dict[f"unknown_{to_snake_case(original_key_stripped)}"] = value_stripped
        else:
            # Handle lines without '=', perhaps log them or store as a special key
            # For now, we'll store it if it's the first such line, to capture malformed input.
            if "malformed_input_line" not in report_dict:
                report_dict["malformed_input_line"] = line_item.strip()


    # --- Data Standardization and Enrichment ---

    # 1. Standardize the *value* of 'error_type' to snake_case.
    #    This is crucial for consistent dispatching in reporter.py.
    if "error_type" in report_dict:
        report_dict["error_type"] = to_snake_case(str(report_dict["error_type"]))
    else:
        # If ERROR_TYPE was somehow missed, provide a default.
        report_dict["error_type"] = "unknown_proofreader_error"

    # 2. Normalize/default 'line_number'
    #    Ensure it's a string representing a number or "unknown".
    raw_line_num = report_dict.get("line_number")
    if raw_line_num is None or not str(raw_line_num).isdigit() or int(raw_line_num) <= 0:
        report_dict["line_number"] = "unknown"
    else:
        report_dict["line_number"] = str(raw_line_num) # Ensure it's a string

    # 3. Default 'problem_snippet' if not provided but 'line_content_raw' is.
    if "problem_snippet" not in report_dict and report_dict.get("line_content_raw"):
        report_dict["problem_snippet"] = report_dict.get("line_content_raw")

    # 4. Add file paths for context/hints (useful for specialist reporters).
    #    These come from environment variables set by the Coordinator.
    report_dict["md_file_for_hint"] = os.environ.get("MDFILE", "not_specified.md")
    report_dict["tex_file_for_hint"] = os.environ.get("TEXFILE", "not_specified.tex")


    # --- Output JSON ---
    try:
        # Print the final standardized JSON object to stdout.
        print(json.dumps(report_dict))
    except TypeError as e:
        # This is a fallback for a critical error during JSON serialization.
        # Output an error report to stderr to avoid corrupting stdout for the Reporter.
        critical_error_report = {
            "receptionist_json_serialization_error": True,
            "error_message": str(e),
            "original_dict_preview": {k: str(v)[:50] + '...' if len(str(v)) > 50 else str(v) 
                                      for k, v in report_dict.items()}, # Preview of dict
            "raw_input_data_preview": raw_data_string[:200] + ('...' if len(raw_data_string) > 200 else '')
        }
        print(json.dumps(critical_error_report), file=sys.stderr)
        sys.exit(1) # Signal an error to the calling script (reporter.py)

if __name__ == "__main__":
    main()
