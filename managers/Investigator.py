#!/usr/bin/env python3
# managers/Investigator.py - SDE Investigator Manager
#
# Version: 5.1.6 (Aligned with data_model.py V5.4.1, SDE V5.1.3 Coordinator)
# Date: 2025-06-25 (Updated from V5.1.5)
# Author: Diagnostic Systems Group
#
# Philosophy (SDE V5.1 - Development Mode):
#   - Acts as the "Investigator" manager in the SDE pipeline.
#   - Receives a full DiagnosticJob JSON object via stdin when called with --process-job.
#   - Analyzes LaTeX compilation logs (from DiagnosticJob.tex_compiler_raw_log) by
#     delegating to `investigator-team/error_finder.py` if TeX compilation failed.
#   - Populates DiagnosticJob.actionable_leads with findings, adhering to data_model.py V5.4.1.
#   - Updates DiagnosticJob.final_job_outcome.
#   - Outputs the entire, updated DiagnosticJob JSON to stdout.
#   - Adheres to "crash violently" via assertions for development.
#
# Role: THE LOG INVESTIGATION MANAGER
#
# Invoked by Coordinator if TeX-to-PDF compilation fails. Analyzes TeX logs via
# `error_finder.py` to create `ActionableLead` objects.
#
# Responsibilities:
#   - Accept a `DiagnosticJob`.
#   - If TeX failed, manage temp files for `error_finder.py`.
#   - Invoke `error_finder.py`.
#   - Transform JSON output from `error_finder.py` into `ActionableLead` Pydantic models.
#   - Update `DiagnosticJob.actionable_leads` and `DiagnosticJob.final_job_outcome`.
#   - Return updated `DiagnosticJob` JSON.
#
# Interaction:
#   `Coordinator` -> (pipes DiagnosticJob JSON) -> `Investigator.py --process-job`
#       `Investigator.py` -> (calls `utils.process_runner.run_script` to execute) -> `investigator-team/error_finder.py`
#   `Coordinator` <- (receives updated DiagnosticJob JSON) <- `Investigator.py`
#
# Interface (when called by manager_runner.py / service_runner.py):
#   Invocation: python3 managers/Investigator.py --process-job
#   Stdin: Full DiagnosticJob JSON string.
#   Stdout: Full, updated DiagnosticJob JSON string.
#   Exit Code: 0 on success; non-zero on assertion failure or specialist crash.
#
# Environment Variables:
#   TMPDIR (optional, for temporary files)
#   DEBUG (optional, for verbose logging, read from environment)
# --------------------------------------------------------------------------------

import argparse
import json
import logging
import os
import sys
import tempfile
import uuid # For generating lead_ids (though ActionableLead now has default_factory)
from typing import Dict, List, Any, Optional

# --- Attempt to import SDE utilities ---
try:
    from utils.data_model import DiagnosticJob, ActionableLead, SourceContextSnippet
    from utils.process_runner import run_script as run_external_specialist_tool
except ModuleNotFoundError:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from utils.data_model import DiagnosticJob, ActionableLead, SourceContextSnippet
        from utils.process_runner import run_script as run_external_specialist_tool
    except ModuleNotFoundError as e_inner:
        print(f"CRITICAL INVESTIGATOR ERROR: Failed to import SDE utilities. Error: {e_inner}", file=sys.stderr)
        # Define dummy classes to allow script to parse args but fail functionally.
        class DiagnosticJob: pass # type: ignore
        class ActionableLead: pass # type: ignore
        class SourceContextSnippet: pass # type: ignore
        def run_external_specialist_tool(*args, **kwargs) -> Dict[str, Any]: # type: ignore
            raise NotImplementedError("Dummy run_external_specialist_tool due to import failure.")

# --- Logging Setup ---
DEBUG_ENV = os.environ.get("DEBUG", "false").lower()
APP_LOG_LEVEL = logging.INFO if DEBUG_ENV == "true" else logging.WARNING

logger = logging.getLogger(__name__)
logger.setLevel(APP_LOG_LEVEL)

if not logging.getLogger().hasHandlers() and not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(asctime)s - INVESTIGATOR (%(name)s) - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

# --- Configuration for Specialist Script ---
MANAGERS_DIR = os.path.dirname(os.path.abspath(__file__))
INVESTIGATOR_TEAM_DIR = os.path.join(MANAGERS_DIR, "investigator-team")
ERROR_FINDER_PY_PATH = os.path.join(INVESTIGATOR_TEAM_DIR, "error_finder.py")

assert os.path.isfile(ERROR_FINDER_PY_PATH), \
    f"CRITICAL INVESTIGATOR SETUP ERROR: investigator-team/error_finder.py not found at {ERROR_FINDER_PY_PATH}"

# --- Outcome Constants ---
OUTCOME_TEX_ERROR_REMEDIES_FOUND = "TexCompilationError_RemediesProvided" # If leads are found
OUTCOME_TEX_ERROR_NO_LEADS = "TexCompilationError_NoLeadsFound" # If TeX failed but no specific leads
OUTCOME_SPECIALIST_TOOL_FAILURE = "InvestigatorSpecialistToolFailure"

# --- Helper Function for TeX Snippet (retained for context creation) ---
def _create_source_context_snippet(
    content: str,
    line_number_str: str,
    source_type: str, # e.g., "generated_tex", "tex_compilation_log"
    window: int = 2
) -> Optional[SourceContextSnippet]:
    """Creates a SourceContextSnippet Pydantic model from content and line number."""
    if not content or not line_number_str.isdigit():
        if line_number_str != "unknown": # Only log if it was supposed to be a number
             logger.debug(f"Cannot create snippet for {source_type}: content empty or line '{line_number_str}' not a digit.")
        return None
    
    target_line_num = int(line_number_str)
    lines = content.splitlines()
    
    if not (1 <= target_line_num <= len(lines)): # Line numbers are 1-based
        logger.debug(f"Line number {target_line_num} out of bounds for {source_type} (total lines: {len(lines)}).")
        return None

    target_line_idx = target_line_num - 1 # Convert to 0-based index
    start_idx = max(0, target_line_idx - window)
    end_idx = min(len(lines), target_line_idx + window + 1)
    
    snippet_lines = [f"{'>> ' if i == target_line_idx else '   '}l.{i+1} {lines[i]}" for i in range(start_idx, end_idx)]
    snippet_text = "\n".join(snippet_lines)

    return SourceContextSnippet(
        source_document_type=source_type,
        central_line_number=target_line_num,
        snippet_text=snippet_text
    )

# --- Main Processing Function ---
def process_diagnostic_job(diagnostic_job: DiagnosticJob) -> DiagnosticJob:
    logger.info(f"[{diagnostic_job.case_id}] Investigator: Starting processing.")

    assert diagnostic_job.md_to_tex_conversion_successful, \
        "Investigator precondition failed: MD-to-TeX must be successful."
    assert not diagnostic_job.tex_to_pdf_compilation_successful, \
        "Investigator precondition failed: TeX-to-PDF must have been unsuccessful."
    assert diagnostic_job.tex_compiler_raw_log is not None, \
        "Investigator precondition failed: tex_compiler_raw_log is missing."
    assert diagnostic_job.generated_tex_content is not None, \
        "Investigator precondition failed: generated_tex_content is missing."

    log_content = diagnostic_job.tex_compiler_raw_log
    tex_content = diagnostic_job.generated_tex_content
    newly_found_leads: List[ActionableLead] = []

    with tempfile.TemporaryDirectory(prefix="sde_investigator_ef_", dir=os.environ.get("TMPDIR")) as tmp_dir_path:
        tmp_log_file_path = os.path.join(tmp_dir_path, "input.log")
        tmp_tex_file_path = os.path.join(tmp_dir_path, "input.tex")

        with open(tmp_log_file_path, "w", encoding='utf-8') as f_log: f_log.write(log_content)
        with open(tmp_tex_file_path, "w", encoding='utf-8') as f_tex: f_tex.write(tex_content)
        
        logger.info(f"[{diagnostic_job.case_id}] Investigator: Calling specialist 'investigator-team/error_finder.py' with log '{tmp_log_file_path}' and tex '{tmp_tex_file_path}'")
        
        error_findings: Dict[str, Any] = run_external_specialist_tool(
            command_parts=[
                sys.executable, ERROR_FINDER_PY_PATH,
                "--log-file", tmp_log_file_path,
                "--tex-file", tmp_tex_file_path
            ],
            expect_json_output=True
        )
        
        assert isinstance(error_findings, dict), \
            f"utils.process_runner.run_script (for error_finder.py) did not return a dict. Got: {type(error_findings)}"

        error_line_in_tex_str = error_findings.get("error_line_in_tex", "unknown")
        log_excerpt_str = error_findings.get("log_excerpt", "")
        error_signature = error_findings.get("error_signature", "LATEX_UNKNOWN_ERROR")
        raw_error_message = error_findings.get("raw_error_message") # This is the primary error line from log

        primary_context_snippets_for_lead: List[SourceContextSnippet] = []
        
        # Create context snippet from TeX source if line number is known
        tex_context_snippet = _create_source_context_snippet(
            content=tex_content,
            line_number_str=error_line_in_tex_str,
            source_type="generated_tex"
        )
        if tex_context_snippet:
            primary_context_snippets_for_lead.append(tex_context_snippet)

        # Create context snippet from the log excerpt itself
        if log_excerpt_str:
            log_context_snippet = SourceContextSnippet(
                source_document_type="tex_compilation_log",
                # central_line_number for log snippet might be harder to pinpoint relative to whole log,
                # can be omitted or set if error_finder provides it.
                snippet_text=log_excerpt_str 
            )
            primary_context_snippets_for_lead.append(log_context_snippet)
        
        # Determine if a meaningful lead was found by error_finder.py
        if error_signature == "ERROR_FINDER_LOG_READ_FAILURE":
            diagnostic_job.final_job_outcome = OUTCOME_SPECIALIST_TOOL_FAILURE
            problem_desc = f"Specialist tool 'error_finder.py' failed to process log. Details: {log_excerpt_str or raw_error_message or 'Unknown tool error'}"
            logger.error(f"[{diagnostic_job.case_id}] Investigator: {problem_desc}")
            lead = ActionableLead(
                # lead_id uses default_factory
                source_service="InvestigatorManager", # As per data_model.py V5.4.1
                problem_description=problem_desc,
                primary_context_snippets=primary_context_snippets_for_lead, # Might be empty if error_finder fails early
                internal_details_for_oracle={
                    "error_signature_code_from_tool": error_signature,
                    "tool_name": "error_finder.py"
                }
            )
            newly_found_leads.append(lead)
        elif raw_error_message: # If error_finder identified a primary error message
            problem_desc = raw_error_message # Use the direct error message as problem_description
            
            lead = ActionableLead(
                source_service="InvestigatorManager",
                problem_description=problem_desc,
                primary_context_snippets=primary_context_snippets_for_lead,
                internal_details_for_oracle={
                    "error_signature_code_from_tool": error_signature,
                    "tex_error_line_reported_by_tool": error_line_in_tex_str,
                    "tool_name": "error_finder.py"
                    # raw_log_excerpt is now part of primary_context_snippets
                }
            )
            newly_found_leads.append(lead)
            diagnostic_job.final_job_outcome = OUTCOME_TEX_ERROR_REMEDIES_FOUND # TeX error, leads found
            logger.info(f"[{diagnostic_job.case_id}] Investigator: Lead created based on error_finder.py. Signature: {error_signature}")
        else: # error_finder.py ran but did not identify a raw_error_message
            diagnostic_job.final_job_outcome = OUTCOME_TEX_ERROR_NO_LEADS # TeX error, but no specific leads
            logger.warning(f"[{diagnostic_job.case_id}] Investigator: error_finder.py found no specific 'raw_error_message'. Signature: {error_signature}. Log excerpt: {log_excerpt_str or 'N/A'}")

    if not isinstance(diagnostic_job.actionable_leads, list):
        diagnostic_job.actionable_leads = []
    diagnostic_job.actionable_leads.extend(newly_found_leads)
    
    diagnostic_job.current_pipeline_stage = "InvestigatorManager_Complete"
    logger.info(f"[{diagnostic_job.case_id}] Investigator: Processing finished. Total leads in job: {len(diagnostic_job.actionable_leads)}. Outcome: {diagnostic_job.final_job_outcome}")
    return diagnostic_job

# --- Script Entry Point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDE Investigator Manager: Analyzes TeX compilation logs using error_finder.py.")
    parser.add_argument(
        "--process-job", action="store_true",
        help="Process a DiagnosticJob JSON from stdin and output updated JSON to stdout."
    )
    args = parser.parse_args()

    if args.process_job:
        initial_job_json_str = ""
        try:
            initial_job_json_str = sys.stdin.read()
            assert initial_job_json_str, "Investigator (--process-job): Received empty stdin."
            diagnostic_job_input = DiagnosticJob.model_validate_json(initial_job_json_str)
            diagnostic_job_output = process_diagnostic_job(diagnostic_job_input)
            sys.stdout.write(diagnostic_job_output.model_dump_json())
            logger.info(f"[{getattr(diagnostic_job_output, 'case_id', 'unknown')}] Investigator: Successfully completed --process-job execution.")
            sys.exit(0)
        except AssertionError as e:
            logger.error(f"Investigator (--process-job): Assertion Error: {e}", exc_info=True)
            print(f"Investigator Assertion Error: {e}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e_json:
            logger.error(f"Investigator (--process-job): JSONDecodeError: {e_json}. Input snippet: '{initial_job_json_str[:200]}...'", exc_info=True)
            print(f"Investigator JSONDecodeError: {e_json}", file=sys.stderr)
            sys.exit(1)
        except Exception as e_main: # Catches Pydantic ValidationError from model_validate_json or process_job
            case_id_for_error = "unknown_case"
            try: temp_data = json.loads(initial_job_json_str); case_id_for_error = temp_data.get("case_id", "unknown_case_in_json")
            except: pass
            logger.error(f"[{case_id_for_error}] Investigator (--process-job): Unexpected error: {type(e_main).__name__} - {e_main}", exc_info=True)
            print(f"Investigator Unexpected Error: {type(e_main).__name__} - {e_main}", file=sys.stderr)
            sys.exit(1)
    else:
        logger.warning("Investigator: Not called with --process-job. Displaying help.")
        parser.print_help(sys.stderr)
        sys.exit(2)
