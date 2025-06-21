#!/usr/bin/env python3
# managers/miner-team/tex_compiler.py
"""
TeX-to-PDF Compiler - Specialist for Miner Manager (V1.0)

This module is responsible for compiling a TeX file to PDF using pdflatex.
It handles multiple pdflatex runs, captures the compilation log, and reports
on success or failure. It does not parse TeX errors from the log; that is
left to the Investigator manager.

Designed to be imported and used by Miner.py.
Assumes it runs within a Python process where `utils` package is on PYTHONPATH.
Fails violently for critical setup issues (e.g., pdflatex not found, utils not importable).
"""

import sys
import os
import logging
import pathlib
import subprocess # For specific exception types
from typing import List, Optional, NamedTuple, Dict, Any

# SDE utilities (expected to be on PYTHONPATH)
from utils.data_model import ActionableLead, SourceContextSnippet # type: ignore
from utils.process_runner import run_script # type: ignore

logger = logging.getLogger(__name__)
if not logger.handlers: # Basic config if not already configured by a parent
    LOG_LEVEL_TC = logging.DEBUG if os.environ.get("DEBUG", "false").lower() == "true" else logging.INFO
    handler_tc = logging.StreamHandler(sys.stderr)
    formatter_tc = logging.Formatter('%(asctime)s - TEX_COMPILER (%(name)s) - %(levelname)s - %(message)s')
    handler_tc.setFormatter(formatter_tc)
    logger.addHandler(handler_tc)
    logger.setLevel(LOG_LEVEL_TC)
    logger.propagate = False

class TexCompilationResult(NamedTuple):
    """Data class to hold the results of the TeX-to-PDF compilation."""
    compilation_successful: bool
    pdf_file_path: Optional[pathlib.Path]
    tex_compiler_raw_log: Optional[str]
    # This lead is for failures of the compilation *process* (e.g., tool timeout),
    # not for specific TeX errors found in the log.
    actionable_lead: Optional[ActionableLead] 


def _create_tex_compiler_failure_lead(
    case_id: str,
    problem_description: str,
    tool_name: str = "pdflatex",
    internal_details: Optional[Dict[str, Any]] = None,
    context_snippets: Optional[List[SourceContextSnippet]] = None
) -> ActionableLead:
    """Helper to create an ActionableLead for TeX compilation process failures."""
    final_internal_details = {
        "tool_responsible": tool_name,
        "stage_of_failure": "tex-to-pdf-compilation-process"
    }
    if internal_details:
        final_internal_details.update(internal_details)

    return ActionableLead(
        source_service="Miner", # Attributed to Miner, as this specialist acts on its behalf
        problem_description=problem_description,
        primary_context_snippets=context_snippets if context_snippets else [],
        internal_details_for_oracle=final_internal_details
    )

def compile_tex_to_pdf(
    case_id: str, # For logging
    tex_file_path: pathlib.Path,
    output_directory: pathlib.Path,
    pdflatex_options: Optional[List[str]] = None,
    max_runs: int = 2
) -> TexCompilationResult:
    """
    Compiles the given TeX file to PDF using pdflatex.

    Args:
        case_id: The case ID for logging.
        tex_file_path: Absolute path to the input TeX file.
        output_directory: Absolute path to the directory for PDF and logs.
        pdflatex_options: Optional list of additional pdflatex command-line options.
        max_runs: Maximum number of pdflatex executions.

    Returns:
        TexCompilationResult: An object containing success status, PDF path,
                              raw log, and an ActionableLead if the compilation
                              process itself failed (e.g., timeout).

    Raises:
        FileNotFoundError: If pdflatex executable is not found by process_runner.
        subprocess.TimeoutExpired: If pdflatex times out (propagated by process_runner).
        AssertionError: For critical precondition failures.
    """
    assert tex_file_path.is_file(), f"TexCompiler: Input TeX file not found: {tex_file_path}"
    assert output_directory.is_dir(), f"TexCompiler: Output directory not found: {output_directory}"
    assert max_runs > 0, "TexCompiler: max_runs must be positive."

    logger.info(f"[{case_id}] TexCompiler: Starting TeX-to-PDF compilation for {tex_file_path} in {output_directory}")

    base_pdflatex_cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-output-directory=" + str(output_directory)
    ]
    custom_options = pdflatex_options if pdflatex_options else []
    final_pdflatex_cmd = base_pdflatex_cmd + custom_options + [str(tex_file_path)]

    process_pdflatex: Optional[subprocess.CompletedProcess] = None
    final_pdf_produced_and_valid = False
    captured_tex_log: Optional[str] = None
    log_prefix = f"TexCompiler[{case_id}]"

    # This outer try-except is for errors from run_script itself (tool not found, timeout)
    try:
        for run_number in range(1, max_runs + 1):
            logger.info(f"[{log_prefix}] pdflatex run #{run_number} (max {max_runs})...")
            
            # process_runner.run_script uses check=True by default.
            # If pdflatex exits non-zero, it will raise CalledProcessError.
            try:
                process_pdflatex = run_script(
                    command_parts=final_pdflatex_cmd,
                    timeout=60, # Generous timeout for pdflatex
                    expect_json_output=False,
                    log_prefix_for_caller=log_prefix,
                    # pdflatex doesn't need SDE PYTHONPATH
                    set_project_pythonpath=False,
                    # cwd=output_directory # pdflatex -output-directory handles this well
                )
                # If we are here, pdflatex exited 0 for this run
                logger.info(f"[{log_prefix}] pdflatex run #{run_number} exited 0.")

            except subprocess.CalledProcessError as cpe:
                # pdflatex exited non-zero. This is a TeX compilation error.
                logger.error(f"[{log_prefix}] pdflatex run #{run_number} FAILED with RC={cpe.returncode}.")
                process_pdflatex = cpe # Store the completed process object with error info
                # Capture log from this failing run
                pdflatex_log_file_on_err = output_directory / f"{tex_file_path.stem}.log"
                if pdflatex_log_file_on_err.is_file():
                    captured_tex_log = pdflatex_log_file_on_err.read_text(encoding="utf-8", errors="replace")
                else:
                    captured_tex_log = (f"pdflatex .log file NOT FOUND after error at {pdflatex_log_file_on_err}.\n"
                                        f"RC: {cpe.returncode}.\nStdout: {cpe.stdout}\nStderr: {cpe.stderr}")
                break # Stop further runs

            # After each run (successful or not), try to get the .log file
            pdflatex_log_file = output_directory / f"{tex_file_path.stem}.log"
            if pdflatex_log_file.is_file():
                captured_tex_log = pdflatex_log_file.read_text(encoding="utf-8", errors="replace")
                logger.debug(f"[{log_prefix}] Captured {pdflatex_log_file.name} (Length: {len(captured_tex_log or '')}) after run #{run_number}")
            elif process_pdflatex: # If log file not found, use process stdout/stderr
                captured_tex_log = (f"pdflatex .log file NOT FOUND at {pdflatex_log_file} after run #{run_number}.\n"
                                    f"RC: {process_pdflatex.returncode}.\n"
                                    f"Stdout: {process_pdflatex.stdout}\nStderr: {process_pdflatex.stderr}")
                logger.warning(f"[{log_prefix}] pdflatex .log file not found after run #{run_number}.")
            
            # Check if PDF was actually created and is valid after a successful (RC=0) run
            pdf_output_file_check = output_directory / f"{tex_file_path.stem}.pdf"
            if process_pdflatex and process_pdflatex.returncode == 0:
                if not pdf_output_file_check.is_file() or pdf_output_file_check.stat().st_size == 0:
                    logger.warning(f"[{log_prefix}] pdflatex run #{run_number} exited 0, but PDF at {pdf_output_file_check} not found or empty. Treating as failure.")
                    # This run failed to produce a valid PDF despite RC=0
                    final_pdf_produced_and_valid = False
                    break # Stop further runs, something is wrong
                else:
                    # PDF is good for this run. If this is the last configured run, mark as overall success.
                    if run_number == max_runs:
                        final_pdf_produced_and_valid = True
                    logger.info(f"[{log_prefix}] pdflatex run #{run_number} successful, PDF found and non-empty.")
            
            if process_pdflatex and process_pdflatex.returncode == 0 and run_number < max_runs and final_pdf_produced_and_valid: # If it's not the last run and it was successful
                 logger.info(f"[{log_prefix}] Proceeding to pdflatex run #{run_number + 1} for references/TOC.")
            # Loop continues or breaks based on conditions above

        # After all runs or break
        assert process_pdflatex is not None, f"[{case_id}] TexCompiler: pdflatex subprocess logic error."

        pdf_file_final = output_directory / f"{tex_file_path.stem}.pdf"
        if final_pdf_produced_and_valid: # Checked after the loop completes or breaks successfully
            logger.info(f"[{log_prefix}] TeX-to-PDF compilation successful. PDF at {pdf_file_final}")
            return TexCompilationResult(True, pdf_file_final, captured_tex_log, None)
        else:
            logger.error(f"[{log_prefix}] TeX-to-PDF compilation FAILED overall. Final relevant pdflatex RC: {process_pdflatex.returncode}.")
            # No ActionableLead created here for TeX content errors; Investigator handles that using the log.
            return TexCompilationResult(False, None, captured_tex_log, None)

    except FileNotFoundError as e_fnf: # From run_script if pdflatex itself not found
        logger.critical(f"[{log_prefix}] FATAL - pdflatex command not found: {e_fnf.filename}. {e_fnf}", exc_info=True)
        lead = _create_tex_compiler_failure_lead(
            case_id=case_id,
            problem_description=f"pdflatex command ('{e_fnf.filename}') not found. Ensure LaTeX distribution is installed and pdflatex is in system PATH.",
            internal_details={"error_type": "CommandNotFound", "command": e_fnf.filename}
        )
        # Propagate FileNotFoundError to Miner to handle it as a critical infrastructure issue
        raise # Let Miner catch this specific FileNotFoundError and handle it

    except subprocess.TimeoutExpired as te:
        logger.error(f"[{log_prefix}] pdflatex process timed out: {te}", exc_info=True)
        lead = _create_tex_compiler_failure_lead(
            case_id=case_id,
            problem_description=f"pdflatex process timed out after {te.timeout} seconds.",
            internal_details={"error_type": "Timeout", "timeout_seconds": te.timeout, "command_hint": str(te.cmd)}
        )
        # Propagate TimeoutExpired to Miner
        raise # Let Miner catch this specific TimeoutExpired and handle it

    # Other exceptions from run_script (e.g., if it raised something custom) would propagate.


if __name__ == '__main__':
    print("Running TeX Compiler Standalone Test...", file=sys.stderr)
    
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    test_case_id_standalone = "tc_standalone_test_01"
    
    with tempfile.TemporaryDirectory(prefix="sde_tc_test_") as tmpdir_name:
        tmpdir = pathlib.Path(tmpdir_name)
        
        # Test 1: Valid TeX file
        valid_tex_content = "\\documentclass{article}\\title{Test}\\author{Me}\\date{\\today}\\begin{document}\\maketitle Hello PDF!\\end{document}"
        tex_file_ok = tmpdir / "test_ok.tex"
        tex_file_ok.write_text(valid_tex_content)

        print(f"\n--- Test 1: OK TeX ({tex_file_ok}) ---", file=sys.stderr)
        try:
            result_ok = compile_tex_to_pdf(test_case_id_standalone, tex_file_ok, tmpdir)
            print(f"Compilation Successful: {result_ok.compilation_successful}", file=sys.stderr)
            if result_ok.pdf_file_path:
                print(f"PDF Path: {result_ok.pdf_file_path} (Exists: {result_ok.pdf_file_path.exists()})", file=sys.stderr)
            if result_ok.actionable_lead:
                print(f"Lead: {result_ok.actionable_lead.model_dump_json(indent=2)}", file=sys.stderr)
            assert result_ok.compilation_successful and result_ok.pdf_file_path and result_ok.pdf_file_path.exists()

        except Exception as e:
            print(f"Test 1 FAILED with exception: {e}", file=sys.stderr)
            # This might happen if pdflatex is not installed on the system running the test.

        # Test 2: TeX file that will cause pdflatex to error out
        error_tex_content = "\\documentclass{article}\\begin{document} Hello \\undefinedcommand \\end{document}"
        tex_file_err = tmpdir / "test_err.tex"
        tex_file_err.write_text(error_tex_content)

        print(f"\n--- Test 2: Error TeX ({tex_file_err}) ---", file=sys.stderr)
        try:
            result_err = compile_tex_to_pdf(test_case_id_standalone, tex_file_err, tmpdir)
            print(f"Compilation Successful: {result_err.compilation_successful}", file=sys.stderr)
            assert not result_err.compilation_successful
            assert result_err.tex_compiler_raw_log is not None
            assert result_err.actionable_lead is None # This specialist doesn't make leads for TeX content errors
            if result_err.tex_compiler_raw_log:
                print(f"TeX Log (first 200 chars): {result_err.tex_compiler_raw_log[:200]}...", file=sys.stderr)
        except Exception as e:
            print(f"Test 2 FAILED with exception: {e}", file=sys.stderr)


        # Test 3: Non-existent TeX file (should raise AssertionError in compile_tex_to_pdf)
        print(f"\n--- Test 3: Non-existent TeX file ---", file=sys.stderr)
        tex_file_missing = tmpdir / "missing.tex"
        try:
            compile_tex_to_pdf(test_case_id_standalone, tex_file_missing, tmpdir)
            print("Test 3 FAILED: Expected AssertionError for missing file.", file=sys.stderr)
        except AssertionError as e_assert:
            print(f"Test 3 PASSED: Caught expected AssertionError: {e_assert}", file=sys.stderr)
        except Exception as e:
            print(f"Test 3 FAILED with unexpected exception: {e}", file=sys.stderr)


        print("\nStandalone tests for tex_compiler completed.", file=sys.stderr)
