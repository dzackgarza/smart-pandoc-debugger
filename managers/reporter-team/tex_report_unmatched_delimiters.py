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
    left_count = data.get("left_count", "0")
    right_count = data.get("right_count", "0")
    # md_file_for_hint = data.get("md_file_for_hint", "your_markdown_file.md") # Available if needed

    found_part_desc = f"'{problem_snippet}'"
    if "\\left(" in problem_snippet: found_part_desc = "'\\left(...'"
    elif "\\left[" in problem_snippet: found_part_desc = "'\\left[...'"
    elif "\\left{" in problem_snippet: found_part_desc = "'\\left\\{...'"
    elif "\\right)" in problem_snippet: found_part_desc = "'\\right)...'"
    elif "\\right]" in problem_snippet: found_part_desc = "'\\right]...'"
    elif "\\right}" in problem_snippet: found_part_desc = "'\\right\\}...'"

    missing_part = "a corresponding delimiter"
    try:
        lc = int(left_count)
        rc = int(right_count)
        if lc > rc:
            missing_part_base = "a matching '\\right"
            if "\\left(" in problem_snippet: missing_part = f"{missing_part_base})'"
            elif "\\left[" in problem_snippet: missing_part = f"{missing_part_base}]'"
            elif "\\left{" in problem_snippet: missing_part = f"{missing_part_base}}}'"
            elif "\\left." in problem_snippet: missing_part = f"{missing_part_base}.'"
            else: missing_part = f"{missing_part_base}(type)'"
        elif rc > lc:
            missing_part_base = "a matching '\\left"
            if "\\right)" in problem_snippet: missing_part = f"{missing_part_base}('"
            elif "\\right]" in problem_snippet: missing_part = f"{missing_part_base}['"
            elif "\\right}" in problem_snippet: missing_part = f"{missing_part_base}{{'"
            elif "\\right." in problem_snippet: missing_part = f"{missing_part_base}.'"
            else: missing_part = f"{missing_part_base}(type)'"
    except ValueError:
        missing_part = "valid count data was not provided"

    print(f"Error: Unmatched delimiter count for {found_part_desc} — missing {missing_part}. Review your math expression in the TeX source.")
    print()
    print("Details (from TeX file analysis):")
    print(f"  Line number (TeX): {line_number}")
    print(f"  Problem snippet (TeX): {problem_snippet}")
    print(f"  Full line content (TeX): {line_content_raw}")
    print(f"  Counts: {left_count} \\left vs {right_count} \\right")
    print()
    print("#CONTEXT_BLOCK_TEX_PLACEHOLDER#")
    print()
    print("Hint: Ensure every \\left has a corresponding \\right (and vice-versa) within the same mathematical expression in your TeX source.")
    print("      This usually originates from your Markdown math.")
    print()

if __name__ == "__main__":
    main()
