#!/usr/bin/env python3
"""
Smart Pandoc Debugger - Intake Clerk

The Intake Clerk is the human-in-the-loop component that serves as the initial point of contact
for documents entering the Smart Pandoc Debugger pipeline. This role is responsible for:

1. Receiving and validating markdown documents
2. Performing initial quality checks
3. Preparing documents for the diagnostic pipeline
4. Ensuring proper metadata and context is attached
5. Handing off to the next stage of the pipeline

As a human role, the Intake Clerk may need to make judgment calls about document quality,
appropriateness for debugging, and initial categorization of issues.
"""

import os
import sys
import json
import uuid
import argparse
import time
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from ..data_model import DiagnosticJob, PipelineStatus

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class IntakeClerk:
    """
    The Intake Clerk is the human-in-the-loop component that serves as the initial
    point of contact for documents entering the Smart Pandoc Debugger pipeline.
    
    Responsibilities include:
    - Validating markdown document structure
    - Performing initial quality checks
    - Attaching metadata and context
    - Preparing documents for the diagnostic pipeline
    - Making judgment calls about document quality and appropriateness
    - Ensuring proper handoff to the next stage of the pipeline
    
    The Intake Clerk's work is crucial for ensuring that only properly formatted
    and appropriate documents enter the automated diagnostic pipeline.
    """
    
    # Document types we can process
    DOCUMENT_TYPES = {
        'article': 'Standard academic or technical article',
        'thesis': 'Thesis or dissertation',
        'book': 'Book or long document',
        'presentation': 'Presentation slides',
        'other': 'Other document type'
    }
    
    @classmethod
    def eprint(cls, *args, **kwargs):
        """Prints to stderr with class name prefix and color coding."""
        print(f"{Colors.FAIL}[{cls.__name__}]{Colors.ENDC}", *args, file=sys.stderr, **kwargs)
    
    @classmethod
    def log(cls, message: str, level: str = 'info'):
        """Log a message with appropriate formatting and color coding."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if level.lower() == 'error':
            prefix = f"{Colors.FAIL}ERROR{Colors.ENDC}"
        elif level.lower() == 'warning':
            prefix = f"{Colors.WARNING}WARN {Colors.ENDC}"
        elif level.lower() == 'success':
            prefix = f"{Colors.OKGREEN} OK  {Colors.ENDC}"
        elif level.lower() == 'info':
            prefix = f"{Colors.OKBLUE} INFO{Colors.ENDC}"
        else:
            prefix = "     "
            
        # Format the message with word wrapping
        wrapper = textwrap.TextWrapper(
            width=80,
            initial_indent='  ',
            subsequent_indent='  ',
            break_long_words=False,
            break_on_hyphens=False
        )
        
        # Print the log message
        print(f"{timestamp} {prefix} {message}")
        
        # Return the formatted message for potential further processing
        return message
    
    @classmethod
    def _analyze_document_structure(cls, markdown_content: str) -> Dict[str, Any]:
        """
        Perform initial analysis of the document structure.
        
        Args:
            markdown_content: The markdown content to analyze
            
        Returns:
            Dict containing analysis results
        """
        analysis = {
            'has_math': '```math' in markdown_content or '$$' in markdown_content,
            'has_tables': '|' in markdown_content and '--' in markdown_content,
            'has_code_blocks': '```' in markdown_content,
            'has_images': '![' in markdown_content,
            'has_links': '](' in markdown_content,
            'has_headings': any(line.startswith('#') for line in markdown_content.split('\n')),
            'line_count': len(markdown_content.split('\n')),
            'word_count': len(markdown_content.split())
        }
        
        # Determine document type based on content
        if any(heading in markdown_content.lower() for heading in ['# abstract', '## abstract']):
            doc_type = 'article'
        elif any(heading in markdown_content.lower() for heading in ['# introduction', '## introduction']):
            doc_type = 'article'
        elif any(heading in markdown_content.lower() for heading in ['# chapter', '## chapter']):
            doc_type = 'book'
        else:
            doc_type = 'other'
            
        analysis['document_type'] = doc_type
        
        return analysis
    
    @classmethod
    def _perform_initial_checks(cls, markdown_content: str) -> Tuple[List[str], List[str]]:
        """
        Perform initial quality checks on the markdown content.
        
        This method checks for common issues in markdown documents that could cause
        problems during processing. It looks for unclosed code blocks, unclosed math
        blocks, and other potential issues.
        
        Args:
            markdown_content: The markdown content to check
            
        Returns:
            Tuple of (warnings, errors) found during initial checks
        """
        warnings = []
        errors = []
        lines = markdown_content.split('\n')
        
        # Check for empty code blocks
        if '```' in markdown_content and '```\n\n```' in markdown_content:
            warnings.append("Found empty code blocks (triple backticks with no content)")
        
        # Check for unclosed code blocks
        code_blocks = markdown_content.split('```')
        if len(code_blocks) > 1:  # If there are any code blocks
            # Skip the first element as it's content before the first ```
            for i, block in enumerate(code_blocks[1::2], 1):
                if not block.strip():
                    # Find the line number of the empty code block
                    line_num = len(markdown_content[:markdown_content.find('```')].split('\n'))
                    warnings.append(f"Empty code block starting at line {line_num}")
        
        # Check for unclosed code blocks (odd number of ```)
        if markdown_content.count('```') % 2 != 0:
            # Find the line number of the last ```
            last_code_pos = markdown_content.rfind('```')
            line_num = len(markdown_content[:last_code_pos].split('\n'))
            errors.append(f"Unclosed code block detected (odd number of triple backticks) starting at line {line_num}")
        
        # Check for unclosed math blocks ($$)
        if markdown_content.count('$$') % 2 != 0:
            # Find the line number of the last $$
            last_math_pos = markdown_content.rfind('$$')
            line_num = len(markdown_content[:last_math_pos].split('\n'))
            errors.append(f"Unclosed math block detected (odd number of $$) starting at line {line_num}")
        
        # Check for unclosed inline math ($...$)
        # This is a simple check that might have false positives with escaped $ or in code blocks
        if markdown_content.count('$') % 2 != 0:
            # Try to find the unclosed math
            last_dollar_pos = markdown_content.rfind('$')
            line_num = len(markdown_content[:last_dollar_pos].split('\n'))
            warnings.append(f"Possible unclosed inline math expression (odd number of $) near line {line_num}")
        
        # Check for extremely long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 1000:  # Arbitrary threshold for very long lines
                warnings.append(f"Line {i} is very long ({len(line)} characters)")
                break
                
        # Check for common markdown issues
        for i, line in enumerate(lines, 1):
            # Check for ATX headers with spaces after #
            if line.startswith('##') and not line.startswith('###') and ' ' not in line.lstrip('#'):
                warnings.append(f"Possible malformed ATX header at line {i}: '{line.strip()}'")
            
            # Check for setext headers without following === or ---
            if i < len(lines) and line.strip() and not line.startswith(('#', ' ', '\t', '>', '-', '*', '`')):
                next_line = lines[i] if i < len(lines) else ""
                if next_line.strip() and all(c in '=-' for c in next_line.strip()) and len(set(next_line.strip())) == 1:
                    if len(next_line.strip()) < len(line.strip()):
                        warnings.append(f"Setext header underlining too short at line {i+1}")
        
        return warnings, errors
    
    @classmethod
    def process_job(cls, markdown_content: str) -> Dict[str, Any]:
        """
        Process a new diagnostic job with the given markdown content.
        
        This is where the human Intake Clerk would review the document,
        perform initial checks, and prepare it for the diagnostic pipeline.
        
        Args:
            markdown_content: Raw markdown content to be diagnosed.
            
        Returns:
            dict: Initialized DiagnosticJob as a dictionary.
            
        Raises:
            AssertionError: If required preconditions are not met.
        """
        # Log the start of processing
        cls.log("Starting document intake process...")
        start_time = time.time()
        
        # Validate input
        if markdown_content is None:
            cls.log("Error: Markdown content cannot be None", 'error')
            raise ValueError("Markdown content cannot be None")
            
        if not isinstance(markdown_content, str):
            cls.log(f"Error: Expected string for markdown_content, got {type(markdown_content)}", 'error')
            raise TypeError("Markdown content must be a string")
            
        if not markdown_content.strip():
            cls.log("Error: Markdown content cannot be empty", 'error')
            raise ValueError("Markdown content cannot be empty")
        
        # Perform initial document analysis
        cls.log("Analyzing document structure...")
        analysis = cls._analyze_document_structure(markdown_content)
        
        # Perform initial quality checks
        cls.log("Performing initial quality checks...")
        warnings, errors = cls._perform_initial_checks(markdown_content)
        
        # Log the results of the analysis
        doc_type = cls.DOCUMENT_TYPES.get(analysis['document_type'], 'Unknown')
        cls.log(f"Document type: {doc_type}")
        
        if analysis['has_math']:
            cls.log("Document contains mathematical formulas", 'info')
        if analysis['has_tables']:
            cls.log("Document contains tables", 'info')
        if analysis['has_code_blocks']:
            cls.log("Document contains code blocks", 'info')
            
        # Log any warnings or errors
        for warning in warnings:
            cls.log(f"Warning: {warning}", 'warning')
            
        for error in errors:
            cls.log(f"Error: {error}", 'error')
        
        # Create initial job data
        job_data = {
            "job_id": str(uuid.uuid4()),
            "original_markdown_path": "input.md",  # This will be updated by the caller if needed
            "status": PipelineStatus.READY_FOR_MINER.value,
            "markdown_content": markdown_content,
            "markdown_proofer_errors": errors,  # Include any errors found during initial checks
            "actionable_leads": [],
            "markdown_remedies": [],
            "metadata": {
                "document_type": analysis['document_type'],
                "analysis": analysis,
                "warnings": warnings,
                "intake_timestamp": datetime.utcnow().isoformat(),
                "intake_duration_seconds": time.time() - start_time
            },
            "history": [
                f"Job created at {datetime.utcnow().isoformat()} by Intake Clerk",
                f"Document type: {doc_type}",
                f"Lines: {analysis['line_count']}, Words: {analysis['word_count']}",
                *[f"Warning: {w}" for w in warnings],
                *[f"Error: {e}" for e in errors]
            ]
        }
        
        # Validate against Pydantic model
        try:
            job = DiagnosticJob(**job_data)
            return job.model_dump()
        except Exception as e:
            cls.eprint(f"Failed to validate job data: {e}")
            raise
    
    @classmethod
    def from_stdin(cls) -> Dict[str, Any]:
        """
        Read markdown content from stdin and process it as a new job.
        
        Returns:
            dict: Initialized DiagnosticJob as a dictionary.
        """
        markdown_content = sys.stdin.read()
        job_data = cls.process_job(markdown_content)
        job_data["original_markdown_path"] = "stdin"
        return job_data
    
    @classmethod
    def from_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Read markdown content from a file and process it as a new job.
        
        Args:
            file_path: Path to the markdown file.
            
        Returns:
            dict: Initialized DiagnosticJob as a dictionary.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        job_data = cls.process_job(markdown_content)
        job_data["original_markdown_path"] = os.path.abspath(file_path)
        return job_data


def main():
    """
    Main entry point for the Intake Clerk CLI.
    
    Usage:
        python -m smart_pandoc_debugger.managers.IntakeClerk [options] [file]
        
    If no file is provided, reads from stdin.
    """
    parser = argparse.ArgumentParser(
        description='Smart Pandoc Debugger - Intake Clerk',
        usage='%(prog)s [options] [file]'
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        default=None,
        help='Path to markdown file (reads from stdin if not provided)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Write output to file (default: stdout)'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show version and exit'
    )
    
    args = parser.parse_args()
    
    if args.version:
        from smart_pandoc_debugger import __version__
        print(f"Smart Pandoc Debugger v{__version__}")
        sys.exit(0)
    
    try:
        # Process input
        if args.file:
            job_data = IntakeClerk.from_file(args.file)
        else:
            job_data = IntakeClerk.from_stdin()
        
        # Output the job data as JSON
        output = json.dumps(job_data, indent=2)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output + '\n')
        else:
            print(output)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
