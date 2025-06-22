"""
Consolidated test suite for error_finder.py

This file combines all test cases from:
- test_error_finder.py
- test_error_finder_unit.py
- test_error_finder_comprehensive.py

Uses pytest for better test organization and features.
"""

import os
import json
import pytest
import tempfile
from pathlib import Path

# Import the module to test
sys.path.insert(0, str(Path(__file__).parent.parent))
from DEBUG_error_finder.error_finder import find_primary_error

# --- Test Fixtures ---

@pytest.fixture
temp_files():
    """Fixture to create and clean up temporary files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        log_file = temp_dir / 'test.log'
        tex_file = temp_dir / 'test.tex'
        yield temp_dir, log_file, tex_file

# --- Test Data ---

# Test cases organized by error type
TEST_CASES = {
    # Math Mode Errors
    'missing_math_delimiter': {
        'log': """! Missing $ inserted.
<inserted text> 
                $
<to be read again> 
                   \\
l.27 \\end{align}""",
        'tex': "a = b + c",
        'expected': {
            'error_signature': 'LATEX_MISSING_MATH_DELIMITERS',
            'error_line_in_tex': 'unknown'
        }
    },
    
    'undefined_control_sequence': {
        'log': """! Undefined control sequence.
l.6 \\nonexistentcommand""",
        'tex': "\\documentclass{article}\\n\\begin{document}\\n\\nonexistentcommand\\end{document}",
        'expected': {
            'error_signature': 'LATEX_UNDEFINED_CONTROL_SEQUENCE',
            'error_line_in_tex': 'unknown'
        }
    },
    
    'unbalanced_braces': {
        'log': """! Missing } inserted.
l.6 f(x) = \\frac{1}{1 + e^{-x}}""",
        'tex': "$f(x) = \\frac{1}{1 + e^{-x}}$",
        'expected': {
            'error_signature': 'LATEX_UNBALANCED_BRACES',
            'error_line_in_tex': 'unknown'
        }
    },
    
    'mismatched_delimiters': {
        'log': """! Missing \\right.\nl.6 \\left[\\left(\\frac{a}{b}\\right]""",
        'tex': "$\\left[\\left(\\frac{a}{b}\\right]$",
        'expected': {
            'error_signature': 'LATEX_MISMATCHED_DELIMITERS',
            'error_line_in_tex': 'unknown'
        }
    },
    
    'runaway_argument': {
        'log': """Runaway argument?
{This is a runaway argument that never ends
! Paragraph ended before \\@vspace was complete.
<to be read again> 
                   \\par 
l.28""",
        'tex': "Some text with a runaway argument",
        'expected': {
            'error_signature': 'LATEX_NO_ERROR_MESSAGE_IDENTIFIED',
            'error_line_in_tex': 'unknown'
        }
    }
}

# --- Test Functions ---

def test_error_finder_basic(temp_files):
    """Test basic error finding functionality."""
    temp_dir, log_file, tex_file = temp_files
    
    test_case = TEST_CASES['missing_math_delimiter']
    log_file.write_text(test_case['log'])
    tex_file.write_text(test_case['tex'])
    
    result = find_primary_error(test_case['log'])
    
    assert result['error_signature'] == test_case['expected']['error_signature']
    assert result['error_line_in_tex'] == test_case['expected']['error_line_in_tex']

@pytest.mark.parametrize('test_name', TEST_CASES.keys())
def test_error_finder_parameterized(temp_files, test_name):
    """Test error finder with parameterized test cases."""
    temp_dir, log_file, tex_file = temp_files
    test_case = TEST_CASES[test_name]
    
    log_file.write_text(test_case['log'])
    tex_file.write_text(test_case['tex'])
    
    result = find_primary_error(test_case['log'])
    
    assert result['error_signature'] == test_case['expected']['error_signature']
    assert result['error_line_in_tex'] == test_case['expected']['error_line_in_tex']

def test_error_finder_integration(temp_files):
    """Test error finder with a more complex integration scenario."""
    temp_dir, log_file, tex_file = temp_files
    
    # Create a more complex test case
    log_content = """This is a test log with multiple messages
! Undefined control sequence.
l.6 \nonexistentcommand

! Missing $ inserted.
<inserted text> 
                $
<to be read again> 
                   \\
l.27 \end{align}"""
    
    tex_content = """\documentclass{article}
\begin{document}
\nonexistentcommand
\end{document}"""
    
    log_file.write_text(log_content)
    tex_file.write_text(tex_content)
    
    result = find_primary_error(log_content)
    
    # Should catch the first error (undefined control sequence)
    assert result['error_signature'] == 'LATEX_UNDEFINED_CONTROL_SEQUENCE'
    assert 'log_excerpt' in result

# --- Command Line Interface ---

def test_command_line_interface(temp_files):
    """Test the command line interface of error_finder.py"""
    temp_dir, log_file, tex_file = temp_files
    
    test_case = TEST_CASES['undefined_control_sequence']
    log_file.write_text(test_case['log'])
    tex_file.write_text(test_case['tex'])
    
    # Run the script directly
    cmd = f"python -m DEBUG_error_finder.error_finder --log-file {log_file} --tex-file {tex_file}"
    result = os.popen(cmd).read()
    
    try:
        result_data = json.loads(result)
        assert result_data['error_signature'] == test_case['expected']['error_signature']
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output: {result}")

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])
