#!/usr/bin/env python3
import sys
import re

def find_math_regions(line_content):
    """
    Finds regions in a line that are likely LaTeX math environments
    \\(...\\) or \\[...\\] (e.g. \\( ... \\) or \\[ ... \\]). Returns a list of dicts.
    This is a simple heuristic and might not cover all complex cases or nested scenarios.
    """
    regions = []
    # Find \( ... \)
    # Using a non-greedy match for the content inside
    for m in re.finditer(r"\\\(.*?\\\)", line_content):
        regions.append({"type": "inline", "start": m.start(), "end": m.end(), "content": m.group(0)})
    
    # Find \[ ... \]
    for m in re.finditer(r"\\\[.*?\\\]", line_content): # Non-greedy match
        regions.append({"type": "display", "start": m.start(), "end": m.end(), "content": m.group(0)})
    
    # If no explicit math envs, but line contains relevant commands or common delimiters, consider whole line.
    # Added \{, \}, \[, \], \(, \) to the heuristic pattern.
    # Ensured to escape regex special characters like [, ], (, ).
    heuristic_pattern = r'\\left|\\right|\\frac|\\sqrt|\\sum|\\int|\\text\{|\\label\{|\{|\}|\\\[|\\\]|\\\(|\\\)'
    if not regions and re.search(heuristic_pattern, line_content):
         regions.append({"type": "heuristic_math_line", "start": 0, "end": len(line_content), "content": line_content})

    # Sort by start position to process in order
    regions.sort(key=lambda r: r["start"])
    return regions

def process_lines(input_stream, source_name="input"):
    """
    Processes lines from an input stream (file or stdin) to find unbalanced delimiters.
    Returns True if an error was found and printed, False otherwise.
    """
    found_errors_list = [] # Collect all errors here
    for i, line_content_raw in enumerate(input_stream):
        line_number = i + 1 # Line number is relative to the start of the input_stream
        line_content_raw = line_content_raw.rstrip('\n')

        math_regions = find_math_regions(line_content_raw)

        if not math_regions:
            # find_math_regions includes a heuristic for full line if specific math regions aren't found.
            pass

        for region in math_regions:
            segment_to_check = region["content"]

            delimiters = [
                ('{', '}', 'CurlyBraces'),
                ('(', ')', 'Parentheses'),
                ('[', ']', 'SquareBrackets')
            ]

            for open_delim, close_delim, name in delimiters:
                open_count = segment_to_check.count(open_delim)
                close_count = segment_to_check.count(close_delim)

                if open_count != close_count:
                    error_type = f"Unbalanced{name}"
                    problem_snippet = segment_to_check
                    
                    error_message = f"{error_type}:{line_number}:{open_count}:{close_count}:{problem_snippet}:{line_content_raw}"
                    found_errors_list.append(error_message)
                    # Do not return or exit; continue checking for more errors.

    # After checking all lines and regions, print all found errors.
    for error_msg in found_errors_list:
        print(error_msg)

    return bool(found_errors_list) # Return True if any errors were found

def main():
    # Script exits with 0 if an error is found and printed (and processing stops),
    # or if no errors are found after processing all input.
    # Script exits with 2 for argument or file errors.

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if filepath == "-": # Explicitly use stdin if "-" is given as argument
            process_lines(sys.stdin, source_name="stdin")
            sys.exit(0) # Assume sys.exit(0) is desired after processing stdin, error or not.
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if process_lines(f, source_name=filepath):
                    sys.exit(0) # Error found and printed by process_lines
                else:
                    sys.exit(0) # No error found
        except FileNotFoundError:
            print(f"Error: TeX file not found: {filepath}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error processing file {filepath}: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        # Read from stdin if no file argument is provided
        if process_lines(sys.stdin, source_name="stdin"):
            sys.exit(0) # Error found and printed
        else:
            sys.exit(0) # No error found

if __name__ == "__main__":
    main()
