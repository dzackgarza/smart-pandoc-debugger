#!/usr/bin/env python3
"""
Math Mode Syntax Checker
Validates LaTeX math expressions for common syntax issues.
"""
import sys
import re
from typing import List, Dict, Tuple, Optional


class MathModeValidator:
    """Validates LaTeX math mode syntax."""
    
    def __init__(self):
        # Mathematical functions that should have backslash
        self.math_functions = {
            'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh', 'arcsin', 'arccos', 'arctan',
            'log', 'ln', 'exp', 'max', 'min', 'sup', 'inf', 'lim', 'det', 'dim',
            'ker', 'deg', 'gcd', 'hom', 'arg', 'Pr'
        }
        
        # Commands that require amsmath package
        self.amsmath_commands = {
            'text', 'DeclareMathOperator', 'operatorname', 'intertext', 'shortintertext'
        }
        
        # Valid bracket sizes
        self.bracket_sizes = ['bigl', 'Bigl', 'biggl', 'Biggl', 'bigr', 'Bigr', 'biggr', 'Biggr']
    
    def find_unclosed_fractions(self, content: str, line_num: int) -> Optional[Dict]:
        """Find unclosed \frac commands."""
        frac_pattern = r'\\frac\s*\{[^}]*\}?\s*\{[^}]*$'
        if re.search(frac_pattern, content):
            return {
                'error_type': 'UnclosedFraction',
                'line_num': line_num,
                'pattern': '\\frac{}{',
                'suggestion': 'Add closing brace }',
                'content': content
            }
        return None
    
    def find_missing_braces_in_exponents(self, content: str, line_num: int) -> Optional[Dict]:
        """Find exponents with multiple characters not in braces."""
        # Pattern: x^23 should be x^{23}
        exponent_pattern = r'(\w+|\})\^([a-zA-Z0-9]{2,})'
        match = re.search(exponent_pattern, content)
        if match:
            return {
                'error_type': 'MissingBracesInExponent',
                'line_num': line_num,
                'found': match.group(0),
                'suggestion': f"{match.group(1)}^{{{match.group(2)}}}",
                'content': content
            }
        return None
    
    def find_missing_math_function_backslash(self, content: str, line_num: int) -> Optional[Dict]:
        """Find math functions missing backslash."""
        for func in self.math_functions:
            # Look for function names not preceded by backslash
            pattern = rf'(?<!\\)\b{func}\s*\('
            if re.search(pattern, content):
                return {
                    'error_type': 'MissingMathFunctionBackslash',
                    'line_num': line_num,
                    'function': func,
                    'suggestion': f'\\{func}',
                    'content': content
                }
        return None
    
    def find_amsmath_without_package(self, content: str, line_num: int) -> Optional[Dict]:
        """Find commands that require amsmath package."""
        for cmd in self.amsmath_commands:
            pattern = rf'\\{cmd}\b'
            if re.search(pattern, content):
                return {
                    'error_type': 'AmsmathCommandWithoutPackage',
                    'line_num': line_num,
                    'command': cmd,
                    'suggestion': 'Add \\usepackage{amsmath} to document preamble',
                    'content': content
                }
        return None
    
    def find_nested_exponent_issues(self, content: str, line_num: int) -> Optional[Dict]:
        """Find nested exponents that need additional braces."""
        # Pattern: e^{x^2} should be e^{x^{2}}
        nested_pattern = r'(\w+)\^\{([^{}]*\^[^{}{}]*)\}'
        match = re.search(nested_pattern, content)
        if match:
            inner = match.group(2)
            # Check if the inner exponent has proper braces
            if not re.search(r'\^\{.*\}', inner):
                return {
                    'error_type': 'NestedExponentNeedsBraces',
                    'line_num': line_num,
                    'found': match.group(0),
                    'suggestion': "{base}^{{{inner_fixed}}}".format(base=match.group(1), inner_fixed=re.sub(r'\^([^{}]+)', r'^{\1}', inner)),
                    'content': content
                }
        return None


def check_math_mode_syntax(tex_file: str) -> Optional[str]:
    """Check for math mode syntax issues in TeX file."""
    validator = MathModeValidator()
    
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('%'):
                    continue
                
                # Check if line contains math mode
                if ('$' in line or '\\(' in line or '\\[' in line or 
                    'align' in line or 'equation' in line):
                    
                    # Check for various issues
                    for check_func in [
                        validator.find_unclosed_fractions,
                        validator.find_missing_braces_in_exponents,
                        validator.find_missing_math_function_backslash,
                        validator.find_amsmath_without_package,
                        validator.find_nested_exponent_issues
                    ]:
                        error = check_func(line, line_num)
                        if error:
                            # Format: ErrorType:LineNum:FoundPattern:Suggestion:ProblemSnippet:OriginalLine
                            problem_snippet = error.get('found', error.get('function', error.get('command', error.get('pattern', ''))))
                            return f"{error['error_type']}:{line_num}:{problem_snippet}:{error['suggestion']}:{problem_snippet}:{line}"
                            
    except FileNotFoundError:
        return None
    except Exception:
        return None
        
    return None


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <tex_file>", file=sys.stderr)
        sys.exit(2)
    
    result = check_math_mode_syntax(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
    
    sys.exit(0)


if __name__ == "__main__":
    main() 