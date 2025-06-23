#!/usr/bin/env python3
import sys
import re

# Global patterns and maps for efficiency if script is imported vs run directly
LEFT_PATTERN = re.compile(r"(\\left)\s*([\[({|.])")
RIGHT_PATTERN = re.compile(r"(\\right)\s*([\])}|.])") # Note: | is its own closer usually
DELIMITER_PAIRS = {
    '(': ')',
    '[': ']',
    '{': '}',
    '|': '|',
    '.': '.' # \left. matches \right. (often used for one-sided delimiters)
}

def process_lines(input_stream, source_name="input"):
    """
    Processes lines from an input stream to find mismatched \leftX ... \rightY delimiters.
    Returns True if an error was found and printed, False otherwise.
    """
    error_found = False
    # The stack needs to persist across lines if we are to find \left( in line 1 and \right) in line 2.
    # However, the current script logic is line-by-line.
    # For this refactoring, we keep line-by-line logic.
    # A true multi-line \left \right checker would require a different approach (e.g. processing a whole environment block).
    # For now, `left_delims` is reset per line.
    
    for i, line_content_raw in enumerate(input_stream):
        line_number = i + 1 # Relative to the input stream
        line_content = line_content_raw.rstrip('\n')

        left_delims = [] # Stack for \left tokens on the current line

        tokens = []
        for match in LEFT_PATTERN.finditer(line_content):
            tokens.append({'type': 'left', 'char': match.group(2), 'full': match.group(0), 'pos': match.start()})
        for match in RIGHT_PATTERN.finditer(line_content):
            tokens.append({'type': 'right', 'char': match.group(2), 'full': match.group(0), 'pos': match.start()})

        tokens.sort(key=lambda t: t['pos'])

        for token in tokens:
            if token['type'] == 'left':
                left_delims.append(token)
            elif token['type'] == 'right':
                if not left_delims:
                    # Unmatched \right on this line (no preceding \left on this line)
                    # This script focuses on X vs Y mismatch. Count issues are for check_unmatched_left_right.awk
                    continue
                
                last_left = left_delims.pop()
                expected_closer = DELIMITER_PAIRS.get(last_left['char'])
                
                if token['char'] != expected_closer:
                    error_type = "MismatchedPairedDelimiters"
                    problem_snippet = f"{last_left['full']} ... {token['full']}"
                    val1 = last_left['char']
                    val2 = token['char']

                    print(f"{error_type}:{line_number}:{val1}:{val2}:{problem_snippet}:{line_content}")
                    error_found = True
                    return error_found # Exit after first error

        # Unclosed \left delimiters on this line are implicitly handled by check_unmatched_left_right.awk for counts.
        # If left_delims is not empty here, it means a \left on this line was not closed *on this same line*.

    return error_found


def main():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if filepath == "-": # Explicitly use stdin
            process_lines(sys.stdin, source_name="stdin")
            sys.exit(0) # Original script exits 0 whether error found or not, if not file/arg error
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if process_lines(f, source_name=filepath):
                    sys.exit(0) # Error found and printed
                else:
                    sys.exit(0) # No error found
        except FileNotFoundError:
            print(f"Error: TeX file not found: {filepath}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error processing file {filepath}: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        # Read from stdin if no file argument
        if process_lines(sys.stdin, source_name="stdin"):
            sys.exit(0) # Error found and printed
        else:
            sys.exit(0) # No error found

if __name__ == "__main__":
    main()
