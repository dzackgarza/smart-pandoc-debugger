#!/usr/bin/env python3
# managers/investigator-team/undefined_command_proofer.py
"""
SDE Investigator Team: Undefined Command Proofer

This specialist tool analyzes LaTeX compilation logs for "Undefined control sequence"
errors and provides detailed information about the undefined command.
"""

import os
import sys
import re
import logging
import argparse
import json
from typing import Dict, List, Optional, Any, Set

# Add project root to path for imports
try:
    from smart_pandoc_debugger.data_model import ActionableLead, SourceContextSnippet
except ImportError:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, "..", "..", "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from smart_pandoc_debugger.data_model import ActionableLead, SourceContextSnippet

# --- Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Common LaTeX commands and their packages
COMMAND_PACKAGES: Dict[str, str] = {
    # Math commands
    '\\text': 'amsmath',
    '\\DeclareMathOperator': 'amsmath',
    '\\numberwithin': 'amsmath',
    '\\intertext': 'amsmath',
    '\\mathtoolsset': 'mathtools',
    '\\prescript': 'mathtools',
    '\\DeclarePairedDelimiter': 'mathtools',
    
    # Graphics
    '\\includegraphics': 'graphicx',
    '\\rotatebox': 'graphicx',
    '\\scalebox': 'graphicx',
    '\\resizebox': 'graphicx',
    '\\includegraphics': 'graphicx',
    
    # Tables
    '\\toprule': 'booktabs',
    '\\midrule': 'booktabs',
    '\\bottomrule': 'booktabs',
    '\\cmidrule': 'booktabs',
    '\\addlinespace': 'booktabs',
    
    # Hyperlinks
    '\\url': 'hyperref',
    '\\href': 'hyperref',
    '\\hyperref': 'hyperref',
    '\\autoref': 'hyperref',
    '\\nameref': 'hyperref',
    
    # Algorithms
    '\\begin{algorithm}': 'algorithm',
    '\\begin{algorithmic}': 'algorithmic',
    '\\State': 'algorithmic',
    '\\For': 'algorithmic',
    '\\If': 'algorithmic',
    '\\Else': 'algorithmic',
    '\\ElsIf': 'algorithmic',
    '\\EndFor': 'algorithmic',
    '\\EndIf': 'algorithmic',
    
    # Listings
    '\\lstinputlisting': 'listings',
    '\\lstset': 'listings',
    '\\begin{lstlisting}': 'listings',
    
    # SI units
    '\\si': 'siunitx',
    '\\SI': 'siunitx',
    '\\num': 'siunitx',
    '\\ang': 'siunitx',
    '\\siunitxsetup': 'siunitx',
    
    # Other common packages
    '\\usepackage': 'latex',
    '\\documentclass': 'latex',
    '\\input': 'latex',
    '\\include': 'latex',
    '\\bibliography': 'latex',
    '\\bibliographystyle': 'latex',
    '\\cite': 'latex',
    '\\ref': 'latex',
    '\\label': 'latex',
}

def find_undefined_commands(log_content: str) -> List[Dict[str, Any]]:
    """
    Find all undefined command errors in the LaTeX log.
    
    Args:
        log_content: The content of the LaTeX compilation log
        
    Returns:
        A list of dictionaries, each containing information about an undefined command
    """
    # Pattern for undefined control sequence errors
    pattern = re.compile(
        r"! Undefined control sequence\\.*?l\\.(\\d+).*?\\\\([a-zA-Z@]+)",
        re.DOTALL
    )
    
    # Alternative pattern for different LaTeX error format
    alt_pattern = re.compile(
        r"! LaTeX Error: (\\\\[a-zA-Z@]+) undefined.*?l\\.(\\d+)",
        re.DOTALL
    )
    
    results = []
    seen_commands: Set[str] = set()
    
    # Search for the primary pattern
    for match in pattern.finditer(log_content):
        line_number = int(match.group(1))
        command = '\\' + match.group(2)
        
        if command not in seen_commands:
            seen_commands.add(command)
            results.append({
                'command': command,
                'line_number': line_number,
                'error_type': 'UNDEFINED_CONTROL_SEQUENCE'
            })
    
    # Search for the alternative pattern
    for match in alt_pattern.finditer(log_content):
        command = match.group(1)
        line_number = int(match.group(2))
        
        if command not in seen_commands:
            seen_commands.add(command)
            results.append({
                'command': command,
                'line_number': line_number,
                'error_type': 'UNDEFINED_COMMAND'
            })
    
    return results

def suggest_package(command: str) -> str:
    """
    Suggest a package that might provide the missing command.
    
    Args:
        command: The undefined LaTeX command
        
    Returns:
        The name of a suggested package or an empty string if no suggestion is available
    """
    return COMMAND_PACKAGES.get(command, '')

def create_actionable_lead(error_info: Dict[str, Any], source_file: Optional[str] = None) -> ActionableLead:
    """
    Create an ActionableLead for an undefined command error.
    
    Args:
        error_info: Dictionary containing error details
        source_file: Optional path to the source file
        
    Returns:
        An ActionableLead object with the error information
    """
    command = error_info.get('command', '\\unknown')
    line_number = error_info.get('line_number', 0)
    error_type = error_info.get('error_type', 'UNDEFINED_CONTROL_SEQUENCE')
    
    # Get package suggestion
    suggested_package = suggest_package(command)
    
    # Create the fix message
    if suggested_package:
        if suggested_package == 'latex':
            fix = f"The command {command} is a basic LaTeX command. Check for typos or missing document class."
        else:
            fix = f"Add '\\usepackage{{{suggested_package}}}' to your preamble to define {command}."
    else:
        fix = f"Define the command {command} using '\\newcommand' or check for typos."
    
    # Create context snippet
    context = [
        SourceContextSnippet(
            content=f"Undefined command: {command}",
            line_number=line_number,
            file_path=source_file
        )
    ]
    
    return ActionableLead(
        lead_type=error_type,
        description=f"Undefined LaTeX command: {command}",
        fix=fix,
        context=context,
        severity='error',
        confidence=0.9,
        source_file=source_file,
        line_number=line_number,
        column_number=0,
        raw_error_message=f"Undefined command: {command}"
    )

def run_undefined_command_proofer(log_file_path: str, source_file: Optional[str] = None) -> List[ActionableLead]:
    """
    Parses a LaTeX log file to find 'Undefined control sequence' errors.
    
    Args:
        log_file_path: Path to the LaTeX compilation log file
        source_file: Optional path to the source file being compiled
        
    Returns:
        A list of ActionableLead objects for each undefined command found
    """
    logger.debug(f"UndefinedCommandProofer: Starting analysis of {log_file_path}")
    
    if not os.path.exists(log_file_path):
        logger.error(f"Log file not found at {log_file_path}")
        return []

    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
            log_content = f.read()
            
        errors = find_undefined_commands(log_content)
        leads = []
        
        for error in errors:
            if source_file and os.path.exists(source_file):
                lead = create_actionable_lead(error, source_file)
            else:
                lead = create_actionable_lead(error)
            leads.append(lead)
            
        return leads
        
    except Exception as e:
        logger.error(f"Error processing log file {log_file_path}: {str(e)}", exc_info=True)
        return []

def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(
        description="Finds undefined LaTeX commands in compilation logs."
    )
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to the LaTeX compilation log file."
    )
    parser.add_argument(
        "--source-file",
        help="Path to the source file being compiled (optional)."
    )
    args = parser.parse_args()
    
    try:
        leads = run_undefined_command_proofer(args.log_file, args.source_file)
        
        if args.source_file and os.path.exists(args.source_file):
            # Return full ActionableLead objects
            print(json.dumps([lead.to_dict() for lead in leads]))
        else:
            # Return simplified output
            print(json.dumps([{
                'command': lead.context[0].content.replace('Undefined command: ', ''),
                'line': lead.line_number,
                'type': lead.lead_type
            } for lead in leads]))
            
    except Exception as e:
        print(json.dumps({
            'error': 'PROCESSING_ERROR',
            'message': f"Failed to process log file: {str(e)}"
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
