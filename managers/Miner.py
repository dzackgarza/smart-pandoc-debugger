#!/usr/bin/env python3
# Miner.py - SDE V5.1.5: Orchestrator for MD Proofing & Conversion/Compilation Specialists
#
# Version: 1.1.0 (Delegates MD-to-TeX and TeX-to-PDF to specialist modules)
# Date: 2025-06-25 (Updated)
# Author: Diagnostic Systems Group
#
# Role (Expanded for SDE V5.1.5):
#   - Primary Manager in the SDE pipeline, called by `coordinator.py`.
#   - Receives a `DiagnosticJob` Pydantic model instance via `utils.manager_runner.py`.
#   - Responsibilities (Assertion-Driven: Assumes valid inputs from runner):
#       0. Markdown Proofreading:
#          - Delegates to `managers.miner_team.markdown_proofer.run_markdown_checks`.
#          - If errors, populates `DiagnosticJob` and returns early.
#       1. MD-to-TeX Conversion (if MD proofing passes):
#          - Delegates to `managers.miner_team.pandoc_tex_converter.convert_md_to_tex`.
#          - Updates `DiagnosticJob` based on the specialist's result.
#          - If failed, populates `DiagnosticJob` and returns early.
#       2. TeX-to-PDF Compilation (if MD-to-TeX succeeds):
#          - Delegates to `managers.miner_team.tex_compiler.compile_tex_to_pdf`.
#          - Updates `DiagnosticJob` based on the specialist's result.
#   - Returns the updated `DiagnosticJob` model instance.
#   - FAILS VIOLENTLY for unhandled Python errors from specialists or unmet assertions.
#     Catches specific operational errors (Tool not found, Timeout) from specialists to create leads.
#   - RETAINS TEMPORARY FILES INDEFINITELY (created by Miner itself for MD file).
#     Specialists manage their own temporary files if any beyond what Miner provides.
#
# Interface (as called by `manager_runner.py`):
#   - Input: `DiagnosticJob` Pydantic model.
#   - Output: Updated `DiagnosticJob` Pydantic model.
#   - Standard CLI: Expects `--process-job` flag.
#
# Environment Assumptions (Asserted or will cause failure if unmet):
#   - `pandoc` and `pdflatex` are in PATH (checked by specialists).
#   - All SDE utility and team modules are importable.
# --------------------------------------------------------------------------------

import sys
import os
import json
import logging
import argparse
import tempfile
import pathlib
import subprocess # For specific exception types from specialists
from typing import List, Optional, Dict, Any # Keep for type hinting

# SDE utilities and Miner team specialists
from utils.data_model import DiagnosticJob, ActionableLead, SourceContextSnippet # type: ignore
from managers.miner_team.markdown_proofer import run_markdown_checks # type: ignore
from managers.miner_team.pandoc_tex_converter import convert_md_to_tex, PandocConversionResult # type: ignore
from managers.miner_team.tex_compiler import compile_tex_to_pdf, TexCompilationResult # type: ignore

# --- Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    DEBUG_ENV_MINER = os.environ.get("DEBUG", "false").lower()
    MINER_LOG_LEVEL = logging.DEBUG if DEBUG_ENV_MINER == "true" else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(asctime)s - MINER (%(name)s) - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(MINER_LOG_LEVEL)
    logger.propagate = False

# --- Outcome Constants ---
OUTCOME_MD_PROOFING_FAILED = "MarkdownError_ProofingLeadsProvided"
OUTCOME_MD_TO_TEX_CONVERSION_FAILED = "MarkdownError_MdToTexConversionFailed"
OUTCOME_SUCCESS_PDF_VALID = "CompilationSuccess_PDFShouldBeValid"
OUTCOME_MD_TO_TEX_SUCCESS_PROCEED_TO_TEX_COMPILE = "MDtoTeX_Success_ProceedToTeXCompile"
OUTCOME_TEX_COMPILATION_FAILED_FOR_INVESTIGATION = "TexCompilationError_LeadsPendingInvestigation"
OUTCOME_MINER_INFRASTRUCTURE_ERROR = "MinerInfrastructureError" # For Miner's own setup like tempdir
# Specific timeout/tool error outcomes for leads created by Miner when specialists raise these
OUTCOME_MINER_PANDOC_TOOL_ERROR = "Miner_PandocToolError" # e.g. Pandoc not found or timed out
OUTCOME_MINER_PDFLATEX_TOOL_ERROR = "Miner_PdflatexToolError" # e.g. pdflatex not found or timed out
OUTCOME_MINER_UNEXPECTED_CRITICAL_ERROR = "MinerUnexpectedCriticalError"
OUTCOME_MINER_CRASHED_IN_MAIN_LOGIC = "MinerCrashedInMainLogic"


def _create_miner_level_tool_failure_lead( # For when specialists raise FileNotFoundError/Timeout
    problem_description: str,
    source_component_tool: str, # e.g., "pandoc_tex_converter", "tex_compiler"
    stage: str, # e.g., "md-to-tex_specialist_call", "tex-to-pdf_specialist_call"
    exception_obj: Exception
) -> ActionableLead:
    """Helper to create ActionableLead when a specialist call results in critical tool error."""
    details = {
        "error_type": type(exception_obj).__name__,
        "exception_str": str(exception_obj)
    }
    if isinstance(exception_obj, FileNotFoundError):
        details["missing_command"] = exception_obj.filename
    elif isinstance(exception_obj, subprocess.TimeoutExpired):
        details["timeout_seconds"] = exception_obj.timeout
        details["command_hint"] = str(exception_obj.cmd)

    return ActionableLead(
        source_service="Miner", 
        problem_description=problem_description,
        primary_context_snippets=[],
        internal_details_for_oracle={
            "tool_responsible": source_component_tool, # The specialist that failed
            "stage_of_failure": stage,
            **details # Merge specific exception details
        }
    )

def process_job(diagnostic_job_model: DiagnosticJob) -> DiagnosticJob:
    assert isinstance(diagnostic_job_model, DiagnosticJob), "Input must be a DiagnosticJob Pydantic model."
    dj = diagnostic_job_model
    case_id = dj.case_id
    logger.info(f"[{case_id}] Miner V1.1.0: Starting processing (delegating to specialists).")
    dj.current_pipeline_stage = "Miner_Initializing"

    assert dj.original_markdown_content and dj.original_markdown_content.strip(), \
        f"[{case_id}] Miner: Precondition failed - original_markdown_content is empty."

    temp_dir_path_str = "" 
    try:
        temp_dir_path_str = tempfile.mkdtemp(prefix=f"sde_miner_{case_id}_")
        temp_dir = pathlib.Path(temp_dir_path_str)
        dj.internal_tool_outputs_verbatim["miner_temp_dir"] = str(temp_dir)
        logger.info(f"[{case_id}] Miner: Using temporary directory for MD file: {temp_dir}")
    except Exception as e_tempdir: # Should ideally not happen if OS is stable
        logger.critical(f"[{case_id}] Miner: FATAL - Failed to create temporary directory: {e_tempdir}", exc_info=True)
        dj.final_job_outcome = OUTCOME_MINER_INFRASTRUCTURE_ERROR
        dj.current_pipeline_stage = "Miner_Failed_TempDir"
        if dj.actionable_leads is None: dj.actionable_leads = []
        # Using direct ActionableLead instantiation for this critical internal failure
        dj.actionable_leads.append(ActionableLead( 
            source_service="Miner",
            problem_description=f"Miner infrastructure failure: Could not create temp directory. System error: {e_tempdir}",
            internal_details_for_oracle={"error_type": "InfrastructureError_TempDir", "exception_str": str(e_tempdir)}
        ))
        raise # Crash Miner if temp dir cannot be made

    md_file = temp_dir / "input.md"
    tex_file = temp_dir / "output.tex" # Specialists will write to this path in Miner's temp_dir
    
    try:
        md_file.write_text(dj.original_markdown_content, encoding="utf-8")

        # --- 0. Markdown Proofreading ---
        dj.current_pipeline_stage = "Miner_MarkdownProofing"
        logger.info(f"[{case_id}] Miner: Delegating to markdown_proofer.")
        # run_markdown_checks can raise if checkers are missing or its own utils fail
        markdown_leads = run_markdown_checks(dj.case_id, str(md_file.resolve()), calling_manager_name="Miner")
        
        if markdown_leads:
            logger.warning(f"[{case_id}] Miner: Markdown proofreading found {len(markdown_leads)} issues.")
            if dj.actionable_leads is None: dj.actionable_leads = []
            dj.actionable_leads.extend(markdown_leads)
            dj.md_to_tex_conversion_attempted = False 
            dj.md_to_tex_conversion_successful = False
            dj.final_job_outcome = OUTCOME_MD_PROOFING_FAILED
            dj.current_pipeline_stage = "Miner_MarkdownProofingFailed"
            return dj # Early exit

        logger.info(f"[{case_id}] Miner: Markdown proofreading passed.")

        # --- 1. MD-to-TeX Conversion (Delegated) ---
        dj.current_pipeline_stage = "Miner_MDtoTeX_Delegation"
        dj.md_to_tex_conversion_attempted = True # Mark attempt before calling specialist
        logger.info(f"[{case_id}] Miner: Delegating MD-to-TeX to pandoc_tex_converter for {md_file} -> {tex_file}.")
        
        pandoc_result: PandocConversionResult = convert_md_to_tex(
            case_id, md_file, tex_file
        )
        
        # Update DiagnosticJob from PandocConversionResult
        dj.md_to_tex_conversion_successful = pandoc_result.conversion_successful
        dj.generated_tex_content = pandoc_result.generated_tex_content
        dj.md_to_tex_raw_log = pandoc_result.pandoc_raw_log
        if pandoc_result.actionable_lead:
            if dj.actionable_leads is None: dj.actionable_leads = []
            dj.actionable_leads.append(pandoc_result.actionable_lead)
            dj.final_job_outcome = OUTCOME_MD_TO_TEX_CONVERSION_FAILED
            dj.current_pipeline_stage = "Miner_MdToTexFailedViaSpecialist"
            logger.info(f"[{case_id}] Miner: pandoc_tex_converter reported MD-to-TeX failure.")
            return dj

        logger.info(f"[{case_id}] Miner: pandoc_tex_converter reported MD-to-TeX success.")
        dj.final_job_outcome = OUTCOME_MD_TO_TEX_SUCCESS_PROCEED_TO_TEX_COMPILE

        # --- 2. TeX-to-PDF Compilation (Delegated) ---
        assert dj.generated_tex_content, f"[{case_id}] Miner: TeX content missing after supposed MD-to-TeX success."
        # tex_file should have been written by pandoc_tex_converter if successful.
        assert tex_file.is_file(), f"[{case_id}] Miner: TeX file {tex_file} not found after MD-to-TeX success."

        dj.current_pipeline_stage = "Miner_TeXtoPDF_Delegation"
        dj.tex_to_pdf_compilation_attempted = True # Mark attempt
        logger.info(f"[{case_id}] Miner: Delegating TeX-to-PDF to tex_compiler for {tex_file}.")

        tex_comp_result: TexCompilationResult = compile_tex_to_pdf(
            case_id, tex_file, temp_dir # tex_compiler writes PDF to temp_dir
        )

        # Update DiagnosticJob from TexCompilationResult
        dj.tex_to_pdf_compilation_successful = tex_comp_result.compilation_successful
        dj.tex_compiler_raw_log = tex_comp_result.tex_compiler_raw_log
        # Note: tex_compiler specialist provides a lead for *tool* failures (timeout, not found),
        # not for TeX content errors. TeX content errors mean compilation_successful is False,
        # and Investigator will use the raw_log.

        if tex_comp_result.actionable_lead: # This implies a tool failure within tex_compiler
            if dj.actionable_leads is None: dj.actionable_leads = []
            dj.actionable_leads.append(tex_comp_result.actionable_lead)
            # Set a specific outcome for this kind of failure if not already implied by successful=False
            dj.final_job_outcome = OUTCOME_MINER_PDFLATEX_TOOL_ERROR # Example
            dj.current_pipeline_stage = "Miner_TexToPdfFailedViaSpecialistToolError"
            logger.error(f"[{case_id}] Miner: tex_compiler reported a tool failure: {tex_comp_result.actionable_lead.problem_description}")
            return dj # Return early due to pdflatex tool issue

        if dj.tex_to_pdf_compilation_successful:
            logger.info(f"[{case_id}] Miner: tex_compiler reported TeX-to-PDF success. PDF at {tex_comp_result.pdf_file_path}")
            dj.final_job_outcome = OUTCOME_SUCCESS_PDF_VALID
            # We might want to store dj.pdf_file_path = str(tex_comp_result.pdf_file_path) if model supports
        else:
            logger.warning(f"[{case_id}] Miner: tex_compiler reported TeX-to-PDF failure. Investigator will use the log.")
            dj.final_job_outcome = OUTCOME_TEX_COMPILATION_FAILED_FOR_INVESTIGATION
            # No specific leads from Miner for TeX content errors here; Investigator handles it.

    # Catch exceptions that specialists (pandoc_tex_converter, tex_compiler) are designed to propagate
    # These indicate problems with the tools themselves, not the content they process (unless it's a crash from bad content)
    except FileNotFoundError as e_fnf: # Propagated from a specialist via process_runner
        tool_name_from_specialist = "pandoc" if "pandoc" in str(e_fnf.filename).lower() else \
                                    "pdflatex" if "pdflatex" in str(e_fnf.filename).lower() else \
                                    e_fnf.filename or "UnknownTool"
        logger.critical(f"[{case_id}] Miner: FATAL - Specialist reported command not found: {tool_name_from_specialist}. Temp dir: {temp_dir_path_str}", exc_info=True)
        dj.final_job_outcome = OUTCOME_MINER_INFRASTRUCTURE_ERROR
        dj.current_pipeline_stage = f"Miner_Failed_SpecialistCommandNotFound_{tool_name_from_specialist}"
        if dj.actionable_leads is None: dj.actionable_leads = []
        dj.actionable_leads.append(_create_miner_level_tool_failure_lead(
            problem_description=f"Required command '{tool_name_from_specialist}' not found by specialist. Ensure it is installed and in system PATH.",
            source_component_tool=f"Specialist({tool_name_from_specialist})", stage="command_check",
            exception_obj=e_fnf
        ))
        raise # Re-raise to crash Miner as this is a setup/env issue.
    except subprocess.TimeoutExpired as e_timeout: # Propagated from a specialist
        tool_name_from_specialist_timeout = "UnknownTool"
        if e_timeout.cmd: # Try to determine which tool
            cmd_str = str(e_timeout.cmd).lower()
            tool_name_from_specialist_timeout = "pandoc" if "pandoc" in cmd_str else \
                                               "pdflatex" if "pdflatex" in cmd_str else \
                                               (e_timeout.cmd[0] if isinstance(e_timeout.cmd, list) and e_timeout.cmd else "SpecialistTool")

        logger.error(f"[{case_id}] Miner: Specialist reported subprocess timeout for {tool_name_from_specialist_timeout}: {e_timeout}. Temp dir: {temp_dir_path_str}", exc_info=True)
        dj.final_job_outcome = (OUTCOME_MINER_PANDOC_TIMEOUT if tool_name_from_specialist_timeout == "pandoc" 
                                else OUTCOME_MINER_PDFLATEX_TIMEOUT if tool_name_from_specialist_timeout == "pdflatex" 
                                else f"Miner_SpecialistToolTimeout_{tool_name_from_specialist_timeout}")
        dj.current_pipeline_stage = f"Miner_Failed_SpecialistTimeout_{tool_name_from_specialist_timeout}"
        if dj.actionable_leads is None: dj.actionable_leads = []
        dj.actionable_leads.append(_create_miner_level_tool_failure_lead(
             problem_description=f"Specialist tool '{tool_name_from_specialist_timeout}' timed out after {e_timeout.timeout} seconds.",
             source_component_tool=f"Specialist({tool_name_from_specialist_timeout})", stage="execution_timeout",
             exception_obj=e_timeout
        ))
        raise # Re-raise
    except Exception as e_general: # Catch any other truly unexpected exception from specialists or Miner's own logic
        logger.critical(f"[{case_id}] Miner: UNEXPECTED CRITICAL ERROR in process_job. Temp dir: {temp_dir_path_str}: {e_general}", exc_info=True)
        dj.final_job_outcome = OUTCOME_MINER_UNEXPECTED_CRITICAL_ERROR
        dj.current_pipeline_stage = "Miner_Crashed_ProcessJobUnhandled"
        if dj.actionable_leads is None: dj.actionable_leads = []
        dj.actionable_leads.append(_create_miner_level_tool_failure_lead(
             problem_description=f"Miner encountered an unexpected critical error in its main processing logic: {type(e_general).__name__}",
             source_component_tool="MinerCoreLogic", stage="runtime_error_process_job",
             exception_obj=e_general
        ))
        raise # Re-raise

    dj.current_pipeline_stage = "Miner_Complete"
    logger.info(f"[{case_id}] Miner: Processing finished. Final Outcome: {dj.final_job_outcome}")
    return dj

# --- Main CLI Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDE Miner Manager V1.1.0 (Delegating to Specialists)")
    parser.add_argument('--process-job', action='store_true', help="Required flag to process DiagnosticJob JSON from stdin.")
    args = parser.parse_args()

    assert args.process_job, "Miner.py: Must be called with --process-job flag."
    
    input_json_str = sys.stdin.read()
    assert input_json_str.strip(), "Miner.py: Received empty or whitespace-only input from stdin."
        
    diagnostic_job_dict_input = json.loads(input_json_str) 
    diagnostic_job_model_input = DiagnosticJob(**diagnostic_job_dict_input) 
    
    case_id_main = getattr(diagnostic_job_model_input, 'case_id', 'unknown_case_in_main')
    logger.info(f"[{case_id_main}] Miner (__main__ V1.1.0): --process-job received, starting logic.")
    
    final_dj_state_for_output = diagnostic_job_model_input 
    try:
        final_dj_state_for_output = process_job(diagnostic_job_model_input)
    except Exception as e_crash: 
        logger.critical(f"[{case_id_main}] Miner (__main__): CRASH from process_job(): {e_crash}", exc_info=True)
        
        # Ensure final_job_outcome and current_pipeline_stage reflect the crash
        current_outcome = getattr(final_dj_state_for_output, 'final_job_outcome', None)
        is_already_error_outcome = current_outcome and any(
            err_indicator in str(current_outcome).lower() 
            for err_indicator in ["error", "timeout", "failed", "crashed"]
        )
        if not is_already_error_outcome:
            final_dj_state_for_output.final_job_outcome = OUTCOME_MINER_CRASHED_IN_MAIN_LOGIC
        
        current_stage = getattr(final_dj_state_for_output, 'current_pipeline_stage', None)
        is_already_failed_stage = current_stage and any(
            err_indicator in str(current_stage).lower() for err_indicator in ["failed", "crashed"]
        )
        if not is_already_failed_stage:
            final_dj_state_for_output.current_pipeline_stage = "Miner_Crashed_CaughtInMain" # type: ignore
        
        # Add a generic lead about this __main__ level crash if no specific critical lead already exists
        is_critical_lead_present = False
        if isinstance(final_dj_state_for_output.actionable_leads, list):
            for lead_item in final_dj_state_for_output.actionable_leads:
                if isinstance(lead_item, ActionableLead): # Check type
                    desc_lower = lead_item.problem_description.lower()
                    if any(keyword in desc_lower for keyword in CRITICAL_LEAD_KEYWORDS): # Define CRITICAL_LEAD_KEYWORDS
                        is_critical_lead_present = True
                        break
        
        CRITICAL_LEAD_KEYWORDS = ["crashed", "fatal", "timeout", "command not found", "infrastructure error", "critical error"]
        if not is_critical_lead_present:
            crash_lead_desc = f"Miner script process_job() crashed unexpectedly (caught in __main__): {type(e_crash).__name__}"
            if final_dj_state_for_output.actionable_leads is None: final_dj_state_for_output.actionable_leads = []
            # Use _create_miner_level_tool_failure_lead for consistency, adapting it
            final_dj_state_for_output.actionable_leads.append(_create_miner_level_tool_failure_lead(
                problem_description=crash_lead_desc,
                source_component_tool="MinerMainBlock", stage="runtime_crash_handling",
                exception_obj=e_crash # Pass the exception object
            ))

        output_json_str = final_dj_state_for_output.model_dump_json(
            indent=2 if os.environ.get("SDE_PRETTY_PRINT_JSON", "false").lower() == "true" else None
        )
        sys.stdout.write(output_json_str) 
        sys.stdout.flush()
        sys.exit(1) 

    # If process_job completed without raising an exception to here:
    output_json_str = final_dj_state_for_output.model_dump_json(
        indent=2 if os.environ.get("SDE_PRETTY_PRINT_JSON", "false").lower() == "true" else None
    )
    sys.stdout.write(output_json_str)
    sys.stdout.flush()
    
    logger.info(f"[{final_dj_state_for_output.case_id}] Miner (__main__): Successfully completed execution.")
    sys.exit(0)
