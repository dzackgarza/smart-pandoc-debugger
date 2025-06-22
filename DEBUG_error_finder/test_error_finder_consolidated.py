"""
Focused test suite for error_finder.py

30+ direct unit tests that verify core functionality
"""

import os
import sys
import json
import re
import pytest
from pathlib import Path
from typing import List, Tuple

# Import the module to test
sys.path.insert(0, str(Path(__file__).parent.parent))
from DEBUG_error_finder.error_finder import find_primary_error

def test_undefined_control_sequence():
    log = "! Undefined control sequence.\\nl.6 \\nonexistentcommand"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNDEFINED_CONTROL_SEQUENCE'

def test_missing_dollar():
    log = "! Missing $ inserted.\\n<inserted text> $\\n<to be read again> \\\\"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_MATH_DELIMITERS'

def test_unbalanced_braces():
    log = "! Missing } inserted.\\nl.6 f(x) = \\frac{1}{1 + e^{-x}}"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNBALANCED_BRACES'

def test_mismatched_delimiters():
    log = "! Missing \\right.\\nl.6 \\left[\\left(\\frac{a}{b}\\right]"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISMATCHED_DELIMITERS'

def test_runaway_argument():
    log = "Runaway argument?\\n{This is a runaway argument\\n! Paragraph ended before \\@vspace was complete."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_NO_ERROR_MESSAGE_IDENTIFIED'

def test_undefined_environment():
    log = "! LaTeX Error: Environment blah undefined.\\nl.5 \\begin{blah}"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNDEFINED_ENVIRONMENT'

def test_missing_begin_document():
    log = "! LaTeX Error: Missing \\begin{document}."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_BEGIN_DOCUMENT'

def test_file_not_found():
    log = "! LaTeX Error: File `missing.sty' not found."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_FILE_NOT_FOUND'

def test_extra_right_brace():
    log = "! Too many }'s.\\nl.6 \\end{document}"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_TOO_MANY_CLOSING_BRACES'

def test_missing_endcsname():
    log = "! Missing \\endcsname inserted."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_ENDCSNAME'

def test_illegal_unit():
    log = "! Illegal unit of measure (pt inserted)."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_ILLEGAL_UNIT'

def test_undefined_citation():
    log = "! LaTeX Error: Citation `key' on page 1 undefined."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNDEFINED_CITATION'

def test_double_subscript():
    log = "! Double subscript.\\nl.6 a_{b}_{c}"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_DOUBLE_SUBSCRIPT'

def test_misplaced_alignment():
    log = "! Misplaced alignment tab character &.\\nl.6 a & b"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISPLACED_ALIGNMENT_TAB'

def test_extra_alignment_tab():
    log = "! Extra alignment tab has been changed to \\cr.\\nl.6 a & b & c"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_EXTRA_ALIGNMENT_TAB'

def test_missing_number():
    log = "! Missing number, treated as zero.\\n<to be read again>"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_NUMBER'

def test_undefined_reference():
    log = "! LaTeX Warning: Reference `fig:myfig' on page 1 undefined."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNDEFINED_REFERENCE'

def test_missing_package():
    log = "! LaTeX Error: File `missingpackage.sty' not found."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_FILE_NOT_FOUND'

def test_math_mode_error():
    log = "! Missing $ inserted.\\n<inserted text> \\$\\n<to be read again> \\\\"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_MATH_DELIMITERS'

def test_undefined_color():
    log = "! Package xcolor Error: Undefined color `mycolor'."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNDEFINED_COLOR'

def test_missing_math_shift():
    log = "! Display math should end with \\."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_MATH_DELIMITERS'

def test_bad_math_delimiter():
    log = "! LaTeX Error: Bad math environment delimiter."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_BAD_MATH_DELIMITER'

def test_illegal_character():
    log = "! Package inputenc Error: Unicode character α (U+03B1) not set up for use with LaTeX."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNICODE_ERROR'

def test_missing_equals():
    log = "! Missing = inserted for \\ifdim.\\n<to be read again>"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_EQUALS'

def test_undefined_tab_position():
    log = r"""! Misplaced \noalign.\nl.123 \hline"""
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_TABULAR_ERROR'

def test_missing_math_shift_after():
    log = r"""! Missing $ inserted.
<inserted text> \$
<to be read again> \end"""
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_MATH_DELIMITERS'

def test_undefined_theorem_style():
    log = r"""! LaTeX Error: Environment mytheorem undefined."""
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNDEFINED_ENVIRONMENT'

def test_missing_begin():
    log = r"""! LaTeX Error: \begin{document} ended by \end{myenv}."""
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_ENVIRONMENT_END_MISMATCH'

def test_extra_end():
    log = r"""! LaTeX Error: \begin{document} on input line 1 ended by \end{myenv}."""
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_ENVIRONMENT_END_MISMATCH'

def test_missing_end_group():
    log = r"""! Missing } inserted.
<inserted text> }"""
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNBALANCED_BRACES'

def test_undefined_font():
    log = r"""! Font U/psy/m/n/10=psyr at 10.0pt not loadable: Metric (TFM) file not found."""
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNDEFINED_FONT'

def test_missing_pgfkeys():
    log = r"""! Package pgfkeys Error: I do not know the key '/tikz/mykey'"""
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_PGFKEYS_ERROR'

def test_unknown_graphics_extension():
    log = "! LaTeX Error: Unknown graphics extension: .eps"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_GRAPHICS_ERROR'

def test_missing_csname():
    log = "! Missing \\endcsname inserted.\\n<to be read again> \\relax"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_ENDCSNAME'

def test_no_output():
    log = "No pages of output"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_NO_OUTPUT_GENERATED'

def test_empty_log():
    result = find_primary_error("")
    assert result['error_signature'] == 'LATEX_NO_ERROR_MESSAGE_IDENTIFIED'

def test_multiple_errors():
    log = """! First error
l.1 First error line
! Second error
l.2 Second error line"""
    result = find_primary_error(log)
    assert 'First error' in result['log_excerpt']

def test_error_after_warning():
    log = """Warning: This is just a warning
! Real error
l.42 Something went wrong"""
    result = find_primary_error(log)
    assert 'Real error' in result['log_excerpt']

def test_line_number_extraction():
    log = "! Undefined control sequence.\\nl.42 \\nonexistent"
    result = find_primary_error(log)
    assert 'l.42' in result['log_excerpt']

def test_no_error_in_log():
    log = "This is a normal compilation log with no errors"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_NO_ERROR_MESSAGE_IDENTIFIED'

# --- New Test Cases ---

def test_nested_math_delimiters():
    log = "! Display math should end with $$.\\nl.6 $$E = mc^2$"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_MATH_DELIMITERS'

def test_misplaced_math_shift():
    log = "! Missing $ inserted.\\n<inserted text> $\\nl.6 $x = $y$"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_MATH_DELIMITERS'

def test_equation_numbering_conflict():
    log = "! LaTeX Error: There's no line here to end.\\nl.10 \\\\"
    result = find_primary_error(log)
    assert 'error_signature' in result

def test_missing_math_environment():
    log = "! LaTeX Error: \\begin{equation} on input line 5 ended by \\end{document}."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_ENVIRONMENT_END_MISMATCH'

def test_inline_math_newline():
    log = "! Missing $ inserted.\\n<inserted text> $\\nl.6 $x = y\\\
y$"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_MATH_DELIMITERS'

def test_multirow_span_error():
    log = "! Misplaced \\noalign.\\nl.15 \\hline\\"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_TABULAR_ERROR'

def test_multicolumn_span_error():
    log = "! Illegal unit of measure (pt inserted).\\n<to be read again> } \\nl.20 \\multicolumn{2}{c}{text}"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_ILLEGAL_UNIT'

def test_tabular_newline_error():
    log = "! Misplaced \\noalign.\\n<argument> \\hline \\nl.25 \\end{tabular}"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_TABULAR_ERROR'

def test_missing_column_specifier():
    log = "! Misplaced \\omit.\\nl.30 \\begin{tabular}{ll} a & b \\\\ \\hline"
    result = find_primary_error(log)
    assert 'tabular' in result['log_excerpt']

def test_array_stretch_error():
    log = "! Missing number, treated as zero.\\n<to be read again> \\relax \\nl.35 \\renewcommand{\\arraystretch}{1.5}"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_MISSING_NUMBER'

def test_duplicate_label():
    log = "! Package amsmath Error: Multiple \\label's: label 'eq:1' will be lost.\\nl.40 \\label{eq:1}"
    result = find_primary_error(log)
    assert 'label' in result['log_excerpt']

def test_reference_to_undefined_section():
    log = "! Reference `sec:nonexistent' on page 1 undefined.\\nl.45 \\ref{sec:nonexistent}"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_UNDEFINED_REFERENCE'

def test_cross_reference_format():
    log = "! Missing \\begin{document}.\\nl.50 \\ref{}"
    result = find_primary_error(log)
    assert 'error_signature' in result

def test_page_reference_error():
    log = "! Missing \\begin{document}.\\nl.55 \\pageref{key}"
    result = find_primary_error(log)
    assert 'error_signature' in result

def test_hyperref_link_error():
    log = "! Argument of \\@setref has an extra }.\\nl.60 \\href{http://example.com}{Example}"
    result = find_primary_error(log)
    assert 'error_signature' in result

def test_missing_caption():
    log = "! LaTeX Error: \\caption outside float.\\nl.65 \\caption{Figure}"
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_CAPTION_OUTSIDE_FLOAT'

def test_caption_outside_float():
    log = "! LaTeX Error: \\caption outside float.\\nl.70 \\caption{Figure}"
    result = find_primary_error(log)
    assert 'caption' in result['log_excerpt']

def test_float_placement_error():
    log = "! LaTeX Error: Unknown float option `H'.\\nl.75 \\begin{figure}[H]"
    result = find_primary_error(log)
    assert 'float' in result['log_excerpt']

def test_subfigure_error():
    log = "! Package subcaption Error: This package can't be used in cooperation\\nwith the subfigure package."
    result = find_primary_error(log)
    assert 'subcaption' in result['log_excerpt']

def test_wrapfigure_error():
    log = "! Package wrapfig Error: wrapfigure used inside a conflicting environment.\\nl.80 \\begin{wrapfigure}"
    result = find_primary_error(log)
    assert 'wrapfig' in result['log_excerpt']

def test_missing_bibitem():
    log = "! LaTeX Error: Something's wrong--perhaps a missing \\item.\\nl.85 \\bibitem{key}"
    result = find_primary_error(log)
    assert 'bibitem' in result['log_excerpt']

def test_bibtex_style_error():
    log = "! LaTeX Error: Style `unsrt' not found.\\nl.90 \\bibliographystyle{unsrt}"
    result = find_primary_error(log)
    assert 'Style' in result['log_excerpt']

def test_natbib_command_error():
    log = "! Package natbib Error: Bibliography not compatible with (sub)float package.\\nl.95 \\citep{key}"
    result = find_primary_error(log)
    assert 'natbib' in result['log_excerpt']

def test_multiple_bibliographies():
    log = "! LaTeX Error: Can be used only in preamble.\\nl.100 \\bibliography{refs}"
    result = find_primary_error(log)
    assert 'preamble' in result['log_excerpt']

def test_citation_style_mismatch():
    log = "! Package natbib Error: Bibliography not compatible with (sub)float package.\\nl.105 \\cite{key}"
    result = find_primary_error(log)
    assert 'natbib' in result['log_excerpt']

def test_tikz_scope_error():
    log = "! Package pgfkeys Error: I do not know the key '/tikz/scope/color'\\nl.110 \\begin{scope}[color=red]"
    result = find_primary_error(log)
    assert 'pgfkeys' in result['log_excerpt']

def test_algorithm2e_error():
    log = "! LaTeX Error: Environment algorithm undefined.\\nl.115 \\begin{algorithm}"
    result = find_primary_error(log)
    assert 'algorithm' in result['log_excerpt']

def test_minted_environment_error():
    log = "! Package minted Error: You must invoke LaTeX with the -shell-escape flag.\\nl.120 \\begin{minted}"
    result = find_primary_error(log)
    assert 'minted' in result['log_excerpt']

def test_beamer_frame_error():
    log = "! LaTeX Error: Missing \\begin{document}.\\nl.125 \\begin{frame}"
    result = find_primary_error(log)
    assert 'frame' in result['log_excerpt']

def test_custom_command_conflict():
    log = "! LaTeX Error: Command \\mycommand already defined.\\nl.130 \\newcommand{\\mycommand}{}"
    result = find_primary_error(log)
    assert 'Command' in result['log_excerpt']
def test_latex3_package_error():
    log = "! LaTeX3 Error: A sequence was misused."
    result = find_primary_error(log)
    assert 'LaTeX3' in result['log_excerpt']

def test_font_encoding_error():
    log = "! LaTeX Error: Encoding scheme `T1' unknown."
    result = find_primary_error(log)
    assert 'Encoding' in result['log_excerpt']

def test_missing_input_file():
    log = "! LaTeX Error: File `missing.tex' not found."
    result = find_primary_error(log)
    assert result['error_signature'] == 'LATEX_FILE_NOT_FOUND'

def test_include_error():
    log = "! LaTeX Error: Missing \\begin{document}.\\nl.10 \\include{file}"
    result = find_primary_error(log)
    assert 'include' in result['log_excerpt']

def test_verbatim_error():
    log = "! LaTeX Error: \\verb ended by end of line.\\nl.15 \\verb|text"
    result = find_primary_error(log)
    assert 'verb' in result['log_excerpt']

def test_bbl_file_error():
    log = "! LaTeX Error: Something's wrong--perhaps a missing \\item.\\nl.20 \\begin{thebibliography}"
    result = find_primary_error(log)
    assert 'bibliography' in result['log_excerpt']

def test_csquotes_error():
    log = "! Package csquotes Error: Invalid style."
    result = find_primary_error(log)
    assert 'csquotes' in result['log_excerpt']

def test_enumitem_error():
    log = "! Package enumitem Error: Unknown label 'foo' for 'label='.\\nl.25 \\begin{enumerate}[label=foo]"
    result = find_primary_error(log)
    assert 'enumitem' in result['log_excerpt']

def test_fancyhdr_error():
    log = "! LaTeX Error: \\headheight is too small."
    result = find_primary_error(log)
    assert 'headheight' in result['log_excerpt']

def test_geometry_error():
    log = "! Package geometry Error: \\paperwidth (0.0pt) too short."
    result = find_primary_error(log)
    assert 'geometry' in result['log_excerpt']

def test_graphicx_error():
    log = "! LaTeX Error: Unknown graphics extension: .eps."
    result = find_primary_error(log)
    assert 'graphics extension' in result['log_excerpt']

def test_hyperref_error():
    log = "! Package hyperref Error: Wrong DVI mode driver option."
    result = find_primary_error(log)
    assert 'hyperref' in result['log_excerpt']

def test_listings_error():
    log = "! Package Listings Error: File 'code.py' not found."
    result = find_primary_error(log)
    assert 'Listings' in result['log_excerpt']

def test_microtype_error():
    log = "! Package microtype Error: Unknown protrusion list `nonexistent'."
    result = find_primary_error(log)
    assert 'microtype' in result['log_excerpt']

def test_parskip_error():
    log = "! LaTeX Error: Missing \\begin{document}.\\nl.5 \\setlength{\\parskip}{10pt}"
    result = find_primary_error(log)
    assert 'parskip' in result['log_excerpt']

def test_siunitx_error():
    log = "! Package siunitx Error: Invalid number '1x'."
    result = find_primary_error(log)
    assert 'siunitx' in result['log_excerpt']

def test_titlesec_error():
    log = "! Package titlesec Error: Entered in horizontal mode."
    result = find_primary_error(log)
    assert 'titlesec' in result['log_excerpt']

def test_todonotes_error():
    log = "! Package todonotes Error: You have to use the 'draft' option."
    result = find_primary_error(log)
    assert 'todonotes' in result['log_excerpt']

def test_url_error():
    log = "! LaTeX Error: \\url ended by end of line.\\nl.10 \\url{http://example.com"
    result = find_primary_error(log)
    assert 'url' in result['log_excerpt']

def test_xcolor_error():
    log = "! Package xcolor Error: Undefined color 'mycolor'."
    result = find_primary_error(log)
    assert 'xcolor' in result['log_excerpt']

def performance_log():
    """Generate a large log file for performance testing."""
    log_lines = []
    for i in range(1000):
        if i % 100 == 0:
            log_lines.append(f"! Error in line {i}: Some error occurred")
        log_lines.append(f"Some log message {i}")
    return "\n".join(log_lines)

# --- Test Data ---

# --- Test Data ---
# Test cases organized by category
# Each test case includes:
# - log: Simulated LaTeX log output
# - tex: Corresponding TeX source
# - expected: Expected results
# - description: Human-readable description
# - tags: Categories for filtering

TEST_CASES = {
    # --- Math Mode Errors ---
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
        },
        'description': 'Detects missing math delimiters',
        'tags': ['math', 'syntax']
    },
    
    'nested_math': {
        'log': """! Missing $ inserted.
l.42 $a_{b_{c_}}$\nin math mode""",
        'tex': "$a_{b_{c_}}$",
        'expected': {
            'error_signature': 'LATEX_MISSING_MATH_DELIMITERS',
            'error_line_in_tex': 'unknown'
        },
        'description': 'Handles nested math expressions',
        'tags': ['math', 'nested']
    },
    
    # --- Control Sequences ---
    'undefined_control_sequence': {
        'log': """! Undefined control sequence.\\nl.6 \\nonexistentcommand""",
        'tex': "\\documentclass{article}\\n\\begin{document}\\n\\nonexistentcommand\\end{document}",
        'expected': {
            'error_signature': 'LATEX_UNDEFINED_CONTROL_SEQUENCE',
            'error_line_in_tex': 'unknown'
        },
        'description': 'Detects undefined control sequences',
        'tags': ['control', 'syntax']
    },
    
    'undefined_environment': {
        'log': """! LaTeX Error: Environment nonexistent undefined.\\nl.5 \\begin{nonexistent}""",
        'tex': "\\begin{nonexistent}\n\\end{nonexistent}",
        'expected': {
            'error_signature': 'LATEX_UNDEFINED_ENVIRONMENT',
            'error_line_in_tex': 'unknown'
        },
        'description': 'Detects undefined environments',
        'tags': ['environment', 'syntax']
    },
    
    # --- Syntax Errors ---
    'unbalanced_braces': {
        'log': """! Missing } inserted.\\nl.6 f(x) = \\frac{1}{1 + e^{-x}}""",
        'tex': "$f(x) = \\frac{1}{1 + e^{-x}}$",
        'expected': {
            'error_signature': 'LATEX_UNBALANCED_BRACES',
            'error_line_in_tex': 'unknown'
        },
        'description': 'Detects unbalanced braces',
        'tags': ['syntax', 'braces']
    },
    
    'mismatched_delimiters': {
        'log': """! Missing \\right.\\nl.6 \\left[\\left(\\frac{a}{b}\\right]""",
        'tex': "$\\left[\\left(\\frac{a}{b}\\right]$",
        'expected': {
            'error_signature': 'LATEX_MISMATCHED_DELIMITERS',
            'error_line_in_tex': 'unknown'
        },
        'description': 'Detects mismatched delimiters',
        'tags': ['syntax', 'delimiters']
    },
    
    # --- Complex Cases ---
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
        },
        'description': 'Handles runaway arguments',
        'tags': ['complex', 'syntax']
    },
    
    'nested_environments': {
        'log': """! LaTeX Error: \\begin{itemize} on input line 42 ended by \\end{enumerate}.\\nl.45 \\end{enumerate}""",
        'tex': """\\begin{itemize}
\\item First
\\begin{enumerate}
\\item Nested
\\end{enumerate}
\\end{itemize}""",
        'expected': {
            'error_signature': 'LATEX_ENVIRONMENT_END_MISMATCH',
            'error_line_in_tex': 'unknown'
        },
        'description': 'Handles nested environment errors',
        'tags': ['environment', 'nested']
    },
    
    # --- Real-world Examples ---
    'table_errors': {
        'log': """! Misplaced \\noalign.\\nl.123 \\hline""",
        'tex': """\\begin{tabular}{ll}
a & b \\
\\hline\\hline
c & d\\
\\end{tabular}""",
        'expected': {
            'error_signature': 'LATEX_TABULAR_ERROR',
            'error_line_in_tex': 'unknown'
        },
        'description': 'Detects table formatting errors',
        'tags': ['tables', 'realworld']
    },
    
    'unicode_math': {
        'log': """! Package inputenc Error: Unicode character α (U+03B1) not set up for use with LaTeX.""",
        'tex': "$\\alpha + β$",
        'expected': {
            'error_signature': 'LATEX_UNICODE_ERROR',
            'error_line_in_tex': 'unknown'
        },
        'description': 'Handles Unicode in math mode',
        'tags': ['unicode', 'math']
    }
}

# --- Test Utilities ---

def get_test_cases(*tags: str) -> List[Tuple[str, dict]]:
    """Filter test cases by tags."""
    if not tags:
        return list(TEST_CASES.items())
    return [
        (name, case) for name, case in TEST_CASES.items()
        if any(tag in case.get('tags', []) for tag in tags)
    ]

# --- Test Functions ---

class TestErrorFinderBasic:
    """Basic functionality tests."""
    
    def test_import(self):
        """Verify the module can be imported."""
        from DEBUG_error_finder import error_finder
        assert hasattr(error_finder, 'find_primary_error')
    
    def test_empty_log(self):
        """Test with empty log input."""
        result = find_primary_error("")
        assert result['error_signature'] == 'LATEX_NO_ERROR_MESSAGE_IDENTIFIED'

class TestErrorDetection:
    """Error detection test cases."""
    
    @pytest.mark.parametrize('test_name,test_case', get_test_cases())
    def test_error_detection(self, temp_files, test_name, test_case):
        """Parameterized test for error detection."""
        temp_dir, log_file, tex_file, _ = temp_files
        
        # Write test files
        log_file.write_text(test_case['log'])
        tex_file.write_text(test_case['tex'])
        
        # Run the test
        result = find_primary_error(test_case['log'])
        
        # Verify results
        assert result['error_signature'] == test_case['expected']['error_signature']
        assert 'log_excerpt' in result
        
        if 'error_line_in_tex' in test_case['expected'] and \
           test_case['expected']['error_line_in_tex'] != 'unknown':
            assert result['error_line_in_tex'] == test_case['expected']['error_line_in_tex']
    
    @pytest.mark.parametrize('test_name,test_case', get_test_cases('math'))
    def test_math_errors(self, temp_files, test_name, test_case):
        """Test math-specific error detection."""
        temp_dir, log_file, tex_file, _ = temp_files
        log_file.write_text(test_case['log'])
        tex_file.write_text(test_case['tex'])
        
        result = find_primary_error(test_case['log'])
        assert 'math' in result['error_signature'].lower() or \
               result['error_signature'] == 'LATEX_NO_ERROR_MESSAGE_IDENTIFIED'

class TestErrorRecovery:
    """Test error recovery and multiple error handling."""
    
    def test_multiple_errors(self, temp_files):
        """Test that the first error is correctly identified."""
        temp_dir, log_file, tex_file, _ = temp_files
        
        log_content = """! First error
l.1 First error line
! Second error
l.2 Second error line"""
        
        result = find_primary_error(log_content)
        assert 'First error' in result['log_excerpt']
    
    def test_error_after_warning(self, temp_files):
        """Test that errors after warnings are caught."""
        temp_dir, log_file, tex_file, _ = temp_files
        
        log_content = """Warning: This is just a warning
! Real error
l.42 Something went wrong"""
        
        result = find_primary_error(log_content)
        assert 'Real error' in result['log_excerpt']

class TestPerformance:
    """Performance testing."""
    
    @pytest.mark.benchmark
    def test_performance(self, benchmark, performance_log):
        """Benchmark error detection performance."""
        def run():
            return find_primary_error(performance_log)
        
        result = benchmark(run)
        assert 'error_signature' in result
    
    def test_large_log_performance(self):
        """Test with a very large log file."""
        large_log = "\n".join(f"Log line {i}" for i in range(10000))
        large_log += "\n! Error at the end\nl.10000 Something broke"
        
        start_time = time.time()
        result = find_primary_error(large_log)
        duration = time.time() - start_time
        
        assert 'error_signature' in result
        assert duration < 1.0  # Should process in under 1 second

class TestIntegration:
    """Integration tests with real-world scenarios."""
    
    def test_complex_document(self, temp_files):
        """Test with a complex document structure."""
        temp_dir, log_file, tex_file, aux_file = temp_files
        
        tex_content = r"""\documentclass{article}
\usepackage{amsmath}
\begin{document}
\section{Test}
\begin{equation}
    E = mc^2
\end{equation}
\begin{itemize}
    \item First item
    \item Second item with \textbf{bold} text
\end{itemize}
\end{document}
"""
        log_content = """This is pdfTeX, Version 3.14159265-2.6-1.40.21 (TeX Live 2020) (preloaded format=pdflatex)
 restricted \write18 enabled.
entering extended mode
(./test.tex
LaTeX2e <2020-10-01> patch level 2
L3 programming layer <2020-10-05> xparse <2020-03-03>
(/usr/local/texlive/2020/texmf-dist/tex/latex/base/article.cls
Document Class: article 2020/04/10 v1.4m Standard LaTeX document class
(/usr/local/texlive/2020/texmf-dist/tex/latex/base/size10.clo))
(/usr/local/texlive/2020/texmf-dist/tex/latex/amsmath/amsmath.sty
For additional information on amsmath, use the `?' option.
(/usr/local/texlive/2020/texmf-dist/tex/latex/amsmath/amstext.sty
(/usr/local/texlive/2020/texmf-dist/tex/latex/amsmath/amsgen.sty))
(/usr/local/texlive/2020/texmf-dist/tex/latex/amsmath/amsbsy.sty)
(/usr/local/texlive/2020/texmf-dist/tex/latex/amsmath/amsopn.sty))
No file test.aux.
[1{/usr/local/texlive/2020/texmf-var/fonts/map/pdftex/updmap/pdftex.map}]
! Undefined control sequence.
l.6 \nonexistentcommand
"""
        
        tex_file.write_text(tex_content)
        log_file.write_text(log_content)
        aux_file.write_text("\relax ")
        
        result = find_primary_error(log_content)
        assert result['error_signature'] == 'LATEX_UNDEFINED_CONTROL_SEQUENCE'

class TestCommandLine:
    """Command line interface tests."""
    
    def test_cli_basic(self, temp_files, monkeypatch):
        """Test basic CLI functionality."""
        temp_dir, log_file, tex_file, _ = temp_files
        test_case = TEST_CASES['undefined_control_sequence']
        
        log_file.write_text(test_case['log'])
        tex_file.write_text(test_case['tex'])
        
        # Mock command line arguments
        monkeypatch.setattr(
            'sys.argv',
            ['error_finder.py', '--log-file', str(log_file), '--tex-file', str(tex_file)]
        )
        
        # Import here to avoid import side effects
        from DEBUG_error_finder.error_finder import main
        
        # Capture stdout
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            main()
            output = sys.stdout.getvalue()
            result = json.loads(output)
            assert result['error_signature'] == test_case['expected']['error_signature']
        finally:
            sys.stdout = old_stdout
    
    def test_cli_missing_args(self, capsys):
        """Test CLI with missing arguments."""
        with pytest.raises(SystemExit):
            from DEBUG_error_finder.error_finder import main
            import sys
            sys.argv = ['error_finder.py']
            main()
        
        captured = capsys.readouterr()
        assert 'error' in captured.err.lower() or 'required' in captured.err.lower()

# --- Main Test Runner ---

if __name__ == "__main__":
    # Run tests with increased verbosity and show short tracebacks
    pytest.main([
        "-v",               # Verbose output
        "--tb=short",        # Shorter tracebacks
        "-x",                # Stop on first failure
        "--durations=10",    # Show slowest tests
        "--cov=DEBUG_error_finder",  # Coverage reporting
        __file__
    ])
