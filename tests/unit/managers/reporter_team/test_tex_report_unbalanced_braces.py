# tests/unit/managers/reporter_team/test_tex_report_unbalanced_braces.py
import pytest
import json
import io
import sys
from unittest.mock import patch

# Assuming the script is in the correct path to be imported
from smart_pandoc_debugger.managers.reporter_team.tex_report_unbalanced_braces import main as trub_main

# Helper function to run the script's main() with mocked stdin/stdout
def run_script_with_input(json_data):
    """Runs the tex_report_unbalanced_braces script's main function with the given JSON data."""
    # Prepare the JSON input string
    input_str = json.dumps(json_data)

    # Mock stdin, stdout, and argv
    # No argv needed as script reads from stdin when no args
    with patch('sys.stdin', io.StringIO(input_str)):
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            try:
                trub_main()
            except SystemExit as e:
                # The script calls sys.exit(). We can check the exit code if needed.
                # For these tests, we are primarily interested in stdout.
                # Pass if exit code is 0, otherwise raise to see the error.
                if e.code != 0 and e.code is not None: # None can happen if main completes without exit
                    raise
            return mock_stdout.getvalue()

def test_report_missing_closing_curly_brace_default_type():
    """Test report for a missing closing curly brace (default error_type_detail)."""
    data = {
        "line_number": "15",
        "problem_snippet": "Text with { an open brace",
        "line_content_raw": "Full line: Text with { an open brace but no close",
        "open_count": "1",
        "close_count": "0"
        # No "error_type_detail", defaults to CurlyBraces
    }
    output = run_script_with_input(data)

    assert "Error: Unbalanced brace in TeX snippet 'Text with { an open brace'" in output
    assert "an opening '{' is present but not closed. Add a matching '}'." in output
    assert "Braces counts: 1 open '{' vs 0 close '}'" in output
    assert "Hint: Check for missing or extra braces '{' or '}' in your TeX math expression." in output

def test_report_missing_closing_parenthesis():
    """Test report for a missing closing parenthesis."""
    data = {
        "line_number": "16",
        "problem_snippet": "Text with ( an open paren",
        "line_content_raw": "Full line: Text with ( an open paren but no close",
        "open_count": "1",
        "close_count": "0",
        "error_type_detail": "Parentheses"
    }
    output = run_script_with_input(data)

    assert "Error: Unbalanced parenthesis in TeX snippet 'Text with ( an open paren'" in output
    assert "an opening '(' is present but not closed. Add a matching ')'." in output
    assert "Parentheses counts: 1 open '(' vs 0 close ')'" in output
    assert "Hint: Check for missing or extra parentheses '(' or ')' in your TeX math expression." in output

def test_report_missing_opening_square_bracket():
    """Test report for a missing opening square bracket."""
    data = {
        "line_number": "20",
        "problem_snippet": "Text with an extra ]",
        "line_content_raw": "Full line: Text with an extra ] bracket",
        "open_count": "0",
        "close_count": "1",
        "error_type_detail": "SquareBrackets"
    }
    output = run_script_with_input(data)
    assert "Error: Unbalanced square bracket in TeX snippet 'Text with an extra ]'" in output
    assert "a closing ']' is present without a matching opening '['. Check for an extra ']' or a missing '['." in output
    assert "Square brackets counts: 0 open '[' vs 1 close ']'" in output
    assert "Hint: Check for missing or extra square brackets '[' or ']' in your TeX math expression." in output

def test_report_unexpected_closing_curly_brace_in_snippet():
    """Test specific handling for '}' in problem_snippet when type is CurlyBraces."""
    data = {
        "line_number": "25",
        "problem_snippet": " $x^2}$ ",
        "line_content_raw": "Math: $x^2}$ should be $x^{2}$",
        "open_count": "0",
        "close_count": "1",
        "error_type_detail": "CurlyBraces"
    }
    output = run_script_with_input(data)
    assert "Error: Unexpected closing brace '}' found in TeX snippet ' $x^2}$ '." in output
    assert "Check for an extra '}' or a missing opening '$' in your Markdown." in output
    assert "Hint: Verify brace balancing in your TeX source." in output

def test_report_unexpected_closing_parenthesis_in_snippet_no_special_handling():
    """Test that the special '}' check does not apply to other delimiter types."""
    data = {
        "line_number": "26",
        "problem_snippet": " $x^2)$ ",
        "line_content_raw": "Math: $x^2)$ should be $x^{2}$",
        "open_count": "0",
        "close_count": "1",
        "error_type_detail": "Parentheses"
    }
    output = run_script_with_input(data)
    assert "Error: Unbalanced parenthesis in TeX snippet ' $x^2)$ '" in output
    assert "a closing ')' is present without a matching opening '('. Check for an extra ')' or a missing '('." in output
    # Ensure the special hint for '}' is not present
    assert "Verify brace balancing in your TeX source." not in output
    assert "Hint: Check for missing or extra parentheses '(' or ')' in your TeX math expression." in output


def test_report_invalid_count_data_for_parentheses():
    """Test report when count data is not valid for parentheses."""
    data = {
        "line_number": "30",
        "problem_snippet": "Some ( text",
        "line_content_raw": "Some ( text with invalid count",
        "open_count": "one",
        "close_count": "0",
        "error_type_detail": "Parentheses"
    }
    output = run_script_with_input(data)
    assert "Error: Unbalanced parenthesis issue detected in TeX snippet 'Some ( text'." in output
    assert "parenthesis count data was invalid." in output
    assert "Parentheses counts: one open '(' vs 0 close ')'" in output
    assert "Hint: Check for missing or extra parentheses '(' or ')' in your TeX math expression." in output

def test_report_unknown_line_number_default_type():
    """Test with unknown line number, defaulting to CurlyBraces."""
    data = {
        "line_number": "unknown",
        "problem_snippet": "{",
        "line_content_raw": "A line with { issues",
        "open_count": "2", # Deliberate mismatch with snippet for test
        "close_count": "1"
        # "error_type_detail": "CurlyBraces" (default)
    }
    output = run_script_with_input(data)
    assert "Error: Unbalanced brace in TeX snippet '{'" in output
    assert "an opening '{' is present but not closed. Add a matching '}'." in output
    assert "Line number (TeX): unknown" in output
    assert "Braces counts: 2 open '{' vs 1 close '}'" in output

# These tests are now updated to reflect the generic nature of the reporter script
# when `error_type_detail` is provided.
