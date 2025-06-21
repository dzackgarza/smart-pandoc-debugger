#!/usr/bin/env python3
# managers/Oracle.py - SDE V5.1 Oracle Manager
#
# Version: 5.1.4 (Corrected __main__ argparse, uses seer.py V2.0.0)
# Date: 2025-06-25 (Refactored from V5.1.3)
# Author: Diagnostic Systems Group
#
# Philosophy (SDE V5.1 - Development Mode):
#   - Acts as the "Oracle" manager in the SDE V5.1 pipeline.
#   - Receives a full DiagnosticJob JSON object via stdin when called with --process-job.
#   - Iterates through DiagnosticJob.actionable_leads.
#   - For each lead, attempts to generate one or more MarkdownRemedy objects.
#   - Delegates complex error snippet interpretation to `oracle-team/seer.py`.
#   - Populates DiagnosticJob.markdown_remedies.
#   - Outputs the entire, updated DiagnosticJob JSON to stdout.
#   - Adheres to "crash violently" via assertions for development.
#
# Role: THE ORACLE MANAGER
#
# This manager is invoked by the Coordinator if ActionableLeads exist.
# Its primary goal is to transform these leads into concrete, user-guiding
# MarkdownRemedy objects. It does NOT set final_job_outcome itself.
#
# Responsibilities:
#   - Accept a `DiagnosticJob` JSON object.
#   - For each `ActionableLead`:
#     - Analyze lead properties.
#     - If applicable (e.g., for TeX errors with a log excerpt), invoke `oracle-team/seer.py`.
#     - Transform suggestions from `seer.py` (or apply internal heuristics) into `MarkdownRemedy` objects.
#   - Update `DiagnosticJob.markdown_remedies`.
#   - Return the updated `DiagnosticJob` JSON.
#
# Interaction:
#   `Coordinator` -> (pipes DiagnosticJob JSON) -> `Oracle.py --process-job`
#       `Oracle.py` -> (analyzes leads)
#       `Oracle.py` -> (calls `utils.process_runner.run_script` to execute) -> `oracle-team/seer.py`
#   `Coordinator` <- (receives updated DiagnosticJob JSON) <- `Oracle.py`
#
# Interface (when called by manager_runner.py / service_runner.py):
#   Invocation: python3 managers/Oracle.py --process-job
#   Stdin: Full DiagnosticJob JSON string.
#   Stdout: Full, updated DiagnosticJob JSON string.
#   Exit Code: 0 on success; non-zero on assertion failure or specialist crash.
#
# Environment Variables:
#   SDE_SEER_PY_BIN (optional, path to seer.py, defaults to managers/oracle-team/seer.py)
#   DEBUG (optional, for verbose logging, read from environment)
#   TMPDIR (optional, for temporary files used when calling seer.py)
# --------------------------------------------------------------------------------

import argparse
import json
import logging
import os
import sys
import tempfile
import uuid
import datetime
from typing import Dict, List, Any, Optional

# --- Attempt to import SDE utilities ---
try:
    from utils.data_model import DiagnosticJob, ActionableLead, MarkdownRemedy, SourceContextSnippet
    from utils.process_runner import run_script as run_external_specialist_tool
except ModuleNotFoundError:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from utils.data_model import DiagnosticJob, ActionableLead, MarkdownRemedy, SourceContextSnippet
        from utils.process_runner import run_script as run_external_specialist_tool
    except ModuleNotFoundError as e_inner:
        print(f"CRITICAL ORACLE ERROR: Failed to import SDE utilities. Error: {e_inner}", file=sys.stderr)
        class DiagnosticJob: pass # type: ignore
        class ActionableLead: pass # type: ignore
        class MarkdownRemedy: pass # type: ignore
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
    formatter = logging.Formatter('%(asctime)s - ORACLE (%(name)s) - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

# --- Configuration for Specialist Script ---
MANAGERS_DIR = os.path.dirname(os.path.abspath(__file__))
ORACLE_TEAM_DIR = os.path.join(MANAGERS_DIR, "oracle-team")
SEER_PY_PATH = os.environ.get("SDE_SEER_PY_BIN", os.path.join(ORACLE_TEAM_DIR, "seer.py"))

assert os.path.isfile(SEER_PY_PATH), \
    f"CRITICAL ORACLE SETUP ERROR: oracle-team/seer.py not found at {SEER_PY_PATH}"

# --- Helper to create MarkdownRemedy (aligns with data_model.py V5.4.1) ---
def _create_markdown_remedy(
    lead: ActionableLead,
    case_id: str,
    explanation_message: str, # This will be the main user-facing explanation
    confidence: float = 0.7,
    source_tool_tag: str = "OracleManager(internal_heuristic)", # e.g., "OracleManager(seer::brackets)"
    instruction_for_md_fix: Optional[str] = None, # Specific instruction if different from explanation
    suggested_md_after_fix: Optional[str] = None  # Snippet of what MD should look like
) -> MarkdownRemedy:
    """Helper to create a MarkdownRemedy Pydantic object."""
    
    target_md_context: Optional[SourceContextSnippet] = None
    # Try to find Markdown context from the lead if it refers to Markdown.
    # Leads from Investigator (TeX errors) might not have direct MD context yet.
    if lead.primary_context_snippets:
        for snippet in lead.primary_context_snippets:
            if snippet.source_document_type == "markdown":
                target_md_context = snippet
                break
    
    # If instruction_for_md_fix is not given, use a generic one or derive from explanation.
    final_instruction = instruction_for_md_fix or \
                        f"Please review your Markdown based on the following: {explanation_message}"

    remedy_data = {
        # remedy_id uses Pydantic default_factory
        "applies_to_lead_id": lead.lead_id,
        "source_service": source_tool_tag, # Aligns with ActionableLead.source_service
        "explanation": explanation_message,
        "instruction_for_markdown_fix": final_instruction,
        "markdown_context_to_change": target_md_context,
        "suggested_markdown_after_fix": suggested_md_after_fix,
        "confidence_score": confidence, # Renamed from confidence to confidence_score in data_model.py? Assuming so.
        # timestamp_generated uses Pydantic default_factory or can be added
        # user_feedback is Optional
        # notes: Optional[str] = Field(None, ...)
    }
    return MarkdownRemedy(**remedy_data)


# --- Main Processing Function ---
def process_diagnostic_job(diagnostic_job: DiagnosticJob) -> DiagnosticJob:
    logger.info(f"[{diagnostic_job.case_id}] Oracle: Starting processing. Number of leads: {len(diagnostic_job.actionable_leads or [])}")

    assert isinstance(diagnostic_job.actionable_leads, list), \
        "Oracle received DiagnosticJob where actionable_leads is not a list."

    if diagnostic_job.markdown_remedies is None:
        diagnostic_job.markdown_remedies = []

    for lead in diagnostic_job.actionable_leads:
        assert isinstance(lead, ActionableLead), f"Item in actionable_leads is not an ActionableLead: {type(lead)}"
        logger.info(f"[{diagnostic_job.case_id}] Oracle: Processing lead ID {lead.lead_id}, source: {lead.source_service}, problem: '{lead.problem_description[:70]}...'")

        remedies_for_this_lead: List[MarkdownRemedy] = []
        lead_raw_log_excerpt: Optional[str] = None

        # Extract raw_log_excerpt if available (might be in primary_context_snippets or internal_details_for_oracle)
        if lead.primary_context_snippets:
            for snippet in lead.primary_context_snippets:
                if snippet.source_document_type == "tex_compilation_log" or \
                   snippet.source_document_type == "md_to_tex_log":
                    lead_raw_log_excerpt = snippet.snippet_text
                    break
        if not lead_raw_log_excerpt and lead.internal_details_for_oracle:
            # Fallback check if older lead format might put it here
            lead_raw_log_excerpt = lead.internal_details_for_oracle.get("raw_pandoc_output_for_oracle") or \
                                   lead.internal_details_for_oracle.get("raw_log_excerpt")


        # --- Internal Heuristics (Example for Pandoc MD-to-TeX failure from Miner) ---
        if lead.source_service == "Miner" and \
           lead.internal_details_for_oracle and \
           lead.internal_details_for_oracle.get("tool") == "pandoc" and \
           lead.internal_details_for_oracle.get("stage") == "md-to-tex":
            
            remedies_for_this_lead.append(_create_markdown_remedy(
                lead=lead, case_id=diagnostic_job.case_id,
                explanation_message=f"Pandoc (Markdown-to-TeX converter) failed. This usually means there's an issue with your Markdown syntax that Pandoc cannot process for LaTeX output. Review the Pandoc error log (if available in the lead's context) and your Markdown document for complex or malformed structures (e.g., tables, lists, raw TeX blocks, special characters). The error started with: '{(lead.problem_description or 'Pandoc error')[:150]}...'",
                confidence=0.65,
                source_tool_tag="OracleManager(internal_pandoc_rules)"
            ))

        # --- Delegate to seer.py for leads with a snippet suitable for its analysis ---
        # Typically, these are TeX error leads from Investigator which have a log excerpt.
        elif lead_raw_log_excerpt and lead_raw_log_excerpt.strip():
            logger.info(f"[{diagnostic_job.case_id}] Oracle: Lead {lead.lead_id} has a log excerpt. Invoking seer.py.")
            
            error_line_from_lead = "unknown"
            if lead.internal_details_for_oracle and lead.internal_details_for_oracle.get("tex_error_line_reported_by_tool"):
                error_line_from_lead = str(lead.internal_details_for_oracle.get("tex_error_line_reported_by_tool", "unknown"))
            elif lead.primary_context_snippets: # Check primary contexts for line number
                for snippet_ctx in lead.primary_context_snippets:
                    if snippet_ctx.source_document_type == "generated_tex" and snippet_ctx.central_line_number is not None:
                        error_line_from_lead = str(snippet_ctx.central_line_number)
                        break
            
            tmp_snippet_file_path = "" # Ensure it's defined for finally block
            try:
                # Write snippet to a temporary file for seer.py
                with tempfile.NamedTemporaryFile(mode="w", delete=False, prefix="oracle_seer_snippet_", suffix=".log", encoding='utf-8', dir=os.environ.get("TMPDIR")) as tmp_snippet_file:
                    tmp_snippet_file.write(lead_raw_log_excerpt)
                    tmp_snippet_file_path = tmp_snippet_file.name
                
                command_parts_for_seer = [
                    sys.executable, SEER_PY_PATH,
                    "--error-snippet-file", tmp_snippet_file_path,
                    "--error-line", error_line_from_lead
                ]
                
                seer_suggestions_list: List[Dict[str, Any]] = run_external_specialist_tool(
                    command_parts=command_parts_for_seer,
                    expect_json_output=True
                )
            except Exception as e_seer_call:
                logger.error(f"[{diagnostic_job.case_id}] Oracle: Failed to invoke or process output from seer.py for lead {lead.lead_id}. Error: {e_seer_call}", exc_info=True)
                seer_suggestions_list = [] # Proceed with no suggestions from seer
            finally:
                if tmp_snippet_file_path and os.path.exists(tmp_snippet_file_path):
                    os.remove(tmp_snippet_file_path)

            assert isinstance(seer_suggestions_list, list), \
                f"seer.py (for lead {lead.lead_id}) did not return a JSON list. Got: {type(seer_suggestions_list)}"

            logger.info(f"[{diagnostic_job.case_id}] Oracle: seer.py returned {len(seer_suggestions_list)} suggestions for lead {lead.lead_id}.")

            for suggestion in seer_suggestions_list:
                assert isinstance(suggestion, dict), f"Suggestion from seer.py is not a dictionary: {suggestion}"
                msg = suggestion.get("message", "Seer.py provided a suggestion without a clear message.")
                conf = float(suggestion.get("confidence", 0.5))
                origin = suggestion.get("origin", "seer.py::unknown_rule")
                
                remedies_for_this_lead.append(_create_markdown_remedy(
                    lead=lead, case_id=diagnostic_job.case_id,
                    explanation_message=msg, # Seer's message becomes the remedy explanation
                    confidence=conf,
                    source_tool_tag=f"OracleManager({origin})"
                ))
        
        if not remedies_for_this_lead:
            logger.warning(f"[{diagnostic_job.case_id}] Oracle: No specific remedies generated for lead ID {lead.lead_id} (source: {lead.source_service}, problem: '{lead.problem_description[:70]}...'). Creating generic guidance.")
            remedies_for_this_lead.append(_create_markdown_remedy(
                lead=lead, case_id=diagnostic_job.case_id,
                explanation_message=f"An issue was identified: '{lead.problem_description}'. Review your Markdown source, especially any content related to this problem description or any provided context snippets from the lead. Specific automated fix suggestions are not yet available for this particular lead.",
                confidence=0.25,
                source_tool_tag="OracleManager(generic_guidance)"
            ))
        
        if not isinstance(diagnostic_job.markdown_remedies, list):
             diagnostic_job.markdown_remedies = []
        diagnostic_job.markdown_remedies.extend(remedies_for_this_lead)

    diagnostic_job.current_pipeline_stage = "OracleManager_Complete"
    logger.info(f"[{diagnostic_job.case_id}] Oracle: Processing finished. Total remedies in job: {len(diagnostic_job.markdown_remedies or [])}")
    return diagnostic_job

# --- Script Entry Point ---
if __name__ == "__main__":
    # Oracle Manager is invoked by manager_runner (or service_runner)
    # It only expects --process-job.
    # Arguments like --error-snippet are for its specialist tools (e.g., seer.py), NOT for Oracle.py itself.
    parser = argparse.ArgumentParser(description="SDE Oracle Manager: Generates remedies from actionable leads.")
    parser.add_argument(
        "--process-job",
        action="store_true",
        help="Process a DiagnosticJob JSON from stdin and output updated JSON to stdout."
    )
    args = parser.parse_args() # This will show help if --process-job is missing or if unknown args are given.

    if args.process_job:
        initial_job_json_str = ""
        try:
            initial_job_json_str = sys.stdin.read()
            assert initial_job_json_str, "Oracle (--process-job): Received empty stdin."
            diagnostic_job_input = DiagnosticJob.model_validate_json(initial_job_json_str) # Can raise Pydantic ValidationError
            
            diagnostic_job_output = process_diagnostic_job(diagnostic_job_input)
            
            sys.stdout.write(diagnostic_job_output.model_dump_json())
            logger.info(f"[{getattr(diagnostic_job_output, 'case_id', 'unknown')}] Oracle: Successfully completed --process-job execution.")
            sys.exit(0)
        except AssertionError as e: # Catches our own explicit assertions
            logger.error(f"Oracle (--process-job): Assertion Error: {e}", exc_info=True)
            print(f"Oracle Assertion Error: {e}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e_json: # From model_validate_json if input is not JSON
            logger.error(f"Oracle (--process-job): JSONDecodeError: {e_json}. Input snippet: '{initial_job_json_str[:200]}...'", exc_info=True)
            print(f"Oracle JSONDecodeError: {e_json}", file=sys.stderr)
            sys.exit(1)
        except Exception as e_main: # Catches Pydantic ValidationError, or errors from process_job
            case_id_for_error = "unknown_case_oracle_main"
            try: 
                temp_data = json.loads(initial_job_json_str)
                case_id_for_error = temp_data.get("case_id", "unknown_case_in_json")
            except: pass
            logger.error(f"[{case_id_for_error}] Oracle (--process-job): Unexpected error: {type(e_main).__name__} - {e_main}", exc_info=True)
            print(f"Oracle Unexpected Error: {type(e_main).__name__} - {e_main}", file=sys.stderr)
            sys.exit(1)
    else:
        # This path is taken if script is run without --process-job (e.g. direct run with -h)
        logger.warning("Oracle: Not called with --process-job. Displaying help. This is expected if testing manager directly or asking for help.")
        parser.print_help(sys.stderr) # Print help to stderr as it's informational/error for this invocation path
        sys.exit(2) # Standard exit code for CLI usage error
