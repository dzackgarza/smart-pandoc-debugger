# Smart Pandoc Debugger - Implementation Plan

This document provides detailed implementation guidance for the highest priority tasks identified in the MVP_TODO.md file.

## 1. Core Infrastructure Setup

### Create a system-wide executable script

```bash
#!/bin/bash
# smart-pandoc-debugger - Main executable for the Smart Pandoc Debugger
#
# This script serves as the main entry point for the Smart Pandoc Debugger.
# It sets up the necessary environment and invokes the Python-based intake.py script.

# Determine the absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Enable debug mode if DEBUG environment variable is set
if [ -n "${DEBUG}" ]; then
    echo "Debug mode enabled" >&2
fi

# Read Markdown content from stdin and pipe it to intake.py
cat | python3 "${SCRIPT_DIR}/intake.py"

# Exit with the same status as intake.py
exit $?
```

Save this script as `smart-pandoc-debugger` in the project root, then make it executable:

```bash
chmod +x smart-pandoc-debugger
```

To make it available system-wide, either:
1. Add the project directory to your PATH:
   ```bash
   export PATH="$PATH:/path/to/smart-pandoc-debugger"
   ```
2. Or create a symlink in a directory that's already in your PATH:
   ```bash
   sudo ln -s /path/to/smart-pandoc-debugger/smart-pandoc-debugger /usr/local/bin/
   ```

## 2. Miner Manager Implementation

### Implement `managers/miner_team/markdown_proofer.py`

Create the directory structure if it doesn't exist:

```bash
mkdir -p managers/miner_team
touch managers/miner_team/__init__.py
```

Create `managers/miner_team/markdown_proofer.py` with the following content:

```python
#!/usr/bin/env python3
# managers/miner_team/markdown_proofer.py - Markdown Proofreading Specialist
#
# This specialist checks Markdown content for common errors that would prevent
# successful conversion to TeX/PDF, such as:
# - Missing dollar signs for math expressions
# - Mismatched delimiters
# - Unbalanced braces
#
# It returns a list of ActionableLead objects for any issues found.

import os
import re
import logging
from typing import List, Optional

# Import SDE utilities
try:
    from utils.data_model import ActionableLead, SourceContextSnippet
except ImportError:
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from utils.data_model import ActionableLead, SourceContextSnippet

# Set up logging
logger = logging.getLogger(__name__)
DEBUG_ENV = os.environ.get("DEBUG", "false").lower()
LOG_LEVEL = logging.DEBUG if DEBUG_ENV == "true" else logging.INFO
logger.setLevel(LOG_LEVEL)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - MARKDOWN_PROOFER - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def run_markdown_checks(case_id: str, markdown_file_path: str, calling_manager_name: str = "Miner") -> List[ActionableLead]:
    """
    Analyze a Markdown file for common errors that would prevent successful conversion to TeX/PDF.
    
    Args:
        case_id: Unique identifier for the diagnostic job
        markdown_file_path: Path to the Markdown file to analyze
        calling_manager_name: Name of the manager calling this function (for ActionableLead.source_service)
        
    Returns:
        List of ActionableLead objects for any issues found
    """
    logger.info(f"[{case_id}] Starting Markdown proofing on {markdown_file_path}")
    
    # Read the Markdown file
    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except Exception as e:
        logger.error(f"[{case_id}] Failed to read Markdown file: {e}")
        return [ActionableLead(
            source_service=calling_manager_name,
            problem_description=f"Failed to read Markdown file: {e}",
            primary_context_snippets=[]
        )]
    
    # Initialize the list of leads
    leads: List[ActionableLead] = []
    
    # Check for common errors
    leads.extend(_check_missing_dollar_signs(case_id, markdown_content, calling_manager_name))
    leads.extend(_check_mismatched_delimiters(case_id, markdown_content, calling_manager_name))
    leads.extend(_check_unbalanced_braces(case_id, markdown_content, calling_manager_name))
    
    logger.info(f"[{case_id}] Markdown proofing complete. Found {len(leads)} issues.")
    return leads

def _check_missing_dollar_signs(case_id: str, markdown_content: str, calling_manager_name: str) -> List[ActionableLead]:
    """Check for potential math expressions without dollar signs."""
    leads = []
    
    # Simple pattern to detect potential math expressions without dollar signs
    # This is a basic heuristic and may have false positives/negatives
    math_patterns = [
        r'(?<!\$)(?<!\\)\b(sin|cos|tan|log|ln|exp|sqrt|frac|alpha|beta|gamma|delta|theta|lambda|pi|sigma|sum|int|lim)\b(?!\$)',
        r'(?<!\$)[a-zA-Z]\s*=\s*[a-zA-Z0-9](?!\$)',
        r'(?<!\$)[a-zA-Z]\s*\^\s*[a-zA-Z0-9](?!\$)',
        r'(?<!\$)[a-zA-Z]\s*_\s*[a-zA-Z0-9](?!\$)'
    ]
    
    for pattern in math_patterns:
        for match in re.finditer(pattern, markdown_content):
            start_pos = max(0, match.start() - 20)
            end_pos = min(len(markdown_content), match.end() + 20)
            context = markdown_content[start_pos:end_pos]
            
            # Get line number
            line_number = markdown_content[:match.start()].count('\n') + 1
            
            leads.append(ActionableLead(
                source_service=calling_manager_name,
                problem_description="Potential math expression without dollar signs",
                primary_context_snippets=[SourceContextSnippet(
                    source_document_type="markdown",
                    central_line_number=line_number,
                    snippet_text=context,
                    location_detail=f"Character position {match.start()}"
                )],
                internal_details_for_oracle={
                    "error_type": "MARKDOWN_MISSING_DOLLAR_SIGNS",
                    "match_text": match.group(0)
                }
            ))
    
    return leads

def _check_mismatched_delimiters(case_id: str, markdown_content: str, calling_manager_name: str) -> List[ActionableLead]:
    """Check for mismatched delimiters like \left( without \right), etc."""
    leads = []
    
    # Check for \left without matching \right
    left_pattern = r'\\left(\(|\[|\{|\|)'
    right_pattern = r'\\right(\)|\]|\}|\|)'
    
    left_matches = list(re.finditer(left_pattern, markdown_content))
    right_matches = list(re.finditer(right_pattern, markdown_content))
    
    if len(left_matches) != len(right_matches):
        # Simple heuristic: if counts don't match, there's likely a mismatch
        leads.append(ActionableLead(
            source_service=calling_manager_name,
            problem_description="Mismatched \\left and \\right delimiters",
            primary_context_snippets=[SourceContextSnippet(
                source_document_type="markdown",
                central_line_number=None,
                snippet_text=markdown_content[:200] + "..." if len(markdown_content) > 200 else markdown_content,
                location_detail="Found in document"
            )],
            internal_details_for_oracle={
                "error_type": "MARKDOWN_MISMATCHED_DELIMITERS",
                "left_count": len(left_matches),
                "right_count": len(right_matches)
            }
        ))
    
    return leads

def _check_unbalanced_braces(case_id: str, markdown_content: str, calling_manager_name: str) -> List[ActionableLead]:
    """Check for unbalanced braces in math environments."""
    leads = []
    
    # Extract math environments
    math_environments = []
    
    # Inline math $...$
    inline_math_pattern = r'\$(.*?)\$'
    math_environments.extend(re.findall(inline_math_pattern, markdown_content))
    
    # Display math $$...$$
    display_math_pattern = r'\$\$(.*?)\$\$'
    math_environments.extend(re.findall(display_math_pattern, markdown_content))
    
    for math_env in math_environments:
        # Check for balanced braces
        open_braces = math_env.count('{')
        close_braces = math_env.count('}')
        
        if open_braces != close_braces:
            # Find the line number
            math_start = markdown_content.find(math_env)
            line_number = markdown_content[:math_start].count('\n') + 1
            
            leads.append(ActionableLead(
                source_service=calling_manager_name,
                problem_description="Unbalanced braces in math environment",
                primary_context_snippets=[SourceContextSnippet(
                    source_document_type="markdown",
                    central_line_number=line_number,
                    snippet_text=math_env,
                    location_detail=f"Math environment at line {line_number}"
                )],
                internal_details_for_oracle={
                    "error_type": "MARKDOWN_UNBALANCED_BRACES",
                    "open_brace_count": open_braces,
                    "close_brace_count": close_braces
                }
            ))
    
    return leads

# For testing when run directly
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python markdown_proofer.py <markdown_file_path>")
        sys.exit(1)
    
    leads = run_markdown_checks("test_case", sys.argv[1])
    for lead in leads:
        print(f"Problem: {lead.problem_description}")
        for snippet in lead.primary_context_snippets:
            print(f"Line {snippet.central_line_number}: {snippet.snippet_text}")
        print()
```

### Implement `managers/miner_team/pandoc_tex_converter.py`

Create `managers/miner_team/pandoc_tex_converter.py` with the following content:

```python
#!/usr/bin/env python3
# managers/miner_team/pandoc_tex_converter.py - Pandoc-based MD-to-TeX Converter
#
# This specialist handles the conversion of Markdown to TeX using Pandoc.
# It returns a PandocConversionResult object with the results of the conversion.

import os
import subprocess
import logging
import pathlib
from typing import Optional, Dict, Any

# Import SDE utilities
try:
    from utils.data_model import ActionableLead, SourceContextSnippet, PandocConversionResult
except ImportError:
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from utils.data_model import ActionableLead, SourceContextSnippet, PandocConversionResult

# Set up logging
logger = logging.getLogger(__name__)
DEBUG_ENV = os.environ.get("DEBUG", "false").lower()
LOG_LEVEL = logging.DEBUG if DEBUG_ENV == "true" else logging.INFO
logger.setLevel(LOG_LEVEL)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - PANDOC_CONVERTER - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def convert_md_to_tex(
    case_id: str,
    markdown_file_path: pathlib.Path,
    output_tex_file_path: pathlib.Path,
    pandoc_options_override: Optional[Dict[str, Any]] = None
) -> PandocConversionResult:
    """
    Convert a Markdown file to TeX using Pandoc.
    
    Args:
        case_id: Unique identifier for the diagnostic job
        markdown_file_path: Path to the Markdown file to convert
        output_tex_file_path: Path where the generated TeX file should be written
        pandoc_options_override: Optional dictionary of Pandoc options to override defaults
        
    Returns:
        PandocConversionResult object with the results of the conversion
    """
    logger.info(f"[{case_id}] Starting Pandoc conversion: {markdown_file_path} -> {output_tex_file_path}")
    
    # Default Pandoc options
    pandoc_cmd = [
        "pandoc",
        "-f", "markdown-auto_identifiers",  # Input format with options to minimize problematic label/hypertarget generation
        "-t", "latex",                      # Output format
        "--standalone",                     # Generate a standalone document
        "-o", str(output_tex_file_path),    # Output file
        str(markdown_file_path)             # Input file
    ]
    
    # Apply any overrides
    if pandoc_options_override:
        # This is a simplified approach; a real implementation would need more sophisticated option handling
        for key, value in pandoc_options_override.items():
            if key.startswith("-"):
                pandoc_cmd.append(key)
                if value is not None:
                    pandoc_cmd.append(str(value))
            else:
                pandoc_cmd.append(f"--{key}")
                if value is not None:
                    pandoc_cmd.append(str(value))
    
    logger.debug(f"[{case_id}] Pandoc command: {' '.join(pandoc_cmd)}")
    
    try:
        # Run Pandoc
        process = subprocess.run(
            pandoc_cmd,
            capture_output=True,
            text=True,
            check=False,  # Don't raise an exception on non-zero exit code
            timeout=30    # Timeout after 30 seconds
        )
        
        # Combine stdout and stderr for the log
        pandoc_log = f"STDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"
        
        # Check if Pandoc succeeded
        if process.returncode != 0:
            logger.warning(f"[{case_id}] Pandoc failed with return code {process.returncode}")
            
            # Create an ActionableLead for the failure
            lead = ActionableLead(
                source_service="Miner",
                problem_description=f"Pandoc failed to convert Markdown to TeX (return code {process.returncode})",
                primary_context_snippets=[SourceContextSnippet(
                    source_document_type="md_to_tex_log",
                    central_line_number=None,
                    snippet_text=pandoc_log,
                    location_detail="Pandoc error output"
                )],
                internal_details_for_oracle={
                    "error_type": "PANDOC_CONVERSION_FAILED",
                    "return_code": process.returncode,
                    "tool_responsible": "pandoc",
                    "stage_of_failure": "md-to-tex"
                }
            )
            
            # Check if the output file was created despite the error
            generated_tex_content = None
            if output_tex_file_path.exists():
                try:
                    generated_tex_content = output_tex_file_path.read_text(encoding="utf-8")
                except Exception as e:
                    logger.error(f"[{case_id}] Failed to read generated TeX file: {e}")
            
            return PandocConversionResult(
                conversion_successful=False,
                generated_tex_content=generated_tex_content,
                pandoc_raw_log=pandoc_log,
                actionable_lead=lead
            )
        
        # Pandoc succeeded, read the generated TeX file
        try:
            generated_tex_content = output_tex_file_path.read_text(encoding="utf-8")
            
            # Basic validation: check if the TeX file contains \documentclass
            if "\\documentclass" not in generated_tex_content:
                logger.warning(f"[{case_id}] Generated TeX file does not contain \\documentclass")
                
                lead = ActionableLead(
                    source_service="Miner",
                    problem_description="Pandoc generated an invalid TeX file (missing \\documentclass)",
                    primary_context_snippets=[SourceContextSnippet(
                        source_document_type="generated_tex_partial_or_invalid",
                        central_line_number=None,
                        snippet_text=generated_tex_content[:200] + "..." if len(generated_tex_content) > 200 else generated_tex_content,
                        location_detail="Beginning of generated TeX"
                    )],
                    internal_details_for_oracle={
                        "error_type": "PANDOC_GENERATED_INVALID_TEX",
                        "tool_responsible": "pandoc",
                        "stage_of_failure": "md-to-tex-validation"
                    }
                )
                
                return PandocConversionResult(
                    conversion_successful=False,
                    generated_tex_content=generated_tex_content,
                    pandoc_raw_log=pandoc_log,
                    actionable_lead=lead
                )
            
            logger.info(f"[{case_id}] Pandoc conversion successful")
            return PandocConversionResult(
                conversion_successful=True,
                generated_tex_content=generated_tex_content,
                pandoc_raw_log=pandoc_log,
                actionable_lead=None
            )
            
        except Exception as e:
            logger.error(f"[{case_id}] Failed to read generated TeX file: {e}")
            
            lead = ActionableLead(
                source_service="Miner",
                problem_description=f"Failed to read generated TeX file: {e}",
                primary_context_snippets=[SourceContextSnippet(
                    source_document_type="md_to_tex_log",
                    central_line_number=None,
                    snippet_text=pandoc_log,
                    location_detail="Pandoc output"
                )],
                internal_details_for_oracle={
                    "error_type": "TEX_FILE_READ_ERROR",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    "tool_responsible": "pandoc_tex_converter",
                    "stage_of_failure": "post-pandoc-file-read"
                }
            )
            
            return PandocConversionResult(
                conversion_successful=False,
                generated_tex_content=None,
                pandoc_raw_log=pandoc_log,
                actionable_lead=lead
            )
            
    except subprocess.TimeoutExpired as e:
        logger.error(f"[{case_id}] Pandoc timed out after {e.timeout} seconds")
        
        lead = ActionableLead(
            source_service="Miner",
            problem_description=f"Pandoc timed out after {e.timeout} seconds",
            primary_context_snippets=[],
            internal_details_for_oracle={
                "error_type": "PANDOC_TIMEOUT",
                "timeout_seconds": e.timeout,
                "tool_responsible": "pandoc",
                "stage_of_failure": "md-to-tex"
            }
        )
        
        return PandocConversionResult(
            conversion_successful=False,
            generated_tex_content=None,
            pandoc_raw_log=f"TIMEOUT: Pandoc process timed out after {e.timeout} seconds",
            actionable_lead=lead
        )
        
    except FileNotFoundError as e:
        logger.error(f"[{case_id}] Pandoc executable not found: {e}")
        
        lead = ActionableLead(
            source_service="Miner",
            problem_description="Pandoc executable not found. Please ensure Pandoc is installed and in your PATH.",
            primary_context_snippets=[],
            internal_details_for_oracle={
                "error_type": "PANDOC_NOT_FOUND",
                "missing_command": "pandoc",
                "tool_responsible": "pandoc",
                "stage_of_failure": "md-to-tex"
            }
        )
        
        return PandocConversionResult(
            conversion_successful=False,
            generated_tex_content=None,
            pandoc_raw_log="ERROR: Pandoc executable not found",
            actionable_lead=lead
        )
        
    except Exception as e:
        logger.error(f"[{case_id}] Unexpected error running Pandoc: {e}")
        
        lead = ActionableLead(
            source_service="Miner",
            problem_description=f"Unexpected error running Pandoc: {type(e).__name__}: {e}",
            primary_context_snippets=[],
            internal_details_for_oracle={
                "error_type": "PANDOC_UNEXPECTED_ERROR",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "tool_responsible": "pandoc",
                "stage_of_failure": "md-to-tex"
            }
        )
        
        return PandocConversionResult(
            conversion_successful=False,
            generated_tex_content=None,
            pandoc_raw_log=f"ERROR: Unexpected error running Pandoc: {type(e).__name__}: {e}",
            actionable_lead=lead
        )

# For testing when run directly
if __name__ == "__main__":
    import sys
    import tempfile
    
    if len(sys.argv) < 2:
        print("Usage: python pandoc_tex_converter.py <markdown_file_path>")
        sys.exit(1)
    
    md_path = pathlib.Path(sys.argv[1])
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = pathlib.Path(temp_dir) / "output.tex"
        result = convert_md_to_tex("test_case", md_path, tex_path)
        
        print(f"Conversion successful: {result.conversion_successful}")
        if result.actionable_lead:
            print(f"Problem: {result.actionable_lead.problem_description}")
        if result.generated_tex_content:
            print(f"Generated TeX (first 200 chars): {result.generated_tex_content[:200]}...")
        print(f"Pandoc log: {result.pandoc_raw_log}")
```

### Implement `managers/miner_team/tex_compiler.py`

Create `managers/miner_team/tex_compiler.py` with the following content:

```python
#!/usr/bin/env python3
# managers/miner_team/tex_compiler.py - TeX-to-PDF Compiler Specialist
#
# This specialist handles the compilation of TeX to PDF using pdflatex.
# It returns a TexCompilationResult object with the results of the compilation.

import os
import subprocess
import logging
import pathlib
import re
from typing import Optional, List, Dict, Any

# Import SDE utilities
try:
    from utils.data_model import ActionableLead, SourceContextSnippet, TexCompilationResult
except ImportError:
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from utils.data_model import ActionableLead, SourceContextSnippet, TexCompilationResult

# Set up logging
logger = logging.getLogger(__name__)
DEBUG_ENV = os.environ.get("DEBUG", "false").lower()
LOG_LEVEL = logging.DEBUG if DEBUG_ENV == "true" else logging.INFO
logger.setLevel(LOG_LEVEL)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - TEX_COMPILER - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def compile_tex_to_pdf(
    case_id: str,
    tex_file_path: pathlib.Path,
    output_directory: pathlib.Path,
    pdflatex_options: Optional[List[str]] = None,
    max_runs: int = 2
) -> TexCompilationResult:
    """
    Compile a TeX file to PDF using pdflatex.
    
    Args:
        case_id: Unique identifier for the diagnostic job
        tex_file_path: Path to the TeX file to compile
        output_directory: Directory where the PDF and auxiliary files should be written
        pdflatex_options: Optional list of additional pdflatex command-line options
        max_runs: Maximum number of pdflatex runs to perform (for resolving references)
        
    Returns:
        TexCompilationResult object with the results of the compilation
    """
    logger.info(f"[{case_id}] Starting TeX compilation: {tex_file_path}")
    
    # Ensure the output directory exists
    output_directory.mkdir(parents=True, exist_ok=True)
    
    # Get the base name of the TeX file (without extension)
    tex_base_name = tex_file_path.stem
    
    # Expected paths for output files
    log_file_path = output_directory / f"{tex_base_name}.log"
    pdf_file_path = output_directory / f"{tex_base_name}.pdf"
    
    # Default pdflatex command
    pdflatex_cmd = [
        "pdflatex",
        "-interaction=nonstopmode",  # Don't stop on errors
        "-file-line-error",          # Show file and line info for errors
        f"-output-directory={output_directory}",
        tex_file_path
    ]
    
    # Add any additional options
    if pdflatex_options:
        pdflatex_cmd.extend(pdflatex_options)
    
    logger.debug(f"[{case_id}] pdflatex command: {' '.join(map(str, pdflatex_cmd))}")
    
    try:
        # Run pdflatex multiple times to resolve references
        full_log = ""
        for run in range(1, max_runs + 1):
            logger.info(f"[{case_id}] pdflatex run {run}/{max_runs}")
            
            process = subprocess.run(
                pdflatex_cmd,
                capture_output=True,
                text=True,
                check=False,  # Don't raise an exception on non-zero exit code
                timeout=60     # Timeout after 60 seconds
            )
            
            # Append to the full log
            full_log += f"\n--- PDFLATEX RUN {run}/{max_runs} ---\n"
            full_log += f"STDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}\n"
            
            # Check if pdflatex succeeded
            if process.returncode != 0:
                logger.warning(f"[{case_id}] pdflatex run {run} failed with return code {process.returncode}")
                
                # Try to read the log file if it exists
                log_content = None
                if log_file_path.exists():
                    try:
                        log_content = log_file_path.read_text(encoding="utf-8")
                        full_log += f"\n--- LOG FILE CONTENT ---\n{log_content}\n"
                    except Exception as e:
                        logger.error(f"[{case_id}] Failed to read log file: {e}")
                
                # Create an ActionableLead for the failure
                lead = ActionableLead(
                    source_service="Miner",
                    problem_description=f"pdflatex failed with return code {process.returncode}",
                    primary_context_snippets=[SourceContextSnippet(
                        source_document_type="tex_compilation_log",
                        central_line_number=None,
                        snippet_text=full_log,
                        location_detail="pdflatex error output"
                    )],
                    internal_details_for_oracle={
                        "error_type": "PDFLATEX_COMPILATION_FAILED",
                        "return_code": process.returncode,
                        "tool_responsible": "pdflatex",
                        "stage_of_failure": "tex-to-pdf",
                        "run_number": run
                    }
                )
                
                return TexCompilationResult(
                    compilation_successful=False,
                    pdf_file_path=None,
                    tex_compiler_raw_log=full_log,
                    actionable_lead=lead
                )
            
            # Check if we need another run
            if run < max_runs:
                # Simple heuristic: check if the log contains "Rerun" messages
                if log_file_path.exists():
                    try:
                        log_content = log_file_path.read_text(encoding="utf-8")
                        if not re.search(r"Rerun to get (cross-references|citations) right", log_content):
                            logger.info(f"[{case_id}] No need for additional pdflatex runs")
                            break
                    except Exception as e:
                        logger.error(f"[{case_id}] Failed to read log file: {e}")
        
        # Final check: does the PDF exist and is it non-empty?
        if not pdf_file_path.exists() or pdf_file_path.stat().st_size == 0:
            logger.warning(f"[{case_id}] PDF file not created or empty: {pdf_file_path}")
            
            # Try to read the log file if it exists
            log_content = None
            if log_file_path.exists():
                try:
                    log_content = log_file_path.read_text(encoding="utf-8")
                    full_log += f"\n--- FINAL LOG FILE CONTENT ---\n{log_content}\n"
                except Exception as e:
                    logger.error(f"[{case_id}] Failed to read log file: {e}")
            
            lead = ActionableLead(
                source_service="Miner",
                problem_description="pdflatex did not create a valid PDF file",
                primary_context_snippets=[SourceContextSnippet(
                    source_document_type="tex_compilation_log",
                    central_line_number=None,
                    snippet_text=full_log,
                    location_detail="pdflatex output"
                )],
                internal_details_for_oracle={
                    "error_type": "PDFLATEX_NO_PDF_CREATED",
                    "tool_responsible": "pdflatex",
                    "stage_of_failure": "tex-to-pdf-validation"
                }
            )
            
            return TexCompilationResult(
                compilation_successful=False,
                pdf_file_path=None,
                tex_compiler_raw_log=full_log,
                actionable_lead=lead
            )
        
        # Read the final log file
        log_content = None
        if log_file_path.exists():
            try:
                log_content = log_file_path.read_text(encoding="utf-8")
                full_log += f"\n--- FINAL LOG FILE CONTENT ---\n{log_content}\n"
            except Exception as e:
                logger.error(f"[{case_id}] Failed to read log file: {e}")
        
        logger.info(f"[{case_id}] TeX compilation successful: {pdf_file_path}")
        return TexCompilationResult(
            compilation_successful=True,
            pdf_file_path=pdf_file_path,
            tex_compiler_raw_log=full_log,
            actionable_lead=None
        )
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"[{case_id}] pdflatex timed out after {e.timeout} seconds")
        
        lead = ActionableLead(
            source_service="Miner",
            problem_description=f"pdflatex timed out after {e.timeout} seconds",
            primary_context_snippets=[],
            internal_details_for_oracle={
                "error_type": "PDFLATEX_TIMEOUT",
                "timeout_seconds": e.timeout,
                "tool_responsible": "pdflatex",
                "stage_of_failure": "tex-to-pdf"
            }
        )
        
        return TexCompilationResult(
            compilation_successful=False,
            pdf_file_path=None,
            tex_compiler_raw_log=f"TIMEOUT: pdflatex process timed out after {e.timeout} seconds",
            actionable_lead=lead
        )
        
    except FileNotFoundError as e:
        logger.error(f"[{case_id}] pdflatex executable not found: {e}")
        
        lead = ActionableLead(
            source_service="Miner",
            problem_description="pdflatex executable not found. Please ensure pdflatex is installed and in your PATH.",
            primary_context_snippets=[],
            internal_details_for_oracle={
                "error_type": "PDFLATEX_NOT_FOUND",
                "missing_command": "pdflatex",
                "tool_responsible": "pdflatex",
                "stage_of_failure": "tex-to-pdf"
            }
        )
        
        return TexCompilationResult(
            compilation_successful=False,
            pdf_file_path=None,
            tex_compiler_raw_log="ERROR: pdflatex executable not found",
            actionable_lead=lead
        )
        
    except Exception as e:
        logger.error(f"[{case_id}] Unexpected error running pdflatex: {e}")
        
        lead = ActionableLead(
            source_service="Miner",
            problem_description=f"Unexpected error running pdflatex: {type(e).__name__}: {e}",
            primary_context_snippets=[],
            internal_details_for_oracle={
                "error_type": "PDFLATEX_UNEXPECTED_ERROR",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "tool_responsible": "pdflatex",
                "stage_of_failure": "tex-to-pdf"
            }
        )
        
        return TexCompilationResult(
            compilation_successful=False,
            pdf_file_path=None,
            tex_compiler_raw_log=f"ERROR: Unexpected error running pdflatex: {type(e).__name__}: {e}",
            actionable_lead=lead
        )

# For testing when run directly
if __name__ == "__main__":
    import sys
    import tempfile
    
    if len(sys.argv) < 2:
        print("Usage: python tex_compiler.py <tex_file_path>")
        sys.exit(1)
    
    tex_path = pathlib.Path(sys.argv[1])
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = pathlib.Path(temp_dir)
        result = compile_tex_to_pdf("test_case", tex_path, output_dir)
        
        print(f"Compilation successful: {result.compilation_successful}")
        if result.actionable_lead:
            print(f"Problem: {result.actionable_lead.problem_description}")
        if result.pdf_file_path:
            print(f"Generated PDF: {result.pdf_file_path}")
        print(f"Log (first 200 chars): {result.tex_compiler_raw_log[:200]}...")
```

## 3. Investigator Manager Implementation

### Move and enhance `error_finder.py`

First, create the investigator-team directory:

```bash
mkdir -p managers/investigator-team
touch managers/investigator-team/__init__.py
```

Then, copy and enhance the error_finder.py file:

```bash
cp /workspace/smart-pandoc-debugger/DEBUG_error_finder/error_finder.py /workspace/smart-pandoc-debugger/managers/investigator-team/
```

Edit the file to enhance its error detection capabilities. The key enhancements should include:

1. Better detection of "Undefined control sequence" errors
2. Detection of "Missing dollar sign" errors
3. Detection of "Mismatched delimiters" errors
4. Detection of "Unbalanced braces" errors
5. Detection of "Runaway argument" errors
6. Detection of "Undefined environment" errors

## 4. Oracle Manager Implementation

The Oracle Manager should be enhanced to provide specific, helpful remedies for common error types. The implementation should focus on direct error detection as specified in HACKATHON.md.

## 5. Reporter Manager Implementation

The Reporter Manager should be enhanced to generate clear, actionable reports that include relevant context from the original Markdown document and provide clear instructions for fixing the identified issues.

## Testing Strategy

1. Create a shell script to run the tests
2. Test each component individually
3. Test the entire pipeline with various error scenarios
4. Ensure no regressions in existing functionality