#!/usr/bin/env python3

import re
import sys


def find_math_regions(line_content):
    """
    Find regions in a line that are likely LaTeX math environments.

    Returns a list of dictionaries with region information.
    This is a simple heuristic and might not cover all complex cases or nested scenarios.
    """
    regions = []
    # Find \( ... \)
    pattern = re.compile(r"\\\(.*?\\\)")
    for m in pattern.finditer(line_content):
        regions.append({
            "type": "inline",
            "start": m.start(),
            "end": m.end(),
            "content": m.group(0)
        })

    # Find \[ ... \]
    pattern = re.compile(r"\\\[.*?\\\]")
    for m in pattern.finditer(line_content):
        regions.append({
            "type": "display",
            "start": m.start(),
            "end": m.end(),
            "content": m.group(0)
        })

    # If no explicit math envs, but line contains relevant commands
    if not regions and re.search(
        r'\\left|\\right|\\frac|\\sqrt|\\sum|\\int|\\text\{|\\label\{',
        line_content
    ):
        regions.append({
            "type": "heuristic_math_line",
            "start": 0,
            "end": len(line_content),
            "content": line_content
        })

    # Sort by start position to process in order
    regions.sort(key=lambda r: r["start"])
    return regions


def main():
    """Check a TeX file for unbalanced braces in math regions."""
    if len(sys.argv) < 2:
        print(
            "Usage: python3 check_tex_unbalanced_braces.py <tex_file>",
            file=sys.stderr
        )
        sys.exit(2)

    filepath = sys.argv[1]
    error_found = False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line_content_raw in enumerate(f):
                line_number = i + 1
                line_content_raw = line_content_raw.rstrip('\n')

                math_regions = find_math_regions(line_content_raw)

                # find_math_regions includes a heuristic for full line
                # if specific math regions aren't found

                for region in math_regions:
                    segment_to_check = region["content"]

                    # Count raw braces (both { and })
                    open_braces = segment_to_check.count('{')
                    close_braces = segment_to_check.count('}')

                    if open_braces != close_braces:
                        error_type = "UnbalancedBraces"
                        # The math region itself is the best snippet
                        problem_snippet = segment_to_check

                        # Output: ErrorType:LineNum:OpenCount:CloseCount:...
                        print(
                            f"{error_type}:{line_number}:"
                            f"{open_braces}:{close_braces}:"
                            f"{problem_snippet}:{line_content_raw}"
                        )
                        error_found = True
                        # Continue processing to find more errors

    except FileNotFoundError:
        print(f"Error: TeX file not found: {filepath}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error processing file {filepath}: {e}", file=sys.stderr)
        sys.exit(2)

    if not error_found:
        sys.exit(0)


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
