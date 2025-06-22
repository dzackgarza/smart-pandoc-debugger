#!/usr/bin/env python3
# managers/investigator-team/undefined_command_proofer.py
"""
SDE Investigator Team: Undefined Command Proofer

This specialist tool analyzes LaTeX compilation logs for "Undefined control sequence"
errors.
"""

import argparse
import json
import re
import sys

def find_undefined_command(log_content: str):
    """
    Checks for "Undefined control sequence." errors in the log.
    """
    pattern = re.compile(r"Undefined control sequence\.")
    match = pattern.search(log_content)

    if match:
        return {
            "error_signature": "LATEX_UNDEFINED_CONTROL_SEQUENCE",
            "raw_error_message": "Undefined control sequence.",
        }
    return None

def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(description="Finds 'Undefined control sequence.' errors in LaTeX logs.")
    parser.add_argument("--log-file", required=True, help="Path to the TeX compilation log file.")
    args = parser.parse_args()

    try:
        with open(args.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
    except Exception:
        print(json.dumps({}))
        sys.exit(0)

    result = find_undefined_command(log_content)
    if result:
        print(json.dumps(result))
    else:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
