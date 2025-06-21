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
    md_file_for_hint = data.get("md_file_for_hint", "your_markdown_file.md")
    
    print(f"Error: Unterminated math mode — started with '$' but no closing '$' found for '{problem_snippet}'. Add a closing '$'.")
    print()
    print("Details (from Markdown file analysis):")
    print(f"  Line number (Markdown): {line_number}")
    print(f"  Problematic content (Markdown): {problem_snippet}")
    print(f"  Full line content (Markdown): {line_content_raw}")
    print()
    print("Problematic Markdown line content:")
    print(f"  L{line_number} (MD): {line_content_raw}")
    print()
    print(f"Hint: Check line {line_number} in your Markdown file ('{md_file_for_hint}') for a missing closing '$' that matches an opening '$'.")
    print()

if __name__ == "__main__":
    main()
