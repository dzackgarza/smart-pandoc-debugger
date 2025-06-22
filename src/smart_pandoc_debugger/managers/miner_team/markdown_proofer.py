#!/usr/bin/env python3
# managers/miner-team/markdown_proofer.py
"""
Markdown Proofer - Team Member for Miner Manager (V1.3 - Uses utils.process_runner)

Orchestrates Markdown checker scripts using `utils.process_runner.run_script`.
Designed to be imported and used directly by the Miner Manager.
Assumes it runs within a Python process where `utils` package is on PYTHONPATH.
Fails violently for its own critical errors (e.g., misconfigured checkers).
Handles checker tool failures (non-zero exit without specific output, timeouts) by creating ActionableLeads.
"""

import sys
import os
import logging
import subprocess # For specific exception types like TimeoutExpired, CalledProcessError
from typing import List, Tuple, Optional

from utils.data_model import ActionableLead, SourceContextSnippet # type: ignore
from utils.process_runner import run_script # type: ignore (This is now the primary way to run checkers)

# Configure logger for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    DEBUG_MODE_PROOFER = os.environ.get("DEBUG", "false").lower() == "true"
    PROOFER_LOG_LEVEL = logging.DEBUG if DEBUG_MODE_PROOFER else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(asctime)s - MD_PROOFER (%(name)s) - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(PROOFER_LOG_LEVEL)
    logger.propagate = False


# --- Configuration for Markdown Checkers ---
PROOFER_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKER_SUB_DIR = "markdown_proofer_team"
CHECKER_TEAM_DIR_MD = os.path.join(PROOFER_SCRIPT_DIR, CHECKER_SUB_DIR)

MARKDOWN_CHECKERS_CONFIG: List[Tuple[str, str]] = [
    ("check_markdown_unclosed_dollar.py", "python"),
    ("check_markdown_unclosed_envs.py", "python"),
]

# _parse_checker_output_to_lead function (V1.2 draft was good, no changes needed here)
def _parse_checker_output_to_lead(
    checker_output_line: str,
    source_document_type: str,
    calling_manager_name: str
) -> ActionableLead:
    """
    Parses a colon-delimited output line from a checker script
    and transforms it into an ActionableLead Pydantic object.
    Expected Format: ERROR_TYPE:LINE_NUM:VAL1:VAL2:SNIPPET:CONTENT
    """
    parts = checker_output_line.strip().split(':', 5)
    assert len(parts) == 6, \
        f"Malformed checker output: '{checker_output_line}'. Expected 6 colon-separated parts."

    error_type, line_num_str, val1, val2, snippet_val, content_val = parts
    
    line_num: Optional[int]
    try:
        line_num = int(line_num_str)
    except ValueError: 
        logger.error(f"Invalid line number from checker: '{line_num_str}' in '{checker_output_line}'. This is a checker bug.")
        raise ValueError(f"Checker returned non-integer line number: {line_num_str}")

    details_for_oracle = {"original_error_type": error_type}
    problem_desc_detail = ""

    if error_type == "UnterminatedInlineMathMarkdown":
        problem_desc_detail = f"Unterminated inline math (started with '$'). Open delims: {val1}, Close delims: {val2}."
        details_for_oracle.update({"open_delim_count": val1, "close_delim_count": val2})
    elif error_type == "UnclosedMarkdownEnvironment":
        problem_desc_detail = f"Unclosed Markdown environment: '{val1}'."
        details_for_oracle.update({"env_name": val1})
    elif error_type == "MismatchedMarkdownEnvironment":
        problem_desc_detail = f"Mismatched Markdown environment. Expected closing for '{val1}', but found closing for '{val2}'."
        details_for_oracle.update({"expected_env_name": val1, "found_env_name": val2})
    else: 
        problem_desc_detail = f"Checker reported: {error_type} (vals: {val1}, {val2})."
        details_for_oracle.update({"checker_val1": val1, "checker_val2": val2})
        logger.warning(f"Unknown ERROR_TYPE '{error_type}' from checker. Using generic parsing.")

    context_text = snippet_val.strip() if snippet_val.strip() else content_val.strip()
    assert context_text, f"Checker output for {error_type} provided no context snippet or line content."

    snippet_args = {
        "source_document_type": source_document_type,
        "central_line_number": line_num,
        "snippet_text": context_text,
    }
    if content_val.strip() and content_val.strip() != context_text:
        snippet_args["location_detail"] = f"Full line: '{content_val.strip()}'"
    if snippet_val.strip():
        snippet_args["notes"] = f"Original problem snippet reported: '{snippet_val.strip()}'."
    
    lead_context_snippet = SourceContextSnippet(**snippet_args)

    final_problem_description = f"{error_type}: {problem_desc_detail} (at line ~{line_num if line_num is not None else 'N/A'})"

    lead = ActionableLead(
        source_service=calling_manager_name,
        problem_description=final_problem_description,
        primary_context_snippets=[lead_context_snippet],
        internal_details_for_oracle=details_for_oracle
    )
    return lead


def run_markdown_checks(
    case_id: str,
    markdown_file_path: str,
    calling_manager_name: str = "Miner"
) -> List[ActionableLead]:
    """
    Orchestrates execution of Markdown checker scripts using utils.process_runner.run_script.
    Fails fast on first error from a checker or if a checker tool itself fails.
    Lets OS-level errors from run_script (e.g., FileNotFoundError for python3) propagate.
    """
    assert os.path.isabs(markdown_file_path), "markdown_file_path must be absolute."
    assert os.path.isfile(markdown_file_path), f"Markdown file not found: {markdown_file_path}"

    logger.info(f"[{case_id}] MD_Proofer V1.3: Starting Markdown checks on {markdown_file_path} from {CHECKER_TEAM_DIR_MD}.")
    found_leads: List[ActionableLead] = []

    for checker_script_name, script_type in MARKDOWN_CHECKERS_CONFIG:
        checker_script_full_path = os.path.join(CHECKER_TEAM_DIR_MD, checker_script_name)
        
        assert os.path.isfile(checker_script_full_path), \
            f"[{case_id}] MD_Proofer: CRITICAL - MD checker script not found: {checker_script_full_path}"

        command: List[str]
        if script_type == "python":
            command = [sys.executable, checker_script_full_path, markdown_file_path]
        else:
            # Should not be reached if MARKDOWN_CHECKERS_CONFIG is correct
            raise AssertionError(f"Unsupported script type '{script_type}' for MD checker {checker_script_name}.")
        
        log_prefix = f"MD_Proofer[{case_id}]"
        logger.debug(f"[{log_prefix}] Running MD checker: {' '.join(command)}")
        
        try:
            # utils.process_runner.run_script uses check=True, so it will raise
            # CalledProcessError if the checker exits non-zero.
            # It will also propagate TimeoutExpired or FileNotFoundError for the command itself.
            # We set expect_json_output=False as checkers output colon-delimited strings.
            process_result = run_script(
                command_parts=command, 
                timeout=15,
                expect_json_output=False, # Checkers output plain text / colon-delimited
                log_prefix_for_caller=log_prefix,
                set_project_pythonpath=True # Crucial if checkers import 'utils'
            )
            # If run_script with check=True succeeds, it means checker exited 0.
            # Checker contract: exit 0 AND no stdout = success.
            # Checker contract: exit 0 AND stdout with finding = finding.
            # (Note: proofreader.sh logic was: exit 1 and stdout on finding. run_script(check=True) would fail this.)
            #
            # REVISING LOGIC based on run_script(check=True):
            # If run_script completes, it means checker exited 0.
            # We then check its stdout for a finding.
            
            checker_stdout = process_result.stdout.strip() if process_result.stdout else ""
            # Stderr is logged by run_script itself if it's notable.

            if checker_stdout: # Checker exited 0 but *did* report a finding via stdout
                logger.info(f"[{log_prefix}] MD Checker {checker_script_name} found an issue (RC=0, with stdout): {checker_stdout}")
                lead = _parse_checker_output_to_lead(checker_stdout, "markdown", calling_manager_name)
                found_leads.append(lead)
                return found_leads # Stop on first finding

            # If we reach here, checker exited 0 and had no stdout -> success for this checker

        except subprocess.CalledProcessError as cpe:
            # This means the checker script itself exited non-zero.
            # This could be because it found an error (and printed to stdout as per old contract)
            # OR because the checker script itself crashed.
            checker_stdout_on_err = cpe.stdout.strip() if cpe.stdout else ""
            checker_stderr_on_err = cpe.stderr.strip() if cpe.stderr else ""
            logger.error(f"[{log_prefix}] MD Checker '{checker_script_name}' exited non-zero (RC={cpe.returncode}). Stdout: '{checker_stdout_on_err}', Stderr: '{checker_stderr_on_err}'")

            if checker_stdout_on_err: # Checker exited non-zero AND printed a finding
                logger.info(f"[{log_prefix}] MD Checker {checker_script_name} reported finding via stdout and non-zero exit: {checker_stdout_on_err}")
                lead = _parse_checker_output_to_lead(checker_stdout_on_err, "markdown", calling_manager_name)
                found_leads.append(lead)
                return found_leads # Stop on first finding
            else: # Checker exited non-zero and NO stdout finding -> likely a checker tool crash
                tool_failure_lead = ActionableLead(
                    source_service=calling_manager_name,
                    problem_description=f"Internal Markdown checker tool '{checker_script_name}' failed or crashed (RC={cpe.returncode}).",
                    internal_details_for_oracle={
                        "checker_script": checker_script_name, 
                        "return_code": cpe.returncode, 
                        "stderr_from_checker": checker_stderr_on_err if checker_stderr_on_err else "No stderr.",
                        "stdout_on_error": checker_stdout_on_err # Could be empty
                    }
                )
                found_leads.append(tool_failure_lead)
                return found_leads # Stop on checker tool failure

        except subprocess.TimeoutExpired as te:
            logger.error(f"[{log_prefix}] MD Checker {checker_script_name} timed out: {te}")
            timeout_lead = ActionableLead(
                source_service=calling_manager_name,
                problem_description=f"Internal Markdown checker '{checker_script_name}' timed out during execution.",
                internal_details_for_oracle={"checker_script": checker_script_name, "stage": "timeout", "details": str(te)}
            )
            found_leads.append(timeout_lead)
            return found_leads # Stop on timeout
        
        # FileNotFoundError for the command itself will propagate from run_script and crash this module,
        # which is the desired "fail violently" behavior for critical setup/environment issues.

    logger.info(f"[{case_id}] MD_Proofer: All Markdown checks passed successfully.")
    return found_leads


if __name__ == '__main__':
    # (Standalone test block - largely same as V1.2, relies on utils being on PYTHONPATH)
    print("Running Markdown Proofer Standalone Test (V1.3)...", file=sys.stderr)
    
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    dummy_md_content = "# Test Document\n\nThis is $unclosed.\n\\begin{env}\nNot closed."
    test_case_id = "md_proofer_test_standalone_v1.3"
    
    import tempfile
    with tempfile.TemporaryDirectory(prefix="sde_mdproofer_test_") as tmpdir:
        dummy_md_path = os.path.join(tmpdir, "test_doc.md")
        with open(dummy_md_path, "w") as f:
            f.write(dummy_md_content)
        
        print(f"Testing with dummy file: {dummy_md_path}", file=sys.stderr)
        
        assert os.path.isdir(CHECKER_TEAM_DIR_MD), \
            (f"ERROR: Checker directory for testing not found at {CHECKER_TEAM_DIR_MD}\n"
             f"Current PROOFER_SCRIPT_DIR: {PROOFER_SCRIPT_DIR}\n"
             "Ensure markdown_proofer_team with checkers is correctly placed relative to markdown_proofer.py")

        leads = run_markdown_checks(test_case_id, dummy_md_path, "StandaloneTester")
        
        if leads:
            print(f"\n--- Leads Found ({len(leads)}) ---", file=sys.stderr)
            for i, lead_obj in enumerate(leads):
                print(f"  Lead #{i+1}: {lead_obj.model_dump_json(indent=2)}", file=sys.stderr)
        else:
            print("\n--- No Leads Found ---", file=sys.stderr)
