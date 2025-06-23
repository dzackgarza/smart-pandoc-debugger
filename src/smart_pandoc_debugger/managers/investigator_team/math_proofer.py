#!/usr/bin/env python3
"""
SDE Investigator Team: Math Proofer Dispatcher

This script acts as a dispatcher for various math validation tools
that check LaTeX math expressions. It runs them in sequence and returns the
first actionable lead found.
"""
import os
import sys
import logging
import subprocess
from typing import Optional

# Add project root to path for imports
try:
    from utils.data_model import ActionableLead, SourceContextSnippet
except ImportError:
    # Handle case where script is run standalone for testing
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from utils.data_model import ActionableLead, SourceContextSnippet

# --- Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Specialist Configuration ---
TEX_PROOFER_TEAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex_proofer_team")
MATH_MODE_SYNTAX_SCRIPT = os.path.join(TEX_PROOFER_TEAM_DIR, "check_math_mode_syntax.py")
DOLLAR_DELIMITERS_SCRIPT = os.path.join(TEX_PROOFER_TEAM_DIR, "check_dollar_delimiters.py")
ALIGN_ENVIRONMENT_SCRIPT = os.path.join(TEX_PROOFER_TEAM_DIR, "check_align_environment.py")
MATH_CONTENT_VALIDATION_SCRIPT = os.path.join(TEX_PROOFER_TEAM_DIR, "check_math_content_validation.py")
UNMATCHED_INLINE_MATH_SCRIPT = os.path.join(TEX_PROOFER_TEAM_DIR, "check_unmatched_inline_math.awk")


def _run_specialist_script(script_path: str, tex_file: str) -> Optional[str]:
    """Runs a specialist script and returns its stdout if it finds an error."""
    if not os.path.exists(script_path):
        logger.warning(f"Specialist script not found: {script_path}")
        return None
        
    if script_path.endswith('.awk'):
        command = ['awk', '-f', script_path, tex_file]
    else:
        command = [sys.executable, script_path, tex_file]
        
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
        if process.returncode == 0 and process.stdout:
            logger.debug(f"Math specialist '{os.path.basename(script_path)}' found an issue: {process.stdout.strip()}")
            return process.stdout.strip()
        elif process.returncode != 0:
            logger.error(f"Math specialist '{os.path.basename(script_path)}' failed with rc={process.returncode}. Stderr: {process.stderr.strip()}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"Math specialist '{os.path.basename(script_path)}' timed out.")
    except Exception as e:
        logger.error(f"Error running math specialist '{os.path.basename(script_path)}': {e}", exc_info=True)
    return None


def _parse_math_mode_syntax_error(output: str) -> ActionableLead:
    """Parse output from math mode syntax checker."""
    # Format: ErrorType:LineNum:FoundPattern:Suggestion:ProblemSnippet:OriginalLine
    parts = output.split(':', 5)
    error_type = parts[0]
    line_num = int(parts[1])
    found_pattern = parts[2]
    suggestion = parts[3]
    original_line = parts[5] if len(parts) > 5 else parts[4]
    
    snippet_text = f"Line {line_num}: {original_line}\nFound: {found_pattern}"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    
    problem_descriptions = {
        'UnclosedFraction': 'Unclosed \\frac command detected in math mode.',
        'MissingBracesInExponent': 'Exponent with multiple characters needs braces.',
        'MissingMathFunctionBackslash': 'Mathematical function missing backslash prefix.',
        'AmsmathCommandWithoutPackage': 'Command requires amsmath package.',
        'NestedExponentNeedsBraces': 'Nested exponent needs additional braces.'
    }
    
    return ActionableLead(
        source_service="MathProofer_SyntaxChecker",
        problem_description=problem_descriptions.get(error_type, f"Math syntax error: {error_type}"),
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": f"LATEX_MATH_{error_type.upper()}",
            "suggested_fix": suggestion
        }
    )


def _parse_dollar_delimiter_error(output: str) -> ActionableLead:
    """Parse output from dollar delimiter checker."""
    # Format: ErrorType:LineNum:Delimiter:Suggestion:ProblemSnippet:OriginalLine
    parts = output.split(':', 5)
    error_type = parts[0]
    line_num = int(parts[1])
    delimiter = parts[2]
    suggestion = parts[3]
    original_line = parts[5] if len(parts) > 5 else parts[4]
    
    snippet_text = f"Line {line_num}: {original_line}\nUnclosed delimiter: {delimiter}"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    
    return ActionableLead(
        source_service="MathProofer_DelimiterChecker",
        problem_description=f"Unclosed math delimiter '{delimiter}' detected.",
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": "LATEX_UNCLOSED_MATH_DELIMITER",
            "suggested_fix": suggestion
        }
    )


def _parse_align_environment_error(output: str) -> ActionableLead:
    """Parse output from align environment checker."""
    # Format: ErrorType:LineNum:Pattern:Suggestion:ProblemSnippet:OriginalLine
    parts = output.split(':', 5)
    error_type = parts[0]
    line_num = int(parts[1])
    suggestion = parts[3]
    original_line = parts[5] if len(parts) > 5 else parts[4]
    
    snippet_text = f"Line {line_num}: {original_line}"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    
    problem_descriptions = {
        'EmptyLineInAlign': 'Empty line found inside align environment (not allowed).',
        'MissingLineEndInAlign': 'Line in align environment missing \\\\ terminator.',
        'NestedEquationEnvironment': 'Nested equation environments are not allowed.'
    }
    
    return ActionableLead(
        source_service="MathProofer_AlignChecker",
        problem_description=problem_descriptions.get(error_type, f"Align environment error: {error_type}"),
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": f"LATEX_ALIGN_{error_type.upper()}",
            "suggested_fix": suggestion
        }
    )


def _parse_math_content_error(output: str) -> ActionableLead:
    """Parse output from math content validator."""
    # Format: ErrorType:LineNum:MathType:Suggestion:ProblemSnippet:OriginalContent
    parts = output.split(':', 5)
    error_type = parts[0]
    line_num = int(parts[1])
    math_type = parts[2]
    suggestion = parts[3]
    original_content = parts[5] if len(parts) > 5 else parts[4]
    
    snippet_text = f"Line {line_num} ({math_type} math): {original_content}"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    
    problem_descriptions = {
        'EmptyMathBlock': 'Empty math block detected.',
        'UnbalancedBracesInMath': 'Unbalanced braces within math block.',
        'TextInMathMode': 'Text content in math mode needs \\text{} wrapper.',
        'UnmatchedLeftRight': 'Unmatched \\left and \\right delimiters.'
    }
    
    return ActionableLead(
        source_service="MathProofer_ContentValidator",
        problem_description=problem_descriptions.get(error_type, f"Math content error: {error_type}"),
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": f"LATEX_MATH_CONTENT_{error_type.upper()}",
            "suggested_fix": suggestion
        }
    )


def _parse_unmatched_inline_math(output: str) -> ActionableLead:
    """Parse output from unmatched inline math checker (AWK script)."""
    # Format: UnterminatedInlineMath:LineNum:OpenCount:CloseCount:ProblemSnippet:OriginalLine
    parts = output.split(':', 5)
    line_num = int(parts[1])
    open_count = int(parts[2])
    close_count = int(parts[3])
    problem_snippet = parts[4]
    original_line = parts[5] if len(parts) > 5 else problem_snippet
    
    snippet_text = f"Line {line_num}: {original_line}\nUnmatched \\( \\) delimiters: {open_count} open, {close_count} close"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    
    return ActionableLead(
        source_service="MathProofer_InlineMatchChecker",
        problem_description="Unmatched \\( \\) inline math delimiters detected.",
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": "LATEX_UNTERMINATED_INLINE_MATH"
        }
    )


def run_math_proofer(tex_file_path: str) -> Optional[ActionableLead]:
    """
    Runs various math validation specialists on a TeX file.
    Returns the first actionable lead found.
    """
    logger.debug(f"MathProofer: Running math specialists on {tex_file_path}")

    # List of (script_path, parser_function) pairs
    specialists = [
        (DOLLAR_DELIMITERS_SCRIPT, _parse_dollar_delimiter_error),
        (UNMATCHED_INLINE_MATH_SCRIPT, _parse_unmatched_inline_math),
        (MATH_MODE_SYNTAX_SCRIPT, _parse_math_mode_syntax_error),
        (ALIGN_ENVIRONMENT_SCRIPT, _parse_align_environment_error),
        (MATH_CONTENT_VALIDATION_SCRIPT, _parse_math_content_error),
    ]

    for script_path, parser_func in specialists:
        output = _run_specialist_script(script_path, tex_file_path)
        if output:
            try:
                return parser_func(output)
            except Exception as e:
                logger.error(f"Error parsing output from {os.path.basename(script_path)}: {e}")
                continue

    logger.debug("MathProofer: No math issues found by specialists.")
    return None


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <tex_file>", file=sys.stderr)
        sys.exit(2)
    
    result = run_math_proofer(sys.argv[1])
    if result:
        print(f"Math issue found: {result.problem_description}")
        for snippet in result.primary_context_snippets:
            print(f"Location: Line {snippet.central_line_number}")
            print(f"Context: {snippet.snippet_text}")
        sys.exit(1)
    else:
        print("No math issues found.")
        sys.exit(0)


if __name__ == "__main__":
    main() 