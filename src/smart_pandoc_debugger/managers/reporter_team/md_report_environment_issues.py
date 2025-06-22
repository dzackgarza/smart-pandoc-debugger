#!/usr/bin/env python3
# md_report_environment_issues.py - V1.1: Handles snake_case error_types
#
# Purpose: Generates user-facing reports for Markdown environment issues.
# Input (stdin): JSON object with details of the environment error.
#   Expected error_type values (snake_case):
#     - "unclosed_markdown_environment"
#     - "mismatched_markdown_environment"
# Output (stdout): Formatted error report.
# Output (stderr): Errors if JSON is malformed or error_type is unknown by this script.

import sys
import json
import os # For os.path.basename if used

def main():
    # --- V1.1: No header version/date comments needed for specialist scripts unless desired by you ---
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e: # Be specific with exception
        print(f"REPORTER_TEAM_ERROR ({os.path.basename(sys.argv[0])}): Could not decode JSON input: {e}", file=sys.stderr)
        sys.exit(1) # Exit with error if JSON is bad

    error_type = data.get("error_type", "unknown_markdown_environment_error") # Default to snake_case
    line_number = data.get("line_number", "unknown")
    problem_snippet = data.get("problem_snippet", "")
    line_content_raw = data.get("line_content_raw", "")
    # Use os.path.basename for a cleaner filename in output
    md_file_name_for_hint = os.path.basename(data.get("md_file_for_hint", "your_markdown_file.md"))
    env_name = data.get("env_name", "unknown_env") # Used by unclosed

    # --- V1.1: Changed expected error_type strings to snake_case ---
    if error_type == "unclosed_markdown_environment":
        print(f"Error: Unclosed Markdown environment '{env_name}'.")
        print(f"  The environment started with '{problem_snippet}' on or near line {line_number} of '{md_file_name_for_hint}',")
        print(f"  but no matching '\\end{{{env_name}}}' was found.")
        print()
        print(f"Details from '{md_file_name_for_hint}':")
        print(f"  Approx. Line of '\\begin{{{env_name}}}': {line_number}")
        # problem_snippet is often the \begin line itself for this error type
        print(f"  Reported problematic line content: {problem_snippet}") 
        # line_content_raw might be identical or slightly different based on checker
        if line_content_raw != problem_snippet:
            print(f"  Full raw line content (if different): {line_content_raw}")
        print()
        print(f"Hint: Check '{md_file_name_for_hint}' starting from line {line_number} for a missing '\\end{{{env_name}}}'.")
        print("      Ensure all environments are properly closed in your Markdown source.")
        print()

    elif error_type == "mismatched_markdown_environment":
        expected_env_name = data.get("expected_env_name", "N/A_expected") # More distinct default
        found_env_name = data.get("found_env_name", "N/A_found")     # More distinct default

        if expected_env_name == "N/A_expected": # Indicates a stray \end{}
            print(f"Error: Unexpected closing environment '\\end{{{found_env_name}}}' in Markdown.")
            print(f"  Found on or near line {line_number} of '{md_file_name_for_hint}', but no matching '\\begin{{{found_env_name}}}' was identified.")
        else:
            # Original line number in payload usually refers to the \begin part for this error
            # The checker might not provide the line number of the mismatched \end part.
            print(f"Error: Mismatched Markdown environment closure in '{md_file_name_for_hint}'.")
            print(f"  Started with '\\begin{{{expected_env_name}}}' (on or near line {line_number})")
            print(f"  but encountered a closing environment for '{found_env_name}' instead of '{expected_env_name}'.")
        print()
        print(f"Details from '{md_file_name_for_hint}':")
        if expected_env_name != "N/A_expected":
            print(f"  Opening environment: '\\begin{{{expected_env_name}}}'")
            print(f"  Approx. Line of opening: {line_number}")
            print(f"  Problem snippet (often the opening tag): {problem_snippet}")
        else: # Stray \end
            print(f"  Approx. Line of unexpected '\\end{{{found_env_name}}}': {line_number}")
            print(f"  Problem snippet (the unexpected closing tag): {problem_snippet}")
        if line_content_raw and line_content_raw != problem_snippet:
             print(f"  Full raw line content of reported line: {line_content_raw}")
        print()
        print(f"Hint: Review '{md_file_name_for_hint}' around line {line_number}.")
        print("      Ensure environments are correctly nested and that every '\\begin{{...}}' matches its corresponding '\\end{{...}}'.")
        print()
    else:
        # This message now correctly reflects that the script itself doesn't handle the snake_case error_type
        # it received, if it's not one of the above.
        print(f"REPORTER_TEAM_ERROR ({os.path.basename(sys.argv[0])}): This script does not handle the error type '{error_type}'. Update this script or check reporter.py dispatch.", file=sys.stderr)
        # Exit non-zero if this specialist doesn't know how to handle the type it was given
        # This helps reporter.py know the specialist had an issue.
        sys.exit(1) 

if __name__ == "__main__":
    main()
