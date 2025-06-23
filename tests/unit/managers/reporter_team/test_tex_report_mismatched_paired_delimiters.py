import pytest
import json
import io
import sys
from unittest.mock import patch

from smart_pandoc_debugger.managers.reporter_team.tex_report_mismatched_paired_delimiters import main as trmpd_main

def run_script_with_input(json_data):
    """Runs the script's main function with the given JSON data."""
    input_str = json.dumps(json_data)
    with patch('sys.stdin', io.StringIO(input_str)):
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            try:
                trmpd_main()
            except SystemExit as e:
                if e.code != 0 and e.code is not None:
                    raise
            return mock_stdout.getvalue()

def test_report_mismatched_parenthesis_square():
    r"""Test report for \left( ... \right]."""
    data = {
        "line_number": "42",
        "problem_snippet": "\\left( ... \\right]",
        "line_content_raw": "Full line: \\left( \\frac{1}{2} \\right]",
        "opening_delim_char": "(",
        "closing_delim_char": "]"
    }
    output = run_script_with_input(data)

    assert "Error: Mismatched delimiters in TeX snippet '\\left( ... \\right]'" in output
    assert "'\\left(' should be paired with '\\right)' not '\\right]'" in output
    assert "Line number (TeX): 42" in output
    assert "Problematic pair (TeX): \\left( ... \\right]" in output
    assert "Full line content (TeX): Full line: \\left( \\frac{1}{2} \\right]" in output
    assert "Opening delimiter: \\left(" in output
    assert "Found closing delimiter: \\right]" in output
    assert "Expected closing delimiter: \\right)" in output
    assert "Hint: Check your Markdown source. Ensure that opening delimiters like '\\left(' are matched with the correct closing delimiter '\\right)'." in output

def test_report_mismatched_square_curly():
    r"""Test report for \left[ ... \right}."""
    data = {
        "line_number": "101",
        "problem_snippet": "\\left[ ... \\right}",
        "line_content_raw": "Another example: \\left[ text \\right}",
        "opening_delim_char": "[",
        "closing_delim_char": "}"
    }
    output = run_script_with_input(data)

    assert "Error: Mismatched delimiters in TeX snippet '\\left[ ... \\right}'" in output
    assert "'\\left[' should be paired with '\\right]' not '\\right}'" in output # Expected is ]
    assert "Opening delimiter: \\left[" in output
    assert "Found closing delimiter: \\right}" in output
    assert "Expected closing delimiter: \\right]" in output # Correct expectation
    assert "Hint: Check your Markdown source. Ensure that opening delimiters like '\\left[' are matched with the correct closing delimiter '\\right]'." in output

def test_report_mismatched_dot_pipe():
    r"""Test report for \left. ... \right|."""
    # \left. should be paired with \right.
    data = {
        "line_number": "7",
        "problem_snippet": "\\left. ... \\right|",
        "line_content_raw": "\\left. \\frac{numerator}{denominator} \\right|",
        "opening_delim_char": ".",
        "closing_delim_char": "|"
    }
    output = run_script_with_input(data)

    assert "Error: Mismatched delimiters in TeX snippet '\\left. ... \\right|'" in output
    assert "'\\left.' should be paired with '\\right.' not '\\right|'" in output
    assert "Opening delimiter: \\left." in output
    assert "Found closing delimiter: \\right|" in output
    assert "Expected closing delimiter: \\right." in output
    assert "Hint: Check your Markdown source. Ensure that opening delimiters like '\\left.' are matched with the correct closing delimiter '\\right.'." in output

def test_report_unknown_delimiters_in_input():
    """Test with hypothetical unknown delimiters if checker passes them."""
    # The script has a predefined map, but this tests how it handles chars not in map.
    data = {
        "line_number": "33",
        "problem_snippet": "\\left< ... \\right>", # Assuming checker found this
        "line_content_raw": "Example: \\left< text \\right>",
        "opening_delim_char": "<", # Not in expected_closing_map
        "closing_delim_char": ">"
    }
    output = run_script_with_input(data)

    assert "Error: Mismatched delimiters in TeX snippet '\\left< ... \\right>'" in output
    # expected_closing_map.get('<', '?') will result in '?'
    assert "'\\left<' should be paired with '\\right?' not '\\right>'" in output
    assert "Opening delimiter: \\left<" in output
    assert "Found closing delimiter: \\right>" in output
    assert "Expected closing delimiter: \\right?" in output # Shows '?' due to map miss
    assert "Hint: Check your Markdown source. Ensure that opening delimiters like '\\left<' are matched with the correct closing delimiter '\\right?'." in output

def test_report_missing_fields_in_json():
    """Test behavior with some JSON fields missing, using defaults."""
    data = {
        # "line_number": "unknown", # Missing, should default
        "problem_snippet": "\\left( ... \\right]",
        # "line_content_raw": "", # Missing, should default
        "opening_delim_char": "(",
        "closing_delim_char": "]"
    }
    output = run_script_with_input(data)

    assert "Error: Mismatched delimiters in TeX snippet '\\left( ... \\right]'" in output
    assert "'\\left(' should be paired with '\\right)' not '\\right]'" in output
    assert "Line number (TeX): unknown" in output # Default value
    assert "Problematic pair (TeX): \\left( ... \\right]" in output
    assert "Full line content (TeX): " in output # Default empty string
    assert "Opening delimiter: \\left(" in output
    assert "Found closing delimiter: \\right]" in output
    assert "Expected closing delimiter: \\right)" in output
    assert "Hint: Check your Markdown source. Ensure that opening delimiters like '\\left(' are matched with the correct closing delimiter '\\right)'." in output

# Consider if any other specific logic paths in the script need testing,
# e.g. if the JSON input itself is malformed (though that's a generic issue).
# The script's core logic is fairly straightforward: receive JSON, format strings.
# The main variations are the delimiter characters.
