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
    open_count_str = data.get("open_count", "0")
    close_count_str = data.get("close_count", "0")
    # md_file_for_hint = data.get("md_file_for_hint", "your_markdown_file.md")
    
    main_error_printed = False
    brace_issue_desc = ""
    hint_text = "Check for missing or extra braces '{' or '}' in your TeX math expression."
    
    try:
        open_count = int(open_count_str)
        close_count = int(close_count_str)

        if open_count > close_count:
            brace_issue_desc = "a '{' is opened but not closed. Add a matching '}'."
        elif close_count > open_count:
            if '}' in problem_snippet: 
                print(f"Error: Unexpected closing brace '}}' found in TeX snippet '{problem_snippet}'. Check for an extra '}}' or a missing opening '$' in your Markdown.")
                hint_text = "Verify brace balancing in your TeX source. If math delimiters are also suspect, ensure they are correctly paired in Markdown."
                main_error_printed = True
            else:
                brace_issue_desc = "a '}' is present without a matching open '{'. Check for an extra '}' or a missing '{'."
        # This case should ideally not be reached if checker guarantees open_count != close_count for this error_type
        elif open_count == close_count and open_count > 0 : # or some other condition if counts are equal but it's an error
             brace_issue_desc = f"brace counts ({open_count} vs {close_count}) are equal but reported as unbalanced. This might be a checker issue."
        else: # Should not be hit if error_type is UnbalancedBraces
             brace_issue_desc = "brace counts are reported as unbalanced with unclear details."

    except ValueError:
        brace_issue_desc = "brace count data was invalid."

    if not main_error_printed:
        if brace_issue_desc:
            print(f"Error: Unbalanced brace in TeX snippet '{problem_snippet}' — {brace_issue_desc}")
        else: 
            print(f"Error: Unbalanced brace issue detected in TeX snippet '{problem_snippet}'.")
            
    print()
    print("Details (from TeX file analysis):")
    print(f"  Line number (TeX): {line_number}")
    print(f"  Problem snippet (TeX): {problem_snippet}")
    print(f"  Full line content (TeX): {line_content_raw}")
    print(f"  Brace counts: {open_count_str} open '{{' vs {close_count_str} close '}}'")
    print()
    print("#CONTEXT_BLOCK_TEX_PLACEHOLDER#")
    print()
    print(f"Hint: {hint_text} Usually this means a similar issue exists in your Markdown math.")
    print()

if __name__ == "__main__":
    main()
