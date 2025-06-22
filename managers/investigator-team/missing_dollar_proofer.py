#!/usr/bin/env python3
# managers/investigator-team/missing_dollar_proofer.py
"""
SDE Investigator Team: Missing Dollar Proofer
"""

import argparse
import json
import re
import sys
from typing import Dict, Optional

def find_missing_dollar_errors(tex_content: str) -> Optional[Dict]:
    """
    Proactively checks for lines that look like math but aren't enclosed in $.
    """
    suspicious_lines = []
    # Heuristic: find lines with function-like patterns (e.g., "f(x) =")
    # that are not commented out and not in a math env.
    math_pattern_re = re.compile(r'\w\(\w\)\s*=')

    for i, line in enumerate(tex_content.splitlines()):
        is_in_math = ("$" in line or r"\(" in line or r"\[" in line)
        if math_pattern_re.search(line) and not is_in_math and not line.strip().startswith("%"):
            suspicious_lines.append(f"L{i+1}: {line.strip()}")
    
    if suspicious_lines:
        first_suspicious_line_num_match = re.search(r"L(\d+)", suspicious_lines[0])
        error_line = first_suspicious_line_num_match.group(1) if first_suspicious_line_num_match else "unknown"
        
        return {
            "error_line_in_tex": error_line,
            "log_excerpt": "Proactive check found potential missing math delimiters on these lines:\n" + "\n".join(suspicious_lines),
            "error_signature": "LATEX_MISSING_DOLLAR",
            "raw_error_message": "Suspicious line(s) found without math delimiters.",
        }
    return None

def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(description="Proactively finds missing dollar signs in TeX files.")
    parser.add_argument("--tex-file", required=True, help="Path to the source TeX file.")
    args = parser.parse_args()

    try:
        with open(args.tex_file, "r", encoding="utf-8") as f:
            tex_content = f.read()
    except Exception:
        # If we can't read the file, we can't check it. Exit gracefully.
        print(json.dumps({}))
        sys.exit(0)

    result = find_missing_dollar_errors(tex_content)
    if result:
        print(json.dumps(result))
    else:
        # No error found, output empty JSON
        print(json.dumps({}))

if __name__ == "__main__":
    main() 