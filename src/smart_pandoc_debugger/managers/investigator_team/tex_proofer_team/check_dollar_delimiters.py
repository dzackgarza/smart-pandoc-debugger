#!/usr/bin/env python3
"""
Dollar Delimiter Checker
Checks for unclosed $ and $$ delimiters in LaTeX documents.
"""
import sys
import re
from typing import List, Dict, Optional


def check_dollar_delimiters(tex_file: str) -> Optional[str]:
    """Check for unclosed dollar delimiters in TeX file."""
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
            
        # Track dollar signs across the entire document
        single_dollar_count = 0
        double_dollar_count = 0
        
        # Find all dollar signs and track their positions
        i = 0
        while i < len(content):
            if content[i] == '$':
                # Check for double dollar
                if i + 1 < len(content) and content[i + 1] == '$':
                    double_dollar_count += 1
                    i += 2  # Skip both dollars
                else:
                    single_dollar_count += 1
                    i += 1
            else:
                i += 1
        
        # Check for unclosed single dollars
        if single_dollar_count % 2 != 0:
            # Find the line with the unmatched dollar
            dollar_positions = []
            for line_num, line in enumerate(lines, 1):
                line_dollars = 0
                for char_pos, char in enumerate(line):
                    if char == '$':
                        # Check if it's not part of $$
                        if ((char_pos == 0 or line[char_pos - 1] != '$') and 
                            (char_pos == len(line) - 1 or line[char_pos + 1] != '$')):
                            line_dollars += 1
                            dollar_positions.append((line_num, char_pos, line))
                
                # If odd number of dollars on this line, this might be the problematic line
                if line_dollars % 2 != 0:
                    return f"UnclosedDollarDelimiter:{line_num}:$:Add closing $:{line.strip()}:{line.strip()}"
        
        # Check for unclosed double dollars
        if double_dollar_count % 2 != 0:
            # Find the line with the unmatched $$
            for line_num, line in enumerate(lines, 1):
                if '$$' in line:
                    return f"UnclosedDoubleDollarDelimiter:{line_num}:$$:Add closing $$:{line.strip()}:{line.strip()}"
                    
    except FileNotFoundError:
        return None
    except Exception:
        return None
        
    return None


def check_display_math_delimiters(tex_file: str) -> Optional[str]:
    """Check for unclosed \\[ \\] delimiters."""
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
            
        # Count \[ and \] delimiters
        open_brackets = len(re.findall(r'\\\[', content))
        close_brackets = len(re.findall(r'\\\]', content))
        
        if open_brackets != close_brackets:
            # Find the problematic line
            for line_num, line in enumerate(lines, 1):
                if '\\[' in line or '\\]' in line:
                    if open_brackets > close_brackets:
                        suggestion = "Add closing \\]"
                        delimiter = "\\["
                    else:
                        suggestion = "Add opening \\["
                        delimiter = "\\]"
                    return f"UnclosedDisplayMathDelimiter:{line_num}:{delimiter}:{suggestion}:{line.strip()}:{line.strip()}"
                    
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
    
    # Check dollar delimiters first
    result = check_dollar_delimiters(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
        
    # Check display math delimiters
    result = check_display_math_delimiters(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
    
    sys.exit(0)


if __name__ == "__main__":
    main() 