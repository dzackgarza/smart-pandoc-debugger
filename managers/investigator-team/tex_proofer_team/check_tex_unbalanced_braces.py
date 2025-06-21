#!/usr/bin/env python3
import sys
import re

def find_math_regions(line_content):
    """
    Finds regions in a line that are likely LaTeX math environments
    \(...\) or \[...\]. Returns a list of (start_index, end_index, content) tuples.
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
    
    # If no explicit math envs, but line contains relevant commands, consider whole line
    if not regions and re.search(r'\\left|\\right|\\frac|\\sqrt|\\sum|\\int|\\text\{|\\label\{', line_content):
         regions.append({"type": "heuristic_math_line", "start": 0, "end": len(line_content), "content": line_content})

    # Sort by start position to process in order
    regions.sort(key=lambda r: r["start"])
    return regions

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_tex_unbalanced_braces.py <tex_file>", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]
    error_found = False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line_content_raw in enumerate(f):
                line_number = i + 1
                line_content_raw = line_content_raw.rstrip('\n')

                math_regions = find_math_regions(line_content_raw)

                if not math_regions: # Only check lines with identified math or math-related commands
                    # Check the whole line if it looks like it might contain math commands
                    # This is similar to the awk script's initial line filter.
                    # Redundant if find_math_regions already adds heuristic_math_line
                    # if not re.search(r'\\\(|\\\[|\\left|\\right|\\begin\{equation\}|\\frac|\\sqrt|\\sum|\\int|\\text\{|\\label\{', line_content_raw):
                    #    continue # Skip lines unlikely to contain relevant brace issues
                    pass # find_math_regions includes a heuristic for full line if specific math regions aren't found

                for region in math_regions:
                    segment_to_check = region["content"]
                    
                    # Count non-escaped { and }
                    # Python's re.findall is good for this.
                    # To find '{' not preceded by '\', use negative lookbehind `(?<!\\){`
                    # For TeX, `\{` is a literal brace, so we just count raw `{` and `}`.
                    open_braces = segment_to_check.count('{')
                    close_braces = segment_to_check.count('}')

                    if open_braces != close_braces:
                        error_type = "UnbalancedBraces"
                        problem_snippet = segment_to_check # The math region itself is the best snippet
                        
                        # Output: ErrorType:LineNum:OpenCount:CloseCount:ProblemSnippet:OriginalLineContent
                        print(f"{error_type}:{line_number}:{open_braces}:{close_braces}:{problem_snippet}:{line_content_raw}")
                        error_found = True
                        sys.exit(0) # Exit after first error region on the first error line
                
                if error_found: # Should have been caught by sys.exit(0) in loop
                    break

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
