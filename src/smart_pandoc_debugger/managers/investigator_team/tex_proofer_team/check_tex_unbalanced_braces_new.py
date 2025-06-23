#!/usr/bin/env python3
"""
LaTeX Math Delimiter Checker

A simple and reliable tool to check for unbalanced delimiters in LaTeX math mode.
Handles $...$, \(...\), \[...\], and \left...\right pairs.
"""

import sys
from typing import Dict, List, Optional, Tuple

def find_math_regions(line: str) -> List[Dict]:
    """Find all math regions in a line of text.
    
    Returns a list of dictionaries with 'type', 'start', 'end', and 'content' keys.
    """
    regions = []
    i = 0
    n = len(line)
    
    while i < n:
        # Handle $...$ (inline math)
        if line[i] == '$':
            if i + 1 < n and line[i+1] == '$':  # Display math ($$...$$)
                end = line.find('$$', i+2)
                if end != -1:
                    regions.append({
                        'type': 'display_math',
                        'start': i,
                        'end': end + 2,
                        'content': line[i+2:end]
                    })
                    i = end + 2
                    continue
            else:  # Inline math ($...$)
                end = line.find('$', i+1)
                if end != -1:
                    regions.append({
                        'type': 'inline_math',
                        'start': i,
                        'end': end + 1,
                        'content': line[i+1:end]
                    })
                    i = end + 1
                    continue
        # Handle \(...\) and \[...\]
        elif line[i] == '\\' and i+1 < n and line[i+1] in '([':
            delimiter = line[i+1]
            end_delim = {'(': ')', '[': ']'}[delimiter]
            end = line.find('\\' + end_delim, i+2)
            if end != -1:
                regions.append({
                    'type': 'inline_math' if delimiter == '(' else 'display_math',
                    'start': i,
                    'end': end + 2,
                    'content': line[i+2:end]
                })
                i = end + 2
                continue
        i += 1
    return regions

def check_balanced_math(content: str) -> Optional[Tuple[str, int, str]]:
    """Check for balanced delimiters in math content.
    
    Args:
        content: The math content to check (without the delimiters)
        
    Returns:
        Tuple of (error_type, position, message) if unbalanced, else None
    """
    stack = []
    delimiters = {
        '{': '}',
        '[': ']',
        '(': ')',
        '\\{': '\\}',
        '\\[': '\\]',
        '\\(': '\\)',
        '\\left': '\\right'
    }
    
    i = 0
    n = len(content)
    
    while i < n:
        # Check for backslash commands first
        if content[i] == '\\':
            # Check for \left, \right, etc.
            for delim in ['\\left', '\\right', '\\{', '\\}', '\\[', '\\]', '\\(', '\\)']:
                if content.startswith(delim, i):
                    if delim in delimiters:  # Opening delimiter
                        stack.append((delim, i))
                    else:  # Closing delimiter
                        expected_opener = {v: k for k, v in delimiters.items()}.get(delim)
                        if not stack or stack[-1][0] != expected_opener:
                            return 'unmatched_close', i, f"Unmatched '{delim}'"
                        stack.pop()
                    i += len(delim)
                    break
            else:
                i += 1  # Skip unknown command
        else:
            # Check regular delimiters
            char = content[i]
            if char in delimiters:
                stack.append((char, i))
            elif char in delimiters.values():
                expected_opener = {v: k for k, v in delimiters.items()}.get(char)
                if not stack or stack[-1][0] != expected_opener:
                    return 'unmatched_close', i, f"Unmatched '{char}'"
                stack.pop()
            i += 1
    
    if stack:
        delim, pos = stack[0]
        return 'unmatched_open', pos, f"Unmatched '{delim}'"
    
    return None

def process_file(filename: str) -> List[str]:
    """Process a file and return error messages for unbalanced delimiters."""
    errors = []
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            regions = find_math_regions(line)
            for region in regions:
                result = check_balanced_math(region['content'])
                if result:
                    error_type, pos, msg = result
                    # Calculate the actual position in the original line
                    actual_pos = region['start'] + 1 + pos  # +1 for the opening $
                    # Get the problematic line with a caret
                    context = line.rstrip()
                    pointer = ' ' * (actual_pos - 1) + '^'
                    errors.append(
                        f"{filename}:{line_num}:{actual_pos}: {msg}\n"
                        f"{context}\n"
                        f"{pointer}"
                    )
    return errors

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tex_file>", file=sys.stderr)
        sys.exit(1)
    
    errors = process_file(sys.argv[1])
    if errors:
        for error in errors:
            print(error)
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
