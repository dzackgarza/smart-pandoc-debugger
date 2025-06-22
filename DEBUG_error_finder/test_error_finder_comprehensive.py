#!/usr/bin/env python3
"""
Comprehensive test suite for error_finder.py

This file contains individual test cases for all expected functionality
in the error_finder.py module, organized by error type.
"""

import unittest
import json
import os
import tempfile
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the functions we want to test
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Use direct import with the correct path
from managers.investigator_team.error_finder import find_primary_error

class TestErrorFinder(unittest.TestCase):    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, 'test.log')
        self.tex_file = os.path.join(self.temp_dir.name, 'test.tex')
    
    def tearDown(self):
        """Clean up after each test method."""
        self.temp_dir.cleanup()
    
    def run_error_finder(self, log_content, tex_content):
        """Helper method to run error_finder with given inputs."""
        with open(self.log_file, 'w') as f:
            f.write(log_content)
        with open(self.tex_file, 'w') as f:
            f.write(tex_content)
        
        # Import here to ensure fresh state for each test
        from managers.investigator_team.error_finder import find_primary_error
        return find_primary_error(log_content)

    # --- Test Cases ---
    
    # 1. Missing Math Delimiters Tests
    def test_missing_math_delimiters_simple(self):
        """Test detection of missing math delimiters in simple equations."""
        log = "! Missing $ inserted."
        tex = "f(x) = 2x + 3"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISSING_MATH_DELIMITERS')
        self.assertIn('Missing $ inserted', result.get('raw_error_message', ''))
    
    def test_missing_math_delimiters_with_equals(self):
        """Test detection when equals sign is present."""
        log = "! Missing $ inserted.\n<*> f(x) = 2x + 3"
        tex = "f(x) = 2x + 3"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISSING_MATH_DELIMITERS')
    
    # 2. Undefined Control Sequence Tests
    def test_undefined_control_sequence(self):
        """Test detection of undefined control sequences."""
        log = "! Undefined control sequence.\nl.6 \\nonexistentcommand"
        tex = "\\documentclass{article}\n\\begin{document}\\nonexistentcommand\\end{document}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_UNDEFINED_CONTROL_SEQUENCE')
    
    # 3. Mismatched Delimiters Tests
    def test_mismatched_delimiters_basic(self):
        """Test detection of basic mismatched delimiters."""
        log = "! Missing $ inserted.\nl.6 \\left(\\frac{a}{b}\\right]"
        tex = "$\\left(\\frac{a}{b}\\right]$"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISMATCHED_DELIMITERS')
        self.assertIn('Missing $ inserted', result.get('raw_error_message', ''))
    
    def test_mismatched_delimiters_nested(self):
        """Test detection with nested delimiters."""
        log = "! Missing \\right.\nl.6 \\left[\\left(\\frac{a}{b}\\right]"
        tex = "$\\left[\\left(\\frac{a}{b}\\right]$"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISMATCHED_DELIMITERS')
    
    # 4. Unbalanced Braces Tests
    def test_unbalanced_braces_simple(self):
        """Test detection of simple unbalanced braces."""
        log = "! Missing } inserted.\nl.6 f(x) = \\frac{1}{1 + e^{-x}}"
        tex = "$f(x) = \\frac{1}{1 + e^{-x}}$"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_UNBALANCED_BRACES')
        self.assertIn('Unbalanced braces', result.get('raw_error_message', ''))
    
    def test_unbalanced_braces_complex(self):
        """Test detection in complex expressions."""
        log = "! Extra }, or forgotten $.\nl.6 \\frac{1}{1 + e^{-x}}}}"
        tex = "$\\frac{1}{1 + e^{-x}}}}$"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_UNBALANCED_BRACES')
    
    # 5. Math Environment Tests
    def test_math_environment_success(self):
        """Test successful math environment detection."""
        log = "Output written on test.pdf (1 page, 1234 bytes)."
        tex = "$x = 5$"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_COMPILATION_SUCCESS')
        self.assertIn('Output written on', result.get('raw_error_message', ''))
    
    def test_math_environment_missing_end(self):
        """Test detection of missing \\end in math environment."""
        log = "! Missing $ inserted.\nl.6 \\begin{align*} a = b + c"
        tex = "\\begin{align*} a = b + c"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISSING_END')
    
    # 6. Nested Math Tests
    def test_nested_math_simple(self):
        """Test handling of simple nested math expressions."""
        log = "! Missing $ inserted.\nl.6 a_{b_c}"
        tex = "$a_{b_c}$"
        result = self.run_error_finder(log, tex)
        # This test may need adjustment based on implementation
        self.assertIn(result.get('error_signature'), 
                     ['LATEX_MISSING_MATH_DELIMITERS', 'LATEX_NESTED_MATH'])
    
    def test_nested_math_complex(self):
        """Test handling of complex nested math."""
        log = "! Missing } inserted.\nl.6 \\sum_{i=1}^{n} a_i"
        tex = "$\\sum_{i=1}^{n} a_i$"
        result = self.run_error_finder(log, tex)
        self.assertIn(result.get('error_signature'),
                    ['LATEX_UNBALANCED_BRACES', 'LATEX_NESTED_MATH'])
    
    # 7. Math Operator Tests
    def test_math_operators_correct(self):
        """Test correct math operator usage."""
        log = "Output written on test.pdf"
        tex = "$\\sin(x) + \\cos(y) = 1$"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_NO_ERROR_MESSAGE_IDENTIFIED')
    
    def test_math_operators_incorrect(self):
        """Test detection of incorrect math operator usage."""
        log = "! Undefined control sequence.\\nl.6 sin(x)"
        tex = "$sin(x)$"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_UNDEFINED_CONTROL_SEQUENCE')
    
    # 8. Special Character Tests
    def test_special_characters(self):
        """Test handling of special characters."""
        log = "! Missing $ inserted.\nl.6 # $ % & ~ _ ^ \\ { }"
        tex = "# $ % & ~ _ ^ \\ { }"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISSING_MATH_DELIMITERS')
    
    # 9. File Not Found Tests
    def test_file_not_found(self):
        """Test handling of missing files."""
        log = "! LaTeX Error: File `missing-figure' not found."
        tex = "\\includegraphics{missing-figure}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_FILE_NOT_FOUND')
    
    # 10. Environment Tests
    def test_undefined_environment(self):
        """Test detection of undefined environments."""
        log = "! LaTeX Error: Environment nonexistentenv undefined."
        tex = "\\begin{nonexistentenv} test \\end{nonexistentenv}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_UNDEFINED_ENVIRONMENT')
    
    # 11. Argument Tests
    def test_missing_argument(self):
        """Test detection of missing arguments."""
        log = "! Missing { inserted.\nl.6 \\textbf"
        tex = "\\textbf"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_GENERIC_ERROR')
        self.assertIn('Missing {', result.get('raw_error_message', ''))
    
    # 12. Runaway Argument Tests
    def test_runaway_argument(self):
        """Test detection of runaway arguments."""
        log = "! Paragraph ended before \\\\textbf was complete."
        tex = "\\\\textbf{unclosed"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_UNEXPECTED_PARAGRAPH_END')
    
    # 13. Math Mode Tests
    def test_math_mode_error(self):
        """Test detection of math mode errors."""
        log = "! Missing $ inserted.\nl.6 x^2"
        tex = "x^2"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISSING_MATH_DELIMITERS')
    
    # 14. Multiple Errors Test
    def test_multiple_errors(self):
        """Test handling of multiple errors in the log."""
        log = """! Undefined control sequence.\nl.5 \\nonxistent\nl.6 \\nonxistent\n! Missing $ inserted.\nl.7 $x = 5"""
        tex = "\\nonxistent\\nonxistent\\$x = 5"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISSING_MATH_DELIMITERS')
        self.assertIn('Missing $ inserted', result.get('raw_error_message', ''))
    
    # 15. Complex Math Expression Test
    def test_complex_math_expression(self):
        """Test handling of complex math expressions."""
        log = """! Missing $ inserted.\nl.6 \\sum_{i=1}^{n} \\sqrt{\\frac{a_i^2 + b_i^2}{2}}"""
        tex = "$\\sum_{i=1}^{n} \\sqrt{\\frac{a_i^2 + b_i^2}{2}}$"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISSING_MATH_DELIMITERS')
    
    # 16. Table Environment Test
    def test_table_environment(self):
        """Test handling of table environment."""
        log = "! Misplaced \\noalign.\\l.15 \\end{tabular}"
        tex = "\\begin{tabular}{ll}\\na & b\\\\\\n\\end{tabular}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_GENERIC_ERROR')
        self.assertIn('Misplaced', result.get('raw_error_message', ''))
    
    # 17. Figure Environment Test
    def test_figure_environment(self):
        """Test handling of figure environment."""
        log = """! Missing endcsname inserted.\nl.34 \\includegraphics[width=0.8\\textwidth]{image.png}"""
        tex = """\\begin{figure}
               \\centering
               \\includegraphics[width=0.8\\textwidth]{image.png}
               \\caption{A figure}
               \\label{fig:my_label}
               \\end{figure}"""
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_GRAPHICS_ERROR')
    
    # 18. Citation Test
    def test_font_command_error(self):
        """Test handling of font command errors."""
        log = """! LaTeX Error: The font size command \\\\Large is not robust.\\nl.15 \\\\Large{Big Text}"""
        tex = "\\\\Large{Big Text}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_FONT_COMMAND_ERROR')
    
    # 19. Label Test
    def test_label_error(self):
        """Test handling of label errors."""
        log = "! LaTeX Error: Label `fig:my_label' multiply defined.\\nl.10 \\label{fig:my_label}"
        tex = "\\label{fig:my_label}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_GENERIC_ERROR')
    
    # 20. Package Error Test
    def test_package_error(self):
        """Test handling of package errors."""
        log = "! LaTeX Error: File `nonexistent.sty' not found.\\nl.2 \\usepackage{nonexistent}"
        tex = """\\documentclass{article}
               \\usepackage{nonexistent}
               \\begin{document}
               Test
               \\end{document}"""
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_FILE_NOT_FOUND')
    
    # 21. Document Class Test
    def test_document_class_error(self):
        """Test handling of document class errors."""
        log = """! LaTeX Error: File `nonexistent.cls' not found.\\nl.1 \\documentclass{nonexistent}"""
        tex = "\\documentclass{nonexistent}\
               \\begin{document}\
               Test\n               \\end{document}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_DOCUMENT_CLASS_ERROR')
    
    # 22. Math Font Test
    def test_math_font_error(self):
        """Test handling of math font errors."""
        log = r"! LaTeX Error: Command \mathds already defined.\nl.10 \DeclareMathAlphabet{\mathds}{U}{bbold}{m}{n}"
        tex = r"""\\documentclass{article}
               \\usepackage{dsfont}
               \\begin{document}
               $\mathds{R}$
               \\end{document}"""
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_COMMAND_ALREADY_DEFINED')
        self.assertIn('Command', result.get('raw_error_message', ''))
    
    # 23. Counter Error Test
    def test_counter_error(self):
        """Test handling of counter errors."""
        log = """! LaTeX Error: No counter 'nonexistent' defined.\nl.15 \\setcounter{nonexistent}{1}"""
        tex = "\\setcounter{nonexistent}{1}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_COUNTER_ERROR')
    
    # 24. Float Error Test
    def test_float_error(self):
        """Test handling of float errors."""
        log = """! LaTeX Error: Too many unprocessed floats.\\nl.50 \\begin{figure}"""
        tex = """\\begin{figure}[h]
               \\centering
               \\includegraphics{image}
               \\caption{Test}
               \\end{figure}"""
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_FLOAT_ERROR')
    
    # 25. Cross-Reference Test
    def test_reference_error(self):
        """Test handling of reference errors."""
        log = "! LaTeX Error: Reference `fig:my_label' on page 1 undefined.\\nl.20 \\ref{fig:my_label}"
        tex = "\\ref{fig:my_label}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_GENERIC_ERROR')
    
    # 26. Math Alignment Test
    def test_math_alignment_error(self):
        """Test handling of math alignment errors."""
        log = """! Package amsmath Error: Erroneous nesting of equation structures.\\nl.15 \\end{align}"""
        tex = """\\begin{align}
               a &= b + c \\
               d &= e + f \\
               \\end{align}"""
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MATH_ALIGNMENT_ERROR')
    
    # 27. Verbatim Environment Test
    def test_verbatim_error(self):
        """Test handling of verbatim environment errors."""
        log = "! LaTeX Error: \\begin{verbatim} on input line 5 ended by \\end{document}."
        tex = "\\begin{verbatim}\\nsome text\\end{document}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_ENVIRONMENT_END_MISMATCH')
        self.assertIn('verbatim', result.get('raw_error_message', ''))
    
    # 28. Hyperref Test
    def test_hyperref_error(self):
        """Test handling of hyperref errors."""
        log = """! Package hyperref Error: Invalid UTF-8 byte sequence.\\nl.30 \\href{http://example.com}{Link}"""
        tex = """\\href{http://example.com}{Link}"""
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_HYPERREF_ERROR')
    
    # 29. Bibliography Test
    def test_bibliography_error(self):
        """Test handling of bibliography errors."""
        log = """! LaTeX Error: No \\bibdata command.\\nl.1 \\bibliographystyle{plain}"""
        tex = """\\\\bibliographystyle{plain}
               \\bibliography{references}"""
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_BIBLIOGRAPHY_ERROR')
    
    # 30. Final Test: Successful Compilation
    def test_successful_compilation(self):
        """Test successful compilation scenario."""
        log = """This is pdfTeX, Version 3.14159265-2.6-1.40.21 (TeX Live 2020) (preloaded format=pdflatex)
               restricted \\write18 enabled.
               Output written on document.pdf (1 page, 12345 bytes)."""
        tex = """\\documentclass{article}
               \\begin{document}
               Hello, world!
               \\end{document}"""
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_NO_ERROR_MESSAGE_IDENTIFIED')
        self.assertEqual(result.get('error_line_in_tex'), 'unknown')
    
    # 31. Alignment Tests
    def test_alignment_error(self):
        """Test detection of alignment errors."""
        log = "! Misplaced alignment tab character &."
        tex = """\\\\begin{align}
               a &= b + c \\
               d &= e + f \\
               \\end{align}"""
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_MISPLACED_ALIGNMENT_TAB')
    
    # 15. Font Command Tests
    def test_font_command_error(self):
        """Test detection of font command errors."""
        log = "! Font \\foo=foo at 10.0pt not loadable: Metric (TFM) file not found."
        tex = "\\foo{test}"
        result = self.run_error_finder(log, tex)
        self.assertEqual(result.get('error_signature'), 'LATEX_FONT_ERROR')

if __name__ == '__main__':
    unittest.main(verbosity=2)
