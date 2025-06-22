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
    from utils.data_model import DiagnosticJob, ActionableLead, MarkdownRemedy, SourceContextSnippet
    from managers.oracle_team.seer import extract_primary_error_details
except ModuleNotFoundError:
    # If the script is run directly, the utils module might not be in the Python path.
    # Add the project root to the path.
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_script_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        from utils.data_model import DiagnosticJob, ActionableLead, MarkdownRemedy, SourceContextSnippet
        from managers.oracle_team.seer import extract_primary_error_details
    except ModuleNotFoundError as e:
        print(f"CRITICAL ORACLE ERROR: Failed to import SDE utilities or Seer specialist. Error: {e}", file=sys.stderr)
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
    It now uses the 'seer' specialist to analyze raw TeX logs if present.
    """
    logger.info(f"[{diagnostic_job.case_id}] Oracle: Consulting with {len(diagnostic_job.actionable_leads or [])} initial lead(s).")
    
    try:
        # If a raw TeX log is available from a failed compilation, analyze it first.
        if diagnostic_job.tex_compiler_raw_log and not diagnostic_job.tex_to_pdf_compilation_successful:
            logger.info(f"[{diagnostic_job.case_id}] Oracle: Found raw TeX log. Delegating to Seer for analysis.")
            
            seer_findings = extract_primary_error_details(diagnostic_job.tex_compiler_raw_log)
            
            if seer_findings and seer_findings.get("raw_error_message"):
                # --- BEGIN DEBUG LOGGING (DO NOT REMOVE - Heisenbug) ---
                logger.info(f"[{diagnostic_job.case_id}] Oracle: Seer raw findings: {json.dumps(seer_findings, indent=2)}")
                # --- END DEBUG LOGGING ---
                logger.info(f"[{diagnostic_job.case_id}] Oracle: Seer found primary error: {seer_findings['raw_error_message']}")
                
                # Convert line number safely
                line_num_str = seer_findings.get('error_line_in_tex')
                line_num = int(line_num_str) if line_num_str and line_num_str.isdigit() else None

                # Ensure all values in seer_findings are strings for internal_details_for_oracle
                safe_seer_findings = {k: str(v) for k, v in seer_findings.items()}

                # Create a new, high-confidence lead based on the Seer's direct analysis.
                # This lead becomes the primary focus for generating a remedy.
                oracle_lead = ActionableLead(
                    source_service="Oracle",
                    problem_description=f"Primary TeX compilation error identified: {seer_findings['raw_error_message']}",
                    primary_context_snippets=[
                        SourceContextSnippet(
                            source_document_type="tex_compilation_log",
                            central_line_number=line_num,
                            snippet_text=seer_findings.get('log_excerpt') or "N/A"
                        )
                    ],
                    internal_details_for_oracle=safe_seer_findings, # Pass all seer findings for internal use
                    confidence_score=0.95
                )
                if diagnostic_job.actionable_leads is None:
                    diagnostic_job.actionable_leads = []
                diagnostic_job.actionable_leads.append(oracle_lead)

        if diagnostic_job.markdown_remedies is None:
            diagnostic_job.markdown_remedies = []
        
        if not diagnostic_job.actionable_leads:
            logger.warning(f"[{diagnostic_job.case_id}] Oracle: No actionable leads were provided. Nothing to do.")
            diagnostic_job.final_job_outcome = "NoActionableLeads_OracleBypassed"
            return diagnostic_job

        for lead in diagnostic_job.actionable_leads:
            raw_error = None
            if lead.internal_details_for_oracle:
                raw_error = lead.internal_details_for_oracle.get("raw_error_message")
            
            logger.info(f"[{diagnostic_job.case_id}] Oracle: Processing lead {lead.lead_id} with raw error: {raw_error}")

            remedy_explanation = None
            instruction_for_fix = None
            
            # This logic now checks the raw message found by our Seer.
            if raw_error:
                if "Missing $" in raw_error:
                    remedy_explanation = "Missing math delimiters"
                    instruction_for_fix = "Check for math expressions that are not enclosed in '$...$' or '$$...$$'."
                elif "Undefined control sequence" in raw_error:
                    remedy_explanation = "Undefined control sequence"
                    instruction_for_fix = "This error means you used a LaTeX command (like \\this) that isn't defined. Check for typos in the command name or ensure the necessary package is included in your Pandoc template or metadata."
                elif "Mismatched" in raw_error: # A more generic check
                    remedy_explanation = "Mismatched delimiters"
                    instruction_for_fix = "You have a mismatch in paired delimiters like parentheses, brackets, or braces. For example, using '\\left(' with '\\right]' instead of '\\right)'. Check your math expressions for these mismatches."
                elif "Runaway argument" in raw_error:
                    remedy_explanation = "Runaway argument?"
                    instruction_for_fix = "This error usually means you have a command with a missing closing brace '}'. LaTeX reads until the end of the file looking for it. Find the command and add the closing brace."
                elif "Unbalanced braces" in raw_error or "Too many }" in raw_error:
                    remedy_explanation = "Unbalanced braces"
                    instruction_for_fix = "You have an unequal number of opening and closing curly braces '{' and '}'. Check your document for LaTeX commands or math expressions where you may have forgotten a brace or added an extra one."

            if remedy_explanation:
                remedy = MarkdownRemedy(
                    applies_to_lead_id=lead.lead_id,
                    source_service="OracleManager",
                    explanation=f"A '{remedy_explanation}' error was detected. This is a common issue when compiling LaTeX.",
                    instruction_for_markdown_fix=instruction_for_fix or "No specific instruction available.",
                    markdown_context_to_change=None,
                    suggested_markdown_after_fix=None,
                    confidence_score=0.90,
                    notes=f"Generated from raw error: {raw_error}"
                )
                diagnostic_job.markdown_remedies.append(remedy)
                logger.info(f"[{diagnostic_job.case_id}] Oracle: Generated remedy for lead {lead.lead_id}: '{remedy_explanation}'")
            else:
                logger.warning(f"[{diagnostic_job.case_id}] Oracle: No remedy defined for raw error: {raw_error}")

        if diagnostic_job.markdown_remedies:
            diagnostic_job.final_job_outcome = "TexCompilationError_RemediesProvided"
        else:
            # If leads were present but no remedies were generated
            diagnostic_job.final_job_outcome = "TexCompilationError_NoRemediesFound"
            
    except Exception as e:
        logger.error(f"[{diagnostic_job.case_id}] Oracle: CRASHED during processing. Error: {e}", exc_info=True)
        diagnostic_job.final_job_outcome = "OracleError_UnhandledException"
        # Also add a remedy to inform the user of the crash
        crash_remedy = MarkdownRemedy(
            applies_to_lead_id=None,
            source_service="OracleManager",
            explanation="The Oracle itself encountered an internal error while analyzing your document.",
            instruction_for_markdown_fix=f"Please report this as a bug. Details: {type(e).__name__}: {e}",
            confidence_score=1.0,
            notes="This remedy indicates a failure within the Smart Diagnostic Engine, not your document."
        )
        if diagnostic_job.markdown_remedies is None:
            diagnostic_job.markdown_remedies = []
        diagnostic_job.markdown_remedies.append(crash_remedy)


    diagnostic_job.current_pipeline_stage = "OracleManager_Complete"
    logger.info(f"[{diagnostic_job.case_id}] Oracle: Processing finished. Total remedies: {len(diagnostic_job.markdown_remedies or [])}")
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
            sys.stdout.flush()
            logger.info(f"[{getattr(diagnostic_job_output, 'case_id', 'unknown')}] Oracle: Successfully completed --process-job execution.")
            sys.stderr.flush()
            sys.exit(0)
        except Exception as e_main:
            case_id_for_error = "unknown_case_oracle_main"
            try: 
                temp_data = json.loads(initial_job_json_str)
                case_id_for_error = temp_data.get("case_id", "unknown_case_in_json")
            except: pass
            logger.error(f"[{case_id_for_error}] Oracle (--process-job): Unexpected error: {type(e_main).__name__} - {e_main}", exc_info=True)
            sys.stderr.flush()
            print(f"Oracle Unexpected Error: {type(e_main).__name__} - {e_main}", file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
    else:
        logger.warning("Oracle: Not called with --process-job. Displaying help.")
        sys.stderr.flush()
        parser.print_help(sys.stderr)
        sys.stderr.flush()
        sys.exit(2)
