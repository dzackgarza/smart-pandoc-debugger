import subprocess # Used to run external commands (like Pandoc)
import os         # Used for interacting with the operating system (e.g., checking file existence, path manipulation)
import sys        # Provides access to system-specific parameters and functions (e.g., sys.stdin, sys.stdout, sys.stderr)
import re         # Regular expression module for pattern matching in text
from typing import Callable, Dict, List, Optional, Tuple, Any, Generator
from pydantic import BaseModel, Field # Pydantic for structured data validation

# --- SCRIPT VERSION ---
# Version: 0.1.0
# --- END SCRIPT VERSION ---

# --- SCRIPT DESIGN PHILOSOPHY: CONTRIBUTION & ADHERENCE GUIDELINES ---
# This script is a specialized internal debugging tool, designed to function as a Unix pipe.
# Its design prioritizes internal rigor and immediate error surfacing.
# Adhere to the following principles when contributing:
#
# 1.  **Purpose:** Exclusively for debugging failed Pandoc/LaTeX compilations. Assumes
#     Markdown content is piped via stdin, and generates a debug report to stdout.
#
# 2.  **Input/Output (Pipe Focus):**
#     * **Input:** Accepts Markdown content ONLY on `stdin`. No file path arguments for input.
#     * **Output (Report Only):** Prints structured debug reports (problems, context, solutions)
#         ONLY to `stdout` as ASCII text.
#         * **Success (No Errors/Warnings from Pandoc):** If Pandoc exits with code 0 and its `stderr` is empty,
#             this script now outputs a minimal "Status Report: No problems found".
#         * **Success with Warnings/Info (Non-PDF):** If Pandoc exits with code 0 but its `stderr` is *not* empty,
#             and the output format is *not* PDF, a report detailing these warnings/info is printed to `stdout`.
#         * **Success (PDF Output):** If Pandoc exits with code 0 for a PDF output, any `stderr` content
#             (warnings/info) is *ignored* and a "No problems found" status is reported. The assumption is that
#             if the PDF builds, we are successful regardless of warnings.
#         * **Failure/Errors:** A detailed report of structured problems is printed to `stdout`.
#     * **Side Channel:** Operational messages (e.g., "Attempting to compile...") go to `stderr`
#         to avoid polluting the primary `stdout` report pipe.
#     * **No File Generation:** This script explicitly does NOT generate output files (e.g., `.html`, `.pdf`).
#
# 3.  **External Dependencies (No Checks):**
#     * **Do not** add checks for Pandoc or LaTeX installations.
#     * **Assume** Pandoc/LaTeX are correctly installed and in PATH.
#     * **Embrace crashes:** If `pandoc` or `pdflatex` is missing/inaccessible, the
#         script *will* crash with a Python `FileNotFoundError`. This is intentional;
#         it's an environment issue, not a script bug to handle gracefully.
#
# 4.  **Assertions (Internal Rigor):**
#     * **Use `assert`** for validating critical internal assumptions (e.g., parameters being non-empty).
#     * **Expect crashes:** An `AssertionError` signals an *internal* script logic flaw or
#         violation of its operational assumptions. These must be fixed by developers.
#
# 5.  **Internal Development Tool (Crash Philosophy - Softened):**
#     * This is for *internal* use. The "crash if our code is wrong" philosophy is paramount.
#     * For log parsing, if a critical error keyword is detected in `stderr` but
#         no pattern captures it, the script *will* now *report* a specific internal
#         parsing error rather than crashing directly via `assert False`. This highlights
#         a gap in our parsing logic that requires developer attention, but allows the script
#         to complete its analysis.
#
# 6.  **Log Assumptions & Regex Stagnation:**
#     * **Assume well-formed logs:** Do not implement extensive error handling for malformed
#         or unusual log edge cases.
#     * **Assume fixed Pandoc and LaTeX versions:** Regex patterns are *not* dynamically updated.
#     * **Manual updates only:** Any changes to `ERROR_PATTERNS`, `GENERIC_CRITICAL_PATTERNS`,
#         `WARNING_PATTERNS`, or `TROUBLESHOOTING_TIPS` must be done manually by developers.
#
# 7.  **MVP Focus (Errors & Actionable Warnings):**
#     * Current scope focuses on critical errors that *break* the PDF build.
#     * If Pandoc exits successfully but emits warnings to `stderr`, these *are* reported in a
#         simplified format, as they are often actionable issues (e.g., deprecations, syntax quirks).
#     * The goal is to provide **actionable intelligence**, not just a simple pass/fail.
# --- END SCRIPT DESIGN PHILOSOPHY: CONTRIBUTION & ADHERENCE GUIDELINES ---


# --- SUGGESTED FUTURE IMPROVEMENTS & EXTENSIONS (MVP Roadmap) ---
#
# A.  **Improvements (Enhancing Current Rigor and Maintainability):**
#
#     1.  **More Granular Internal Parsing Error Reporting:**
#         * **Current Pitfall:** When a critical keyword is found but no pattern matches,
#             it reports a generic "Unhandled critical log entry."
#         * **Future Improvement:** Introduce specific `ParserError` subclasses or a
#             more detailed `ParsedError` structure (e.g., `ParsedError(type="PatternMissing", original_line=line)`)
#             to differentiate *why* the parser couldn't handle a critical log entry.
#             This provides even more precise feedback to developers on where a new pattern is needed.
#         * **Benefit:** Faster identification of which part of the log parsing logic requires updating.
#
#     2.  **Strict Typing for Pattern Definitions:**
#         * **Current State:** `ERROR_PATTERNS` and `GENERIC_CRITICAL_PATTERNS_DEFS` are lists of `Dict[str, Any]`.
#         * **Future Improvement:** Define a `Pydantic` `BaseModel` (e.g., `PatternDefinition`) for
#             each dictionary entry. This would enforce type checking on the pattern `id`, `regex`, `handler`,
#             `is_multiline_start`, and `priority` fields.
#         * **Benefit:** Compile-time validation of pattern definitions, reducing errors when adding or modifying rules.
#
#     3.  **Refined `_get_troubleshooting_tip_for_error` Logic:**
#         * **Current State:** The function uses a series of `if/elif` checks.
#         * **Future Improvement:** Refactor this into a dispatcher pattern similar to
#             `_process_single_log_line`, where a list of rules (e.g., `TipRule(condition_func, tip_key)`) is iterated.
#             Each `condition_func` would check properties of `ParsedError` to decide if a tip applies.
#         * **Benefit:** More declarative and extensible tip matching, easier to add new specific tips.
#
# B.  **Extensions (Building Towards a Useful MVP - Leveraging Current Architecture):**
#
#     1.  **YAML Configuration for Rules (Stubbed in Dev Environment):**
#         * **Goal:** Enable loading `ERROR_PATTERNS`, `GENERIC_CRITICAL_PATTERNS_DEFS`, `WARNING_PATTERNS`,
#             and `TROUBLESHOOTING_TIPS` from an external configuration source.
#         * **Current Status:** Due to limitations in the current development environment (no local file access),
#             the YAML loading mechanism (`_load_config_from_yaml`) remains a stub.
#         * **Future Implementation:** In environments with file access, `PyYAML` could be used to parse a `rules.yaml`
#             file, allowing developers to version control and dynamically update debugging rules.
#             This would involve merging default hardcoded patterns/tips with external configurations.
#         * **MVP Use Case:** When deployed in a suitable environment, allows developers to manage debugging
#             rules externally, supporting version control and dynamic updates without modifying core script logic.
#
# --- END SUGGESTED FUTURE IMPROVEMENTS & EXTENSIONS ---


# --- Pydantic Data Structures for Parsed Output ---
class ParsedMessage(BaseModel):
    """Base model for parsed log messages."""
    message: str = Field(..., description="A human-readable summary of the message.")
    source: str = Field(..., description="The source of the message (e.g., 'Pandoc', 'LaTeX', 'System').")
    line: Optional[int] = Field(None, description="The line number in the source file, if applicable.")
    column: Optional[int] = Field(None, description="The column number in the source file, if applicable.")
    context: Optional[str] = Field(None, description="Additional context or the original log line fragment.")
    id: Optional[str] = Field(None, description="Unique identifier for the parsed message type.") # Added ID field
    
    # Custom method to format the message for display
    def format(self) -> str:
        # Adjusted format to reflect the pipe's ASCII output
        formatted = f"{self.source} {'ERROR' if isinstance(self, ParsedError) else 'WARNING'}: {self.message}"
        if self.line is not None:
            formatted += f" (Line: {self.line}"
            if self.column is not None:
                formatted += f", Col: {self.column}"
            formatted += ")"
        if self.context:
            formatted += f" [Context: '{self.context}']"
        return formatted

class ParsedError(ParsedMessage):
    """Represents a parsed error message."""
    pass

class ParsedWarning(ParsedMessage):
    """Represents a parsed warning message."""
    pass


# --- Context Extraction Helper ---
def _extract_log_context(
    full_log_lines: List[str],
    error_parsed_message: ParsedMessage, # Can be ParsedError or ParsedWarning
    context_range: int = 2
) -> List[str]:
    """
    Extracts context lines around an error message from a full log (e.g., Pandoc's stderr or Markdown source).
    Attempts to highlight the specific error line.
    """
    context_lines: List[str] = []
    
    # Prioritize line number if available and within log bounds
    target_line_idx = None
    if error_parsed_message.line is not None and 1 <= error_parsed_message.line <= len(full_log_lines):
        target_line_idx = error_parsed_message.line - 1 # Convert to 0-based index
    else:
        # Fallback to finding the exact context string if line number is not directly usable
        # This is primarily for LaTeX error lines or unhandled errors where `context` is the raw line.
        try:
            # Find the first occurrence of the raw context string in the log
            for i, line in enumerate(full_log_lines):
                if error_parsed_message.context and error_parsed_message.context.strip() in line.strip():
                    target_line_idx = i
                    break
        except ValueError:
            target_line_idx = None # Not found as a direct substring

    if target_line_idx is None:
        # If no specific line can be found, just return the error's direct context if available
        return [f"   No direct context found in log. Original context: '{error_parsed_message.context}'"] if error_parsed_message.context else []


    start_idx = max(0, target_line_idx - context_range)
    end_idx = min(len(full_log_lines) - 1, target_line_idx + context_range)

    for i in range(start_idx, end_idx + 1):
        line_content = full_log_lines[i]
        prefix = f"{i + 1: >4} | " # 1-based line number, right-aligned
        
        if i == target_line_idx:
            # Mark the error line
            context_lines.append(f"{prefix}{line_content.rstrip()} ((ERROR LINE))")
        else:
            context_lines.append(f"{prefix}{line_content.rstrip()}")
            
    return context_lines


# --- Pattern Handler Functions ---
# These functions take a regex match object and the current line number,
# and return a ParsedMessage (or None if no message should be generated, though
# for matched patterns, we usually expect a message).
# They also return a set of line indices consumed by this handler, useful for multi-line patterns.

def handle_pandoc_location_error(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    IMPLEMENTED. Handles Pandoc errors with file:line:col information.
    Catches precise Markdown syntax errors, YAML header issues reported with location.
    """
    file_name = match.group(1).strip()
    line_num = int(match.group(2))
    col_num = int(match.group(3)) if match.group(3) else None
    error_msg = match.group(4).strip()
    
    return ParsedError(
        id='pandoc_loc_error', # Set ID for specific matching
        message=f"{error_msg} ({file_name})",
        source="Pandoc",
        line=line_num,
        column=col_num,
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_latex_error_start(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    IMPLEMENTED. Handles the start of a LaTeX error, looking for a subsequent line number
    or missing file information using a more functional approach.
    Catches general LaTeX compilation errors, including cascading ones where the root
    might be indicated by 'l.X'. Also covers basic missing file/package issues.
    """
    main_error_msg = match.group(1).strip()
    consumed_indices = [line_idx]

    # Create a stream of potential subsequent context lines
    context_lines_stream = (
        (j, lines[j].strip())
        for j in range(line_idx + 1, min(line_idx + 5, len(lines)))
    )

    # Use next(filter(...)) to find the first relevant context line
    found_context = next(
        filter(
            lambda item: re.match(r'l\.\s*(\d+)\s*(.*)', item[1]) or 
                         (("not found" in item[1].lower() or "missing" in item[1].lower()) and "file" in item[1].lower()),
            context_lines_stream
        ),
        None
    )

    if found_context:
        j, next_line_stripped = found_context
        latex_line_match = re.match(r'l\.\s*(\d+)\s*(.*)', next_line_stripped)
        
        consumed_indices.append(j) # Always consume the found context line
        
        if latex_line_match:
            line_num = int(latex_line_match.group(1))
            context_detail = latex_line_match.group(2).strip()
            return ParsedError(
                id='latex_error_start', # Set ID
                message=f"{main_error_msg}",
                source="LaTeX",
                line=line_num,
                context=context_detail
            ), consumed_indices
        else: # Must be a "not found" or "missing file" context
            return ParsedError(
                id='latex_error_start_missing_file', # Specific ID for this case
                message=f"{main_error_msg} (Potential missing file/package)",
                source="LaTeX",
                context=next_line_stripped
            ), consumed_indices
            
    # If no specific line detail or file context found after looking ahead, just return the main error
    return ParsedError(
        id='latex_error_start_generic', # Specific ID for generic case
        message=main_error_msg,
        source="LaTeX",
        context=lines[line_idx].strip()
    ), [line_idx]


def handle_latex_undefined_control_sequence(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    IMPLEMENTED. Handles 'Undefined control sequence' LaTeX errors.
    Catches misspelled macros or missing packages.
    """
    return ParsedError(
        id='latex_undefined_control_sequence', # Set ID
        message="Undefined control sequence. Check for typos in commands or missing packages.",
        source="LaTeX",
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_latex_package_error(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    IMPLEMENTED. Handles generic LaTeX package errors.
    Catches issues reported by LaTeX packages, often due to incorrect usage.
    """
    package = match.group(1)
    msg = match.group(2)
    line_num = int(match.group(3)) if match.group(3) else None
    return ParsedError(
        id='latex_package_error', # Set ID
        message=f"In package '{package}': {msg}",
        source="LaTeX",
        line=line_num,
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_latex_missing_delimiter(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    IMPLEMENTED. Handles missing or extra delimiter LaTeX errors.
    Catches common issues with unclosed braces, brackets, or other LaTeX delimiters.
    """
    return ParsedError(
        id='latex_missing_delimiter', # Set ID
        message="Missing or extra delimiter/environment component. Check brackets, braces, or `\\begin`/`\\end` pairs.",
        source="LaTeX",
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_latex_environment_mismatch(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    IMPLEMENTED. Handles LaTeX environment mismatch errors.
    Catches issues where a `\begin` environment is ended by a different `\end`.
    """
    return ParsedError(
        id='latex_environment_mismatch', # Set ID
        message=f"Environment Mismatch: {match.group(1).strip()}. Ensure all `\\begin` have matching `\\end`.",
        source="LaTeX",
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_pandoc_general_error(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    IMPLEMENTED. Handles general Pandoc errors without specific line info.
    Catches errors like unrecognized commands or options that Pandoc reports generally.
    """
    return ParsedError(
        id='pandoc_general_error', # Set ID
        message=match.group(1).strip(),
        source="Pandoc",
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_unicode_error_stub(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    STUB. Handles Unicode character problems (e.g., invalid UTF-8, unsupported characters).
    Needs more precise regex and parsing if distinct from generic errors.
    """
    return ParsedError(
        id='unicode_error', # Set ID
        message=f"Unicode Character Issue: {match.group(1).strip()}",
        source="System/Encoding (Stub)",
        line=line_idx + 1,
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_filter_error_stub(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    STUB. Handles custom Pandoc filter (e.g., Lua filters) errors.
    Errors from filters can vary widely; this is a generic placeholder.
    """
    return ParsedError(
        id='filter_error', # Set ID
        message=f"Custom Filter Error: {match.group(1).strip()}",
        source="Pandoc Filter (Stub)",
        line=line_idx + 1,
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_template_error_stub(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    STUB. Handles Pandoc template or variable substitution errors.
    Placeholder for more specific template engine error messages.
    """
    return ParsedError(
        id='template_error', # Set ID
        message=f"Template/Variable Error: {match.group(1).strip()}",
        source="Pandoc Template (Stub)",
        line=line_idx + 1,
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_unreadable_resource_error_stub(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    STUB. Handles issues where external resources (images, files) are found but unreadable/corrupted.
    Distinction from 'file not found' is key here.
    """
    return ParsedError(
        id='unreadable_resource_error', # Set ID
        message=f"Unreadable External Resource: {match.group(1).strip()}",
        source="System/IO (Stub)",
        line=line_idx + 1,
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_yaml_metadata_issue_stub(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    STUB. Handles subtle YAML metadata parsing issues that might not have line:col.
    Catches less obvious YAML formatting problems.
    """
    return ParsedError(
        id='yaml_metadata_issue', # Set ID
        message=f"YAML Metadata Issue: {match.group(1).strip()}",
        source="Pandoc YAML (Stub)",
        line=line_idx + 1,
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_pandoc_warning_generic(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedWarning], List[int]]:
    """
    IMPLEMENTED. Handles generic Pandoc warnings reported to stderr.
    This is used when Pandoc exits with code 0 but still has actionable messages.
    """
    return ParsedWarning(
        id='pandoc_generic_warning', # Set ID
        message=match.group(1).strip(),
        source="Pandoc",
        line=line_idx + 1,
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_pandoc_yaml_warning_specific(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedWarning], List[int]]:
    """
    IMPLEMENTED. Handles specific Pandoc YAML metadata warnings with line/column info.
    """
    line_num = int(match.group(1))
    col_num = int(match.group(2))
    warning_msg = match.group(3).strip()
    return ParsedWarning(
        id='pandoc_yaml_warning', # Specific ID for YAML warning
        message=f"YAML metadata parsing warning: {warning_msg}",
        source="Pandoc",
        line=line_num,
        column=col_num,
        context=lines[line_idx].strip()
    ), [line_idx]

def handle_ambiguous_markdown_syntax(match: re.Match, line_idx: int, lines: List[str]) -> Tuple[Optional[ParsedError], List[int]]:
    """
    IMPLEMENTED. Handles ambiguous Markdown syntax issues.
    Sets a specific ID for these types of errors.
    """
    return ParsedError(
        id='ambiguous_markdown_syntax',
        message=f"Ambiguous Markdown Syntax: {match.group(1).strip()}",
        source="Pandoc",
        line=line_idx + 1,
        context=lines[line_idx].strip()
    ), [line_idx]


# --- Generic Critical Info Patterns and Handlers (Dispatcher for these) ---
# Each entry maps keywords (case-insensitive) to a function that returns a ParsedError.
GENERIC_CRITICAL_PATTERNS_DEFS: Dict[Tuple[str, ...], Callable[[str, int], Tuple[Optional[ParsedError], List[int]]]] = {
    ("fatal error", "failed to parse", "aborting"): 
        lambda line, idx: (ParsedError(id='system_fatal_error', message=f"System/Process Error: {line}", source="System", context=line), [idx]),
    ("missing file", "not found", "cannot open"):
        lambda line, idx: (ParsedError(id='system_missing_file', message=f"Missing Resource/File Error: {line}", source="System", context=line), [idx]),
    ("unknown option", "unrecognized"):
        lambda line, idx: (ParsedError(id='system_config_error', message=f"Configuration/Option Error: {line}", source="System", context=line), [idx]),
    ("segmentation fault", "stack overflow"):
        lambda line, idx: (ParsedError(id='system_runtime_crash', message=f"Runtime/Crash Error: {line}", source="System", context=line), [idx]),
}

def handle_generic_critical_info(line: str, line_idx: int) -> Tuple[Optional[ParsedError], List[int]]:
    """
    Dispatches to specific ParsedError handlers based on critical keywords in the line.
    """
    lower_line = line.lower()
    for keywords, handler_func in GENERIC_CRITICAL_PATTERNS_DEFS.items():
        if any(keyword in lower_line for keyword in keywords):
            return handler_func(line, line_idx)
    return None, []


# --- Externalized Error Pattern Definitions (Currently Hardcoded Defaults) ---
# These are the default patterns. In future, they can be extended/overridden via YAML.
_DEFAULT_ERROR_PATTERNS: List[Dict[str, Any]] = [
    {
        'id': 'pandoc_loc_error',
        'regex': re.compile(r'(?:pandoc:)?\s*(.*?):(\d+)(?::(\d+))?:\s*(Error:.*)'),
        'handler': handle_pandoc_location_error,
        'is_multiline_start': False,
        'priority': 100
    },
    {
        'id': 'latex_error_start',
        'regex': re.compile(r'!(?: LaTeX)? Error:\s*(.*)'),
        'handler': handle_latex_error_start,
        'is_multiline_start': True,
        'priority': 90
    },
    {
        'id': 'latex_environment_mismatch',
        'regex': re.compile(r'LaTeX Error: \s*(\\begin\{(\w+)\} ended by \\end\{(\w+)\}\.)'),
        'handler': handle_latex_environment_mismatch,
        'is_multiline_start': False,
        'priority': 85
    },
    {
        'id': 'latex_missing_delimiter',
        'regex': re.compile(r'Missing (?:delimiter|\\item|brace|endcsname|\$|\&|#|{|}|=|,|\.|\}|\]|\)|\);|\{|\]|\)|\*|\+|\?|\.) inserted\.|Extra (?:delimiter|\\item|brace|\$|\&|#|{|}|=|,|\.|\}|\]|\)|\);|\{|\]|\)|\*|\+|\?|\.)\.'),
        'handler': handle_latex_missing_delimiter,
        'is_multiline_start': False,
        'priority': 80
    },
    {
        'id': 'latex_package_error',
        'regex': re.compile(r'Package (\w+) Error: (.+?)(?: on input line (\d+)\.)?'),
        'handler': handle_latex_package_error,
        'is_multiline_start': False,
        'priority': 75
    },
    {
        'id': 'latex_undefined_control_sequence',
        'regex': re.compile(r'Undefined control sequence\.'),
        'handler': handle_latex_undefined_control_sequence,
        'is_multiline_start': False,
        'priority': 70
    },
    {
        'id': 'pandoc_general_error',
        'regex': re.compile(r'(?:pandoc:)?\s*(Error:.*)'),
        'handler': handle_pandoc_general_error,
        'is_multiline_start': False,
        'priority': 50
    },
    # --- New/Stubbed Error Catches for Comprehensive Coverage ---
    # These patterns are introduced to specifically address common issues identified in the critical analysis.
    # Some are implemented with basic regex, others are stubs for more complex future parsing.
    {
        'id': 'unicode_error',
        'regex': re.compile(r'(?:invalid UTF-8|unsupported character|UnicodeError|illegal byte sequence):?\s*(.*)'),
        'handler': handle_unicode_error_stub, # Currently a stub handler
        'is_multiline_start': False,
        'priority': 45 # Lower priority, as it might overlap with generic errors
    },
    {
        'id': 'filter_error',
        'regex': re.compile(r'(?:Error running filter|Filter returned non-zero exit code|Failed to run Lua filter|lua error|filter terminated|Could not find filter):?\s*(.*)'),
        'handler': handle_filter_error_stub, # Currently a stub handler
        'is_multiline_start': False,
        'priority': 40
    },
    {
        'id': 'template_error',
        'regex': re.compile(r'(?:template error|variable not found|malformed template|template parsing failed|Could not find template|Error in template):?\s*(.*)'),
        'handler': handle_template_error_stub, # Currently a stub handler
        'is_multiline_start': False,
        'priority': 35
    },
    {
        'id': 'unreadable_resource_error',
        'regex': re.compile(r'(?:could not read image|unreadable file|corrupted file|not a supported format|failed to load resource|Could not find image|Could not load image):?\s*(.*)'),
        'handler': handle_unreadable_resource_error_stub, # Currently a stub handler
        'is_multiline_start': False,
        'priority': 30
    },
    {
        'id': 'yaml_metadata_issue',
        'regex': re.compile(r'(?:YAML parse error|invalid YAML|problem with YAML metadata|bad yaml|Could not parse YAML metadata):?\s*(.*)'),
        'handler': handle_yaml_metadata_issue_stub, # Currently a stub handler
        'is_multiline_start': False,
        'priority': 25
    },
    {
        'id': 'ambiguous_markdown_syntax', # Catching common phrases for this type of error
        'regex': re.compile(r'(?:Could not parse table|markdown parsing failed|malformed table|invalid heading|list indentation error|syntax error near|Failed to parse markdown):?\s*(.*)'), # Added 'Could not parse table'
        'handler': handle_ambiguous_markdown_syntax, # Now uses its own handler
        'is_multiline_start': False,
        'priority': 51 # Just above general Pandoc error, to be more specific
    },
    # Specific error for unclosed string literal in code block (Test Case 1)
    {
        'id': 'unclosed_code_string',
        'regex': re.compile(r'Could not parse code block: unterminated string literal(?: in haskell template)?|Could not parse code block: unterminated string'), # Expanded regex
        'handler': lambda match, idx, lines: (ParsedError(id='unclosed_code_string', message="Unclosed string literal in code block.", source="Pandoc", line=idx + 1, context=lines[idx].strip()), [idx]),
        'is_multiline_start': False,
        'priority': 105 # High priority for very specific syntax errors
    },
]

# Sort patterns by priority (descending) so more specific patterns are checked first
_SORTED_DEFAULT_ERROR_PATTERNS = sorted(_DEFAULT_ERROR_PATTERNS, key=lambda p: p['priority'], reverse=True)

# --- Externalized Warning Pattern Definitions ---
_DEFAULT_WARNING_PATTERNS: List[Dict[str, Any]] = [
    {
        'id': 'pandoc_yaml_warning',
        'regex': re.compile(r'\[WARNING\] Could not parse YAML metadata at line (\d+) column (\d+): (.*)'),
        'handler': handle_pandoc_yaml_warning_specific,
        'is_multiline_start': False,
        'priority': 95 # High priority to catch specific warnings
    },
    {
        'id': 'pandoc_generic_warning',
        'regex': re.compile(r'\[WARNING\] (.*)'),
        'handler': handle_pandoc_warning_generic,
        'is_multiline_start': False,
        'priority': 50 # General warning, lower priority than specific ones
    },
    # Add other specific Pandoc/LaTeX warning patterns here as needed
]
_SORTED_DEFAULT_WARNING_PATTERNS = sorted(_DEFAULT_WARNING_PATTERNS, key=lambda p: p['priority'], reverse=True)


# --- Troubleshooting Tip Definitions (Currently Hardcoded Defaults) ---
# These are the default tips. In future, they can be extended/overridden via YAML.
TROUBLESHOOTING_TIPS: Dict[Tuple[str, str], str] = {
    ("Pandoc", "line_specific"): "Investigate Markdown syntax around this line.",
    ("LaTeX", "Undefined control sequence"): "Check for typos in LaTeX commands or missing package imports.",
    ("LaTeX", "Missing delimiter/Environment Mismatch"): "Ensure all `\\begin` environments have matching `\\end` and all braces/brackets are properly closed.",
    ("System", "Missing Resource/File Error"): "Verify paths to external files (images, custom CSS/LaTeX) are correct and files exist.",
    ("Uncategorized", "general"): "If 'Uncategorized Pandoc/LaTeX output detected' appears, you'll need to manually inspect the 'Full Standard Error Output' for unique patterns.",
    ("LaTeX", "pdf_compilation_note"): "PDF compilation requires a full LaTeX distribution (TeX Live, MiKTeX) to be installed and accessible.",
    # --- New Tips for Stubbed/Implemented Errors ---
    ("System/Encoding (Stub)", "Unicode Character Issue"): "Check for unsupported Unicode characters or invalid encoding in your Markdown or included files.",
    ("Pandoc Filter (Stub)", "Custom Filter Error"): "Review the code of your custom Pandoc filter for errors or unexpected behavior.",
    ("Pandoc Template (Stub)", "Template/Variable Error"): "Examine your custom Pandoc template for incorrect variable references or malformed template syntax.",
    ("System/IO (Stub)", "Unreadable External Resource"): "Ensure external files (images, data) are valid, uncorrupted, and in a format supported by Pandoc.",
    ("Pandoc YAML (Stub)", "YAML Metadata Issue"): "Check your YAML front matter for correct syntax, indentation, and valid data types.",
    ("Pandoc", "ambiguous_markdown_syntax"): "Review the general Markdown syntax, especially tables, lists, or heading structures, around the suggested area.",
    ("Pandoc", "unclosed_code_string"): "Ensure all strings within fenced code blocks are properly closed with matching quotes.",
    ("Pandoc", "pandoc_yaml_warning"): "Check your YAML metadata carefully at the specified line and column for syntax errors.", # Tip for the new YAML warning
    ("Pandoc", "pandoc_generic_warning"): "Review this general Pandoc warning; it might indicate a minor syntax issue or deprecated feature.",
}


# --- YAML Loading Stub (for future extension) ---
def _load_config_from_yaml(filepath: str) -> Dict[str, Any]:
    """
    Stub function to load configuration (patterns, tips) from a YAML file.
    For now, it returns an empty dictionary.
    In the future, this would integrate with a YAML parsing library.
    """
    # import yaml
    # try:
    #     with open(filepath, 'r') as f:
    #         return yaml.safe_load(f)
    # except FileNotFoundError:
    #     print(f"Warning: YAML config file '{filepath}' not found. Using default rules.", file=sys.stderr)
    #     return {}
    # except yaml.YAMLError as e:
    #     print(f"Error parsing YAML config file '{filepath}': {e}. Using default rules.", file=sys.stderr)
    #     return {}
    
    # Current stub behavior (due to environment constraints):
    # print(f"Warning: YAML loading is a stub in this environment. Using hardcoded defaults.", file=sys.stderr)
    return {} # For now, return empty dict; actual loading logic to be implemented later


def _get_current_error_patterns() -> List[Dict[str, Any]]:
    """Returns the current error patterns, potentially loaded/merged from YAML."""
    # This function would be extended in the future to merge with YAML configuration.
    current_patterns = list(_SORTED_DEFAULT_ERROR_PATTERNS)
    # If YAML loading were active:
    # yaml_config = _load_config_from_yaml("rules.yaml")
    # if "error_patterns" in yaml_config:
    #     # Add logic to parse and merge YAML-defined patterns, ensuring they have required fields
    #     # and potentially overriding defaults by ID or priority.
    #     pass
    return current_patterns # Already sorted

def _get_current_warning_patterns() -> List[Dict[str, Any]]:
    """Returns the current warning patterns, potentially loaded/merged from YAML."""
    current_patterns = list(_SORTED_DEFAULT_WARNING_PATTERNS)
    return current_patterns


def _get_current_generic_critical_patterns() -> Dict[Tuple[str, ...], Callable[[str, int], Tuple[Optional[ParsedError], List[int]]]]:
    """Returns the current generic critical patterns, potentially loaded/merged from YAML."""
    # This function would be extended in the future to merge with YAML configuration.
    return GENERIC_CRITICAL_PATTERNS_DEFS # For now, return the default directly


def _get_current_troubleshooting_tips() -> Dict[Tuple[str, str], str]:
    """Returns the current troubleshooting tips, potentially loaded/merged from YAML."""
    # This function would be extended in the future to merge with YAML configuration.
    # current_tips = dict(TROUBLESHOOTING_TIPS)
    # If YAML loading were active:
    # yaml_config = _load_config_from_yaml("rules.yaml")
    # if "troubleshooting_tips" in yaml_config:
    #     # Add logic to parse and merge YAML-defined tips.
    #     pass
    return TROUBLESHOOTING_TIPS # For now, return the default directly


def _apply_patterns_to_line(
    line_stripped: str,
    line_idx: int,
    lines: List[str],
    pattern_defs: List[Dict[str, Any]]
) -> Tuple[Optional[ParsedMessage], List[int]]:
    """
    Attempts to apply a list of pattern definitions to a single line.
    Returns the first matched ParsedMessage and the indices of lines consumed.
    """
    for pattern_def in pattern_defs:
        match = pattern_def['regex'].match(line_stripped)
        if match:
            # Call the specific handler for this pattern
            parsed_msg, consumed_indices = pattern_def['handler'](match, line_idx, lines)
            return parsed_msg, consumed_indices
    return None, []


def _process_single_log_line(
    line_idx: int,
    line_stripped: str,
    lines: List[str],
) -> Tuple[Optional[ParsedMessage], List[int]]: # Can return ParsedError or ParsedWarning now
    """
    Acts as a dispatcher to process a single log line using defined patterns.
    It attempts to match against error patterns, then warning patterns,
    and finally a generic critical info handler.
    It now *reports* unhandled critical patterns as specific ParsedErrors.

    Args:
        line_idx (int): The current line's index in the full log.
        line_stripped (str): The current log line, stripped of whitespace.
        lines (List[str]): The complete list of log lines.

    Returns:
        Tuple[Optional[ParsedMessage], List[int]]: A tuple containing the parsed message
        (if any) and a list of line indices consumed by its handler.
    """
    # Attempt to match against error patterns
    parsed_msg, consumed_indices = _apply_patterns_to_line(line_stripped, line_idx, lines, _get_current_error_patterns())
    if parsed_msg:
        # Assert that an error handler returns an error type, maintaining type rigor.
        assert isinstance(parsed_msg, ParsedError), f"Internal Error: Handler for error pattern '{line_stripped}' returned non-ParsedError type."
        return parsed_msg, consumed_indices

    # If not an error, attempt to match against warning patterns (newly re-enabled)
    parsed_msg_warning, consumed_indices_warning = _apply_patterns_to_line(line_stripped, line_idx, lines, _get_current_warning_patterns())
    if parsed_msg_warning:
        assert isinstance(parsed_msg_warning, ParsedWarning), f"Internal Error: Handler for warning pattern '{line_stripped}' returned non-ParsedWarning type."
        return parsed_msg_warning, consumed_indices_warning

    # If no specific pattern matched, try generic critical info handler
    # This acts as a final internal check for important but unpatterned messages.
    generic_msg, generic_consumed_indices = handle_generic_critical_info(line_stripped, line_idx)
    if generic_msg:
        return generic_msg, generic_consumed_indices

    # If still not processed and contains critical keywords,
    # create a ParsedError to *report* this unhandled pattern.
    lower_line = line_stripped.lower()
    if any(keyword in lower_line for keyword in ["error", "fatal", "failed to", "aborting", "segmentation fault"]):
        # This is the "softened" crash. It reports the internal parsing gap as an error.
        return ParsedError(
            id='unhandled_critical_log_entry', # Specific ID for internal parsing errors
            message=f"Unhandled critical log entry: '{line_stripped}'. Developer attention needed.",
            source="ParserInternal", # New source to distinguish internal parser issues
            line=line_idx + 1, # Line numbers are 1-based for users
            context=line_stripped
        ), [line_idx]
    
    return None, [] # No message and no lines consumed by any pattern

def _create_unprocessed_line_stream(
    lines: List[str],
    processed_line_indices: set[int]
) -> Generator[Tuple[int, str], None, None]:
    """
    A generator that yields (index, stripped_line) for lines not yet processed.
    This helps to flatten the main parsing loop by providing a clean stream.
    """
    return (
        (i, line.strip()) 
        for i, line in enumerate(lines) 
        if i not in processed_line_indices
    )


def parse_pandoc_messages(stderr_output: str) -> Tuple[List[ParsedError], List[ParsedWarning]]:
    """
    Parses Pandoc's stderr output to extract human-readable error messages and warnings.

    This function embraces the "crash if our code is wrong" philosophy: it will
    now *report* internal parsing gaps as errors rather than crashing directly.

    Args:
        stderr_output (str): The standard error output as a string from the Pandoc process.

    Returns:
        Tuple[List[ParsedError], List[ParsedWarning]]: Lists of parsed errors and warnings.
    """
    errors: List[ParsedError] = []
    warnings: List[ParsedWarning] = [] # Re-enabled warnings
    lines = stderr_output.strip().split('\n')
    
    # Set to keep track of line indices already processed by a pattern handler
    processed_line_indices: set[int] = set()

    # Process all lines using a more functional approach where possible
    for i, line_stripped in _create_unprocessed_line_stream(lines, processed_line_indices):
        parsed_message, consumed_indices = _process_single_log_line(
            i, line_stripped, lines
        )
        if parsed_message:
            processed_line_indices.update(consumed_indices)
            if isinstance(parsed_message, ParsedError):
                errors.append(parsed_message)
            elif isinstance(parsed_message, ParsedWarning):
                warnings.append(parsed_message)

    # Final fallback for any remaining *unprocessed* lines if no specific messages were captured
    # by the patterns, but the overall stderr output isn't empty.
    if not errors and not warnings and stderr_output.strip():
        remaining_lines = [lines[j] for j in range(len(lines)) if j not in processed_line_indices]
        if remaining_lines:
            errors.append(ParsedError(
                id='uncategorized_output', # Specific ID for uncategorized
                message="Uncategorized Pandoc/LaTeX output detected. Please review full stderr for details.",
                source="Parser",
                context=" | ".join(remaining_lines[:3]) + ("..." if len(remaining_lines) > 3 else "")
            ))

    return errors, warnings


def _get_troubleshooting_tip_for_message(msg: ParsedMessage) -> Optional[str]:
    """
    Generates a specific troubleshooting tip for a ParsedMessage (Error or Warning)
    based on a predefined dictionary and a dispatcher-like matching rule set.
    Prioritizes specific matches over general ones.
    """
    current_tips = _get_current_troubleshooting_tips()

    # Define rules for matching messages to tips. Order matters (most specific first).
    _TIP_MATCHING_RULES = [
        # Errors
        (lambda m: m.source == "Pandoc" and m.id == "pandoc_loc_error", ("Pandoc", "line_specific")),
        (lambda m: m.source == "Pandoc" and m.id == "ambiguous_markdown_syntax", ("Pandoc", "ambiguous_markdown_syntax")),
        (lambda m: m.source == "Pandoc" and m.id == "unclosed_code_string", ("Pandoc", "unclosed_code_string")),
        (lambda m: m.source == "LaTeX" and m.id == "latex_undefined_control_sequence", ("LaTeX", "Undefined control sequence")),
        (lambda m: m.source == "LaTeX" and (m.id == "latex_missing_delimiter" or m.id == "latex_environment_mismatch"), ("LaTeX", "Missing delimiter/Environment Mismatch")),
        (lambda m: m.source == "System" and m.id == "system_missing_file", ("System", "Missing Resource/File Error")),
        (lambda m: m.source == "System/Encoding (Stub)" and m.id == "unicode_error", ("System/Encoding (Stub)", "Unicode Character Issue")),
        (lambda m: m.source == "System/IO (Stub)" and m.id == "unreadable_resource_error", ("System/IO (Stub)", "Unreadable External Resource")),
        (lambda m: m.source == "Pandoc Filter (Stub)" and m.id == "filter_error", ("Pandoc Filter (Stub)", "Custom Filter Error")),
        (lambda m: m.source == "Pandoc Template (Stub)" and m.id == "template_error", ("Pandoc Template (Stub)", "Template/Variable Error")),
        (lambda m: m.source == "Pandoc YAML (Stub)" and m.id == "yaml_metadata_issue", ("Pandoc YAML (Stub)", "YAML Metadata Issue")),
        (lambda m: m.source == "ParserInternal" and m.id == "unhandled_critical_log_entry", ("Parser (Internal Error)", "Unhandled critical log entry")),
        (lambda m: m.source == "Parser" and m.id == "uncategorized_output", ("Uncategorized", "general")),

        # Warnings (specific Pandoc warnings have dedicated tips)
        (lambda m: m.source == "Pandoc" and m.id == "pandoc_yaml_warning", ("Pandoc", "pandoc_yaml_warning")),
        (lambda m: m.source == "Pandoc" and m.id == "pandoc_generic_warning", ("Pandoc", "pandoc_generic_warning")),

        # Fallback generic error/warning tips (should be last)
        (lambda m: isinstance(m, ParsedError) and m.source == "Pandoc", ("Pandoc", "general_error")),
        (lambda m: isinstance(m, ParsedError) and m.source == "LaTeX", ("LaTeX", "general_error")),
        (lambda m: isinstance(m, ParsedError) and m.source == "System", ("System", "general_error")),
        (lambda m: isinstance(m, ParsedWarning) and m.source == "Pandoc", ("Pandoc", "general_warning")), # Generic Pandoc warning tip
    ]

    for condition, tip_key in _TIP_MATCHING_RULES:
        if condition(msg):
            return current_tips.get(tip_key)
    
    return None # No specific tip found for this message type

def _handle_compilation_output(result: subprocess.CompletedProcess, output_format: str, markdown_content_lines: List[str]):
    """
    Handles Pandoc's compilation result, parsing and presenting errors and warnings/tips.
    Prints the report to stdout.
    """
    errors_list, warnings_list = parse_pandoc_messages(result.stderr) # Now gets errors AND warnings
    
    # Determine if it's a "failure" (non-zero exit code) or "success with warnings" (exit code 0 but stderr present)
    is_failure = (result.returncode != 0)
    
    # If PDF output, and success, suppress all stderr.
    if output_format == 'pdf' and result.returncode == 0:
        print(f"\n===== Status Report =====", file=sys.stdout)
        print(f"~~~ No problems found (PDF compiled successfully) ~~~", file=sys.stdout)
        print("=========================", file=sys.stdout)
        return # Exit early, suppressing further output for successful PDF builds.

    if is_failure or errors_list or warnings_list: # Report if any errors OR any warnings detected
        # Report Header
        report_type = "Failure" if is_failure else "Success with Warnings/Info"
        print(f"\n--- Pandoc Compilation Report ({report_type}, Exit Code: {result.returncode}) ---", file=sys.stdout)

        if errors_list:
            # Loop through each problem (parsed error) and print its structured report
            for i, error_msg in enumerate(errors_list):
                print(f"\n===== Problem {i+1} =====", file=sys.stdout)
                print(f"Problem: \"{error_msg.message}\"", file=sys.stdout)
                
                # LaTeX Context (from Pandoc's stderr)
                print("\nLaTeX Context:", file=sys.stdout)
                latex_context = _extract_log_context(result.stderr.splitlines(), error_msg)
                if latex_context:
                    for line in latex_context:
                        print(line, file=sys.stdout)
                else:
                    print("   No specific LaTeX context available for this message.", file=sys.stdout)

                # Markdown Context (from original stdin content)
                print("\nMarkdown Context:", file=sys.stdout)
                markdown_context = _extract_log_context(markdown_content_lines, error_msg)
                if markdown_context:
                    for line in markdown_context:
                        print(line, file=sys.stdout)
                else:
                    print("   No specific Markdown context available for this message.", file=sys.stdout)

                # Solution Tip
                solution_tip = _get_troubleshooting_tip_for_message(error_msg)
                if solution_tip:
                    print(f"\nSolution: {solution_tip}", file=sys.stdout)
                else:
                    print("\nSolution: No specific automated solution found. Review detailed summary and logs.", file=sys.stdout)
                print("=====", file=sys.stdout) # End of problem section
        else:
            # This branch means Pandoc had non-empty stderr (warnings/info) but our parser didn't categorize them as errors.
            print("\nNo specific ERRORs parsed by the debugger. Check the 'Warnings' and 'Full Standard Error Output' sections below.", file=sys.stdout)

        if warnings_list: # Report warnings if present
            print("\n--- Warnings/Informational Messages ---", file=sys.stdout)
            for warning_msg in warnings_list:
                print(f"- {warning_msg.format()}", file=sys.stdout)
                warning_tip = _get_troubleshooting_tip_for_message(warning_msg)
                if warning_tip:
                    print(f"  Tip: {warning_tip}", file=sys.stdout)
            print("---------------------------------------", file=sys.stdout)

    else: # This block is executed if `errors_list` is empty and `warnings_list` is empty
          # This should only be reached if returncode is 0 and stderr is truly empty.
        print(f"\n===== Status Report =====", file=sys.stdout)
        print(f"~~~ No problems found ~~~", file=sys.stdout)
        print("=========================", file=sys.stdout)


    # Always include full logs for comprehensive debugging
    if result.stdout.strip():
        print("\n--- Pandoc Standard Output (Document Content) ---", file=sys.stdout)
        print(result.stdout, file=sys.stdout)

    print("\n--- Full Pandoc Standard Error Output (for advanced debugging) ---", file=sys.stdout)
    full_stderr_lines = result.stderr.strip().split('\n')
    if len(full_stderr_lines) > 50:
        print(f"(Note: Full log is very verbose, {len(full_stderr_lines)} lines total)", file=sys.stdout)
    print(result.stderr if result.stderr.strip() else "No detailed stderr output.", file=sys.stdout)
    print("------------------------------------------------------------------", file=sys.stdout)
    
    # General final tips
    print("\n--- General Troubleshooting Guidance ---", file=sys.stdout)
    print("1. Always prioritize fixes suggested in 'Detailed Error Summary' and specific 'Solutions'.", file=sys.stdout)
    
    # Only print "Uncategorized" tip if there was an uncategorized error or warning reported.
    uncategorized_tip = _get_current_troubleshooting_tips().get(("Uncategorized", "general"))
    if uncategorized_tip and any(m.source == "Parser" and m.id == "uncategorized_output" for m in errors_list + warnings_list):
        print(f"2. {uncategorized_tip}", file=sys.stdout)
    else:
         print("2. If specific solutions don't apply or aren't enough, manually inspect the 'Full Standard Error Output' for unique patterns.", file=sys.stdout)
    
    if output_format == 'pdf':
         print(f"3. {_get_current_troubleshooting_tips().get(('LaTeX', 'pdf_compilation_note'))}", file=sys.stdout)
    
    print("\n--- End of Report ---", file=sys.stdout)


def run_pandoc_analysis_pipe(markdown_content: str, output_format: str = 'markdown'):
    """
    Runs Pandoc with the given Markdown content from stdin, captures its output,
    and then generates a debug report to stdout. This function is designed to
    operate as part of a Unix pipe.

    Args:
        markdown_content (str): The Markdown content read from stdin.
        output_format (str): The desired output format for Pandoc (e.g., 'html', 'pdf').
                             Defaults to 'markdown'.
    """
    # Assertions for internal correctness
    assert isinstance(markdown_content, str), "Internal Error: Markdown content must be a string."
    assert isinstance(output_format, str) and output_format, \
        "Internal Error: output_format must be a non-empty string."

    # Construct the Pandoc command.
    # We explicitly tell Pandoc to read from stdin ('-'), and then specify input/output formats.
    # The primary document output of Pandoc will go to stdout, which we capture.
    command = ['pandoc', '-f', 'markdown', '-t', output_format]

    # Execute the Pandoc command.
    # The 'input' argument pipes markdown_content to Pandoc's stdin.
    result = subprocess.run(
        command,             # The command and its arguments
        input=markdown_content, # Pass markdown content to Pandoc's stdin
        capture_output=True, # Capture Pandoc's stdout and stderr
        text=True,           # Decode stdout/stderr as text using default encoding
        check=False,         # IMPORTANT: Do NOT raise CalledProcessError for non-zero exit codes.
                             # We want to capture Pandoc's stderr for analysis even if it fails.
        encoding='ascii',    # Explicitly specify ASCII encoding for output streams
        errors='replace'     # Replace any characters that cannot be decoded with '?' or similar
    )

    # Convert markdown_content to lines *once* for potential context extraction.
    markdown_content_lines = markdown_content.splitlines()

    # Check Pandoc's exit code and stderr to decide on report type.
    _handle_compilation_output(result, output_format, markdown_content_lines)


if __name__ == "__main__":
    # Read all Markdown content from stdin.
    markdown_input_content = sys.stdin.read()

    # Determine the output format from command-line arguments.
    # The first argument (sys.argv[0]) is the script name.
    # We expect an optional second argument for output format.
    output_format_arg = 'markdown' # Default output format if not specified
    if len(sys.argv) > 1:
        # Only take the first argument as output format, ignore others for simplicity
        # as this is a pipe.
        output_format_arg = sys.argv[1] 

    # Run the Pandoc analysis function.
    run_pandoc_analysis_pipe(markdown_input_content, output_format_arg)
    
# --- EXAMPLE USAGE AS UNIX PIPE ---
# Assuming the script is saved as `pandoc_smart_debugger.py` and made executable:
#
# 1. Debugging a malformed Markdown snippet:
#    printf $'# Heading\n\n- List Item\n  Not a list item\n```python\nprint(\'hello\')\n```\n' | python pandoc_smart_debugger.py
#    # Expected Output: A report to stdout detailing Pandoc's syntax errors (e.g., malformed code block),
#    # including Problem, LaTeX Context, Markdown Context, and Solution.
#
# 2. Debugging a LaTeX error (e.g., trying to compile to PDF with bad LaTeX):
#    printf $'\\documentclass{article}\\begin{document}Hello\\end{document} Missing brace: \\section{' | python pandoc_smart_debugger.py pdf
#    # Expected Output: A report to stdout detailing LaTeX compilation errors (e.g., missing delimiter, undefined control sequence),
#    # with Problem, LaTeX Context, Markdown Context, and Solution.
#
# 3. Debugging a valid Markdown document (successful conversion):
#    printf $'# My Sample Document\n\nThis is a generic markdown document.\n\n## Section 1\nThis is the first section.\n\n## Section 2\nThis is the second section.\n\n- Item 1\n- Item 2\n- Item 3\n\n```python\nprint(\"Hello world!\")\n```\n\n**Bold text** and *italic text*.\n\n[Link to Google](https://www.google.com)\n' | python pandoc_smart_debugger.py html
#    # Expected Output:
#    # ===== Status Report =====
#    # ~~ No problems found ~~~
#    # =========================
#
# 4. Debugging an unknown Pandoc error (invalid YAML metadata):
#    # (This assumes a Pandoc error not covered by current patterns or a Pandoc WARNING)
#    printf $'---\nmetadata: {invalid: ]}\n---\n# Test\n' | python pandoc_smart_debugger.py
#    # Expected Output: A report including either a specific YAML Problem (if pattern matches),
#    # or a "Parser (Internal Error)" Problem (if unrecognized critical log), or a "Success with Warnings/Info" report
#    # if Pandoc considers it a warning.
#
# 5. Debugging a document with an unreadable image link (stub handler):
#    printf $'![Broken Image](file:///path/to/nonexistent/image.png)\n' | python pandoc_smart_debugger.py
#    # Expected Output: A report identifying a "Unreadable External Resource" problem, with relevant context and solution.
#
# 6. Debugging a document with a malformed custom filter call (stub handler):
#    printf $'---\nfilters: [non-existent-filter]\n---\n# Doc\n' | python pandoc_smart_debugger.py
#    # Expected Output: A report indicating a "Custom Filter Error" problem.
#
# 7. Debugging a LaTeX document with Unicode issues (stub handler):
#    printf $'\\documentclass{article}\\usepackage[utf8]{inputenc}\\begin{document}Grüße\\end{document}\n' | python pandoc_smart_debugger.py pdf
#    # (Assuming Pandoc/LaTeX produces a specific Unicode error for 'ü' with misconfig)
#    # Expected Output: A report indicating a "Unicode Character Issue" problem.
#
# 8. Debugging a complex table that Pandoc struggles with (ambiguous Markdown syntax):
#    printf $'| Header 1 | Header 2 |\n|---|---|\n| Cell 1 | Cell 2\n' | python pandoc_smart_debugger.py
#    # Expected Output: A report highlighting "Ambiguous Markdown Syntax" (or a specific Pandoc error if precise) problem.
#
# 9. Debugging a template-related issue (stub handler):
#    printf $'---\ntemplate: bad-template.html\n-\nHello\n' | python pandoc_smart_debugger.py html
#    # Expected Output: A report indicating a "Template/Variable Error" problem or a generic Pandoc error.
# --- END EXAMPLE USAGE ---

