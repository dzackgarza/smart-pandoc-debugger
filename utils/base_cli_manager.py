# utils/base_cli_manager.py - V2.0
# Provides a simple lifecycle function for pipe-based manager scripts.

import sys
import json
import traceback
from .data_model import DiagnosticJob
from .logger_utils import logger
import pydantic

def run_manager_script(processing_function):
    """
    Handles the standard lifecycle of a manager script that operates in a pipe.

    This function is responsible for the boilerplate of:
    1. Reading a JSON string from standard input.
    2. Parsing and validating it into a DiagnosticJob Pydantic model.
    3. Calling the manager's specific `processing_function` with the job object.
    4. Taking the modified job object returned by the processing function.
    5. Serializing it back to a JSON string.
    6. Printing the final JSON to standard output.

    If any part of this process fails (e.g., invalid input JSON, error
    during processing), an error is logged to stderr and the script exits with
    a non-zero status code to halt the pipeline.

    Args:
        processing_function (callable): A function that takes a single
            argument (a DiagnosticJob object) and returns a modified
            DiagnosticJob object.
    """
    # WARNING: This function is the primary entry point for all managers that
    # follow the "Pipe-Script Contract". It is intentionally designed to be
    # fragile. Any exception, from JSON validation to an unhandled error in
    # the 'processing_function', will cause the script to exit with a non-zero
    # status code. This is the core mechanism that halts the Coordinator's
    # pipeline and prevents cascading failures. Do not add broad, silent
    # error catching here without a very good reason.
    try:
        # 1. Read from stdin
        input_json_str = sys.stdin.read()
        if not input_json_str:
            logger.error("BaseCliManager: Stdin was empty. No job to process.")
            sys.exit(1)

        # 2. Parse and validate
        job = DiagnosticJob.parse_raw(input_json_str)
        job.log_message(f"Successfully parsed job. Current status: {job.status.value}")

        # 3. Call the manager's main logic
        updated_job = processing_function(job)

        # 4. Serialize and 5. Print to stdout
        sys.stdout.write(updated_job.model_dump_json(indent=2))

    except json.JSONDecodeError:
        logger.error("BaseCliManager: Failed to decode JSON from stdin.")
        sys.exit(1)
    except pydantic.ValidationError as e:
        logger.error(f"BaseCliManager: Input data failed validation for DiagnosticJob.\n{e}")
        sys.exit(1)
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"BaseCliManager: An unexpected error occurred during job processing: {e}\n{tb_str}")
        # Attempt to write out the job state before failing if possible
        if 'job' in locals() and isinstance(job, DiagnosticJob):
            job.log_message(f"FATAL ERROR: {e}\n{tb_str}")
            sys.stdout.write(job.model_dump_json(indent=2))
        sys.exit(1)
