#!/usr/bin/env python3
# managers/miner-team/pandoc_tex_converter.py
"""
Pandoc Markdown-to-TeX Converter - Specialist for Miner Manager (V2.0)

This module converts a Markdown file to TeX using Pandoc. For debugging purposes,
it attempts to generate simpler TeX by disabling automatic section identifiers,
which can be a source of "Undefined control sequence" errors in pdflatex.
It validates the structural integrity of the generated TeX file (e.g., presence of
`\documentclass`) and reports success or failure along with relevant outputs and
potential ActionableLeads.

Designed to be imported and used by Miner.py.
Assumes it runs within a Python process where `utils` package is on PYTHONPATH.
Fails violently for critical setup issues (e.g., Pandoc not found, utils not importable).
"""

import logging
import pathlib
import subprocess
from typing import List, Optional, NamedTuple

# SDE utilities (expected to be on PYTHONPATH)
from utils.process_runner import run_script

# Define result type locally instead of importing from a central model
PandocConversionResult = NamedTuple("PandocConversionResult", [
    ("conversion_successful", bool),
    ("output_tex_file_path", Optional[pathlib.Path]),
    ("generated_tex_content", Optional[str]),
    ("pandoc_raw_log", Optional[str])
])

logger = logging.getLogger(__name__)

PANDOC_CMD = "pandoc"

def convert_md_to_tex(
    md_file_path: pathlib.Path,
    output_directory: pathlib.Path,
    template_dir: pathlib.Path # Not used by pandoc, but kept for API consistency
) -> PandocConversionResult:
    """
    Converts a Markdown file to a TeX file using Pandoc.
    """
    logger.debug(f"Initiating MD-to-TeX conversion for '{md_file_path}'")

    if not md_file_path.is_file():
        raise FileNotFoundError(f"Input Markdown file does not exist: {md_file_path}")
    if not output_directory.is_dir():
        raise FileNotFoundError(f"Output directory does not exist: {output_directory}")

    output_tex_path = output_directory / f"{md_file_path.stem}.tex"
    
    # This format string aims for maximum compatibility and raw LaTeX passthrough.
    pandoc_format_string = "markdown-auto_identifiers+raw_tex+tex_math_dollars+implicit_figures"

    command = [
        PANDOC_CMD,
        "-f", pandoc_format_string,
        "-t", "latex",
        "--standalone",
        str(md_file_path),
        "-o",
        str(output_tex_path)
    ]

    try:
        proc = run_script(
            command,
            log_prefix_for_caller="PandocTexConverter"
        )
        assert isinstance(proc, subprocess.CompletedProcess), "run_script should return CompletedProcess here."
        
        generated_tex_content = output_tex_path.read_text(encoding='utf-8')
        
        if "\\documentclass" not in generated_tex_content[:500]:
             logger.warning(f"Pandoc conversion seemed to succeed, but output TeX may be invalid (missing \\documentclass).")
             return PandocConversionResult(
                 conversion_successful=False,
                 output_tex_file_path=output_tex_path,
                 generated_tex_content=generated_tex_content,
                 pandoc_raw_log=proc.stderr
             )

        logger.info(f"Pandoc conversion successful for '{md_file_path.name}'.")
        return PandocConversionResult(
            conversion_successful=True,
            output_tex_file_path=output_tex_path,
            generated_tex_content=generated_tex_content,
            pandoc_raw_log=proc.stderr
        )

    except subprocess.CalledProcessError as e:
        logger.warning(f"Pandoc command FAILED with exit code {e.returncode}.")
        return PandocConversionResult(
            conversion_successful=False,
            output_tex_file_path=None,
            generated_tex_content=None,
            pandoc_raw_log=e.stderr
        )
    except FileNotFoundError:
        logger.error(f"CRITICAL: '{PANDOC_CMD}' command not found. Is Pandoc installed and in the system's PATH?")
        return PandocConversionResult(
            conversion_successful=False,
            output_tex_file_path=None,
            generated_tex_content=None,
            pandoc_raw_log=f"'{PANDOC_CMD}' not found. Check Pandoc installation."
        )

# No __main__ block for specialists. They are modules to be called.
