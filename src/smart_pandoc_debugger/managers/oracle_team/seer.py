#!/usr/bin/env python3
"""
SDE Oracle Team: LaTeX Log Seer

This specialist tool analyzes a LaTeX compilation log to find the first and
most likely primary error. It extracts the error message, the line number in
the TeX source where the error occurred, and a relevant excerpt from the log.

It is designed to be a simple, robust extractor, providing the core diagnostic
information needed for a user to solve the problem.
"""

import argparse
import json
import logging
import os
import re
import sys
from typing import Dict, Optional

# --- Logging Setup ---
DEBUG_ENV = os.environ.get("DEBUG", "false").lower()
LOG_LEVEL = logging.DEBUG if DEBUG_ENV == "true" else logging.INFO

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - SEER (%(name)s) - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)
logger.propagate = False
# --- End Logging Setup ---

# Regex to find the line number in a TeX log. It looks for the common
# "l.<number>" pattern which indicates an error at a specific line.
LINE_NUMBER_PATTERN = re.compile(r"^l\.(?P<line_number>\d+)")

def extract_primary_error_details(log_content: str) -> Dict[str, Optional[str]]:
    """
    Parses LaTeX log content to find the first significant error.

    Args:
        log_content: The full content of the LaTeX compilation log.

    Returns:
        A dictionary containing:
            "error_line_in_tex": The line number in the TeX source, or "unknown".
            "log_excerpt": A relevant snippet from the log focusing on the error.
            "raw_error_message": The first line of the LaTeX error message.
    """
    if not log_content.strip():
        logger.warning("Empty log content provided.")
        return {
            "error_line_in_tex": "unknown",
            "log_excerpt": "Log content was empty.",
            "raw_error_message": "No error message found",
        }

    lines = log_content.splitlines()
    
    first_error_message: Optional[str] = None
    error_line_in_tex: str = "unknown"
    log_excerpt_lines = []

    MAX_EXCERPT_LINES = 15
    MAX_SEARCH_DIST_FOR_LINE_NUM = 10

    for i, line in enumerate(lines):
        if line.startswith("! "):  # Found the primary error line
            if first_error_message is not None:
                # We already found the first error, so we can stop.
                break
            
            first_error_message = line[2:].strip()
            log_excerpt_lines.append(line)
            
            # Search subsequent lines for the line number and more context
            for j in range(1, min(len(lines) - i, MAX_EXCERPT_LINES)):
                context_line = lines[i + j]
                log_excerpt_lines.append(context_line)

                # Find line number if we haven't already
                if error_line_in_tex == "unknown" and j <= MAX_SEARCH_DIST_FOR_LINE_NUM:
                    match = LINE_NUMBER_PATTERN.match(context_line.strip())
                    if match:
                        error_line_in_tex = match.group("line_number")

                # Heuristic to stop the excerpt after a blank line or another error
                if (not context_line.strip() and j > 2) or context_line.startswith("! "):
                    break
            
            # Once the first error is found and its context is gathered, stop.
            break

    if not first_error_message:
        logger.info("No lines starting with '!' found in the log. Assuming success or no standard error.")
        return {
            "error_line_in_tex": "unknown",
            "log_excerpt": "No standard LaTeX error messages (lines starting with '!') found in the log.",
            "raw_error_message": None
        }

    return {
        "error_line_in_tex": error_line_in_tex,
        "log_excerpt": "\n".join(log_excerpt_lines).strip(),
        "raw_error_message": first_error_message
    }


def main():
    parser = argparse.ArgumentParser(description="Finds the primary error in a LaTeX log file.")
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to the LaTeX .log file to analyze."
    )
    args = parser.parse_args()

    try:
        with open(args.log_file, 'r', encoding='utf-8', errors='replace') as f:
            log_content = f.read()
    except FileNotFoundError:
        logger.error(f"Log file not found at path: {args.log_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Could not read log file {args.log_file}: {e}")
        sys.exit(1)

    error_details = extract_primary_error_details(log_content)
    
    # Print the resulting dictionary as a JSON object to stdout
    print(json.dumps(error_details, indent=2))


if __name__ == '__main__':
    main()
