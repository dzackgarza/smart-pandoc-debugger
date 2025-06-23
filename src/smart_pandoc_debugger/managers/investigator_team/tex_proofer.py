#!/usr/bin/env python3
"""
SDE Investigator Team: TeX Proofer Dispatcher

This script acts as a dispatcher for various specialist TeX proofing tools
that operate on the command line. It runs them in sequence and returns the
first actionable lead found.
"""
import os
import sys
import logging
import subprocess
from typing import Optional, List

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
TEX_PROOFER_TEAM_DIR = os.path.dirname(os.path.abspath(__file__))
UNBALANCED_BRACES_SCRIPT = os.path.join(TEX_PROOFER_TEAM_DIR, "tex_proofer_team", "check_tex_unbalanced_braces.py")
PAIRED_DELIMITERS_SCRIPT = os.path.join(TEX_PROOFER_TEAM_DIR, "tex_proofer_team", "check_tex_paired_delimiters.py")
MATH_PROOFER_SCRIPT = os.path.join(TEX_PROOFER_TEAM_DIR, "math_proofer.py")


def _run_specialist_script(script_path: str, tex_file: str) -> Optional[str]:
    """Runs a specialist script and returns its stdout if it finds an error."""
    assert os.path.exists(script_path), f"Specialist script not found: {script_path}"
    command = [sys.executable, script_path, tex_file]
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
        # These scripts are designed to exit 0 and print to stdout on finding an error.
        if process.returncode == 0 and process.stdout:
            logger.debug(f"Specialist '{os.path.basename(script_path)}' found an issue: {process.stdout.strip()}")
            return process.stdout.strip()
        elif process.returncode != 0:
            logger.error(f"Specialist '{os.path.basename(script_path)}' failed with rc={process.returncode}. Stderr: {process.stderr.strip()}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"Specialist '{os.path.basename(script_path)}' timed out.")
    except Exception as e:
        logger.error(f"Error running specialist '{os.path.basename(script_path)}': {e}", exc_info=True)
    return None

def _parse_unbalanced_braces(output: str) -> ActionableLead:
    """Parses output from the unbalanced braces script."""
    # Format: ErrorType:LineNum:OpenCount:CloseCount:ProblemSnippet:OriginalLineContent
    parts = output.split(':', 5)
    line_num = int(parts[1])
    snippet_text = f"Line {line_num}: {parts[5]}\nSnippet with error: {parts[4]}"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    return ActionableLead(
        source_service="TexProofer_UnbalancedBraces",
        problem_description="Unbalanced curly braces {} detected in a math environment.",
        primary_context_snippets=[snippet],
        internal_details_for_oracle={"error_signature_code_from_tool": "LATEX_UNBALANCED_BRACES"}
    )

def _parse_mismatched_delimiters(output: str) -> ActionableLead:
    """Parses output from the mismatched delimiters script."""
    # Format: ErrorType:LineNum:Val1:Val2:ProblemSnippet:OriginalLineContent
    parts = output.split(':', 5)
    line_num = int(parts[1])
    snippet_text = f"Line {line_num}: {parts[5]}\nMismatched pair: {parts[4]}"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    return ActionableLead(
        source_service="TexProofer_MismatchedDelimiters",
        problem_description=f"Mismatched paired delimiters. Found opening '{parts[2]}' but closing '{parts[3]}'.",
        primary_context_snippets=[snippet],
        internal_details_for_oracle={"error_signature_code_from_tool": "LATEX_MISMATCHED_DELIMITERS"}
    )


def _run_math_proofer(tex_file_path: str) -> Optional[ActionableLead]:
    """Run the comprehensive math proofer and return parsed result."""
    if not os.path.exists(MATH_PROOFER_SCRIPT):
        logger.debug("Math proofer script not found, skipping math checks")
        return None
        
    command = [sys.executable, MATH_PROOFER_SCRIPT, tex_file_path]
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=15)
        if process.returncode == 1 and process.stdout:
            # Math proofer found an issue
            logger.debug(f"Math proofer found an issue: {process.stdout.strip()}")
            # The math proofer outputs its own ActionableLead description, so we parse it
            # For now, create a basic lead - could be enhanced to parse structured output
            lines = process.stdout.strip().split('\n')
            problem_desc = lines[0].replace("Math issue found: ", "") if lines else "Math validation issue found"
            
            snippet_text = "\n".join(lines[1:]) if len(lines) > 1 else "See math proofer output for details"
            snippet = SourceContextSnippet(
                source_document_type="generated_tex",
                central_line_number=1,  # Default, could be parsed from output
                snippet_text=snippet_text
            )
            
            return ActionableLead(
                source_service="TexProofer_MathValidator",
                problem_description=problem_desc,
                primary_context_snippets=[snippet],
                internal_details_for_oracle={"error_signature_code_from_tool": "LATEX_MATH_VALIDATION_ERROR"}
            )
    except subprocess.TimeoutExpired:
        logger.error("Math proofer timed out")
    except Exception as e:
        logger.error(f"Error running math proofer: {e}")
    
    return None


def run_tex_proofer(tex_file_path: str) -> Optional[ActionableLead]:
    """
    Runs various TeX proofing specialists on a TeX file.
    
    Args:
        tex_file_path: Path to the TeX file to analyze for validation issues.
        
    Returns:
        ActionableLead if any issues are found, None otherwise.
    """
    logger.debug(f"TexProofer: Running specialists on {tex_file_path}")

    # --- Run Math Proofer (Branch 2 Implementation) ---
    math_result = _run_math_proofer(tex_file_path)
    if math_result:
        return math_result

    # --- Run Unbalanced Braces Proofer ---
    unbalanced_output = _run_specialist_script(UNBALANCED_BRACES_SCRIPT, tex_file_path)
    if unbalanced_output:
        return _parse_unbalanced_braces(unbalanced_output)

    # --- Run Mismatched Delimiters Proofer ---
    mismatched_output = _run_specialist_script(PAIRED_DELIMITERS_SCRIPT, tex_file_path)
    if mismatched_output:
        return _parse_mismatched_delimiters(mismatched_output)

    logger.debug("TexProofer: No issues found by specialists.")
    return None
