#!/usr/bin/env python3
# managers/investigator-team/runaway_argument_proofer.py
"""
SDE Investigator Team: Runaway Argument Proofer

This specialist tool analyzes LaTeX compilation logs for a specific type of
"runaway argument" error that manifests as "File ended while scanning use of...".
"""

import argparse
import json
import re
import sys

def find_runaway_argument(log_content: str):
    """
    Checks for "File ended while scanning use of..." errors in the log.
    """
    pattern = re.compile(r"File ended while scanning use of (.*)\.")
    match = pattern.search(log_content)

    if match:
        command = match.group(1)
        return {
            "error_line_in_tex": "unknown", # This error doesn't give a line number
            "log_excerpt": match.group(0),
            "error_signature": "LATEX_RUNAWAY_ARGUMENT",
            "raw_error_message": f"File ended while scanning use of {command}.",
        }
    return None

def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(description="Finds 'File ended while scanning use of...' errors in LaTeX logs.")
    parser.add_argument("--log-file", required=True, help="Path to the TeX compilation log file.")
    args = parser.parse_args()

    try:
        with open(args.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
    except Exception:
        # If we can't read the file, we can't check it. Exit gracefully.
        print(json.dumps({}))
        sys.exit(0)

    result = find_runaway_argument(log_content)
    if result:
        print(json.dumps(result))
    else:
        # No error found, output empty JSON
        print(json.dumps({}))

if __name__ == "__main__":
    main() 