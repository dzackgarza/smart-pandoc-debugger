import pytest
import json
import io
import sys
from unittest.mock import patch

from smart_pandoc_debugger.managers.reporter_team.tex_report_unmatched_delimiters import main as trud_main

def run_script_with_input(json_data):
    """Runs the script's main function with the given JSON data."""
    input_str = json.dumps(json_data)
    with patch('sys.stdin', io.StringIO(input_str)):
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            try:
                trud_main()
            except SystemExit as e:
                if e.code != 0 and e.code is not None:
                    raise
            return mock_stdout.getvalue()

def test_report_more_left_than_right_paren():
    r"""Test report for more \left( than \right)."""
    data = {
        "line_number": "10",
        "problem_snippet": "\\left( a + b", # Snippet showing the start of the issue
        "line_content_raw": "Full line: \\left( a + b \\left( c",
        "left_count": "2",
        "right_count": "0"
    }
    output = run_script_with_input(data)

    assert "Error: Unmatched delimiter count for '\\left(...'" in output # Heuristic based on snippet
    assert "missing a matching '\\right)'" in output
    assert "Line number (TeX): 10" in output
    assert "Problem snippet (TeX): \\left( a + b" in output
    assert "Full line content (TeX): Full line: \\left( a + b \\left( c" in output
    assert "Counts: 2 \\left vs 0 \\right" in output
    assert "Hint: Ensure every \\left has a corresponding \\right (and vice-versa)" in output

def test_report_more_right_than_left_square():
    r"""Test report for more \right] than \left[."""
    data = {
        "line_number": "15",
        "problem_snippet": "\\right] text", # Snippet showing the start of the issue
        "line_content_raw": "Full line: x \\right] y \\right]",
        "left_count": "0",
        "right_count": "2"
    }
    output = run_script_with_input(data)

    assert "Error: Unmatched delimiter count for '\\right]...'" in output
    assert "missing a matching '\\left['" in output
    assert "Line number (TeX): 15" in output
    assert "Problem snippet (TeX): \\right] text" in output
    assert "Full line content (TeX): Full line: x \\right] y \\right]" in output
    assert "Counts: 0 \\left vs 2 \\right" in output

def test_report_more_left_than_right_curly():
    r"""Test report for more \left\{ than \right\}."""
    data = {
        "line_number": "20",
        "problem_snippet": "\\left\\{ content",
        "line_content_raw": "\\left\\{ content is here",
        "left_count": "1",
        "right_count": "0"
    }
    output = run_script_with_input(data)

    assert "Error: Unmatched delimiter count for '\\left\\{...'" in output
    assert "missing a matching '\\right}}'" in output # Note: script generates \right}}
    assert "Counts: 1 \\left vs 0 \\right" in output

def test_report_more_right_than_left_dot():
    r"""Test report for more \right. than \left.."""
    data = {
        "line_number": "25",
        "problem_snippet": "\\right. ",
        "line_content_raw": "text \\right. ",
        "left_count": "0",
        "right_count": "1"
    }
    output = run_script_with_input(data)

    assert "Error: Unmatched delimiter count for '\\right....'" in output # Heuristic for \right.
    assert "missing a matching '\\left.'" in output
    assert "Counts: 0 \\left vs 1 \\right" in output

def test_report_generic_snippet_if_no_specific_delimiter_found():
    """Test when problem_snippet doesn't contain a specific delimiter type."""
    data = {
        "line_number": "30",
        "problem_snippet": "a general problem area", # No \left or \right in snippet
        "line_content_raw": "\\left( general problem area",
        "left_count": "1", # But counts indicate imbalance
        "right_count": "0"
    }
    output = run_script_with_input(data)

    # found_part_desc becomes "'a general problem area'"
    # missing_part becomes "a matching '\right(type)'" because lc > rc but no specific delim in snippet
    assert "Error: Unmatched delimiter count for 'a general problem area'" in output
    assert "missing a matching '\\right(type)'" in output # Generic fallback
    assert "Counts: 1 \\left vs 0 \\right" in output

def test_report_invalid_count_data_string():
    """Test report when count data is not a valid integer string."""
    data = {
        "line_number": "35",
        "problem_snippet": "\\left( problem",
        "line_content_raw": "\\left( problem with counts",
        "left_count": "many", # Invalid
        "right_count": "few"  # Invalid
    }
    output = run_script_with_input(data)

    # The script tries int(left_count) which will raise ValueError
    # missing_part will be "valid count data was not provided"
    assert "Error: Unmatched delimiter count for '\\left(...'" in output
    assert "missing valid count data was not provided" in output
    assert "Counts: many \\left vs few \\right" in output # Shows the invalid data

def test_report_missing_fields_in_json():
    """Test behavior with some JSON fields missing, using defaults."""
    data = {
        # "line_number": "unknown", # Missing
        "problem_snippet": "\\left( snippet",
        # "line_content_raw": "", # Missing
        "left_count": "3",
        "right_count": "1"
    }
    output = run_script_with_input(data)

    assert "Error: Unmatched delimiter count for '\\left(...'" in output
    assert "missing a matching '\\right)'" in output
    assert "Line number (TeX): unknown" in output
    assert "Full line content (TeX): " in output # Default empty string
    assert "Counts: 3 \\left vs 1 \\right" in output

# This script's logic for determining the "missing part" based on problem_snippet content
# is somewhat heuristic. The tests cover the main paths of this heuristic.
