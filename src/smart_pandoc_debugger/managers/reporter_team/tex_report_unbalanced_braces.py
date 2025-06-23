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
    # Input "error_type_detail" could be "CurlyBraces", "Parentheses", "SquareBrackets"
    # This would typically be parsed from the checker's output by the calling manager.
    error_type_detail = data.get("error_type_detail", "CurlyBraces") # Default to braces if not specified

    # md_file_for_hint = data.get("md_file_for_hint", "your_markdown_file.md")

    main_error_printed = False
    issue_desc = ""

    delimiters_map = {
        "CurlyBraces": ("{", "}", "braces", "brace"),
        "Parentheses": ("(", ")", "parentheses", "parenthesis"),
        "SquareBrackets": ("[", "]", "square brackets", "square bracket")
    }

    open_char, close_char, delim_name_plural, delim_name_singular = delimiters_map.get(
        error_type_detail, delimiters_map["CurlyBraces"] # Default to curly braces
    )

    hint_text = f"Check for missing or extra {delim_name_plural} '{open_char}' or '{close_char}' in your TeX math expression."
    
    try:
        open_count = int(open_count_str)
        close_count = int(close_count_str)

        if open_count > close_count:
            issue_desc = f"an opening '{open_char}' is present but not closed. Add a matching '{close_char}'."
        elif close_count > open_count:
            # Generalized message for all delimiter types per PR comment
            issue_desc = f"a closing '{close_char}' is present without a matching opening '{open_char}'. Check for an extra '{close_char}' or a missing '{open_char}'."
            # The generic hint_text defined earlier is already suitable.
            # No need for main_error_printed = True here, will fall through to standard print.
        elif open_count == close_count and open_count > 0:
             issue_desc = f"{delim_name_plural} counts ({open_count} vs {close_count}) are equal but reported as unbalanced. This might be a checker issue."
        else: # Should ideally not be hit if counts are different
             issue_desc = f"{delim_name_plural} counts are reported as unbalanced with unclear details."

    except ValueError:
        issue_desc = f"{delim_name_singular} count data was invalid."

    if not main_error_printed:
        if issue_desc:
            print(f"Error: Unbalanced {delim_name_singular} in TeX snippet '{problem_snippet}' — {issue_desc}")
        else: 
            print(f"Error: Unbalanced {delim_name_singular} issue detected in TeX snippet '{problem_snippet}'.")
            
    print()
    print("Details (from TeX file analysis):")
    print(f"  Line number (TeX): {line_number}")
    print(f"  Problem snippet (TeX): {problem_snippet}")
    print(f"  Full line content (TeX): {line_content_raw}")
    print(f"  {delim_name_plural.capitalize()} counts: {open_count_str} open '{open_char}' vs {close_count_str} close '{close_char}'")
    print()
    print("#CONTEXT_BLOCK_TEX_PLACEHOLDER#")
    print()
    print(f"Hint: {hint_text} Usually this means a similar issue exists in your Markdown math.")
    print()

if __name__ == "__main__":
    main()
