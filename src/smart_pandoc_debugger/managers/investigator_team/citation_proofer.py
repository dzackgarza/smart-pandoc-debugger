#!/usr/bin/env python3
"""
SDE Investigator Team: Citation Proofer Dispatcher

This script acts as a dispatcher for various citation validation tools
that check LaTeX citations and bibliography. It runs them in sequence and returns the
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
CITATION_TEAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "citation_team")
PANDOC_CITATION_SCRIPT = os.path.join(CITATION_TEAM_DIR, "check_pandoc_citations.py")
LATEX_CITATION_SCRIPT = os.path.join(CITATION_TEAM_DIR, "check_latex_citations.py")
BIBLIOGRAPHY_SCRIPT = os.path.join(CITATION_TEAM_DIR, "check_bibliography.py")
CITATION_STYLE_SCRIPT = os.path.join(CITATION_TEAM_DIR, "check_citation_style.py")


def _run_specialist_script(script_path: str, tex_file: str) -> Optional[str]:
    """
    Runs a specialist script and returns its stdout if it finds an error.
    
    Args:
        script_path: Path to the specialist validation script
        tex_file: Path to the TeX file to validate
        
    Returns:
        String output if validation error found, None if no errors or script failure
        
    Note:
        - Return code 0 with stdout indicates validation error found
        - Return code != 0 indicates script execution failure (not validation error)
        - No stdout means no validation issues detected
    """
    if not os.path.exists(script_path):
        logger.warning(f"Citation specialist script not found: {script_path}")
        return None
        
    command = [sys.executable, script_path, tex_file]
        
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
        if process.returncode == 0 and process.stdout:
            logger.debug(f"Citation specialist '{os.path.basename(script_path)}' found an issue: {process.stdout.strip()}")
            return process.stdout.strip()
        elif process.returncode != 0:
            # Non-zero exit code indicates script failure, not a validation error
            logger.error(f"Citation specialist '{os.path.basename(script_path)}' failed with rc={process.returncode}. Stderr: {process.stderr.strip()}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"Citation specialist '{os.path.basename(script_path)}' timed out.")
    except Exception as e:
        logger.error(f"Error running citation specialist '{os.path.basename(script_path)}': {e}", exc_info=True)
    return None


def _parse_pandoc_citation_error(output: str) -> ActionableLead:
    """Parse output from Pandoc citation checker."""
    # Format: ErrorType:LineNum:CitationKey:Suggestion:ProblemSnippet:OriginalLine
    parts = output.split(':', 5)
    error_type = parts[0]
    line_num = int(parts[1])
    citation_key = parts[2]
    suggestion = parts[3]
    original_line = parts[5] if len(parts) > 5 else parts[4]
    
    snippet_text = f"Line {line_num}: {original_line}\nUndefined citation: [@{citation_key}]"
    snippet = SourceContextSnippet(
        source_document_type="markdown",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    
    problem_descriptions = {
        'UndefinedPandocCitation': f'Pandoc citation [@{citation_key}] not found in bibliography.',
        'MissingBibliography': 'No bibliography file found for Pandoc citations.',
        'DuplicateCitationKey': f'Citation key "{citation_key}" appears multiple times in bibliography.'
    }
    
    return ActionableLead(
        source_service="CitationProofer_PandocChecker",
        problem_description=problem_descriptions.get(error_type, f"Pandoc citation error: {error_type}"),
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": f"PANDOC_CITATION_{error_type.upper()}",
            "suggested_fix": suggestion,
            "citation_key": citation_key
        }
    )


def _parse_latex_citation_error(output: str) -> ActionableLead:
    """Parse output from LaTeX citation checker."""
    # Format: ErrorType:LineNum:CitationKey:Suggestion:ProblemSnippet:OriginalLine
    parts = output.split(':', 5)
    error_type = parts[0]
    line_num = int(parts[1])
    citation_key = parts[2]
    suggestion = parts[3]
    original_line = parts[5] if len(parts) > 5 else parts[4]
    
    snippet_text = f"Line {line_num}: {original_line}\nUndefined citation: \\cite{{{citation_key}}}"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    
    problem_descriptions = {
        'UndefinedLatexCitation': f'LaTeX citation \\cite{{{citation_key}}} not found in bibliography.',
        'UnusedBibEntry': f'Bibliography entry "{citation_key}" is defined but never cited.',
        'CitepCitetMisuse': 'Incorrect usage of \\citep vs \\citet (natbib package).'
    }
    
    return ActionableLead(
        source_service="CitationProofer_LatexChecker",
        problem_description=problem_descriptions.get(error_type, f"LaTeX citation error: {error_type}"),
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": f"LATEX_CITATION_{error_type.upper()}",
            "suggested_fix": suggestion,
            "citation_key": citation_key
        }
    )


def _parse_bibliography_error(output: str) -> ActionableLead:
    """Parse output from bibliography checker."""
    # Format: ErrorType:LineNum:BibFile:Suggestion:ProblemSnippet:OriginalLine
    parts = output.split(':', 5)
    error_type = parts[0]
    line_num = int(parts[1])
    bib_file = parts[2]
    suggestion = parts[3]
    original_line = parts[5] if len(parts) > 5 else parts[4]
    
    snippet_text = f"Line {line_num}: {original_line}"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    
    problem_descriptions = {
        'MissingBibliographyCommand': 'Missing \\bibliography{} command in document.',
        'BibliographyFileNotFound': f'Bibliography file "{bib_file}" not found.',
        'MalformedBibEntry': 'Malformed bibliography entry detected.'
    }
    
    return ActionableLead(
        source_service="CitationProofer_BibliographyChecker",
        problem_description=problem_descriptions.get(error_type, f"Bibliography error: {error_type}"),
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": f"BIBLIOGRAPHY_{error_type.upper()}",
            "suggested_fix": suggestion,
            "bibliography_file": bib_file
        }
    )


def _parse_citation_style_error(output: str) -> ActionableLead:
    """Parse output from citation style checker."""
    # Format: ErrorType:LineNum:Command:Suggestion:ProblemSnippet:OriginalLine
    parts = output.split(':', 5)
    error_type = parts[0]
    line_num = int(parts[1])
    command = parts[2]
    suggestion = parts[3]
    original_line = parts[5] if len(parts) > 5 else parts[4]
    
    snippet_text = f"Line {line_num}: {original_line}\nCommand: {command}"
    snippet = SourceContextSnippet(
        source_document_type="generated_tex",
        central_line_number=line_num,
        snippet_text=snippet_text
    )
    
    problem_descriptions = {
        'InconsistentCitationStyle': 'Inconsistent citation style usage detected.',
        'NatbibCommandWithoutPackage': 'Using natbib commands without \\usepackage{natbib}.',
        'BiblatexCommandWithoutPackage': 'Using biblatex commands without \\usepackage{biblatex}.'
    }
    
    return ActionableLead(
        source_service="CitationProofer_StyleChecker",
        problem_description=problem_descriptions.get(error_type, f"Citation style error: {error_type}"),
        primary_context_snippets=[snippet],
        internal_details_for_oracle={
            "error_signature_code_from_tool": f"CITATION_STYLE_{error_type.upper()}",
            "suggested_fix": suggestion,
            "problematic_command": command
        }
    )


def run_citation_proofer(tex_file_path: str) -> Optional[ActionableLead]:
    """
    Runs various citation validation specialists on a TeX file.
    Returns the first actionable lead found.
    """
    logger.debug(f"CitationProofer: Running citation specialists on {tex_file_path}")

    # List of (script_path, parser_function) pairs
    specialists = [
        (PANDOC_CITATION_SCRIPT, _parse_pandoc_citation_error),
        (LATEX_CITATION_SCRIPT, _parse_latex_citation_error),
        (BIBLIOGRAPHY_SCRIPT, _parse_bibliography_error),
        (CITATION_STYLE_SCRIPT, _parse_citation_style_error),
    ]

    for script_path, parser_func in specialists:
        output = _run_specialist_script(script_path, tex_file_path)
        if output:
            try:
                return parser_func(output)
            except Exception as e:
                logger.error(f"Error parsing output from {os.path.basename(script_path)}: {e}")
                continue

    logger.debug("CitationProofer: No citation issues found by specialists.")
    return None


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <tex_file>", file=sys.stderr)
        sys.exit(2)
    
    result = run_citation_proofer(sys.argv[1])
    if result:
        print(f"Citation issue found: {result.problem_description}")
        for snippet in result.primary_context_snippets:
            print(f"Location: Line {snippet.central_line_number}")
            print(f"Context: {snippet.snippet_text}")
        sys.exit(1)
    else:
        print("No citation issues found.")
        sys.exit(0)


if __name__ == "__main__":
    main() 