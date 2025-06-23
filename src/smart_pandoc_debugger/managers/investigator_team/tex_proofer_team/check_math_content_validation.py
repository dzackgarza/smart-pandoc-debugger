#!/usr/bin/env python3
"""
Math Content Validation
Validates the content within math delimiters for LaTeX syntax correctness.
"""
import sys
import re
from typing import List, Dict, Optional, Tuple


class MathContentValidator:
    """Validates LaTeX math content syntax."""
    
    def __init__(self):
        # Valid LaTeX math commands (basic set)
        self.valid_math_commands = {
            'frac', 'sqrt', 'sum', 'prod', 'int', 'oint', 'iint', 'iiint',
            'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta',
            'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'pi', 'rho', 'sigma',
            'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega',
            'Gamma', 'Delta', 'Theta', 'Lambda', 'Xi', 'Pi', 'Sigma', 'Upsilon',
            'Phi', 'Psi', 'Omega',
            'cdot', 'times', 'div', 'pm', 'mp', 'ast', 'star', 'circ', 'bullet',
            'cap', 'cup', 'uplus', 'sqcap', 'sqcup', 'vee', 'wedge',
            'setminus', 'wr', 'diamond', 'bigtriangleup', 'bigtriangledown',
            'triangleleft', 'triangleright', 'lhd', 'rhd', 'unlhd', 'unrhd',
            'oplus', 'ominus', 'otimes', 'oslash', 'odot', 'bigcirc',
            'dagger', 'ddagger', 'amalg',
            'leq', 'prec', 'preceq', 'll', 'subset', 'subseteq', 'sqsubset',
            'sqsubseteq', 'in', 'vdash', 'smile', 'frown', 'geq', 'succ',
            'succeq', 'gg', 'supset', 'supseteq', 'sqsupset', 'sqsupseteq',
            'ni', 'dashv', 'mid', 'parallel', 'equiv', 'sim', 'simeq',
            'asymp', 'approx', 'cong', 'neq', 'doteq', 'notin', 'models',
            'perp', 'bowtie', 'Join', 'propto', 'vdash', 'dashv',
            'leftarrow', 'Leftarrow', 'rightarrow', 'Rightarrow',
            'leftrightarrow', 'Leftrightarrow', 'mapsto', 'hookleftarrow',
            'leftharpoonup', 'leftharpoondown', 'rightleftharpoons',
            'longleftarrow', 'Longleftarrow', 'longrightarrow',
            'Longrightarrow', 'longleftrightarrow', 'Longleftrightarrow',
            'longmapsto', 'hookrightarrow', 'rightharpoonup',
            'rightharpoondown', 'leadsto',
            'uparrow', 'Uparrow', 'downarrow', 'Downarrow', 'updownarrow',
            'Updownarrow', 'nearrow', 'searrow', 'swarrow', 'nwarrow',
            'infty', 'nabla', 'partial', 'exists', 'forall', 'neg', 'emptyset',
            'Re', 'Im', 'top', 'bot', 'angle', 'triangle', 'backslash',
            'prime', 'ell', 'hbar', 'imath', 'jmath', 'wp', 'mho',
            'Box', 'Diamond', 'clubsuit', 'diamondsuit', 'heartsuit', 'spadesuit',
            # Math functions
            'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh', 'arcsin', 'arccos', 'arctan',
            'log', 'ln', 'exp', 'max', 'min', 'sup', 'inf', 'lim', 'det', 'dim',
            'ker', 'deg', 'gcd', 'hom', 'arg', 'Pr',
            # Common LaTeX commands
            'left', 'right', 'text', 'mathrm', 'mathbf', 'mathit', 'mathcal'
        }
        
    def extract_math_blocks(self, content: str) -> List[Tuple[str, int, str]]:
        """Extract all math blocks with their line numbers and types."""
        lines = content.splitlines()
        math_blocks = []
        
        for line_num, line in enumerate(lines, 1):
            # Find inline math $...$
            inline_pattern = r'\$([^$]+)\$'
            for match in re.finditer(inline_pattern, line):
                math_blocks.append((match.group(1), line_num, 'inline'))
            
            # Find inline math \(...\)
            paren_pattern = r'\\\(([^)]*)\\\)'
            for match in re.finditer(paren_pattern, line):
                math_blocks.append((match.group(1), line_num, 'inline'))
                
            # Find display math $$...$$
            display_pattern = r'\$\$([^$]+)\$\$'
            for match in re.finditer(display_pattern, line):
                math_blocks.append((match.group(1), line_num, 'display'))
                
            # Find display math \[...\]
            bracket_pattern = r'\\\[([^\]]*)\\\]'
            for match in re.finditer(bracket_pattern, line):
                math_blocks.append((match.group(1), line_num, 'display'))
        
        return math_blocks
    
    def validate_math_content(self, math_content: str, line_num: int, math_type: str) -> Optional[Dict]:
        """Validate the content within math delimiters."""
        math_content = math_content.strip()
        
        if not math_content:
            return {
                'error_type': 'EmptyMathBlock',
                'line_num': line_num,
                'math_type': math_type,
                'suggestion': 'Add math content or remove delimiters',
                'content': math_content
            }
        
        # Check for unbalanced braces within math
        open_braces = math_content.count('{')
        close_braces = math_content.count('}')
        if open_braces != close_braces:
            return {
                'error_type': 'UnbalancedBracesInMath',
                'line_num': line_num,
                'math_type': math_type,
                'suggestion': f'Balance braces: {open_braces} open, {close_braces} close',
                'content': math_content
            }
        
        # Check for invalid characters in math mode
        # Common text characters that shouldn't be in math
        text_chars = re.findall(r'[a-zA-Z]{3,}', math_content)
        for text_char in text_chars:
            if text_char not in self.valid_math_commands:
                # Skip if it's part of a LaTeX command (starts with backslash)
                if f'\\{text_char}' in math_content:
                    continue
                # Check if it might need \text{} wrapper
                if any(c.islower() for c in text_char) and len(text_char) > 2:
                    # Additional check: skip common valid patterns
                    if text_char in ['left', 'right', 'frac', 'sqrt', 'text']:
                        continue
                    return {
                        'error_type': 'TextInMathMode',
                        'line_num': line_num,
                        'math_type': math_type,
                        'suggestion': f'Use \\text{{{text_char}}} for text',
                        'content': math_content,
                        'found': text_char
                    }
        
        # Check for common syntax errors
        # Unclosed \left without \right
        left_count = len(re.findall(r'\\left[([{\|.]', math_content))
        right_count = len(re.findall(r'\\right[)\]}|.]', math_content))
        if left_count != right_count:
            return {
                'error_type': 'UnmatchedLeftRight',
                'line_num': line_num,
                'math_type': math_type,
                'suggestion': f'Match \\left with \\right: {left_count} left, {right_count} right',
                'content': math_content
            }
        
        return None


def check_math_content_validation(tex_file: str) -> Optional[str]:
    """Check math content validation in TeX file."""
    validator = MathContentValidator()
    
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        math_blocks = validator.extract_math_blocks(content)
        
        for math_content, line_num, math_type in math_blocks:
            error = validator.validate_math_content(math_content, line_num, math_type)
            if error:
                # Format: ErrorType:LineNum:MathType:Suggestion:ProblemSnippet:OriginalContent
                found = error.get('found', math_content[:20] + '...' if len(math_content) > 20 else math_content)
                return f"{error['error_type']}:{line_num}:{math_type}:{error['suggestion']}:{found}:{math_content}"
                
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
    
    result = check_math_content_validation(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
    
    sys.exit(0)


if __name__ == "__main__":
    main() 