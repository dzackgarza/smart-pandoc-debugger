#!/usr/bin/env python3
# managers/Investigator.py - SDE Investigator Manager
#
# Version: 5.2.0 (Python Module Specialists, Fail-Fast)
# Date: 2025-06-26
# Author: Diagnostic Systems Group
#
# Philosophy (SDE V5.2):
#   - Acts as the "Investigator" manager in the SDE pipeline.
#   - Receives a full DiagnosticJob JSON object via stdin when called with --process-job.
#   - Analyzes LaTeX compilation logs (from DiagnosticJob.tex_compiler_raw_log) by
#     delegating to a series of specialist Python modules.
#   - Populates DiagnosticJob.actionable_leads with findings.
#   - Adheres to a "Fail Fast, Fail Loud" philosophy using assertions and propagating exceptions.
#
# Role: THE LOG INVESTIGATION MANAGER
#
# Invoked by Coordinator if TeX-to-PDF compilation fails. Analyzes TeX logs via
# specialist proofer modules to create `ActionableLead` objects.
#
# Responsibilities:
#   - Accept a `DiagnosticJob`.
#   - If TeX compilation failed, orchestrate calls to specialist proofer functions.
#   - Transform return values from proofers into `ActionableLead` Pydantic models.
#   - Update `DiagnosticJob.actionable_leads` and `DiagnosticJob.final_job_outcome`.
#   - Return updated `DiagnosticJob` JSON.
#
# Interface (when called by manager_runner.py):
#   Invocation: python3 managers/Investigator.py --process-job
#   Stdin: Full DiagnosticJob JSON string.
#   Stdout: Full, updated DiagnosticJob JSON string.
#   Exit Code: 0 on success; non-zero on assertion failure or specialist crash.
#
# Environment Variables:
#   DEBUG (optional, for verbose logging, read from environment)
# --------------------------------------------------------------------------------

import argparse
import json
import logging
import os
import sys
import tempfile
from typing import List, Optional

# --- SDE Utility Imports ---
# This script assumes it is run in an environment where 'utils' is on the PYTHONPATH.
# The project's top-level runner should handle this.
try:
    from utils.data_model import DiagnosticJob, ActionableLead, SourceContextSnippet
except ModuleNotFoundError:
    # Add project root to path for standalone script execution
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from utils.data_model import DiagnosticJob, ActionableLead, SourceContextSnippet
    except ModuleNotFoundError as e_inner:
        print(f"CRITICAL INVESTIGATOR ERROR: Failed to import SDE utilities after path correction. Error: {e_inner}", file=sys.stderr)
        sys.exit(1)

# --- Specialist Proofer Imports ---
# These are now imported and called as direct Python functions.
from smart_pandoc_debugger.managers.investigator_team.error_finder_dev import find_primary_error
# from smart_pandoc_debugger.managers.investigator_team.missing_dollar_proofer import find_missing_dollar_errors
# from smart_pandoc_debugger.managers.investigator_team.runaway_argument_proofer import find_runaway_argument
from smart_pandoc_debugger.managers.investigator_team.undefined_command_proofer import run_undefined_command_proofer
# from smart_pandoc_debugger.managers.investigator_team.tex_proofer import run_tex_proofer # This runs multiple sub-proofers

# --- Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    DEBUG_ENV_INVESTIGATOR = os.environ.get("DEBUG", "false").lower()
    INVESTIGATOR_LOG_LEVEL = logging.DEBUG if DEBUG_ENV_INVESTIGATOR == "true" else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(asctime)s - INVESTIGATOR (%(name)s) - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(INVESTIGATOR_LOG_LEVEL)
    logger.propagate = False

# --- Outcome Constants ---
OUTCOME_TEX_COMPILATION_ERROR_LEADS_FOUND = "TexCompilationError_LeadsFound"
OUTCOME_NO_ACTIONABLE_LEADS_FOUND = "NoActionableLeadsFound_ManualReview"
OUTCOME_INVESTIGATOR_INFRASTRUCTURE_ERROR = "InvestigatorInfrastructureError"

# --- Helper Function for TeX Snippet (retained for context creation) ---
def _get_tex_log_snippet(log_content: str, error_line: int, context_window: int = 10) -> SourceContextSnippet:
    """Extracts a text snippet from a log around a specific line number."""
    lines = log_content.splitlines()
    total_lines = len(lines)
    start_line = max(0, error_line - context_window - 1)
    end_line = min(total_lines, error_line + context_window)
    context_lines = lines[start_line:end_line]
    
    logger.debug(f"Extracted log snippet from lines {start_line+1}-{end_line} for error at line {error_line}.")

    return SourceContextSnippet(
        source_document_type="tex_compilation_log",
        central_line_number=error_line,
        snippet_text='\n'.join(context_lines)
    )

def _create_and_run_specialists(diagnostic_job_model: DiagnosticJob, temp_dir: str) -> List[ActionableLead]:
    """
    Creates and runs all specialist proofers on the raw TeX log.
    Implemented with a fail-fast assertion-based model. If any specialist
    encounters an unhandled error, it will propagate up and crash the Investigator.
    """
    dj = diagnostic_job_model
    case_id = dj.case_id
    leads: List[ActionableLead] = []

    assert dj.tex_compiler_raw_log, f"[{case_id}] Investigator: Precondition failed - tex_compiler_raw_log is empty."

    # Write the raw log to a file for the specialists to read
    raw_log_path = os.path.join(temp_dir, f"{case_id}.log")
    logger.debug(f"[{case_id}] Investigator: Writing raw TeX log to {raw_log_path} for specialists.")
    try:
        with open(raw_log_path, 'w', encoding='utf-8') as f:
            f.write(dj.tex_compiler_raw_log)
    except IOError as e:
        logger.error(f"[{case_id}] Failed to write temp log file at {raw_log_path}: {e}")
        # This is an infrastructure failure; raise it to halt execution.
        raise

    # --- Define Specialist Proofers to Run ---
    # Each entry is a tuple: (Proofer Function, proofer_name)
    specialist_proofers_to_run: List[tuple] = [
        # (find_missing_dollar_errors, "MissingDollarProofer"),
        # (run_tex_proofer, "TexProofer"), # For unbalanced braces and mismatched delimiters
        # (find_runaway_argument, "RunawayArgumentProofer"),
        (run_undefined_command_proofer, "UndefinedCommandProofer"),
    ]

    # --- Run Each Specialist ---
    for proofer_function, proofer_name in specialist_proofers_to_run:
        logger.info(f"[{case_id}] Investigator: Running specialist '{proofer_name}'.")
        # All specialists now conform to the (log_file_path: str) -> Optional[ActionableLead] signature
        # Any failure within the specialist will raise an exception and crash the Investigator.
        lead: Optional[ActionableLead] = proofer_function(raw_log_path)
        
        if lead:
            logger.info(f"[{case_id}] Specialist '{proofer_name}' found a lead: {lead.problem_description}")
            assert isinstance(lead, ActionableLead), \
                f"[{case_id}] Contract Violation: Specialist '{proofer_name}' returned a non-ActionableLead object."
            
            # Enrich lead with case_id and other details if not already present
            if not lead.internal_details_for_oracle:
                lead.internal_details_for_oracle = {}
            lead.internal_details_for_oracle["proofer_name"] = proofer_name
            
            leads.append(lead)
        else:
            logger.debug(f"[{case_id}] Specialist '{proofer_name}' did not find any lead.")

    # Legacy error_finder_dev call, now simplified.
    # This can be phased out as more specialist proofers are written.
    logger.debug(f"[{case_id}] Investigator: Running legacy find_primary_error.")
    error_dict = find_primary_error(dj.tex_compiler_raw_log)

    if error_dict and error_dict.get("error_signature") not in ["LATEX_COMPILATION_SUCCESSFUL", "LATEX_UNKNOWN_ERROR"]:
        logger.info(f"[{case_id}] Legacy 'find_primary_error' found a lead with signature: {error_dict.get('error_signature')}")
        
        # Manually construct an ActionableLead from the dictionary
        error_line_str = error_dict.get("error_line_in_tex")
        error_line = int(error_line_str) if error_line_str and error_line_str.isdigit() else 0

        log_excerpt_text = error_dict.get("log_excerpt") or "No log excerpt available."

        snippet = SourceContextSnippet(
            source_document_type="tex_compilation_log",
            central_line_number=error_line,
            snippet_text=log_excerpt_text
        )

        problem_desc_text = error_dict.get("raw_error_message") or "Unknown error"

        error_finder_lead = ActionableLead(
            source_service="Investigator_LegacyErrorFinder",
            problem_description=f"Legacy error finder detected: {problem_desc_text}",
            primary_context_snippets=[snippet],
            internal_details_for_oracle={
                "error_signature_code_from_tool": error_dict.get("error_signature"),
                "proofer_name": "find_primary_error"
            }
        )
        leads.append(error_finder_lead)
        
    logger.info(f"[{case_id}] Investigator: Completed running all specialists. Found {len(leads)} total leads.")
    return leads


def investigate_and_report(diagnostic_job_model: DiagnosticJob) -> DiagnosticJob:
    """
    Main logic for the Investigator manager.
    It sets up a temp directory, runs specialists, and populates the DiagnosticJob.
    """
    dj = diagnostic_job_model
    case_id = dj.case_id

    logger.info(f"[{case_id}] Investigator: Starting investigation.")
    dj.current_pipeline_stage = "Investigator_Initializing"

    assert dj.tex_compiler_raw_log and dj.tex_compiler_raw_log.strip(), \
        f"[{case_id}] Investigator: Precondition failed - tex_compiler_raw_log is missing or empty."
    
    temp_dir = ""
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"sde_investigator_{case_id}_")
        logger.debug(f"[{case_id}] Investigator: Created temporary directory: {temp_dir}")
        dj.internal_tool_outputs_verbatim["investigator_temp_dir"] = temp_dir
    except Exception as e_tempdir:
        logger.critical(f"[{case_id}] Investigator: FATAL - Failed to create temporary directory: {e_tempdir}", exc_info=True)
        dj.final_job_outcome = OUTCOME_INVESTIGATOR_INFRASTRUCTURE_ERROR
        dj.current_pipeline_stage = "Investigator_Failed_TempDir"
        # In a fail-fast model, we stop execution immediately.
        raise
    
    # Run specialists and gather leads. This call will raise an exception if any specialist fails.
    all_leads = _create_and_run_specialists(dj, temp_dir)

    if all_leads:
        logger.info(f"[{case_id}] Investigator: Found {len(all_leads)} actionable leads from specialists.")
        if dj.actionable_leads is None:
            dj.actionable_leads = []
        dj.actionable_leads.extend(all_leads)
        dj.final_job_outcome = OUTCOME_TEX_COMPILATION_ERROR_LEADS_FOUND
    else:
        logger.warning(f"[{case_id}] Investigator: No actionable leads were identified by any specialist.")
        dj.final_job_outcome = OUTCOME_NO_ACTIONABLE_LEADS_FOUND

    dj.current_pipeline_stage = "Investigator_Complete"
    logger.info(f"[{case_id}] Investigator: Investigation finished. Final Outcome: {dj.final_job_outcome}")
    return dj

# --- Main CLI Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDE Investigator Manager: Analyzes TeX compilation logs using specialist Python modules.")
    parser.add_argument(
        "--process-job",
        action="store_true",
        help="Required flag to process DiagnosticJob JSON from stdin."
    )
    args = parser.parse_args()

    assert args.process_job, "Investigator.py: Must be called with --process-job flag."
    
    input_json_str = sys.stdin.read()
    assert input_json_str.strip(), "Investigator.py: Received empty or whitespace-only input from stdin."
        
    diagnostic_job_model_input = DiagnosticJob.model_validate_json(input_json_str) 
    
    case_id_main = getattr(diagnostic_job_model_input, 'case_id', 'unknown_case_in_main')
    logger.info(f"[{case_id_main}] Investigator (__main__): --process-job received, starting logic.")
    
    final_dj_state_for_output = diagnostic_job_model_input
    try:
        final_dj_state_for_output = investigate_and_report(diagnostic_job_model_input)
    except Exception as e_crash: 
        logger.critical(f"[{case_id_main}] Investigator (__main__): CRASH from investigate_and_report(): {e_crash}", exc_info=True)
        
        # In fail-fast, update the job state to reflect the crash,
        # serialize it for debugging, and then exit with non-zero status.
        final_dj_state_for_output.final_job_outcome = f"InvestigatorCrashed_{type(e_crash).__name__}"
        final_dj_state_for_output.current_pipeline_stage = "Investigator_Crashed_CaughtInMain"
        
        output_json_str = final_dj_state_for_output.model_dump_json(
            indent=2 if os.environ.get("SDE_PRETTY_PRINT_JSON", "false").lower() == "true" else None
        )
        sys.stdout.write(output_json_str)
        sys.stdout.flush()
        sys.exit(1) # Exit with a non-zero status code to signal the crash.

    # --- Successful execution path ---
    output_json_str = final_dj_state_for_output.model_dump_json(
        indent=2 if os.environ.get("SDE_PRETTY_PRINT_JSON", "false").lower() == "true" else None
    )
    sys.stdout.write(output_json_str)
    sys.stdout.flush()
    
    logger.info(f"[{final_dj_state_for_output.case_id}] Investigator (__main__): Successfully completed execution.")
    sys.exit(0)
