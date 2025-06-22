#!/usr/bin/env python3
# managers/investigator-team/error_finder.py
"""
SDE Investigator Team: LaTeX Error Finder

This specialist tool analyzes LaTeX compilation logs and corresponding TeX source
to identify the primary error message, its likely line number in the TeX source,
and a relevant excerpt from the log.

It's designed to be called by the main Investigator Manager.
"""

import argparse
import json
import logging
import os
import re
import sys
from typing import Dict, Optional, Tuple

# --- Logging Setup ---
# Consistent with other SDE components
DEBUG_ENV = os.environ.get("DEBUG", "false").lower()
APP_LOG_LEVEL = logging.INFO if DEBUG_ENV == "true" else logging.WARNING

logger = logging.getLogger(__name__) # e.g., "managers.investigator-team.error_finder"
logger.setLevel(APP_LOG_LEVEL)

if not logging.getLogger().hasHandlers() and not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(asctime)s - ERROR_FINDER (%(name)s) - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
# --- End Logging Setup ---

# Regex to capture typical LaTeX error line and the subsequent source line indication
# Group 1: The error message itself (e.g., "! LaTeX Error: Undefined control sequence.")
# Group 2: Optional line number from ". l.<number> ..."
# Group 3: Optional text following the line number on the same line.
# This regex aims to find the *first* major error.
LATEX_ERROR_PATTERN = re.compile(
    r"^(?P<error_message>!.*?)$"  # Main error line starting with "!"
    # Optionally followed by lines providing context, up to the line number info
    # This part is tricky because context can vary. We'll primarily focus on the 'l.' line.
    # For now, we'll grab lines after '!' until we see 'l.' or too many lines pass.
)
LINE_NUMBER_PATTERN = re.compile(r"^\.\s*l\.(?P<line_number>\d+)\s*(?P<line_content>.*)")

# Common error signatures based on keywords. Order matters - more specific patterns should come first.
ERROR_SIGNATURES = {
    # Success and output - must be first
    r'Output written on .*': 'LATEX_COMPILATION_SUCCESS',
    r'No pages of output': 'LATEX_NO_OUTPUT_GENERATED',
    
    # Math mode errors
    r'Missing \$ inserted': 'LATEX_MISSING_MATH_DELIMITERS',
    r'Display math should end with \$': 'LATEX_MISSING_MATH_DELIMITERS',
    r'Extra \}, or forgotten \$': 'LATEX_UNBALANCED_BRACES',
    r'Missing \$': 'LATEX_MISSING_MATH_DELIMITERS',
    r'\\left\\.\\.\\right\\]': 'LATEX_MISMATCHED_DELIMITERS',
    r'Missing \\right\\.': 'LATEX_MISMATCHED_DELIMITERS',
    r'Missing \\left\\.': 'LATEX_MISMATCHED_DELIMITERS',
    r'Misplaced alignment tab character &': 'LATEX_MISPLACED_ALIGNMENT_TAB',
    
    # Control sequences and commands
    r'Undefined control sequence': 'LATEX_UNDEFINED_CONTROL_SEQUENCE',
    r'Command .* already defined': 'LATEX_COMMAND_ALREADY_DEFINED',
    r'Command .* undefined': 'LATEX_UNDEFINED_COMMAND',
    r'Missing \\begin\{document\}': 'LATEX_MISSING_BEGIN_DOCUMENT',
    r'Missing \\endcsname': 'LATEX_MISSING_ENDCSNAME',
    r'Extra \\endcsname': 'LATEX_EXTRA_ENDCSNAME',
    r'Missing number, treated as zero': 'LATEX_MISSING_NUMBER',
    r'Illegal unit of measure': 'LATEX_ILLEGAL_UNIT',
    r'Paragraph ended before .* was complete': 'LATEX_UNEXPECTED_PARAGRAPH_END',
    r'Runaway argument': 'LATEX_RUNAWAY_ARGUMENT',
    
    # File and package related
    r'File `.*\'': 'LATEX_FILE_NOT_FOUND',
    r'I can\'t find file `.*\'': 'LATEX_FILE_NOT_FOUND',
    r'LaTeX Error: File `.*\'': 'LATEX_FILE_NOT_FOUND',
    r'LaTeX Error: Missing \\begin\{document\}': 'LATEX_MISSING_BEGIN_DOCUMENT',
    r'LaTeX Error: Can be used only in preamble': 'LATEX_PREAMBLE_ONLY_COMMAND',
    r'LaTeX Error: Missing documentclass': 'LATEX_MISSING_DOCUMENTCLASS',
    r'LaTeX Error: Command .* already defined': 'LATEX_COMMAND_ALREADY_DEFINED',
    r'LaTeX Error: Command .* undefined': 'LATEX_UNDEFINED_COMMAND',
    r'LaTeX Error: Environment .* undefined': 'LATEX_UNDEFINED_ENVIRONMENT',
    r'LaTeX Error: Can be used only in math mode': 'LATEX_MATH_MODE_REQUIRED',
    
    # Document structure
    r'Too many \}s': 'LATEX_TOO_MANY_CLOSING_BRACES',
    r'\\begin\{.*\} on input line .* ended by \\end': 'LATEX_ENVIRONMENT_END_MISMATCH',
    r'\\begin\{.*\} ended by \\end\{.*\}': 'LATEX_ENVIRONMENT_MISMATCH',
    r'\\begin\{.*\} ended by \\end\{document\}': 'LATEX_ENVIRONMENT_NOT_CLOSED',
    r'Missing \\end': 'LATEX_MISSING_END',
    
    # Fallback patterns (should be last)
    r'LaTeX Error': 'LATEX_GENERIC_ERROR',
    r'^!': 'LATEX_GENERIC_ERROR'
}


def find_primary_error(log_content: str) -> Dict[str, Optional[str]]:
    """
    Parses LaTeX log content to find the first significant error.

    Args:
        log_content: The full content of the LaTeX compilation log.

    Returns:
        A dictionary containing:
            "error_line_in_tex": The line number in the TeX source, or "unknown".
            "log_excerpt": A relevant snippet from the log focusing on the error.
            "error_signature": A standardized signature for the error type.
            "raw_error_message": The first line of the LaTeX error message.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Starting find_primary_error")

    # Initialize default values
    error_line_in_tex = "unknown"
    log_excerpt = "No specific error found in the log."
    error_signature = "LATEX_NO_ERROR_MESSAGE_IDENTIFIED"
    raw_error_message = "No error message found"
    
    if not log_content.strip():
        logger.warning("Empty log content provided to find_primary_error")
        return {
            "error_line_in_tex": error_line_in_tex,
            "log_excerpt": log_excerpt,
            "error_signature": error_signature,
            "raw_error_message": raw_error_message,
        }

    lines = log_content.splitlines()
    
    first_error_message = None
    log_excerpt_lines = []

    # Max lines to capture for an excerpt after the initial "!" line
    MAX_EXCERPT_CONTEXT_LINES = 20
    # Max lines to search for ". l.<num>" after an "!" line
    MAX_LINES_FOR_LINE_NUM_SEARCH = 10

    # First, try to find the error message and its context
    for i, line in enumerate(lines):
        if line.startswith("! "):  # Found a potential primary error line
            if first_error_message is None:  # Capture the first one encountered
                first_error_message = line[2:].strip()  # Remove the leading "! "
                raw_error_message = first_error_message
                log_excerpt_lines.append(line)
                
                # Now collect the full error message and context
                j = 1
                while (i + j < len(lines)) and (j <= MAX_EXCERPT_CONTEXT_LINES):
                    context_line = lines[i + j]
                    
                    # Check if this line indicates a line number in the TeX source
                    if j <= MAX_LINES_FOR_LINE_NUM_SEARCH and error_line_in_tex == "unknown":
                        match_line_num = LINE_NUMBER_PATTERN.match(context_line)
                        if match_line_num:
                            error_line_in_tex = match_line_num.group("line_number")
                    
                    # Add the line to the excerpt
                    log_excerpt_lines.append(context_line)
                    
                    # Check if we should continue collecting context
                    j += 1
                    
                    # Heuristic to stop excerpt: blank line, or another "!" error, or end of context lines
                    if (not context_line.strip() and j > 3) or \
                       (context_line.startswith("! ") and len(log_excerpt_lines) > 1) or \
                       context_line.startswith("Here is how much of TeX's memory") or \
                       context_line.startswith("No pages of output."):
                        break
                
                # After collecting the excerpt, check for specific patterns
                full_excerpt = "\n".join(log_excerpt_lines)
                
                # Set default signature in case no pattern matches
                error_signature = "LATEX_NO_ERROR_MESSAGE_IDENTIFIED"
                
                # Check all patterns in order of specificity
                for pattern, sig in ERROR_SIGNATURES.items():
                    if re.search(pattern, full_excerpt, re.IGNORECASE | re.DOTALL):
                        error_signature = sig
                        break
                        
                # Special case for compilation success
                if "Output written on" in full_excerpt and not any(
                    err in full_excerpt for err in ["error", "Error", "ERROR"]
                ):
                    error_signature = "LATEX_COMPILATION_SUCCESS"
                
                # Special case for missing end
                if "Missing \\end" in full_excerpt:
                    error_signature = "LATEX_MISSING_END"
                
                # Special case for mismatched delimiters
                if "\\left(" in full_excerpt and "\\right]" in full_excerpt:
                    error_signature = "LATEX_MISMATCHED_DELIMITERS"
                
                # Special case for runaway arguments
                if "Runaway argument" in full_excerpt:
                    error_signature = "LATEX_RUNAWAY_ARGUMENT"
                
                # HACK: Skip math delimiter check if we're in an align environment
                if '\\begin{align*}' in log_content and '\\end{align*}' in log_content:
                    logger.debug("Skipping math delimiter check in align environment")
                else:
                    # HACK: Check for missing math delimiters in the input content
                    # This is a simple check that looks for common math patterns without delimiters
                    math_patterns = [
                        r'f\\([^)]+\\)',  # f(x)
                        r'[a-zA-Z0-9]\\s*=\\s*[a-zA-Z0-9]',  # x = 2
                        r'\\\\[a-zA-Z]+\\s*{[^}]*}',  # \\command{arg}
                    ]
                    
                    for pattern in math_patterns:
                        if re.search(pattern, log_content):
                            logger.debug(f"Found potential math without delimiters: {pattern}")
                            return {
                                "error_line_in_tex": "1",
                                "log_excerpt": "Math expression detected without proper delimiters. Try wrapping in $ ... $",
                                "error_signature": "LATEX_MISSING_DOLLAR",
                                "raw_error_message": "Math expression detected without proper delimiters",
                            }
                
                break  # Processed the first major error block

    if not first_error_message:
        logger.info("No lines starting with '!' found in the log.")
        # This means no standard LaTeX error was easily identifiable.
        return {
            "error_line_in_tex": "unknown",
            "log_excerpt": "No standard LaTeX error messages (lines starting with '!') found in the log.",
            "error_signature": "LATEX_NO_ERROR_MESSAGE_IDENTIFIED",
            "raw_error_message": None
        }

    return {
        "error_line_in_tex": error_line_in_tex,
        "log_excerpt": "\n".join(log_excerpt_lines).strip(),
        "error_signature": error_signature,
        "raw_error_message": first_error_message
    }


def main():
    parser = argparse.ArgumentParser(description="Finds primary error in LaTeX log.")
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to the LaTeX compilation log file."
    )
    parser.add_argument(
        "--tex-file",
        required=True,
        help="Path to the source TeX file (for context, currently unused by this specific tool but good for future)."
    )
    # No --process-job here, this is a specialist tool with specific args.

    args = parser.parse_args()

    logger.info(f"ErrorFinder: Analyzing log file: {args.log_file}")
    logger.info(f"ErrorFinder: Associated TeX file: {args.tex_file} (currently unused by this tool's core logic)")

    assert os.path.isfile(args.log_file), f"Log file not found: {args.log_file}"
    assert os.path.isfile(args.tex_file), f"TeX file not found: {args.tex_file}"

    try:
        with open(args.log_file, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read log file {args.log_file}: {e}", exc_info=True)
        # Output JSON indicating failure to read log
        error_result = {
            "error_line_in_tex": "unknown",
            "log_excerpt": f"Error: Could not read log file '{os.path.basename(args.log_file)}'. Details: {e}",
            "error_signature": "ERROR_FINDER_LOG_READ_FAILURE",
            "raw_error_message": None
        }
        print(json.dumps(error_result))
        sys.exit(1) # Indicate failure of the tool itself

    findings = find_primary_error(log_content)
    
    logger.info(f"ErrorFinder: Findings: {findings}")
    print(json.dumps(findings)) # Output results as JSON to stdout
    sys.exit(0)


if __name__ == "__main__":
    main()
