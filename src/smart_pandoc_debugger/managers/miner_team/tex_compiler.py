#!/usr/bin/env python3
# managers/miner-team/tex_compiler.py
"""
TeX-to-PDF Compiler - Specialist for Miner Manager (V1.0)

This module is responsible for compiling a TeX file to PDF using pdflatex.
It handles multiple pdflatex runs, captures the compilation log, and reports
on success or failure. It does not parse TeX errors from the log; that is
left to the Investigator manager.

Designed to be imported and used by Miner.py.
Assumes it runs within a Python process where `utils` package is on PYTHONPATH.
Fails violently for critical setup issues (e.g., pdflatex not found, utils not importable).
"""

import sys
import os
import logging
import pathlib
import subprocess
import shutil
from typing import List, Optional, Union, NamedTuple

# SDE utilities (expected to be on PYTHONPATH)
from utils.process_runner import run_script

# Define result type locally instead of importing from a central model
TexCompilationResult = NamedTuple("TexCompilationResult", [
    ("compilation_successful", bool),
    ("pdf_file_path", Optional[pathlib.Path]),
    ("tex_compiler_raw_log", Optional[str])
])

logger = logging.getLogger(__name__)
if not logger.handlers: # Basic config if not already configured by a parent
    LOG_LEVEL_TC = logging.DEBUG if os.environ.get("DEBUG", "false").lower() == "true" else logging.INFO
    handler_tc = logging.StreamHandler(sys.stderr)
    formatter_tc = logging.Formatter('%(asctime)s - TEX_COMPILER (%(name)s) - %(levelname)s - %(message)s')
    handler_tc.setFormatter(formatter_tc)
    logger.addHandler(handler_tc)
    logger.setLevel(LOG_LEVEL_TC)
    logger.propagate = False

# Constants
PDFLATEX_DEFAULT_CMD = "pdflatex"
MAX_COMPILER_RUNS = 3
ROBUST_HEADER_TEMPLATE_FNAME = "robust_header.tex"


def compile_tex_to_pdf(
    tex_file_path: pathlib.Path,
    output_directory: pathlib.Path,
    template_dir: pathlib.Path
) -> TexCompilationResult:
    """
    Compiles a .tex file to a .pdf using pdflatex.
    """
    logger.debug(f"Initiating TeX compilation for '{tex_file_path}' in '{output_directory}'")

    if not tex_file_path.is_file():
        raise FileNotFoundError(f"Input TeX file does not exist: {tex_file_path}")
    if not output_directory.is_dir():
        raise FileNotFoundError(f"Output directory does not exist: {output_directory}")

    header_template_path = template_dir / ROBUST_HEADER_TEMPLATE_FNAME
    if not header_template_path.is_file():
        raise FileNotFoundError(f"Robust header template not found at: {header_template_path}")

    target_header_path = output_directory / ROBUST_HEADER_TEMPLATE_FNAME
    try:
        shutil.copy(header_template_path, target_header_path)
        logger.debug(f"Copied robust header to '{target_header_path}'")

        log_content = ""
        compilation_successful = False

        for i in range(MAX_COMPILER_RUNS):
            run_number = i + 1
            logger.info(f"Starting pdflatex run #{run_number}/{MAX_COMPILER_RUNS} for '{tex_file_path.name}'...")
            try:
                proc = run_script(
                    [
                        PDFLATEX_DEFAULT_CMD,
                        "-interaction=nonstopmode",
                        f"-output-directory={str(output_directory)}",
                        str(tex_file_path)
                    ],
                    log_prefix_for_caller="TexCompilerSpecialist"
                )
                assert isinstance(proc, subprocess.CompletedProcess)
                
                if run_number == MAX_COMPILER_RUNS:
                    logger.info("Final pdflatex run SUCCEEDED.")
                    compilation_successful = True
                    break 

            except subprocess.CalledProcessError as e:
                logger.warning(f"pdflatex run #{run_number} FAILED with exit code {e.returncode}.")
                compilation_successful = False
                break 
        
    finally:
        if 'target_header_path' in locals() and target_header_path.exists():
            logger.debug(f"Cleaning up temporary header file: '{target_header_path}'")
            target_header_path.unlink()

    pdf_path = output_directory / f"{tex_file_path.stem}.pdf"
    log_path = output_directory / f"{tex_file_path.stem}.log"

    if log_path.exists():
        log_content = log_path.read_text(encoding='utf-8', errors='ignore')

    if compilation_successful and (not pdf_path.exists() or pdf_path.stat().st_size == 0):
        logger.error(f"Compilation reported successful, but output PDF is missing or empty: '{pdf_path}'")
        compilation_successful = False

    return TexCompilationResult(
        compilation_successful=compilation_successful,
        pdf_file_path=pdf_path if compilation_successful else None,
        tex_compiler_raw_log=log_content
    )

# No __main__ block for specialists.
