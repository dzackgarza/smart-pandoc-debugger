#!/usr/bin/env python3
import sys
import re

def main():
    if len(sys.argv) < 2:
        # This error should go to stderr, as it's a usage error of the script itself
        print("Usage: python3 check_markdown_unclosed_dollar.py <markdown_file>", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]
    error_found = False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line_content in enumerate(f):
                line_number = i + 1
                line_content = line_content.rstrip('\n')
                
                # Regex to find unescaped $ delimiters
                # This counts '$' not preceded by a backslash
                # It doesn't handle block $$...$$ delimiters perfectly, assumes they are balanced or on separate lines.
                # A more robust solution might need to track state across lines or use more complex parsing.
                
                # Find all $ not preceded by a backslash
                dollars = []
                for m in re.finditer(r"(?<!\\)\$", line_content):
                    dollars.append(m.start())
                
                if len(dollars) % 2 != 0: # Odd number of $ means at least one is unclosed on this line
                    error_type = "UnterminatedInlineMathMarkdown"
                    
                    # Try to get a snippet from the first unclosed $
                    problem_snippet = ""
                    if dollars:
                        first_dollar_pos = dollars[0]
                        # For an odd count, the problem likely starts at the first $
                        # or if multiple pairs exist, the last unclosed one.
                        # Simple approach: if odd, take from first $ to EOL as "potentially problematic"
                        # More sophisticated: find the segment from the unclosed $.
                        
                        # Simplified snippet: content from the first $ if count is odd.
                        # This might not be the *exact* unclosed segment if multiple pairs exist
                        # and then one unclosed one, but it's a starting point.
                        # A true segment would require pairing logic.
                        
                        # For now, let's identify the segment starting with the first $ on the line
                        # if there's an odd number.
                        segment_start_index = -1
                        temp_dollars = 0
                        temp_segment_start = -1
                        escaped = False
                        
                        # Simplified: assume the problem is with the first $ on a line with an odd number of $
                        # This isn't perfect for lines like "$a=1$ ... $b=2"
                        # but for "$b=2" it will flag it.
                        
                        # Let's just take the content from the first $ as problem_snippet
                        # if number of $ is odd.
                        problem_snippet = line_content[dollars[0]:]
                        # Attempt to remove the leading $ from the snippet itself for user message
                        if problem_snippet.startswith("$"):
                            problem_snippet = problem_snippet[1:]
                            
                    else: # Should not happen if len(dollars) is odd and > 0
                        problem_snippet = line_content

                    # Output: ErrorType:LineNum:OpenCount:CloseCount:ProblemSnippet:OriginalLine
                    # For this Markdown check, Open/Close counts are less direct. We can use 1/0 as placeholder.
                    print(f"{error_type}:{line_number}:1:0:{problem_snippet}:{line_content}")
                    error_found = True
                    sys.exit(0) # Exit after first error line found (for Proofreader to process one)
                    
    except FileNotFoundError:
        print(f"Error: Markdown file not found: {filepath}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error processing file {filepath}: {e}", file=sys.stderr)
        sys.exit(2)

    if not error_found:
        sys.exit(0) # No error found by this specific check

if __name__ == "__main__":
    main()
