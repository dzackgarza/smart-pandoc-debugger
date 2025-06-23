#!/usr/bin/env python3
# managers/investigator-team/undefined_environment_proofer.py
"""
SDE Investigator Team: Undefined Environment Proofer

This specialist tool analyzes LaTeX compilation logs for "Environment ... undefined"
errors and provides detailed information about the undefined environment.
"""

import argparse
import json
import re
import sys
import os
from typing import Dict, Optional, Tuple

from smart_pandoc_debugger.data_model import ActionableLead, SourceContextSnippet

def suggest_package(env_name: str) -> str:
    """
    Suggest a LaTeX package that might provide the given environment.
    
    Args:
        env_name: Name of the LaTeX environment
        
    Returns:
        str: Name of the suggested package, or empty string if no suggestion is available
    """
    # Common LaTeX environments and their packages
    env_to_package = {
        'algorithm': 'algorithm',
        'algorithmic': 'algorithmic',
        'align': 'amsmath',
        'align*': 'amsmath',
        'aligned': 'amsmath',
        'array': 'array',
        'bmatrix': 'amsmath',
        'cases': 'amsmath',
        'center': 'amsmath',
        'comment': 'verbatim',
        'document': 'document',
        'enumerate': 'enumerate',
        'eqnarray': 'amsmath',
        'equation': 'amsmath',
        'figure': 'graphics',
        'figure*': 'graphics',
        'flushleft': 'amsmath',
        'flushright': 'amsmath',
        'gather': 'amsmath',
        'itemize': 'itemize',
        'list': 'list',
        'lstlisting': 'listings',
        'matrix': 'amsmath',
        'minipage': 'graphics',
        'multline': 'amsmath',
        'picture': 'picture',
        'pmatrix': 'amsmath',
        'proof': 'amsthm',
        'quotation': 'quotation',
        'quote': 'quote',
        'split': 'amsmath',
        'subequations': 'amsmath',
        'tabbing': 'tabbing',
        'table': 'tabular',
        'table*': 'tabular',
        'tabular': 'tabular',
        'tabular*': 'tabular',
        'theorem': 'amsthm',
        'theorem*': 'amsthm',
        'titlepage': 'titlepage',
        'verbatim': 'verbatim',
        'verbatim*': 'verbatim',
        'wrapfigure': 'wrapfig',
    }
    
    return env_to_package.get(env_name, '')


def find_undefined_environment(log_content: str) -> Optional[Dict]:
    """
    Checks for "Environment ... undefined." errors in the log and extracts relevant information.
    
    Args:
        log_content: The content of the LaTeX compilation log
        
    Returns:
        A dictionary containing error details or None if no error is found
    """
    # Pattern to match environment undefined errors with line number
    pattern = re.compile(
        r"! LaTeX Error: Environment (\w+) undefined\.\s*"
        r"l\.(\d+)\s*"
        r"You're in trouble here.*?\n"
        r"l\.\d+\s*\\begin\{([^}]+)\}.*?$",
        re.MULTILINE | re.DOTALL
    )
    
    # Alternative pattern for different LaTeX error format
    alt_pattern = re.compile(
        r"! Undefined control sequence\..*?l\.(\d+).*?\n"
        r"<argument> \\begin\{([^}]+)\}",
        re.MULTILINE | re.DOTALL
    )
    
    # Try to match the primary pattern first
    match = pattern.search(log_content)
    if match:
        env_name = match.group(1)
        line_number = int(match.group(2))
        found_env = match.group(3)
        
        # If the environment name doesn't match what was found, use the found one
        if env_name != found_env:
            env_name = found_env
            
        return {
            "error_signature": "LATEX_UNDEFINED_ENVIRONMENT",
            "environment_name": env_name,
            "line_number": line_number,
            "raw_error_message": f"Environment {env_name} undefined.",
            "context": f"Found '\\begin{{{env_name}}}' on line {line_number} but the environment is not defined."
        }
    
    # Try the alternative pattern if the first one didn't match
    alt_match = alt_pattern.search(log_content)
    if alt_match:
        line_number = int(alt_match.group(1))
        env_name = alt_match.group(2)
        
        return {
            "error_signature": "LATEX_UNDEFINED_ENVIRONMENT",
            "environment_name": env_name,
            "line_number": line_number,
            "raw_error_message": f"Environment {env_name} undefined.",
            "context": f"Found '\\begin{{{env_name}}}' on line {line_number} but the environment is not defined."
        }
    
    return None

def suggest_package(environment_name: str) -> str:
    """
    Suggests a package that might provide the missing environment.
    
    Args:
        environment_name: The name of the undefined environment
        
    Returns:
        The name of a suggested package or an empty string if no suggestion is available
    """
    # Common environments and their packages
    environment_packages = {
        'algorithm': 'algorithm',
        'algorithmic': 'algorithmic',
        'align': 'amsmath',
        'align*': 'amsmath',
        'alignat': 'amsmath',
        'alignat*': 'amsmath',
        'aligned': 'amsmath',
        'array': 'array',
        'bmatrix': 'amsmath',
        'cases': 'amsmath',
        'enumerate': 'enumerate',
        'equation': 'amsmath',
        'equation*': 'amsmath',
        'figure': 'graphicx',
        'figure*': 'graphicx',
        'gather': 'amsmath',
        'gather*': 'amsmath',
        'itemize': 'enumerate',
        'list': 'enumerate',
        'matrix': 'amsmath',
        'multline': 'amsmath',
        'pmatrix': 'amsmath',
        'split': 'amsmath',
        'subequations': 'amsmath',
        'table': 'booktabs',
        'table*': 'booktabs',
        'tabular': 'array',
        'theorem': 'amsthm',
        'theorem*': 'amsthm',
    }
    
    return environment_packages.get(environment_name, '')

def create_actionable_lead(error_info: Dict) -> ActionableLead:
    """
    Creates an ActionableLead from error information.
    
    Args:
        error_info: Dictionary containing error details
        
    Returns:
        An ActionableLead object with the error information
    """
    env_name = error_info.get('environment_name', 'unknown')
    suggested_package = suggest_package(env_name)
    
    # Create the fix message
    if suggested_package:
        fix = f"Add '\\usepackage{{{suggested_package}}}' to your preamble."
    else:
        fix = f"Define the '{env_name}' environment using '\\newenvironment' or check for typos."
    
    # Create context snippet
    context = [
        SourceContextSnippet(
            content=f"Found '\\begin{{{env_name}}}' but the environment is not defined.",
            line_number=error_info.get('line_number', 0),
            file_path=None  # Will be set by the caller
        )
    ]
    
    return ActionableLead(
        lead_type='LATEX_UNDEFINED_ENVIRONMENT',
        description=f"Undefined LaTeX environment: {env_name}",
        fix=fix,
        context=context,
        severity='error',
        confidence=0.9,
        source_file=None,  # Will be set by the caller
        line_number=error_info.get('line_number', 0),
        column_number=0,
        raw_error_message=error_info.get('raw_error_message', '')
    )

def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(
        description="Finds 'Environment ... undefined.' errors in LaTeX logs and provides actionable information."
    )
    parser.add_argument(
        "--log-file", 
        required=True, 
        help="Path to the TeX compilation log file."
    )
    parser.add_argument(
        "--source-file",
        help="Path to the source file being compiled (optional)."
    )
    args = parser.parse_args()
    
    try:
        with open(args.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            
        result = find_undefined_environment(log_content)
        
        if result:
            # If source file is provided, create a full ActionableLead
            if args.source_file and os.path.exists(args.source_file):
                result['source_file'] = args.source_file
                lead = create_actionable_lead(result)
                print(lead.to_json())
            else:
                # Just return the basic error info
                print(json.dumps({
                    'error': 'LATEX_UNDEFINED_ENVIRONMENT',
                    'environment': result['environment_name'],
                    'line': result.get('line_number', 0),
                    'message': result['raw_error_message'],
                    'context': result.get('context', '')
                }))
        else:
            print(json.dumps({}))
            
    except Exception as e:
        print(json.dumps({
            'error': 'PROCESSING_ERROR',
            'message': f"Failed to process log file: {str(e)}"
        }))
        sys.exit(1)

if __name__ == "__main__":
    main() 