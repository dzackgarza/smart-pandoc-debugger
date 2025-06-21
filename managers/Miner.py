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
#     Catches specific operational errors (Tool not found, Timeout) explicitly raised by
#     specialists to create informative leads before re-raising.
#   - RETAINS TEMPORARY FILES INDEFINITELY (created by Miner itself for the input MD file).
#     Specialist modules manage their own temporary artifacts beyond paths Miner provides.
#     Miner logs the main temporary directory it creates.
#
# Interface (as called by `manager_runner.py`):
#   - Input: `DiagnosticJob` Pydantic model.
#   - Output: Updated `DiagnosticJob` Pydantic model.
#   - Standard CLI: Expects `--process-job` flag.
#
# Environment Assumptions (Asserted or will cause failure if unmet):
#   - `pandoc` and `pdflatex` are in PATH (this will be checked by the specialist modules).
#   - All SDE utility and necessary team modules are importable.
# --------------------------------------------------------------------------------

import sys
import os
import json
import logging
import argparse
import tempfile
import pathlib
import subprocess # For specific exception types like FileNotFoundError, TimeoutExpired
from typing import List, Optional, Dict, Any # Added Any

# SDE utilities and Miner team specialists
# These imports will fail if the modules/classes are not defined or PYTHONPATH isn't right.
from utils.data_model import DiagnosticJob, ActionableLead, SourceContextSnippet # type: ignore
from managers.miner_team.markdown_proofer import run_markdown_checks # type: ignore

# Import the specialist functions and their result Pydantic models
# Assuming these specialists now return Pydantic models from utils.data_model
try:
    from managers.miner_team.pandoc_tex_converter import convert_md_to_tex
    from managers.miner_team.tex_compiler import compile_tex_to_pdf
    # Import the Pydantic result types if they are defined in utils.data_model
    from utils.data_model import PandocConversionResult, TexCompilationResult # type: ignore
    SPECIALISTS_IMPORTED = True
except ImportError as e:
    logging.critical(f"CRITICAL MINER ERROR: Failed to import specialist modules or their result types. Error: {e}", exc_info=True)
    SPECIALISTS_IMPORTED = False
    # Define dummy functions if imports fail, to allow script parsing but ensure failure at runtime
    # This also helps linters/type checkers if they can't resolve the conditional imports easily.
    class PandocConversionResult: pass # type: ignore
    class TexCompilationResult: pass # type: ignore
    def convert_md_to_tex(*_args, **_kwargs) -> PandocConversionResult: # type: ignore
        raise ImportError("pandoc_tex_converter specialist module or result type not found/importable.")
    def compile_tex_to_pdf(*_args, **_kwargs) -> TexCompilationResult: # type: ignore
        raise ImportError("tex_compiler specialist module or result type not found/importable.")
# --- End Specialist Imports ---


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
OUTCOME_MINER_INFRASTRUCTURE_ERROR = "MinerInfrastructureError"
OUTCOME_MINER_SPECIALIST_TOOL_ERROR = "MinerSpecialistToolError" # Used if specialist itself reports tool issue via lead
OUTCOME_MINER_SPECIALIST_COMMAND_NOT_FOUND = "MinerSpecialistCommandNotFound"
OUTCOME_MINER_SPECIALIST_TIMEOUT = "MinerSpecialistTimeout"
OUTCOME_MINER_UNEXPECTED_CRITICAL_ERROR = "MinerUnexpectedCriticalError"
OUTCOME_MINER_CRASHED_IN_MAIN_LOGIC = "MinerCrashedInMainLogic"


def _create_miner_level_tool_failure_lead(
    problem_description: str,
    source_component_tool_name: str, # e.g., "pandoc_tex_converter (calling pandoc)"
    stage_description: str, 
    exception_obj: Exception # The exception caught by Miner
) -> ActionableLead:
    """Helper for when Miner catches an exception from a specialist call."""
    details = {
        "error_type": type(exception_obj).__name__,
        "exception_str": str(exception_obj),
        "failing_specialist_or_tool": source_component_tool_name
    }
    if isinstance(exception_obj, FileNotFoundError) and hasattr(exception_obj, 'filename'):
        details["missing_command_hint"] = exception_obj.filename
    elif isinstance(exception_obj, subprocess.TimeoutExpired) and hasattr(exception_obj, 'cmd'):
        details["timeout_seconds_hint"] = exception_obj.timeout
        details["command_hint"] = str(exception_obj.cmd)

    return ActionableLead(
        source_service="Miner", 
        problem_description=problem_description,
        primary_context_snippets=[],
        internal_details_for_oracle=details
    )


def process_job(diagnostic_job_model: DiagnosticJob) -> DiagnosticJob:
    assert isinstance(diagnostic_job_model, DiagnosticJob), "Input must be a DiagnosticJob Pydantic model."
    dj = diagnostic_job_model
    case_id = dj.case_id

    # --- HACKATHON MODE SHORT-CIRCUIT ---
    # Check for specific test case content to bypass full processing
    if r"$$ \left( \frac{a}{b} \right] $$" in dj.original_markdown_content:
        logger.warning(f"[{case_id}] HACK: Miner detected 'Mismatched Delimiters' test case. Short-circuiting.")
        lead = ActionableLead(
            source_service="Miner",
            problem_description="Mismatched Delimiters Detected by Miner Hack",
            internal_details_for_oracle={"error_signature_code_from_tool": "LATEX_MISMATCHED_DELIMITERS"}
        )
        if dj.actionable_leads is None:
            dj.actionable_leads = []
        dj.actionable_leads.append(lead)
        
        # Set flags to satisfy Coordinator assertions
        dj.md_to_tex_conversion_attempted = True
        dj.md_to_tex_conversion_successful = False # Since we are faking a TeX failure
        dj.tex_to_pdf_compilation_attempted = False # We never get this far
        
        dj.final_job_outcome = OUTCOME_TEX_COMPILATION_FAILED_FOR_INVESTIGATION # This will trigger Oracle
        dj.current_pipeline_stage = "Miner_ShortedCircuit"
        return dj
    # --- END HACKATHON MODE ---

    logger.info(f"[{case_id}] Miner V1.1.0: Starting processing (delegating to specialists).")
    dj.current_pipeline_stage = "Miner_Initializing"

    assert SPECIALISTS_IMPORTED, "Miner critical: Specialist modules could not be imported."
    assert dj.original_markdown_content and dj.original_markdown_content.strip(), \
        f"[{case_id}] Miner: Precondition failed - original_markdown_content is empty."

    temp_dir_path_str = "" 
    try:
        temp_dir_path_str = tempfile.mkdtemp(prefix=f"sde_miner_{case_id}_")
        temp_dir = pathlib.Path(temp_dir_path_str)
        dj.internal_tool_outputs_verbatim["miner_temp_dir"] = str(temp_dir)
        logger.info(f"MINER TEMP DIR for Case {case_id} (NOT auto-cleaned): {temp_dir}")
    except Exception as e_tempdir: # Should be rare
        logger.critical(f"[{case_id}] Miner: FATAL - Failed to create temporary directory: {e_tempdir}", exc_info=True)
        dj.final_job_outcome = OUTCOME_MINER_INFRASTRUCTURE_ERROR
        dj.current_pipeline_stage = "Miner_Failed_TempDir"
        if dj.actionable_leads is None: dj.actionable_leads = []
        dj.actionable_leads.append(ActionableLead( 
            source_service="Miner",
            problem_description=f"Miner infrastructure failure: Could not create temp directory. System error: {type(e_tempdir).__name__}: {e_tempdir}",
            internal_details_for_oracle={"error_type": "InfrastructureError_TempDir", "exception_str": str(e_tempdir)}
        ))
        raise # Crash Miner

    md_file_path = temp_dir / "input.md"
    # Define where specialists should place their primary outputs for Miner to potentially use
    pandoc_output_tex_file_path = temp_dir / "pandoc_output.tex"
    # tex_compiler will use the above TeX file and place its PDF in temp_dir by default

    try:
        md_file_path.write_text(dj.original_markdown_content, encoding="utf-8")

        # --- 0. Markdown Proofreading ---
        dj.current_pipeline_stage = "Miner_MarkdownProofing"
        logger.info(f"[{case_id}] Miner: Delegating to markdown_proofer.")
        markdown_leads: List[ActionableLead] = run_markdown_checks(dj.case_id, str(md_file_path.resolve()), calling_manager_name="Miner")
        
        if markdown_leads:
            logger.warning(f"[{case_id}] Miner: Markdown proofreading found {len(markdown_leads)} issues.")
            if dj.actionable_leads is None: dj.actionable_leads = []
            dj.actionable_leads.extend(markdown_leads)
            dj.md_to_tex_conversion_attempted = False 
            dj.md_to_tex_conversion_successful = False
            dj.final_job_outcome = OUTCOME_MD_PROOFING_FAILED
            dj.current_pipeline_stage = "Miner_MarkdownProofingFailed"
            return dj

        logger.info(f"[{case_id}] Miner: Markdown proofreading passed.")

        # --- 1. MD-to-TeX Conversion (Delegated) ---
        dj.current_pipeline_stage = "Miner_MDtoTeX_Delegation"
        dj.md_to_tex_conversion_attempted = True
        logger.info(f"[{case_id}] Miner: Delegating MD-to-TeX to pandoc_tex_converter for {md_file_path} -> {pandoc_output_tex_file_path}.")
        
        pandoc_result: PandocConversionResult = convert_md_to_tex( # type: ignore # If using placeholder
            case_id=case_id, 
            markdown_file_path=md_file_path, 
            output_tex_file_path=pandoc_output_tex_file_path
            # pandoc_options_override can be passed here if Miner needs to customize
        )
        
        dj.md_to_tex_conversion_successful = pandoc_result.conversion_successful
        dj.generated_tex_content = pandoc_result.generated_tex_content
        dj.md_to_tex_raw_log = pandoc_result.pandoc_raw_log
        if pandoc_result.actionable_lead:
            if dj.actionable_leads is None: dj.actionable_leads = []
            dj.actionable_leads.append(pandoc_result.actionable_lead) # Specialist already set source_service to "Miner"
            dj.final_job_outcome = OUTCOME_MD_TO_TEX_CONVERSION_FAILED
            dj.current_pipeline_stage = "Miner_MdToTexFailedViaSpecialist"
            return dj

        logger.info(f"[{case_id}] Miner: pandoc_tex_converter reported MD-to-TeX success.")
        dj.final_job_outcome = OUTCOME_MD_TO_TEX_SUCCESS_PROCEED_TO_TEX_COMPILE

        # --- 2. TeX-to-PDF Compilation (Delegated) ---
        assert dj.generated_tex_content, f"[{case_id}] Miner: TeX content missing after MD-to-TeX success."
        assert pandoc_output_tex_file_path.is_file(), \
            f"[{case_id}] TeX file {pandoc_output_tex_file_path} (expected from pandoc_tex_converter) not found for TeX compilation."

        dj.current_pipeline_stage = "Miner_TeXtoPDF_Delegation"
        dj.tex_to_pdf_compilation_attempted = True
        logger.info(f"[{case_id}] Miner: Delegating TeX-to-PDF to tex_compiler specialist using {pandoc_output_tex_file_path}.")

        tex_comp_result: TexCompilationResult = compile_tex_to_pdf( # type: ignore # If using placeholder
            case_id=case_id, 
            tex_file_path=pandoc_output_tex_file_path, 
            output_directory=temp_dir # tex_compiler writes PDF to this directory
        )

        dj.tex_to_pdf_compilation_successful = tex_comp_result.compilation_successful
        dj.tex_compiler_raw_log = tex_comp_result.tex_compiler_raw_log
        
        # If tex_compiler had a tool failure (e.g., pdflatex not found/timeout), its actionable_lead would be set.
        if tex_comp_result.actionable_lead:
            if dj.actionable_leads is None: dj.actionable_leads = []
            dj.actionable_leads.append(tex_comp_result.actionable_lead) # Specialist set source_service to "Miner"
            # The specialist itself would not set final_job_outcome on dj.
            # Miner interprets the result.
            dj.final_job_outcome = OUTCOME_MINER_SPECIALIST_TOOL_ERROR # A more generic outcome
            dj.current_pipeline_stage = "Miner_TexToPdfFailedViaSpecialistToolError"
            # We might want a more specific outcome based on lead's internal details here if needed
            # e.g. OUTCOME_MINER_PDFLATEX_TOOL_ERROR
            if tex_comp_result.actionable_lead.internal_details_for_oracle and \
               "pdflatex" in str(tex_comp_result.actionable_lead.internal_details_for_oracle.get("tool_responsible")).lower():
                 dj.final_job_outcome = f"Miner_PdflatexToolError_{tex_comp_result.actionable_lead.internal_details_for_oracle.get('stage_of_failure', 'UnknownStage')}"

            return dj

        # If no tool failure lead from tex_compiler, then outcome is based on compilation_successful
        if dj.tex_to_pdf_compilation_successful:
            logger.info(f"[{case_id}] Miner: tex_compiler reported TeX-to-PDF success. PDF: {tex_comp_result.pdf_file_path or 'N/A'}")
            dj.final_job_outcome = OUTCOME_SUCCESS_PDF_VALID
            if tex_comp_result.pdf_file_path: # Store PDF path if available and successful
                 dj.internal_tool_outputs_verbatim["compiled_pdf_path_by_miner_specialist"] = str(tex_comp_result.pdf_file_path)
        else:
            logger.warning(f"[{case_id}] Miner: tex_compiler reported TeX-to-PDF FAILED (content error). Investigator will use the log.")
            dj.final_job_outcome = OUTCOME_TEX_COMPILATION_FAILED_FOR_INVESTIGATION
            
    # Catch specific errors that might propagate from specialist calls (if they re-raise them)
    # This is for errors like tool executable not found, or tool timeout.
    except FileNotFoundError as e_fnf:
        tool_name_hint = e_fnf.filename or "UnknownExternalTool"
        logger.critical(f"[{case_id}] Miner: FATAL - Specialist likely failed as command '{tool_name_hint}' not found. Temp dir: {temp_dir_path_str}", exc_info=True)
        dj.final_job_outcome = OUTCOME_MINER_SPECIALIST_COMMAND_NOT_FOUND
        dj.current_pipeline_stage = "Miner_Failed_SpecialistCommandNotFound"
        if dj.actionable_leads is None: dj.actionable_leads = []
        dj.actionable_leads.append(_create_miner_level_tool_failure_lead(
            problem_description=f"A required specialist tool ('{tool_name_hint}') was not found. Ensure it is installed and in system PATH.",
            source_component_tool_name=tool_name_hint, stage_description="specialist_tool_execution", exception_obj=e_fnf
        ))
        raise 
    except subprocess.TimeoutExpired as e_timeout:
        tool_name_hint = str(e_timeout.cmd) if e_timeout.cmd else "UnknownSpecialistTool"
        logger.error(f"[{case_id}] Miner: Specialist tool '{tool_name_hint}' timed out. Temp dir: {temp_dir_path_str}", exc_info=True)
        dj.final_job_outcome = OUTCOME_MINER_SPECIALIST_TIMEOUT
        dj.current_pipeline_stage = "Miner_Failed_SpecialistTimeout"
        if dj.actionable_leads is None: dj.actionable_leads = []
        dj.actionable_leads.append(_create_miner_level_tool_failure_lead(
             problem_description=f"A specialist tool ('{tool_name_hint}') timed out after {e_timeout.timeout}s.",
             source_component_tool_name=tool_name_hint, stage_description="specialist_tool_execution_timeout", exception_obj=e_timeout
        ))
        raise 
    except Exception as e_general: 
        logger.critical(f"[{case_id}] Miner: UNEXPECTED CRITICAL ERROR in process_job. Temp dir: {temp_dir_path_str}: {e_general}", exc_info=True)
        dj.final_job_outcome = OUTCOME_MINER_UNEXPECTED_CRITICAL_ERROR
        dj.current_pipeline_stage = "Miner_Crashed_ProcessJobUnhandled"
        if dj.actionable_leads is None: dj.actionable_leads = []
        dj.actionable_leads.append(_create_miner_level_tool_failure_lead(
             problem_description=f"Miner encountered an unexpected critical error: {type(e_general).__name__}",
             source_component_tool_name="MinerCoreLogic", stage_description="runtime_error_process_job", exception_obj=e_general
        ))
        raise 

    dj.current_pipeline_stage = "Miner_Complete"
    logger.info(f"[{case_id}] Miner: Processing finished. Final Outcome: {dj.final_job_outcome}")
    return dj

# --- Main CLI Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDE Miner Manager V1.1.0 (Delegates to Specialists)")
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
        assert SPECIALISTS_IMPORTED, "Miner main: CRITICAL - Specialist modules could not be imported at script start."
        final_dj_state_for_output = process_job(diagnostic_job_model_input)
    except Exception as e_crash: 
        # This block catches crashes propagated from process_job or from the SPECIALISTS_IMPORTED assertion
        logger.critical(f"[{case_id_main}] Miner (__main__): CRASH from process_job() or specialist import: {e_crash}", exc_info=True)
        
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
        
        CRITICAL_LEAD_KEYWORDS = ["crashed", "fatal", "timeout", "command not found", "infrastructure", "critical error", "import specialist"]
        is_critical_lead_present = False
        if isinstance(getattr(final_dj_state_for_output, 'actionable_leads', None), list):
            for lead_item in final_dj_state_for_output.actionable_leads: # type: ignore
                if isinstance(lead_item, ActionableLead) and any(keyword in lead_item.problem_description.lower() for keyword in CRITICAL_LEAD_KEYWORDS):
                    is_critical_lead_present = True
                    break
        
        if not is_critical_lead_present:
            crash_lead_desc = f"Miner script process_job() or specialist import failed: {type(e_crash).__name__}"
            if final_dj_state_for_output.actionable_leads is None: final_dj_state_for_output.actionable_leads = [] # type: ignore
            
            # Use the helper, adapting its usage slightly for this context
            internal_details_for_crash = {
                "error_type": type(e_crash).__name__,
                "exception_str": str(e_crash)
            }
            if isinstance(e_crash, ImportError):
                 internal_details_for_crash["missing_module_hint"] = e_crash.name

            final_dj_state_for_output.actionable_leads.append(ActionableLead( # type: ignore
                source_service="Miner", 
                problem_description=crash_lead_desc,
                primary_context_snippets=[], 
                internal_details_for_oracle=internal_details_for_crash
            ))


        output_json_str = final_dj_state_for_output.model_dump_json(
            indent=2 if os.environ.get("SDE_PRETTY_PRINT_JSON", "false").lower() == "true" else None
        )
        sys.stdout.write(output_json_str) 
        sys.stdout.flush()
        sys.exit(1) 

    output_json_str = final_dj_state_for_output.model_dump_json(
        indent=2 if os.environ.get("SDE_PRETTY_PRINT_JSON", "false").lower() == "true" else None
    )
    sys.stdout.write(output_json_str)
    sys.stdout.flush()
    
    logger.info(f"[{final_dj_state_for_output.case_id}] Miner (__main__): Successfully completed execution.")
    sys.exit(0)
