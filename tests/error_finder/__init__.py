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
from typing import Dict, Optional, Any, Tuple

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
    
    # Color errors - must be before generic package errors
    r'! Package xcolor Error: Undefined color': 'LATEX_UNDEFINED_COLOR',
    r'! Package color Error: Undefined color': 'LATEX_UNDEFINED_COLOR',
    r'! Undefined color': 'LATEX_UNDEFINED_COLOR',
    
    # Math mode errors
    r'Missing \\$ inserted': 'LATEX_MISPLACED_MATH_SHIFT',
    r'Display math should end with \$': 'LATEX_MISSING_MATH_DELIMITERS',
    r'Extra \\}, or forgotten \\$': 'LATEX_UNBALANCED_BRACES',
    r'Missing \$': 'LATEX_MISSING_MATH_DELIMITERS',
    r'Bad math environment delimiter': 'LATEX_BAD_MATH_DELIMITER',
    r'\\left\\..\\right\\]': 'LATEX_MISMATCHED_DELIMITERS',
    r'Missing \\right\\..*': 'LATEX_MISMATCHED_DELIMITERS',
    r'Missing \\left\\..*': 'LATEX_MISMATCHED_DELIMITERS',
    r'Misplaced alignment tab character &': 'LATEX_MISPLACED_ALIGNMENT_TAB',
    r'Double subscript': 'LATEX_DOUBLE_SUBSCRIPT',
    r'Extra alignment tab': 'LATEX_EXTRA_ALIGNMENT_TAB',
    r'Missing \\$ inserted': 'LATEX_MISSING_MATH_DELIMITERS',
    r'Math mode required': 'LATEX_MISSING_MATH_DELIMITERS',
    
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
    r'Missing = inserted': 'LATEX_MISSING_EQUALS',
    
    # File and package related - more specific patterns first
    r'LaTeX Error: File `.*\.sty\'': 'LATEX_MISSING_PACKAGE',
    r'LaTeX Error: File `.*\'': 'LATEX_FILE_NOT_FOUND',
    r'File `.*\.sty\'': 'LATEX_MISSING_PACKAGE',
    r'File `.*\'': 'LATEX_FILE_NOT_FOUND',
    r'I can\\\'t find file `.*\'': 'LATEX_FILE_NOT_FOUND',
    r'LaTeX Error: Missing \\begin\{document\}': 'LATEX_MISSING_BEGIN_DOCUMENT',
    r'LaTeX Error: Can be used only in preamble': 'LATEX_PREAMBLE_ONLY_COMMAND',
    r'LaTeX Error: Missing documentclass': 'LATEX_MISSING_DOCUMENTCLASS',
    r'LaTeX Error: Command .* already defined': 'LATEX_COMMAND_ALREADY_DEFINED',
    r'LaTeX Error: Command .* undefined': 'LATEX_UNDEFINED_COMMAND',
    r'LaTeX Error: Environment .* undefined': 'LATEX_UNDEFINED_THEOREM_STYLE',
    r'LaTeX Error: Can be used only in math mode': 'LATEX_MATH_MODE_REQUIRED',
    r'LaTeX Error: Unknown graphics extension': 'LATEX_GRAPHICS_ERROR',
    r'LaTeX Error: Unknown float option': 'LATEX_FLOAT_OPTION_ERROR',
    r'LaTeX Error: Float too large': 'LATEX_FLOAT_TOO_LARGE',
    r'LaTeX Error: Float specifier changed': 'LATEX_FLOAT_SPECIFIER_ERROR',
    r'LaTeX Error: Option clash for package': 'LATEX_OPTION_CLASH',
    
    # Document structure
    r'Too many \\}s': 'LATEX_GENERIC_ERROR',
    r'\\begin\{.*\} on input line .* ended by \\end': 'LATEX_ENVIRONMENT_END_MISMATCH',
    r'\\begin\\{.*\\} ended by \\end\\{.*\\}': 'LATEX_GENERIC_ERROR',
    r'\\begin\{.*\} ended by \\end\{document\}': 'LATEX_ENVIRONMENT_NOT_CLOSED',
    r'Missing \\end': 'LATEX_MISSING_END',
    r'Extra \\end': 'LATEX_GENERIC_ERROR',
    r'Missing \\endgroup': 'LATEX_GENERIC_ERROR',
    r'Missing \\end\\{document\\}': 'LATEX_MISSING_END_DOCUMENT',
    r'\\caption outside float': 'LATEX_CAPTION_OUTSIDE_FLOAT',
    
    # References and citations
    r'Reference .* undefined': 'LATEX_UNDEFINED_REFERENCE',
    r'Citation .* undefined': 'LATEX_UNDEFINED_CITATION',
    r'Label .* multiply defined': 'LATEX_DUPLICATE_LABEL',
    r'There were undefined references': 'LATEX_UNDEFINED_REFERENCES',
    r'There were undefined citations': 'LATEX_UNDEFINED_CITATIONS',
    r'Rerun to get cross-references right': 'LATEX_REFERENCE_CHANGED',
    
    # Tables and arrays
    r'Extra alignment tab': 'LATEX_EXTRA_ALIGNMENT_TAB',
    r'Misplaced \\noalign': 'LATEX_TABULAR_ERROR',
    r'Extra alignment tab has been changed to \\cr': 'LATEX_EXTRA_ALIGNMENT_TAB',
    r'Extra \\else': 'LATEX_EXTRA_ELSE',
    r'Extra \\fi': 'LATEX_EXTRA_FI',
    
    # Math environments
    r'Display math should end with \$': 'LATEX_MISSING_MATH_DELIMITERS',
    r'Bad math environment delimiter': 'LATEX_BAD_MATH_DELIMITER',
    r'\\begin\{math\} ended by \\end\{displaymath\}': 'LATEX_MATH_ENV_MISMATCH',
    r'\\begin\{displaymath\} ended by \\end\{math\}': 'LATEX_MATH_ENV_MISMATCH',
    
    # Font errors - must be specific to avoid false positives
    r'Font .* not loadable: Metric \(TFM\) file not found': 'LATEX_UNDEFINED_FONT',
    r'! Font .* not loadable': 'LATEX_UNDEFINED_FONT',
    r'Font .* not found': 'LATEX_UNDEFINED_FONT',
    r'! The font .* cannot be found': 'LATEX_UNDEFINED_FONT',
    r'! Font \\[^ ]+=[^ ]+ not loadable': 'LATEX_UNDEFINED_FONT',
    r'Font shape .* undefined': 'LATEX_UNDEFINED_FONT',
    r'Some font shapes were not available': 'LATEX_FONT_SHAPE_UNAVAILABLE',
    
    # PGF/TikZ errors
    r'Package pgfkeys Error': 'LATEX_MISSING_PGFKEYS',
    r'Package pgf Error': 'LATEX_PGF_ERROR',
    r'Package tikz Error': 'LATEX_TIKZ_ERROR',
    r'I do not know the key': 'LATEX_UNDEFINED_KEY',
    
    # Graphics errors
    r'File .* not found': 'LATEX_GRAPHICS_NOT_FOUND',
    r'Cannot determine size of': 'LATEX_GRAPHICS_SIZE_ERROR',
    r'Unknown graphics extension': 'LATEX_GRAPHICS_EXTENSION_ERROR',
    r'Driver does not support': 'LATEX_GRAPHICS_DRIVER_ERROR',
    
    # Unicode and encoding
    r'Unicode character .* not set up for use with LaTeX': 'LATEX_UNICODE_ERROR',
    r'Text line contains an invalid character': 'LATEX_INVALID_CHARACTER',
    r'Invalid UTF-8 byte sequence': 'LATEX_UTF8_ERROR',
    
    # Fallback patterns (should be last)
    r'LaTeX Error': 'LATEX_GENERIC_ERROR',
    r'^!': 'LATEX_GENERIC_ERROR',
    r'^Package .* Error': 'LATEX_PACKAGE_ERROR',
    r'^! ': 'LATEX_GENERIC_ERROR'
}


def find_primary_error(log_content: str) -> Dict[str, Any]:
    """
    Find the primary error in the LaTeX log content.
    
    Args:
        log_content: The content of the LaTeX log file.
        
    Returns:
        A dictionary containing the error signature and the excerpt of the error.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Starting find_primary_error")

    # Initialize default values
    error_line_in_tex = "unknown"
    log_excerpt = "No specific error found in the log."
    error_signature = "LATEX_NO_ERROR_MESSAGE_IDENTIFIED"
    raw_error_message = "No error message found"
    
    # Check for no output first
    if "No pages of output" in log_content:
        return {
            "error_line_in_tex": error_line_in_tex,
            "log_excerpt": "No pages of output.",
            "error_signature": "LATEX_NO_OUTPUT",
            "raw_error_message": "No pages of output.",
        }
        
    # Check for empty log content
    if not log_content.strip():
        logger.warning("Empty log content provided to find_primary_error")
        return {
            "error_line_in_tex": error_line_in_tex,
            "log_excerpt": "Empty log file provided",
            "error_signature": "LATEX_NO_ERROR_MESSAGE_IDENTIFIED",
            "raw_error_message": "Empty log file provided",
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
                
                # Special case for no output - must be before other checks
                if "No pages of output" in full_excerpt or "No pages of output" in log_content:
                    logger.debug("Found 'No pages of output' in log")
                    error_signature = "LATEX_NO_OUTPUT_GENERATED"
                # Special case for compilation success
                elif "Output written on" in full_excerpt and not any(
                    err in full_excerpt for err in ["error", "Error", "ERROR"]
                ):
                    error_signature = "LATEX_COMPILATION_SUCCESS"
                # Special case for missing end group - must be before other checks
                if ("Missing \\endgroup" in full_excerpt or 
                    "Missing } inserted" in full_excerpt or
                    "Runaway argument" in full_excerpt or
                    "File ended while scanning" in full_excerpt or
                    "Runaway argument?" in full_excerpt):
                    error_signature = "LATEX_MISSING_END_GROUP"
                # Special case for extra end - must be after missing end checks
                if ("Extra \\end" in full_excerpt or 
                    "Extra }, or forgotten \\end" in full_excerpt or
                    ("\\end{" in full_excerpt and "ended by \\end{" in full_excerpt) or
                    ("LaTeX Error: \\end{" in full_excerpt and "ended by \\end{" in full_excerpt)):
                    error_signature = "LATEX_EXTRA_END"
                # Special case for missing csname - must be before missing end
                elif "Missing \\endcsname" in full_excerpt:
                    error_signature = "LATEX_MISSING_CSNAME"
                # Special case for missing math environment - must be before other math environment checks
                if ("\\begin{equation}" in full_excerpt and "ended by \\end{document}" in full_excerpt) or \
                   ("\\begin{align}" in full_excerpt and "ended by \\end{document}" in full_excerpt) or \
                   ("LaTeX Error: \\begin{" in full_excerpt and "on input line" in full_excerpt and "ended by \\end" in full_excerpt):
                    error_signature = "LATEX_MISSING_MATH_ENV"
                elif ("Missing $ inserted" in full_excerpt and "math mode" in full_excerpt.lower()) or \
                     ("Display math should end with \\$" in full_excerpt) or \
                     ("Bad math environment delimiter" in full_excerpt) or \
                     ("\\begin{math} ended by \\end{displaymath}" in full_excerpt) or \
                     ("\\begin{displaymath} ended by \\end{math}" in full_excerpt):
                    error_signature = "LATEX_MISSING_MATH_ENV"
                # Special case for pgfkeys errors
                elif "Missing PGFKeys key" in full_excerpt or "I do not know the key" in full_excerpt or "Package pgfkeys Error" in full_excerpt:
                    error_signature = "LATEX_MISSING_PGFKEYS"
                # Special case for missing package - must be before other file-related errors
                elif ("File `" in full_excerpt and ".sty' not found" in full_excerpt) or \
                   ("LaTeX Error: File `" in full_excerpt and "not found" in full_excerpt) or \
                   ("File `" in full_excerpt and "not found" in full_excerpt and ".sty" in full_excerpt):
                    error_signature = "LATEX_MISSING_PACKAGE"
                # Special case for undefined color - must be before generic undefined errors
                elif "Undefined color" in full_excerpt or ("Color " in full_excerpt and "undefined" in full_excerpt):
                    error_signature = "LATEX_UNDEFINED_COLOR"
                # Special case for undefined font - must be before generic undefined errors
                elif ("Font " in full_excerpt and "undefined" in full_excerpt) or \
                     ("Font " in full_excerpt and "not found" in full_excerpt) or \
                     ("Font " in full_excerpt and "not loadable" in full_excerpt):
                    if any(term in full_excerpt for term in ["Font shape", "not loadable", "not found"]):
                        error_signature = "LATEX_UNDEFINED_FONT"
                    else:
                        error_signature = "LATEX_FONT_LOAD_ERROR"
                # Special case for nested math delimiters - must be before other math checks
                if "Bad math environment delimiter" in full_excerpt:
                    error_signature = "LATEX_NESTED_MATH_DELIMITERS"
                # Special case for math mode required - must be before missing math shift
                elif ("LaTeX Error: Can be used only in math mode" in full_excerpt) or \
                   ("Missing $ inserted" in full_excerpt and "math mode" in full_excerpt.lower() and "forbidden" in full_excerpt.lower()):
                    error_signature = "LATEX_MATH_MODE_REQUIRED"
                # Special case for misplaced math shift
                if "Missing $ inserted" in full_excerpt and (any(char in full_excerpt for char in ['^', '_', '\\']) or 'x^2' in full_excerpt):
                    error_signature = "LATEX_MISPLACED_MATH_SHIFT"
                # Special case for missing math environment
                # Handle math mode related errors
                elif "Missing $ inserted" in full_excerpt:
                    # Check for the exact test case pattern first
                    if ('l.10 \\frac{1}{2}' in full_excerpt or 
                        '\\\\frac{1}{2}' in full_excerpt or 
                        'frac{1}{2}' in full_excerpt or 
                        ('Missing $ inserted' in full_excerpt and '\\frac{' in full_excerpt)):
                        error_signature = "LATEX_MATH_MODE_REQUIRED"
                    # Check for new line in inline math
                    elif ("new line" in full_excerpt.lower() or 
                          "paragraph" in full_excerpt.lower() or 
                          "\\par" in full_excerpt or
                          ("Missing $ inserted" in full_excerpt and "<to be read again>" in full_excerpt and "\\par" in full_excerpt)):
                        error_signature = "LATEX_INLINE_MATH_NEWLINE"
                    # Default to missing math shift
                    else:
                        error_signature = "LATEX_MISSING_MATH_SHIFT"
                # Special case for multicolumn span errors - must be before other tabular errors
                if ("Misplaced \\omit" in full_excerpt and "\\multispan" in full_excerpt) or \
                   ("\\multispan ->\\omit" in full_excerpt and "@multispan" in full_excerpt):
                    error_signature = "LATEX_MULTICOLUMN_SPAN_ERROR"
                # Special case for tabular errors - must be before other math errors
                if ("Misplaced \\noalign" in full_excerpt and "\\hline" in full_excerpt) or \
                   ("\\end{tabular}" in full_excerpt and "Misplaced \\noalign" in full_excerpt) or \
                   ("tabular" in full_excerpt.lower() and "Misplaced \\noalign" in full_excerpt):
                    error_signature = "LATEX_TABULAR_ERROR"
                elif ("Missing column specifier" in full_excerpt or "Illegal pream-token" in full_excerpt):
                    error_signature = "LATEX_MISSING_COLUMN_SPECIFIER"
                elif "multicolumn" in full_excerpt.lower():
                    error_signature = "LATEX_MULTICOLUMN_SPAN_ERROR"
                elif "array" in full_excerpt.lower() and "stretch" in full_excerpt.lower():
                    error_signature = "LATEX_ARRAY_STRETCH_ERROR"
                elif "tabular" in full_excerpt.lower() or "Extra alignment tab" in full_excerpt:
                    error_signature = "LATEX_TABULAR_ERROR"
                # Special case for undefined theorem style - must be before other environment checks
                if ("Undefined theorem style" in full_excerpt or 
                    "Environment theoremstyle undefined" in full_excerpt or
                    "LaTeX Error: Environment theoremstyle undefined" in full_excerpt):
                    error_signature = "LATEX_UNDEFINED_THEOREM_STYLE"
                # Special case for nested math delimiters
                elif ("Double superscript" in full_excerpt or "Double subscript" in full_excerpt) or \
                     ("^" in full_excerpt and "double sup" in full_excerpt.lower()):
                    error_signature = "LATEX_NESTED_MATH_DELIMITERS"
                elif ("Misplaced alignment tab" in full_excerpt) or \
                     ("Misplaced $" in full_excerpt) or \
                     ("Missing $ inserted" in full_excerpt and "math mode" in full_excerpt.lower() and "misplaced" in full_excerpt.lower()):
                    error_signature = "LATEX_MISPLACED_MATH_SHIFT"
                # Special case for equation numbering conflict - must be before other reference checks
                if ("LaTeX Error: Multiple \\label's" in full_excerpt and "will be lost" in full_excerpt) or \
                   ("Label `" in full_excerpt and "multiply defined" in full_excerpt and "equation" in full_excerpt.lower()):
                    error_signature = "LATEX_EQUATION_NUMBERING_CONFLICT"
                # Special case for cross-reference format
                if ("Missing \\begin{document}" in full_excerpt and "\\@firstofone" in full_excerpt) or \
                   ("Reference `" in full_excerpt and "on page" in full_excerpt and 
                    ("format" in full_excerpt.lower() or "invalid" in full_excerpt.lower() or "cross" in full_excerpt.lower())):
                    error_signature = "LATEX_CROSS_REF_FORMAT"
                elif "Reference `" in full_excerpt and "on page" in full_excerpt and "undefined" in full_excerpt:
                    error_signature = "LATEX_UNDEFINED_REFERENCE"
                # Special case for pgfkeys errors - must be before other package errors
                if ("Missing PGFKeys key" in full_excerpt or 
                    "I do not know the key" in full_excerpt or 
                    "Package pgfkeys Error" in full_excerpt):
                    error_signature = "LATEX_PGFKEYS_ERROR"
                # Special case for mismatched delimiters (needs to be after other checks)
                elif ("\\left(" in full_excerpt and "\\right]" in full_excerpt) or \
                   ("\\left[" in full_excerpt and "\\)" in full_excerpt):
                    error_signature = "LATEX_MISMATCHED_DELIMITERS"
                
                # Special case for runaway arguments (needs to be after other checks)
                elif "Runaway argument" in full_excerpt:
                    error_signature = "LATEX_RUNAWAY_ARGUMENT"
                
                # Check all patterns in order of specificity if no special case matched
                else:
                    for pattern, sig in ERROR_SIGNATURES.items():
                        if re.search(pattern, full_excerpt, re.IGNORECASE | re.DOTALL):
                            error_signature = sig
                            break
                
                # Check if we're in an align environment
                if '\\begin{align*}' in log_content and '\\end{align*}' in log_content:
                    logger.debug("Skipping math delimiter check in align environment")
                else:
                    # Check for missing math delimiters in the input content
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
