#!/usr/bin/env python3
import sys
import json

def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        print(f"REPORTER_TEAM_ERROR ({sys.argv[0]}): Could not decode JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    line_number = data.get("line_number", "unknown")
    problem_snippet = data.get("problem_snippet", "")
    line_content_raw = data.get("line_content_raw", "")
    opening_delim_char = data.get("opening_delim_char", "?")
    closing_delim_char = data.get("closing_delim_char", "?")
    # md_file_for_hint = data.get("md_file_for_hint", "your_markdown_file.md")

    expected_closing_map = {'(': ')', '[': ']', '{': '}', '|': '|', '.': '.'}
    expected_closing_char_display = expected_closing_map.get(opening_delim_char, '?')

    print(f"Error: Mismatched delimiters in TeX snippet '{problem_snippet}' — '\\left{opening_delim_char}' should be paired with '\\right{expected_closing_char_display}' not '\\right{closing_delim_char}'.")
    print()
    print("Details (from TeX file analysis):")
    print(f"  Line number (TeX): {line_number}")
    print(f"  Problematic pair (TeX): {problem_snippet}")
    print(f"  Full line content (TeX): {line_content_raw}")
    print(f"  Opening delimiter: \\left{opening_delim_char}")
    print(f"  Found closing delimiter: \\right{closing_delim_char}")
    print(f"  Expected closing delimiter: \\right{expected_closing_char_display}")
    print()
    print("#CONTEXT_BLOCK_TEX_PLACEHOLDER#") 
    print()
    print(f"Hint: Check your Markdown source. Ensure that opening delimiters like '\\left{opening_delim_char}' are matched with the correct closing delimiter '\\right{expected_closing_char_display}'.")
    print()

if __name__ == "__main__":
    main()
