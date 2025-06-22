#!/usr/bin/env python3
# managers/Oracle.py - SDE V5.1 Oracle Manager
#
# HACKATHON MODE: This version is simplified to bypass specialist tools
# and provide direct, hardcoded remedies based on error signatures.
#
import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional

# --- Attempt to import SDE utilities ---
try:
    from utils.data_model import DiagnosticJob, ActionableLead, MarkdownRemedy
except ModuleNotFoundError:
    # If the script is run directly, the utils module might not be in the Python path.
    # Add the project root to the path.
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir) # This should be the 'smart-pandoc-debugger' directory
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        from utils.data_model import DiagnosticJob, ActionableLead, MarkdownRemedy
    except ModuleNotFoundError as e:
        print(f"CRITICAL ORACLE ERROR: Failed to import SDE utilities even after path correction. Error: {e}", file=sys.stderr)
        sys.exit(1) # Exit if we can't import data models

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

# --- Main Processing Function (Hackathon Mode) ---
def consult_the_oracle(diagnostic_job: DiagnosticJob) -> DiagnosticJob:
    """
    The Oracle's main function to analyze leads and provide remedies.
    In hackathon mode, this is simplified to bypass specialist tools.
    """
    logger.info(f"[{diagnostic_job.case_id}] Oracle: Consulting the simplified hackathon oracle with {len(diagnostic_job.actionable_leads)} lead(s).")
    
    if diagnostic_job.markdown_remedies is None:
        diagnostic_job.markdown_remedies = []
    
    if not diagnostic_job.actionable_leads:
        logger.warning(f"[{diagnostic_job.case_id}] Oracle: No actionable leads were provided. Nothing to do.")
        diagnostic_job.final_job_outcome = "NoActionableLeads_OracleBypassed"
        return diagnostic_job

    for lead in diagnostic_job.actionable_leads:
        error_signature = None
        if lead.internal_details_for_oracle:
            error_signature = lead.internal_details_for_oracle.get("error_signature_code_from_tool")
        
        logger.info(f"[{diagnostic_job.case_id}] Oracle: Processing lead {lead.lead_id} with signature: {error_signature}")

        remedy_explanation = None
        instruction_for_fix = None
        # This maps the signature from error_finder.py to the expected test output
        if error_signature == "LATEX_MISSING_DOLLAR":
            remedy_explanation = "Missing math delimiters"
            instruction_for_fix = "Check for math expressions that are not enclosed in '$...$' or '$$...$$'."
        elif error_signature == "LATEX_UNDEFINED_CONTROL_SEQUENCE":
            remedy_explanation = "Undefined control sequence"
            instruction_for_fix = "This error means you used a LaTeX command (like \\this) that isn't defined. Check for typos in the command name or ensure the necessary package is included in your Pandoc template or metadata."
        elif error_signature == "LATEX_MISMATCHED_DELIMITERS":
            remedy_explanation = "Mismatched delimiters"
            instruction_for_fix = "You have a mismatch in paired delimiters like parentheses, brackets, or braces. For example, using '\\left(' with '\\right]' instead of '\\right)'. Check your math expressions for these mismatches."
        elif error_signature == "LATEX_RUNAWAY_ARGUMENT":
            remedy_explanation = "Runaway argument?"
            instruction_for_fix = "This error usually means you have a command with a missing closing brace '}'. LaTeX reads until the end of the file looking for it. Find the command and add the closing brace."
        elif error_signature in ["LATEX_TOO_MANY_CLOSING_BRACES", "LATEX_EXTRA_BRACE_OR_FORGOTTEN_DOLLAR", "LATEX_UNEXPECTED_PARAGRAPH_END", "LATEX_UNBALANCED_BRACES"]:
            remedy_explanation = "Unbalanced braces"
            instruction_for_fix = "You have an unequal number of opening and closing curly braces '{' and '}'. Check your document for LaTeX commands or math expressions where you may have forgotten a brace or added an extra one."
        
        if remedy_explanation:
            remedy = MarkdownRemedy(
                applies_to_lead_id=lead.lead_id,
                source_service="OracleManager_HackathonMode",
                explanation=f"A '{remedy_explanation}' error was detected. This is a common issue when compiling LaTeX.",
                instruction_for_markdown_fix=instruction_for_fix or f"Please check your Markdown file for the '{remedy_explanation}' error. For example, ensure all math environments are properly enclosed in '$' or '$$' and that all brackets and braces are correctly paired.",
                markdown_context_to_change=None,
                suggested_markdown_after_fix=None,
                confidence_score=0.99,
                notes=f"Generated from signature: {error_signature}"
            )
            diagnostic_job.markdown_remedies.append(remedy)
            logger.info(f"[{diagnostic_job.case_id}] Oracle: Generated hackathon remedy for lead {lead.lead_id}: '{remedy_explanation}'")
        else:
            logger.warning(f"[{diagnostic_job.case_id}] Oracle: No hackathon remedy defined for signature: {error_signature}")

    if diagnostic_job.markdown_remedies:
        diagnostic_job.final_job_outcome = "TexCompilationError_RemediesProvided"
    else:
        # If leads were present but no remedies were generated
        diagnostic_job.final_job_outcome = "TexCompilationError_NoRemediesFound"
        
    diagnostic_job.current_pipeline_stage = "OracleManager_Complete"
    logger.info(f"[{diagnostic_job.case_id}] Oracle: Processing finished. Total remedies: {len(diagnostic_job.markdown_remedies)}")
    return diagnostic_job

# --- Script Entry Point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDE Oracle Manager: Generates remedies from actionable leads.")
    parser.add_argument(
        "--process-job",
        action="store_true",
        help="Process a DiagnosticJob JSON from stdin and output updated JSON to stdout."
    )
    args = parser.parse_args()

    if args.process_job:
        initial_job_json_str = ""
        try:
            initial_job_json_str = sys.stdin.read()
            assert initial_job_json_str, "Oracle (--process-job): Received empty stdin."
            
            diagnostic_job_input = DiagnosticJob.model_validate_json(initial_job_json_str)
            
            # Call the main logic function
            diagnostic_job_output = consult_the_oracle(diagnostic_job_input)
            
            sys.stdout.write(diagnostic_job_output.model_dump_json(indent=2))
            logger.info(f"[{getattr(diagnostic_job_output, 'case_id', 'unknown')}] Oracle: Successfully completed --process-job execution.")
            sys.exit(0)
        except Exception as e_main:
            case_id_for_error = "unknown_case_oracle_main"
            try: 
                temp_data = json.loads(initial_job_json_str)
                case_id_for_error = temp_data.get("case_id", "unknown_case_in_json")
            except: pass
            logger.error(f"[{case_id_for_error}] Oracle (--process-job): Unexpected error: {type(e_main).__name__} - {e_main}", exc_info=True)
            print(f"Oracle Unexpected Error: {type(e_main).__name__} - {e_main}", file=sys.stderr)
            sys.exit(1)
    else:
        logger.warning("Oracle: Not called with --process-job. Displaying help.")
        parser.print_help(sys.stderr)
        sys.exit(2)
