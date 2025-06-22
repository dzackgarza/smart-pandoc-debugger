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
#   - Stage 2: Oracle Processing (if TeX compilation fails) (`Oracle.py`)
#   - Stage 3: Report Building (always) (`Reporter.py`)
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
from utils.data_model import DiagnosticJob, PipelineStatus
from utils.manager_runner import run_manager # UPDATED
from utils.logger_utils import logger

# --- Direct Import for Oracle ---
# Bypassing subprocess for the Oracle due to persistent silent failures.
# This aligns with the successful unit test integration pattern.
from managers.Oracle import consult_the_oracle as _invoke_oracle_directly

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
ORACLE_MANAGER_PATH = os.path.join(MANAGERS_DIR_PATH, "Oracle.py")
REPORTER_MANAGER_PATH = os.path.join(MANAGERS_DIR_PATH, "Reporter.py")

# These assertions remain the same
assert os.path.isfile(MINER_MANAGER_PATH), \
    f"CRITICAL SETUP ERROR: Miner Manager script (Miner.py) not found: {MINER_MANAGER_PATH}"
assert os.path.isfile(ORACLE_MANAGER_PATH), \
    f"CRITICAL SETUP ERROR: Oracle Manager script (Oracle.py) not found: {ORACLE_MANAGER_PATH}"
assert os.path.isfile(REPORTER_MANAGER_PATH), \
    f"CRITICAL SETUP ERROR: Reporter Manager script (Reporter.py) not found: {REPORTER_MANAGER_PATH}"

# --- Outcome Constants ---
OUTCOME_MD_ERROR_REMEDIES = "MarkdownError_RemediesProvided"
OUTCOME_TEX_ERROR_REMEDIES = "TexCompilationError_RemediesProvided"
OUTCOME_SUCCESS_PDF_VALID = "CompilationSuccess_PDFShouldBeValid"
OUTCOME_NO_LEADS_MANUAL_REVIEW = "NoActionableLeadsFound_ManualReview"


def _dump_job_state(job: DiagnosticJob, stage_name: str):
    """If in DEBUG mode, saves the current DiagnosticJob state to a JSON file."""
    if DEBUG_ENV == "true":
        dump_dir = os.path.join(PROJECT_ROOT, "debug_dumps")
        os.makedirs(dump_dir, exist_ok=True)
        # Sanitize stage_name for filename
        safe_stage_name = stage_name.replace(" ", "_").lower()
        file_path = os.path.join(dump_dir, f"{job.case_id}_{safe_stage_name}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(job.model_dump_json(indent=2))
            logger.info(f"State dump saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to dump job state to {file_path}: {e}")


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

def _invoke_oracle(diagnostic_job: DiagnosticJob) -> DiagnosticJob:
    """Invokes the Oracle Manager to find remedies for TeX errors."""
    assert isinstance(diagnostic_job, DiagnosticJob), "Input must be a DiagnosticJob instance"
    diagnostic_job.current_pipeline_stage = "Stage_OracleManager"
    logger.info(f"[{diagnostic_job.case_id}] TeX compilation failed. Entering {diagnostic_job.current_pipeline_stage} to find remedies...")
    # --- MODIFIED: Calling Oracle directly instead of via subprocess ---
    diagnostic_job = _invoke_oracle_directly(diagnostic_job)
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
    Orchestrates the SDE diagnostic workflow using a state machine based on PipelineStatus.
    """
    logger.info(f"Coordinator: Starting diagnostic job ID: {diagnostic_job.job_id}")

    # The main pipeline loop. It continues as long as the status is not terminal.
    while True:
        job_id = diagnostic_job.job_id
        current_status = diagnostic_job.status
        logger.info(f"[{job_id}] Current pipeline status: {current_status.value}")
        
        # State Dispatcher
        if current_status == PipelineStatus.READY_FOR_MINER:
            logger.info(f"[{job_id}] Dispatching to Miner.")
            diagnostic_job = run_manager(MINER_MANAGER_PATH, diagnostic_job)
        
        elif current_status == PipelineStatus.MINER_SUCCESS_GATHERED_TEX_LOGS:
            # WARNING: THIS IS A TEMPORARY MVP END-STATE.
            # In a complete implementation, this state should dispatch the job
            # to the Oracle manager for analysis of the TeX logs.
            # The pipeline is intentionally halted here for now.
            logger.info(f"[{job_id}] Miner has gathered TeX logs. Pipeline complete for this stage.")
            break # Exit loop
        
        elif current_status == PipelineStatus.MINER_FAILURE_PANDOC:
            # WARNING: This is a terminal state. No further action is taken.
            logger.error(f"[{job_id}] Miner failed during Pandoc conversion. Halting pipeline.")
            break # Exit loop

        else:
            # WARNING: This is a catch-all for any unhandled or future states.
            # If you add a new PipelineStatus, you MUST add a handler for it above,
            # otherwise the pipeline will halt here.
            logger.error(f"[{job_id}] Reached unhandled or terminal state: {current_status.value}. Halting pipeline.")
            break # Exit loop

        # WARNING: This safety break is critical. If a manager script fails to
        # update the job status, this prevents an infinite loop that would
        # repeatedly call the same manager.
        if diagnostic_job.status == current_status:
            logger.error(f"[{job_id}] Pipeline status did not change from '{current_status.value}'. Halting to prevent infinite loop.")
            break

    logger.info(f"Coordinator: Diagnostic job ID {job_id} completed with final status: {diagnostic_job.status.value}")
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

    # 1. Read input
    try:
        initial_job_json_str = sys.stdin.read()
        if not initial_job_json_str:
            logger.error("Coordinator received empty stdin.")
            sys.exit(1)
        
        initial_diagnostic_job = DiagnosticJob.model_validate_json(initial_job_json_str)
        logger.info(f"Coordinator successfully parsed DiagnosticJob from stdin for job ID: {initial_diagnostic_job.job_id}")

    except Exception as e:
        logger.error(f"Coordinator: Failed to create DiagnosticJob from stdin JSON: {e}", exc_info=True)
        sys.exit(1)

    # 2. Run orchestration
    final_job = orchestrate_diagnostic_job(initial_diagnostic_job)

    # 3. Output result
    sys.stdout.write(final_job.model_dump_json(indent=2))
    logger.info("Coordinator script finished.")
    sys.exit(0)
