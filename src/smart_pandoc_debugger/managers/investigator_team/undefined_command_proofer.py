#!/usr/bin/env python3
# managers/investigator-team/undefined_command_proofer.py
"""
SDE Investigator Team: Undefined Command Proofer

This specialist tool analyzes LaTeX compilation logs for "Undefined control sequence"
errors.
"""

import os
import sys
import re
import logging
import argparse
import json
from typing import Optional

# Add project root to path for imports
try:
    from utils.data_model import ActionableLead, SourceContextSnippet
except ImportError:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from utils.data_model import ActionableLead, SourceContextSnippet

# --- Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_undefined_command_proofer(log_file_path: str) -> Optional[ActionableLead]:
    """
    Parses a LaTeX log file to find an 'Undefined control sequence' error.
    """
    logger.debug(f"UndefinedCommandProofer: Starting analysis of {log_file_path}")
    assert os.path.exists(log_file_path), f"Log file not found at {log_file_path}"

    with open(log_file_path, 'r', encoding='utf-8') as f:
        log_content = f.read()

    # Corrected regex to be more robust against variations in log file format.
    # It looks for the "Undefined control sequence" message, finds the line number
    # on the next line, and then captures the command itself.
    pattern = re.compile(
        r"Undefined control sequence\.\n.*l\.(\d+)\s.*(\\.+)",
        re.MULTILINE
    )
    match = pattern.search(log_content)

    if not match:
        logger.debug("UndefinedCommandProofer: No 'Undefined control sequence' error found.")
        return None

    logger.info("UndefinedCommandProofer: Found 'Undefined control sequence' error.")
    error_line = int(match.group(1))
    command = match.group(2).strip()
    logger.debug(f"UndefinedCommandProofer: Line: {error_line}, Command: {command}")

    # Create a snippet from the log around the error line
    lines = log_content.splitlines()
    context_window = 5
    start_idx = max(0, error_line - context_window - 1)
    end_idx = min(len(lines), error_line + context_window)
    snippet_text = '\n'.join(lines[start_idx:end_idx])

    snippet = SourceContextSnippet(
        source_document_type="tex_compilation_log",
        central_line_number=error_line,
        snippet_text=snippet_text,
        notes=f"The undefined command '{command}' was found near line {error_line} of the TeX file."
    )

    lead = ActionableLead(
        source_service="UndefinedCommandProofer",
        problem_description=f"An 'Undefined control sequence' error was detected. The command `f{command}` is not defined.",
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": "LATEX_UNDEFINED_CONTROL_SEQUENCE",
            "error_line_number": error_line,
            "undefined_command": command
        }
    )
    return lead

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

    result = run_undefined_command_proofer(args.log_file)
    if result:
        print(json.dumps(result))
    else:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
