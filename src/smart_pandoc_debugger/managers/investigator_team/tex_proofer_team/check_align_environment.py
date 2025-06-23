#!/usr/bin/env python3
"""
Align Environment Checker
Validates align environment syntax and structure.
"""
import sys
import re
from typing import List, Dict, Optional


def check_align_environment(tex_file: str) -> Optional[str]:
    """Check for align environment issues."""
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        in_align = False
        align_start_line = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for start of align environment
            if re.search(r'\\begin\{align\*?\}', line):
                in_align = True
                align_start_line = line_num
                continue
                
            # Check for end of align environment
            if re.search(r'\\end\{align\*?\}', line):
                in_align = False
                continue
                
            # If we're inside an align environment
            if in_align:
                # Check for empty lines (not allowed in align)
                if not line:
                    return f"EmptyLineInAlign:{line_num}:Empty line:Remove empty line:{line}:Empty line in align environment"
                
                # Skip comment lines but continue checking
                if line.startswith('%'):
                    continue
                
                # In align environment, all equations should end with \\ 
                # (LaTeX best practice, though the last line is sometimes optional)
                if not line.endswith('\\\\') and not line.endswith('\\\\*'):
                    return f"MissingLineEndInAlign:{line_num}:\\\\:Add \\\\ at end of line:{line}:{line}"
                
                # Count & characters for alignment
                ampersand_count = line.count('&')
                
                # For align environment, equations should have consistent alignment
                # This is a basic check - in practice, align can be more complex
                if ampersand_count > 0:
                    # Basic validation - could be enhanced
                    pass
                    
    except FileNotFoundError:
        return None
    except Exception:
        return None
        
    return None


def check_equation_environment(tex_file: str) -> Optional[str]:
    """Check equation environment for common issues."""
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for nested equation environments (not allowed)
        if re.search(r'\\begin\{equation\}.*?\\begin\{equation\}', content, re.DOTALL):
            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                if '\\begin{equation}' in line:
                    return f"NestedEquationEnvironment:{line_num}:\\begin{{equation}}:Use align or remove nesting:{line.strip()}:{line.strip()}"
                    
        # Check for missing \label after \caption in figures with equations
        # This is more complex and might be better handled elsewhere
        
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
    
    # Check align environment
    result = check_align_environment(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
        
    # Check equation environment
    result = check_equation_environment(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
    
    sys.exit(0)


if __name__ == "__main__":
    main() 