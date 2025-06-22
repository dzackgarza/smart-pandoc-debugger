#!/usr/bin/env python3
"""
SDE Investigator Team: LaTeX Error Finder (Development Version)

This is a development version of the error finder with built-in test runner.
"""

import argparse
import json
import logging
import os
import re
import sys
from typing import Dict, Optional, List, Tuple

# --- Logging Setup ---
DEBUG_ENV = os.environ.get("DEBUG", "false").lower()
APP_LOG_LEVEL = logging.INFO if DEBUG_ENV == "true" else logging.WARNING
logger = logging.getLogger(__name__)
logger.setLevel(APP_LOG_LEVEL)

if not logging.getLogger().hasHandlers() and not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(asctime)s - ERROR_FINDER_DEV - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
# --- End Logging Setup ---

# Common error signatures based on keywords.# Ordered list of error patterns and their corresponding signatures
ERROR_SIGNATURES = [
    # Missing math delimiters - match the exact test case format
    (r"! Missing \$ inserted", "LATEX_MISSING_DOLLAR"),
    
    # Mismatched delimiters - look for patterns like \left( \right]
    (r"Missing \\right\.? inserted", "LATEX_MISMATCHED_DELIMITERS"),
    (r"Extra \\right", "LATEX_MISMATCHED_DELIMITERS"),
    (r"Delimiter .*?\n.*?missing", "LATEX_MISMATCHED_DELIMITERS"),
    (r"\\left\(.*?\\right\]", "LATEX_MISMATCHED_DELIMITERS"),  # Matches \left( ... \right]
    
    # Unbalanced braces - match the exact test case format
    (r"! Missing \\} inserted", "LATEX_UNBALANCED_BRACES"),
    (r"Missing [{}] inserted", "LATEX_UNBALANCED_BRACES"),
    (r"Extra \\}", "LATEX_UNBALANCED_BRACES"),
    (r"Runaway argument", "LATEX_UNBALANCED_BRACES"),
    
    # Undefined control sequences - match the exact test case format
    (r"! Undefined control sequence", "LATEX_UNDEFINED_CONTROL_SEQUENCE"),
    
    # Missing \begin{document}
    (r"Missing \\begin\{document\}", "LATEX_MISSING_DOCUMENT"),
    
    # Math mode errors
    (r"Display math should end with \$\$", "LATEX_MATH_MODE_ERROR"),
    (r"Bad math environment delimiter", "LATEX_MATH_MODE_ERROR"),
    
    # Success case - must be last
    (r"Output written on .*\.pdf", "LATEX_COMPILATION_SUCCESSFUL"),
    (r"Transcript written on", "LATEX_COMPILATION_SUCCESSFUL"),
]

def find_all_errors(log_content: str) -> List[Dict[str, Optional[str]]]:
    """
    Find all errors in the LaTeX log content.
    
    Args:
        log_content: The full content of the LaTeX compilation log.

    Returns:
        A list of error dictionaries, each containing:
            "error_line_in_tex": The line number in the TeX source, or "unknown".
            "log_excerpt": A relevant snippet from the log focusing on the error.
            "error_signature": A standardized signature for the error type.
            "raw_error_message": The first line of the LaTeX error message.
    """
    logger.debug("Starting find_all_errors")
    
    if not log_content.strip():
        logger.warning("Empty log content provided to find_all_errors")
        return []
    
    errors = []
    
    # Process each error signature
    for pattern, signature in ERROR_SIGNATURES:
        # Skip success case when looking for all errors
        if signature == "LATEX_COMPILATION_SUCCESSFUL":
            continue
            
        # Find all non-overlapping matches of this pattern
        for match in re.finditer(pattern, log_content, re.MULTILINE):
            # Get the error line (first line starting with '!' after the match)
            lines = log_content[match.start():].splitlines()
            error_line = next((line for line in lines if line.startswith('! ')), None)
            
            if error_line:
                error = {
                    "error_line_in_tex": "unknown",  # We'll update this if we can find a line number
                    "log_excerpt": error_line,
                    "error_signature": signature,
                    "raw_error_message": error_line[2:].strip()  # Remove '! ' prefix
                }
                
                # Try to find a line number in the context
                context = log_content[max(0, match.start() - 200):match.end() + 200]
                line_num_match = re.search(r'l\.(\d+)', context)
                if line_num_match:
                    error["error_line_in_tex"] = line_num_match.group(1)
                
                errors.append(error)
    
    # If no errors found but compilation was successful, return success
    if not errors and any(re.search(pattern, log_content) 
                         for pattern, sig in ERROR_SIGNATURES 
                         if sig == "LATEX_COMPILATION_SUCCESSFUL"):
        return [{
            "error_line_in_tex": "N/A",
            "log_excerpt": "Compilation successful",
            "error_signature": "LATEX_COMPILATION_SUCCESSFUL",
            "raw_error_message": None
        }]
    
    return errors

def find_primary_error(log_content: str) -> Dict[str, Optional[str]]:
    """
    Parses LaTeX log content to find the first significant error.
    Maintains backward compatibility by returning only the first error.
    
    Args:
        log_content: The full content of the LaTeX compilation log.

    Returns:
        A dictionary containing the first error found, or a default error if none found.
    """
    errors = find_all_errors(log_content)
    
    if not errors:
        # No errors found, check for successful compilation
        if any(re.search(pattern, log_content) 
              for pattern, sig in ERROR_SIGNATURES 
              if sig == "LATEX_COMPILATION_SUCCESSFUL"):
            return {
                "error_line_in_tex": "N/A",
                "log_excerpt": "Compilation successful",
                "error_signature": "LATEX_COMPILATION_SUCCESSFUL",
                "raw_error_message": None
            }
        
        # No errors and no success - return unknown error
        return {
            "error_line_in_tex": "unknown",
            "log_excerpt": "No specific error found in the log.",
            "error_signature": "LATEX_UNKNOWN_ERROR",
            "raw_error_message": "No error message found"
        }
    
    # Return the first error
    return errors[0]

def run_tests() -> bool:
    """
    Run a series of test cases against the error finder.
    
    Returns:
        bool: True if all tests passed, False otherwise.
    """
    test_cases = [
        # Test 1: Missing dollar sign
        ("Missing dollar sign", 
         "! Missing $ inserted.\n<inserted text> $\nl.27 \\end{align}",
         ["LATEX_MISSING_DOLLAR"]),
         
        # Test 2: Undefined control sequence
        ("Undefined control sequence",
         "! Undefined control sequence.\n<argument> \\\\nonexistent\nl.6 \\\\nonexistent",
         ["LATEX_UNDEFINED_CONTROL_SEQUENCE"]),
         
        # Test 3: Mismatched delimiters (should detect both missing $ and mismatched delimiters)
        ("Mismatched delimiters",
         "! Missing $ inserted.\n<inserted text> $\nl.15 $\\\\left( \\\\frac{a}{b} \\\\right]$",
         ["LATEX_MISSING_DOLLAR", "LATEX_MISMATCHED_DELIMITERS"]),
         
        # Test 4: Unbalanced braces
        ("Unbalanced braces",
         "! Missing } inserted.\n<inserted text> }\nl.27 \\\\end{align}",
         ["LATEX_UNBALANCED_BRACES"]),
         
        # Test 5: Compilation success
        ("Compilation success",
         "Output written on test.pdf (1 page, 12345 bytes).\nTranscript written on test.log.",
         ["LATEX_COMPILATION_SUCCESSFUL"]),
         
        # Test 6: Multiple errors in one log
        ("Multiple errors",
         "! Missing $ inserted.\n<inserted text> $\\nl.15 $\\\\left( \\\\frac{a}{b} \\\\right]$\\n"
         "! Undefined control sequence.\n<argument> \\\\nonexistent\\nl.16 \\\\nonexistent",
         ["LATEX_MISSING_DOLLAR", "LATEX_MISMATCHED_DELIMITERS", "LATEX_UNDEFINED_CONTROL_SEQUENCE"]),
    ]
    
    passed = 0
    total = 0
    
    print("\n=== Running Error Finder Tests ===\n")
    
    for name, log, expected_signatures in test_cases:
        total += 1
        print(f"Test {total}: {name}")
        print(f"  Input: {log[:60]}...")
        
        try:
            # Test find_primary_error (backward compatibility)
            if len(expected_signatures) > 0:
                primary_result = find_primary_error(log)
                primary_actual = primary_result.get('error_signature', 'MISSING_SIGNATURE')
                if primary_actual != expected_signatures[0]:
                    print(f"  ❌ FAIL (primary): Expected first signature {expected_signatures[0]}, got {primary_actual}")
                    print(f"  Result: {primary_result}")
                    print()
                    continue
            
            # Test find_all_errors
            all_errors = find_all_errors(log)
            actual_signatures = [e['error_signature'] for e in all_errors]
            
            # Check if all expected signatures are present
            missing = set(expected_signatures) - set(actual_signatures)
            unexpected = set(actual_signatures) - set(expected_signatures)
            
            if not missing and not unexpected:
                print(f"  ✅ PASS: Found all expected signatures: {actual_signatures}")
                passed += 1
            else:
                error_msg = []
                if missing:
                    error_msg.append(f"missing: {', '.join(missing)}")
                if unexpected:
                    error_msg.append(f"unexpected: {', '.join(unexpected)}")
                print(f"  ❌ FAIL: {'; '.join(error_msg)} (expected: {expected_signatures}, got: {actual_signatures})")
                print(f"  All errors found: {all_errors}")
                
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
        
        print()  # Blank line between tests
    
    print(f"\n=== Test Summary ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    return passed == total

def main():
    """Main entry point for the error finder tool."""
    parser = argparse.ArgumentParser(description="LaTeX Error Finder (Development Version)")
    parser.add_argument(
        "--log-file",
        help="Path to the LaTeX compilation log file."
    )
    parser.add_argument(
        "--tex-file",
        help="Path to the source TeX file (currently unused)."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the test suite."
    )
    
    args = parser.parse_args()
    
    if args.test:
        sys.exit(0 if run_tests() else 1)
    
    if not args.log_file:
        parser.print_help()
        sys.exit(1)
    
    try:
        with open(args.log_file, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read log file {args.log_file}: {e}")
        sys.exit(1)
    
    findings = find_primary_error(log_content)
    print(json.dumps(findings, indent=2))

if __name__ == "__main__":
    main()
