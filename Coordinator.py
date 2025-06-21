#!/usr/bin/env python3
# coordinator.py - V5.1.4 "Markdown-Focused Diagnoser" Orchestrator (4-Manager, Assertion-Driven)
#
# Version: 5.1.4 (Uses manager_runner instead of service_runner)
# Date: 2025-06-25 (Original V5.1, updated for V5.1.4)
# Author: Diagnostic Systems Group
#
# Design Philosophy (SDE V5.1 - Development Mode):
#   - Orchestrates a simplified SDE workflow with 4 primary Managers.
#   - Uses a central `DiagnosticJob` Pydantic model.
#   - Managers are independent Python scripts managed by `utils.manager_runner`.
#   - THIS VERSION DOES NOT GUARD AGAINST FAILURES. It uses assertions for preconditions.
#     If an assertion fails or an unhandled exception occurs, the coordinator will crash.
#   - Logging verbosity is controlled by the DEBUG environment variable.
#   - When run as a script (e.g., by intake.py), it expects DiagnosticJob JSON on stdin
#     and outputs the final_user_report_summary to stdout.
#
# Role:
#   Manages the "Diagnostic Assembly Line":
#     1. Receives an initial `DiagnosticJob`.
#     2. Calls the `Miner` Manager for initial processing (MD->TeX, MD fault mining, TeX->PDF).
#     3. Conditionally calls `Investigator` Manager if TeX compilation fails.
#     4. Conditionally calls `Oracle` Manager if actionable leads are found.
#     5. Always calls `Reporter` Manager to build the final report.
#     6. Returns the final, fully processed `DiagnosticJob` (when called as a module function)
#        OR prints its report summary and exits (when run as a script).
#
# Interface (as a Python module):
#   - Primary Function: `orchestrate_diagnostic_job(diagnostic_job: DiagnosticJob) -> DiagnosticJob`
#
# Interface (when run as a script, e.g., by intake.py):
#   - Stdin: Expects a single JSON string representing a `DiagnosticJob`.
#   - Stdout: Prints the `final_user_report_summary` from the processed `DiagnosticJob`.
#   - Stderr: Logs and assertion/error tracebacks.
#   - Exit Code: 0 for success (report generated), non-zero for critical errors.
#
# Manager Pipeline (Simplified - SDE V5.1.4):
#   - Stage 1: Initial Processing & Compilation (`Miner.py`)
#   - Stage 2: TeX Log Investigation (if TeX compilation fails) (`Investigator.py`)
#   - Stage 3: Oracle Processing (if errors and leads exist) (`Oracle.py`)
#   - Stage 4: Report Building (always) (`Reporter.py`)
#
# Environment Assumptions (and asserted):
#   - Python 3.x
#   - `utils.data_model.DiagnosticJob` is importable.
#   - `utils.manager_runner.run_manager` is importable.
#   - All 4 primary Manager scripts exist at specified paths in the `managers/` directory.
#   - Logger configured by calling environment or by __main__ block if run directly.
#     Logging verbosity controlled by DEBUG environment variable.
# --------------------------------------------------------------------------------

import logging
import os
import sys
import json # For loading DiagnosticJob from stdin when run as script

# Updated import to use manager_runner
from utils.data_model import DiagnosticJob
from utils.manager_runner import run_manager # UPDATED

# Determine logging level based on DEBUG environment variable
DEBUG_ENV = os.environ.get("DEBUG", "false").lower()
APP_LOG_LEVEL = logging.INFO if DEBUG_ENV == "true" else logging.WARNING

logger = logging.getLogger(__name__)

# --- Configuration & Path Assertions ---
# Assuming coordinator.py is at the project root alongside 'managers/' and 'utils/'
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MANAGERS_DIR_PATH = os.path.join(PROJECT_ROOT, "managers")

assert os.path.isdir(MANAGERS_DIR_PATH), \
    f"CRITICAL SETUP ERROR: Managers directory not found at expected path: {MANAGERS_DIR_PATH}"

MINER_MANAGER_PATH = os.path.join(MANAGERS_DIR_PATH, "Miner.py")
INVESTIGATOR_MANAGER_PATH = os.path.join(MANAGERS_DIR_PATH, "Investigator.py")
ORACLE_MANAGER_PATH = os.path.join(MANAGERS_DIR_PATH, "Oracle.py")
REPORTER_MANAGER_PATH = os.path.join(MANAGERS_DIR_PATH, "Reporter.py")

# These assertions remain the same
assert os.path.isfile(MINER_MANAGER_PATH), \
    f"CRITICAL SETUP ERROR: Miner Manager script (Miner.py) not found: {MINER_MANAGER_PATH}"
assert os.path.isfile(INVESTIGATOR_MANAGER_PATH), \
    f"CRITICAL SETUP ERROR: Investigator Manager script (Investigator.py) not found: {INVESTIGATOR_MANAGER_PATH}"
assert os.path.isfile(ORACLE_MANAGER_PATH), \
    f"CRITICAL SETUP ERROR: Oracle Manager script (Oracle.py) not found: {ORACLE_MANAGER_PATH}"
assert os.path.isfile(REPORTER_MANAGER_PATH), \
    f"CRITICAL SETUP ERROR: Reporter Manager script (Reporter.py) not found: {REPORTER_MANAGER_PATH}"

# --- Outcome Constants ---
OUTCOME_MD_ERROR_REMEDIES = "MarkdownError_RemediesProvided"
OUTCOME_TEX_ERROR_REMEDIES = "TexCompilationError_RemediesProvided"
OUTCOME_SUCCESS_PDF_VALID = "CompilationSuccess_PDFShouldBeValid"
OUTCOME_NO_LEADS_MANUAL_REVIEW = "NoActionableLeadsFound_ManualReview"


# --- Manager Invocation Functions (Simplified Stages) ---
# Updated to call run_manager instead of run_service
def _invoke_miner(diagnostic_job: DiagnosticJob) -> DiagnosticJob:
    """Invokes the Miner Manager for initial processing and compilation attempts."""
    assert isinstance(diagnostic_job, DiagnosticJob), "Input must be a DiagnosticJob instance"
    diagnostic_job.current_pipeline_stage = "Stage_MinerManager"
    logger.info(f"[{diagnostic_job.case_id}] Entering {diagnostic_job.current_pipeline_stage}...")
    diagnostic_job = run_manager(MINER_MANAGER_PATH, diagnostic_job) # UPDATED
    assert diagnostic_job.md_to_tex_conversion_attempted, \
        "MinerManager failed to mark md_to_tex_conversion_attempted."
    if diagnostic_job.md_to_tex_conversion_successful:
        assert diagnostic_job.tex_to_pdf_compilation_attempted, \
            "MinerManager succeeded MD-to-TeX but failed to mark tex_to_pdf_compilation_attempted."
    assert diagnostic_job.final_job_outcome is not None if \
           diagnostic_job.tex_to_pdf_compilation_successful or \
           not diagnostic_job.md_to_tex_conversion_successful else True, \
        "MinerManager did not set final_job_outcome appropriately after its processing."
    return diagnostic_job

def _invoke_investigator(diagnostic_job: DiagnosticJob) -> DiagnosticJob:
    """Invokes the Investigator Manager if TeX compilation failed."""
    assert isinstance(diagnostic_job, DiagnosticJob), "Input must be a DiagnosticJob instance"
    diagnostic_job.current_pipeline_stage = "Stage_InvestigatorManager"
    logger.info(f"[{diagnostic_job.case_id}] TeX-to-PDF failed. Entering {diagnostic_job.current_pipeline_stage}...")
    diagnostic_job = run_manager(INVESTIGATOR_MANAGER_PATH, diagnostic_job) # UPDATED
    logger.info(f"[{diagnostic_job.case_id}] Investigator output: {diagnostic_job.actionable_leads}")
    diagnostic_job.final_job_outcome = OUTCOME_TEX_ERROR_REMEDIES
    return diagnostic_job

def _invoke_oracle(diagnostic_job: DiagnosticJob) -> DiagnosticJob:
    """Invokes the Oracle Manager if actionable leads exist."""
    assert isinstance(diagnostic_job, DiagnosticJob), "Input must be a DiagnosticJob instance"
    diagnostic_job.current_pipeline_stage = "Stage_OracleManager"
    logger.info(f"[{diagnostic_job.case_id}] {len(diagnostic_job.actionable_leads)} actionable leads found. Entering {diagnostic_job.current_pipeline_stage}...")
    diagnostic_job = run_manager(ORACLE_MANAGER_PATH, diagnostic_job) # UPDATED
    assert isinstance(diagnostic_job.markdown_remedies, list), \
        "OracleManager did not ensure markdown_remedies is a list."
    return diagnostic_job

def _invoke_reporter(diagnostic_job: DiagnosticJob) -> DiagnosticJob:
    """Invokes the Reporter Manager to build the final report."""
    assert isinstance(diagnostic_job, DiagnosticJob), "Input must be a DiagnosticJob instance"
    diagnostic_job.current_pipeline_stage = "Stage_ReporterManager"
    logger.info(f"[{diagnostic_job.case_id}] Entering {diagnostic_job.current_pipeline_stage} to build final report. Current outcome: {diagnostic_job.final_job_outcome}")
    diagnostic_job = run_manager(REPORTER_MANAGER_PATH, diagnostic_job) # UPDATED
    assert diagnostic_job.final_user_report_summary is not None, \
        "ReporterManager failed to populate final_user_report_summary."
    return diagnostic_job

# --- Main Orchestration Logic ---
def orchestrate_diagnostic_job(diagnostic_job: DiagnosticJob) -> DiagnosticJob:
    """
    Orchestrates the SDE V5.1.4 diagnostic workflow with 4 primary Managers.
    Relies on assertions and expects `run_manager` or Managers to raise exceptions on failure.
    """
    assert isinstance(diagnostic_job, DiagnosticJob), \
        "Input to orchestrate_diagnostic_job must be a DiagnosticJob instance."
    logger.info(f"Coordinator: Starting diagnostic job ID: {diagnostic_job.case_id}")
    diagnostic_job.current_pipeline_stage = "Initial"

    diagnostic_job = _invoke_miner(diagnostic_job)

    if diagnostic_job.md_to_tex_conversion_successful and \
       not diagnostic_job.tex_to_pdf_compilation_successful:
        diagnostic_job = _invoke_investigator(diagnostic_job)
    elif not diagnostic_job.md_to_tex_conversion_successful:
        logger.info(f"[{diagnostic_job.case_id}] MD-to-TeX conversion failed. Miner handled MD fault analysis. Outcome: {diagnostic_job.final_job_outcome}")
    elif diagnostic_job.md_to_tex_conversion_successful and diagnostic_job.tex_to_pdf_compilation_successful:
        logger.info(f"[{diagnostic_job.case_id}] Full compilation successful (as per Miner). Outcome: {diagnostic_job.final_job_outcome}")

    if diagnostic_job.actionable_leads and diagnostic_job.final_job_outcome != OUTCOME_SUCCESS_PDF_VALID:
        diagnostic_job = _invoke_oracle(diagnostic_job)
    elif diagnostic_job.final_job_outcome != OUTCOME_SUCCESS_PDF_VALID and not diagnostic_job.actionable_leads:
        logger.warning(f"[{diagnostic_job.case_id}] An error outcome ({diagnostic_job.final_job_outcome}) was set, but no actionable leads found. Setting for manual review.")
        diagnostic_job.final_job_outcome = OUTCOME_NO_LEADS_MANUAL_REVIEW

    diagnostic_job = _invoke_reporter(diagnostic_job)

    diagnostic_job.current_pipeline_stage = "Completed"
    logger.info(f"Coordinator: Diagnostic job ID {diagnostic_job.case_id} completed. Final outcome: {diagnostic_job.final_job_outcome}")
    return diagnostic_job

# --- Script Entry Point Logic (when called by intake.py) ---
if __name__ == "__main__":
    # Configure logging. This will be effective when coordinator.py is run as a script.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(stream=sys.stderr, level=APP_LOG_LEVEL,
                            format='%(asctime)s - COORDINATOR SCRIPT (%(name)s) - %(levelname)s - %(message)s')
    else:
        # Ensure our logger specifically respects APP_LOG_LEVEL if root is already configured
        logging.getLogger(__name__).setLevel(APP_LOG_LEVEL)
        # Also, ensure all handlers for this logger respect the level
        for handler in logging.getLogger(__name__).handlers:
            handler.setLevel(APP_LOG_LEVEL)


    logger.info("Coordinator script started (invoked by intake.py or directly).")

    # 1. Read DiagnosticJob JSON from stdin (piped from intake.py)
    initial_job_json_str = ""
    try:
        initial_job_json_str = sys.stdin.read()
        assert initial_job_json_str, "Coordinator received empty stdin. Expected DiagnosticJob JSON."
        logger.debug(f"Coordinator received JSON from stdin (len: {len(initial_job_json_str)}).")
        
        # 2. Deserialize to DiagnosticJob Pydantic model
        initial_diagnostic_job = DiagnosticJob.model_validate_json(initial_job_json_str)
        logger.info(f"Coordinator successfully parsed DiagnosticJob from stdin for case ID: {initial_diagnostic_job.case_id}")

    except json.JSONDecodeError as e:
        logger.error(f"Coordinator: Failed to decode JSON from stdin: {e}", exc_info=True)
        error_report = {
            "final_user_report_summary": f"CRITICAL COORDINATOR ERROR: Invalid DiagnosticJob JSON received from intake.\nDetails: {e}",
            "final_job_outcome": "CoordinatorError_InvalidInputJSON"
        }
        print(json.dumps(error_report), file=sys.stdout)
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Coordinator: Assertion failed reading/parsing stdin: {e}", exc_info=True)
        error_report = {
            "final_user_report_summary": f"CRITICAL COORDINATOR ERROR: Failed to process input from intake.\nDetails: {e}",
            "final_job_outcome": "CoordinatorError_InputProcessingError"
        }
        print(json.dumps(error_report), file=sys.stdout)
        sys.exit(1)
    except Exception as e: 
        logger.error(f"Coordinator: Failed to create DiagnosticJob from stdin JSON: {e}", exc_info=True)
        error_report = {
            "final_user_report_summary": f"CRITICAL COORDINATOR ERROR: Could not validate DiagnosticJob from intake JSON.\nDetails: {type(e).__name__}: {e}",
            "final_job_outcome": "CoordinatorError_InputValidationError"
        }
        print(json.dumps(error_report), file=sys.stdout)
        sys.exit(1)


    try:
        final_diagnostic_job = orchestrate_diagnostic_job(initial_diagnostic_job)
    except AssertionError as e:
        logger.error(f"Coordinator: Assertion failed during orchestration: {e}", exc_info=True)
        initial_diagnostic_job.final_user_report_summary = (
            f"CRITICAL COORDINATOR ASSERTION ERROR DURING ORCHESTRATION:\n{e}\n"
            f"Please check system logs (stderr) for details.\n"
            f"Case ID: {initial_diagnostic_job.case_id}"
        )
        initial_diagnostic_job.final_job_outcome = "CoordinatorAssertionError_Orchestration"
        final_diagnostic_job = initial_diagnostic_job 
        print(final_diagnostic_job.final_user_report_summary, file=sys.stdout)
        sys.exit(1) 
    except Exception as e:
        logger.error(f"Coordinator: Unhandled exception during orchestration: {e}", exc_info=True)
        initial_diagnostic_job.final_user_report_summary = (
            f"CRITICAL COORDINATOR UNHANDLED EXCEPTION DURING ORCHESTRATION:\n{type(e).__name__}: {e}\n"
            f"Please check system logs (stderr) for details.\n"
            f"Case ID: {initial_diagnostic_job.case_id}"
        )
        initial_diagnostic_job.final_job_outcome = "CoordinatorUnhandledException_Orchestration"
        final_diagnostic_job = initial_diagnostic_job
        print(final_diagnostic_job.final_user_report_summary, file=sys.stdout)
        sys.exit(1)


    if final_diagnostic_job.final_user_report_summary:
        print(final_diagnostic_job.final_user_report_summary, file=sys.stdout)
    else:
        logger.warning(f"Coordinator: final_user_report_summary is None/empty for case {final_diagnostic_job.case_id}. Outcome: {final_diagnostic_job.final_job_outcome}")
        default_error_summary = (
            f"Diagnostic process for case {final_diagnostic_job.case_id} completed, "
            f"but no specific report summary was generated by the Reporter Manager. " # UPDATED
            f"Final Outcome: {final_diagnostic_job.final_job_outcome or 'UnknownOutcome_NoReportSummary'}"
        )
        print(default_error_summary, file=sys.stdout)

    sys.exit(0)
