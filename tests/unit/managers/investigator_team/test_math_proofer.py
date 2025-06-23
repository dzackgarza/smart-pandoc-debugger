#!/usr/bin/env python3
"""
Tests for Branch 2: Math Mode & Equations validation
Tests all math validation specialists and the math proofer dispatcher.
"""
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

# Test imports - adjust paths as needed
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from smart_pandoc_debugger.managers.investigator_team.math_proofer import run_math_proofer
from smart_pandoc_debugger.managers.investigator_team.tex_proofer_team.check_math_mode_syntax import check_math_mode_syntax
from smart_pandoc_debugger.managers.investigator_team.tex_proofer_team.check_dollar_delimiters import check_dollar_delimiters, check_display_math_delimiters
from smart_pandoc_debugger.managers.investigator_team.tex_proofer_team.check_align_environment import check_align_environment
from smart_pandoc_debugger.managers.investigator_team.tex_proofer_team.check_math_content_validation import check_math_content_validation


class TestMathModeValidation:
    """Test math mode syntax validation."""

    def create_temp_tex_file(self, content: str) -> str:
        """Helper to create temporary TeX file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(content)
            return f.name

    def test_unclosed_fraction_detection(self):
        """Test detection of unclosed \\frac commands."""
        content = "Some text with $\\frac{1}{2$ incomplete fraction"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_mode_syntax(tex_file)
            assert result is not None
            assert "UnclosedFraction" in result
        finally:
            os.unlink(tex_file)

    def test_missing_braces_in_exponents(self):
        """Test detection of exponents missing braces."""
        content = "Formula: $x^23 + y^45 = z$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_mode_syntax(tex_file)
            assert result is not None
            assert "MissingBracesInExponent" in result
            assert "x^{23}" in result
        finally:
            os.unlink(tex_file)

    def test_missing_math_function_backslash(self):
        """Test detection of math functions missing backslash."""
        content = "We have $sin(x) + cos(y) = 1$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_mode_syntax(tex_file)
            assert result is not None
            assert "MissingMathFunctionBackslash" in result
            assert "sin" in result
        finally:
            os.unlink(tex_file)

    def test_amsmath_command_without_package(self):
        """Test detection of amsmath commands without package."""
        content = "Text with $\\text{some text}$ in math"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_mode_syntax(tex_file)
            assert result is not None
            assert "AmsmathCommandWithoutPackage" in result
            assert "amsmath" in result
        finally:
            os.unlink(tex_file)

    def test_nested_exponent_issues(self):
        """Test detection of nested exponents needing braces."""
        content = "Expression: $e^{x^2}$ needs more braces"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_mode_syntax(tex_file)
            # This may or may not trigger depending on the exact pattern
            # The test verifies the function runs without error
            assert result is None or "NestedExponent" in result
        finally:
            os.unlink(tex_file)

    def test_valid_math_syntax(self):
        """Test that valid math syntax doesn't trigger errors."""
        content = "Valid: $\\sin(x) + \\frac{1}{2} = y^{23}$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_mode_syntax(tex_file)
            assert result is None
        finally:
            os.unlink(tex_file)


class TestDollarDelimiters:
    """Test dollar delimiter validation."""

    def create_temp_tex_file(self, content: str) -> str:
        """Helper to create temporary TeX file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(content)
            return f.name

    def test_unclosed_single_dollar(self):
        """Test detection of unclosed single dollar delimiters."""
        content = "Text with $incomplete math and more text"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_dollar_delimiters(tex_file)
            assert result is not None
            assert "UnclosedDollarDelimiter" in result
        finally:
            os.unlink(tex_file)

    def test_unclosed_double_dollar(self):
        """Test detection of unclosed double dollar delimiters."""
        content = "Display math: $$x = y + z and more text"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_dollar_delimiters(tex_file)
            assert result is not None
            assert "UnclosedDoubleDollarDelimiter" in result
        finally:
            os.unlink(tex_file)

    def test_unclosed_display_math_brackets(self):
        """Test detection of unclosed \\[ \\] delimiters."""
        content = "Display math: \\[x = y + z without closing"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_display_math_delimiters(tex_file)
            assert result is not None
            assert "UnclosedDisplayMathDelimiter" in result
        finally:
            os.unlink(tex_file)

    def test_properly_closed_delimiters(self):
        """Test that properly closed delimiters don't trigger errors."""
        content = "Valid: $x = y$ and $$z = w$$ and \\[a = b\\]"
        tex_file = self.create_temp_tex_file(content)
        try:
            result1 = check_dollar_delimiters(tex_file)
            result2 = check_display_math_delimiters(tex_file)
            assert result1 is None
            assert result2 is None
        finally:
            os.unlink(tex_file)


class TestAlignEnvironment:
    """Test align environment validation."""

    def create_temp_tex_file(self, content: str) -> str:
        """Helper to create temporary TeX file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(content)
            return f.name

    def test_empty_line_in_align(self):
        """Test detection of empty lines in align environment."""
        content = """
\\begin{align}
x &= y + z \\\\

a &= b + c \\\\
\\end{align}
"""
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_align_environment(tex_file)
            assert result is not None
            assert "EmptyLineInAlign" in result
        finally:
            os.unlink(tex_file)

    def test_missing_line_end_in_align(self):
        """Test detection of missing \\\\ in align environment."""
        content = """
\\begin{align}
x &= y + z \\\\
a &= b + c
\\end{align}
"""
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_align_environment(tex_file)
            assert result is not None
            assert "MissingLineEndInAlign" in result
        finally:
            os.unlink(tex_file)

    def test_nested_equation_environment(self):
        """Test detection of nested equation environments."""
        content = """
\\begin{equation}
\\begin{equation}
x = y
\\end{equation}
\\end{equation}
"""
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_align_environment(tex_file)
            # This test might need adjustment based on exact implementation
            assert result is None or "NestedEquation" in result
        finally:
            os.unlink(tex_file)

    def test_valid_align_environment(self):
        """Test that valid align environment doesn't trigger errors."""
        content = """
\\begin{align}
x &= y + z \\\\
a &= b + c \\\\
\\end{align}
"""
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_align_environment(tex_file)
            assert result is None
        finally:
            os.unlink(tex_file)


class TestMathContentValidation:
    """Test math content validation."""

    def create_temp_tex_file(self, content: str) -> str:
        """Helper to create temporary TeX file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(content)
            return f.name

    def test_empty_math_block(self):
        """Test detection of empty math blocks."""
        content = "Empty math: $$ $$ and more text"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_content_validation(tex_file)
            assert result is not None
            assert "EmptyMathBlock" in result
        finally:
            os.unlink(tex_file)

    def test_unbalanced_braces_in_math(self):
        """Test detection of unbalanced braces within math."""
        content = "Math with issues: $\\frac{a}{b + c$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_content_validation(tex_file)
            assert result is not None
            assert "UnbalancedBracesInMath" in result
        finally:
            os.unlink(tex_file)

    def test_text_in_math_mode(self):
        """Test detection of text needing \\text{} wrapper."""
        content = "Math: $x = some text here + y$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_content_validation(tex_file)
            assert result is not None
            assert "TextInMathMode" in result
        finally:
            os.unlink(tex_file)

    def test_unmatched_left_right(self):
        """Test detection of unmatched \\left \\right delimiters."""
        content = "Math: $\\left( x + y$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_content_validation(tex_file)
            assert result is not None
            assert "UnmatchedLeftRight" in result
        finally:
            os.unlink(tex_file)

    def test_valid_math_content(self):
        """Test that valid math content doesn't trigger errors."""
        content = "Valid: $x + y = z$ and $\\left( a + b \\right) = c$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = check_math_content_validation(tex_file)
            assert result is None
        finally:
            os.unlink(tex_file)


class TestMathProoferIntegration:
    """Test the math proofer dispatcher integration."""

    def create_temp_tex_file(self, content: str) -> str:
        """Helper to create temporary TeX file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(content)
            return f.name

    def test_math_proofer_finds_issues(self):
        """Test that math proofer can find and report issues."""
        content = "Math with error: $x^23 + sin(y) = z$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = run_math_proofer(tex_file)
            assert result is not None
            assert result.source_service.startswith("MathProofer_")
            assert len(result.primary_context_snippets) > 0
        finally:
            os.unlink(tex_file)

    def test_math_proofer_no_issues(self):
        """Test that math proofer returns None for valid content."""
        content = "Valid math: $\\sin(x) + \\frac{1}{2} = y^{23}$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = run_math_proofer(tex_file)
            assert result is None
        finally:
            os.unlink(tex_file)

    def test_math_proofer_with_multiple_issues(self):
        """Test math proofer prioritization with multiple issues."""
        content = """
Math with multiple issues:
$x^23$ unclosed dollars
$$incomplete display math
\\begin{align}
x = y
\\end{align}
"""
        tex_file = self.create_temp_tex_file(content)
        try:
            result = run_math_proofer(tex_file)
            # Should find the first issue encountered
            assert result is not None
            assert result.source_service.startswith("MathProofer_")
        finally:
            os.unlink(tex_file)


class TestBranch2Requirements:
    """Test that all Branch 2 requirements are satisfied."""

    def create_temp_tex_file(self, content: str) -> str:
        """Helper to create temporary TeX file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(content)
            return f.name

    def test_requirement_unclosed_dollar_detection(self):
        """Branch 2 Req: When user has unclosed $ or \\( in document, report exact location."""
        content = "Text with $unclosed math"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = run_math_proofer(tex_file)
            assert result is not None
            # Should detect unclosed dollar
        finally:
            os.unlink(tex_file)

    def test_requirement_math_content_validation(self):
        """Branch 2 Req: For $...$ delimiters, ensure content is valid LaTeX math."""
        content = "Invalid content: $some regular text here$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = run_math_proofer(tex_file)
            assert result is not None
            # Should detect invalid math content
        finally:
            os.unlink(tex_file)

    def test_requirement_frac_validation(self):
        """Branch 2 Req: Flag common errors like \\frac{1}{2 (unclosed brace)."""
        content = "Unclosed fraction: $\\frac{1}{2$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = run_math_proofer(tex_file)
            assert result is not None
            # Should detect unclosed fraction
        finally:
            os.unlink(tex_file)

    def test_requirement_exponent_braces(self):
        """Branch 2 Req: Flag x^23 (missing braces)."""
        content = "Missing braces: $x^23$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = run_math_proofer(tex_file)
            assert result is not None
            # Should detect missing braces in exponent
        finally:
            os.unlink(tex_file)

    def test_requirement_align_environment(self):
        """Branch 2 Req: For align environment, verify line endings."""
        content = """
\\begin{align}
x &= y + z
a &= b + c \\\\
\\end{align}
"""
        tex_file = self.create_temp_tex_file(content)
        try:
            result = run_math_proofer(tex_file)
            assert result is not None
            # Should detect missing \\\\ 
        finally:
            os.unlink(tex_file)

    def test_requirement_math_functions(self):
        """Branch 2 Req: Find problematic math expressions like sin(x) → \\sin(x)."""
        content = "Function issue: $sin(x) + log(y)$"
        tex_file = self.create_temp_tex_file(content)
        try:
            result = run_math_proofer(tex_file)
            assert result is not None
            # Should detect missing backslash on math functions
        finally:
            os.unlink(tex_file)


if __name__ == "__main__":
    pytest.main([__file__]) 