#!/usr/bin/env python3
# Miner.py - SDE V6.0: Adheres to the Pipe-Script Contract
#
# Role:
#   - First-line manager in the SDE pipeline.
#   - Orchestrates markdown-to-tex conversion and tex-to-pdf compilation.
#   - Determines if a job can proceed to the Oracle for deep analysis.
#
# Contract:
#   - Receives a DiagnosticJob via stdin.
#   - Returns the updated DiagnosticJob via stdout.
#   - Uses PipelineStatus to report outcomes.
#   - All logs/errors to stderr.

import pathlib
import sys
import traceback

# Use absolute imports from the project root, set on PYTHONPATH by the runner.
from utils.data_model import DiagnosticJob, PipelineStatus
from utils.logger_utils import logger
from utils.base_cli_manager import run_manager_script
from managers.miner_team import pandoc_tex_converter, tex_compiler

def process_miner_job(job: DiagnosticJob) -> DiagnosticJob:
    """
    Orchestrates the mining process: MD->TeX conversion and TeX->PDF compilation.
    This is the core logic function for the Miner manager.
    """
    job.log_message("Miner processing started.")
    
    # WARNING: This script makes a critical assumption based on the "Pipe-Script
    # Contract" defined in managers/README.md. It assumes that the job's
    # working directory IS the parent directory of the original markdown file.
    # This convention is established by intake.py creating a temp directory
    # and putting the 'input.md' inside it. If this changes, the Miner
    # will break.
    markdown_path = pathlib.Path(job.original_markdown_path)
    work_dir = markdown_path.parent
    work_dir.mkdir(exist_ok=True) # Ensure it exists

    # The template directory is relative to this manager's location.
    template_dir = pathlib.Path(__file__).parent / "miner_team" / "templates"

    # --- Step 1: Convert Markdown to TeX ---
    job.log_message("Miner: Attempting Pandoc conversion.")
    try:
        pandoc_result = pandoc_tex_converter.convert_md_to_tex(
            md_file_path=markdown_path,
            output_directory=work_dir,
            template_dir=template_dir
        )
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"Miner: Unhandled exception during Pandoc conversion: {e}\n{tb_str}")
        job.log_message(f"FATAL: Pandoc specialist crashed: {e}\n{tb_str}")
        job.status = PipelineStatus.MINER_FAILURE_PANDOC
        return job

    if not pandoc_result.conversion_successful:
        job.log_message("Miner: Pandoc conversion failed. Halting pipeline for this job.")
        job.status = PipelineStatus.MINER_FAILURE_PANDOC
        if pandoc_result.pandoc_raw_log:
            log_path = work_dir / "pandoc_error.log"
            log_path.write_text(pandoc_result.pandoc_raw_log)
        return job

    # If conversion was successful, we MUST have a TeX file path.
    tex_file_path = pandoc_result.output_tex_file_path
    if not tex_file_path:
        error_msg = "Miner: Pandoc specialist reported success but returned no TeX file path. Critical error."
        logger.error(error_msg)
        job.log_message(f"FATAL: {error_msg}")
        job.status = PipelineStatus.MINER_FAILURE_PANDOC
        return job

    # Conversion was successful, record the artifacts
    job.generated_tex_path = str(tex_file_path)
    job.log_message(f"Miner: Pandoc conversion successful. TeX file at: {job.generated_tex_path}")
    
    # --- Step 2: Compile TeX to PDF ---
    job.log_message("Miner: Attempting TeX compilation.")
    try:
        compilation_result = tex_compiler.compile_tex_to_pdf(
            tex_file_path=tex_file_path, # Now we know this is not None
            output_directory=work_dir,
            template_dir=template_dir
        )
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"Miner: Unhandled exception during TeX compilation: {e}\n{tb_str}")
        job.log_message(f"FATAL: TeX compiler specialist crashed: {e}\n{tb_str}")
        job.status = PipelineStatus.MINER_SUCCESS_GATHERED_TEX_LOGS
        log_path = work_dir / f"{markdown_path.stem}.log"
        if log_path.exists():
            job.tex_compilation_log_path = str(log_path)
        return job

    # TeX compilation is *expected* to fail for this tool's purpose.
    # We just need to have gathered the logs.
    if compilation_result.tex_compiler_raw_log:
        log_path = work_dir / f"{markdown_path.stem}.log"
        log_path.write_text(compilation_result.tex_compiler_raw_log, encoding='utf-8', errors='ignore')
        job.tex_compilation_log_path = str(log_path)
    
    job.log_message("Miner: TeX compilation finished. Handing off to Oracle.")
    job.status = PipelineStatus.MINER_SUCCESS_GATHERED_TEX_LOGS
    
    synctex_path = work_dir / f"{markdown_path.stem}.synctex.gz"
    if synctex_path.exists():
        job.synctex_path = str(synctex_path)

    return job

if __name__ == '__main__':
    run_manager_script(process_miner_job)
