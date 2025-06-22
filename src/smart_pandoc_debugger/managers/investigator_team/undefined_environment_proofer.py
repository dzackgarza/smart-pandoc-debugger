#!/usr/bin/env python3
# managers/investigator-team/undefined_environment_proofer.py
"""
SDE Investigator Team: Undefined Environment Proofer

This specialist tool analyzes LaTeX compilation logs for "Environment ... undefined"
errors.
"""

import argparse
import json
import re
import sys

def find_undefined_environment(log_content: str):
    """
    Checks for "Environment ... undefined." errors in the log.
    """
    pattern = re.compile(r"Environment (.*) undefined\.")
    match = pattern.search(log_content)

    if match:
        env_name = match.group(1)
        return {
            "error_signature": "LATEX_UNDEFINED_ENVIRONMENT",
            "raw_error_message": f"Environment {env_name} undefined.",
        }
    return None

def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(description="Finds 'Environment ... undefined.' errors in LaTeX logs.")
    parser.add_argument("--log-file", required=True, help="Path to the TeX compilation log file.")
    args = parser.parse_args()

    try:
        with open(args.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
    except Exception:
        print(json.dumps({}))
        sys.exit(0)

    result = find_undefined_environment(log_content)
    if result:
        print(json.dumps(result))
    else:
        print(json.dumps({}))

if __name__ == "__main__":
    main() 