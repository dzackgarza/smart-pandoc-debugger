#!/usr/bin/env python3
import sys
import re

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <tex_file>", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]
    # Pattern to find \leftX or \rightY, capturing X or Y (delimiter char)
    # X and Y can be '(', ')', '[', ']', '{', '}', '.', '|'
    # We also capture the full \leftX or \rightY for snippet purposes.
    # Using non-capturing group for \left or \right: (?:...)
    # delimiter_char_pattern = r"\(|\)|\[|\]|\{|\}|\.|\|" # Common delimiters
    # Using a simpler approach: find \left or \right, then grab next char.
    
    left_pattern = re.compile(r"(\\left)\s*([\[({|.])")
    right_pattern = re.compile(r"(\\right)\s*([\])}|.])") # Note: | is its own closer usually

    # Mapping of open to expected close delimiters
    delimiter_pairs = {
        '(': ')',
        '[': ']',
        '{': '}',
        '|': '|',
        '.': '.' # \left. matches \right. (often used for one-sided delimiters)
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line_content_raw in enumerate(f):
                line_number = i + 1
                line_content = line_content_raw.rstrip('\n')

                left_delims = [] # Stack to store (delimiter_char, full_match_string, start_pos)
                
                # Find all \leftX and \rightY tokens with their positions
                tokens = []
                for match in left_pattern.finditer(line_content):
                    tokens.append({'type': 'left', 'char': match.group(2), 'full': match.group(0), 'pos': match.start()})
                for match in right_pattern.finditer(line_content):
                    tokens.append({'type': 'right', 'char': match.group(2), 'full': match.group(0), 'pos': match.start()})
                
                tokens.sort(key=lambda t: t['pos']) # Process in order of appearance

                for token in tokens:
                    if token['type'] == 'left':
                        left_delims.append(token)
                    elif token['type'] == 'right':
                        if not left_delims:
                            # Found a \right without a preceding \left on this line (unmatched \right)
                            # This might be better handled by the simple count check in check_unmatched_left_right.awk
                            # For this script, we focus on *mismatched pairs*
                            problem_snippet = token['full'] # e.g., "\right)"
                            # print(f"MismatchedDelimiters:{line_number}:0:1:{problem_snippet}:{line_content}")
                            # sys.exit(0) # Report and exit
                            continue # Or let the count checker handle it
                        
                        last_left = left_delims.pop()
                        expected_closer = delimiter_pairs.get(last_left['char'])
                        
                        if token['char'] != expected_closer:
                            error_type = "MismatchedPairedDelimiters"
                            # Create a snippet showing the mismatched pair
                            problem_snippet = f"{last_left['full']} ... {token['full']}"
                            
                            # VAL1 will be the opening delimiter, VAL2 will be the mismatched closing delimiter
                            val1 = last_left['char']
                            val2 = token['char']
                            
                            print(f"{error_type}:{line_number}:{val1}:{val2}:{problem_snippet}:{line_content}")
                            sys.exit(0) # Exit after first error

                # After checking all tokens on a line, if left_delims is not empty,
                # it means there are unclosed \left delimiters.
                # This is already covered by check_unmatched_left_right.awk (counts).
                # This script focuses on X vs Y mismatch.

    except FileNotFoundError:
        print(f"Error: TeX file not found: {filepath}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error processing file {filepath}: {e}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0) # No mismatched pairs found

if __name__ == "__main__":
    main()
