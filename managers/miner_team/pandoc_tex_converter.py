#!/usr/bin/env python3
# managers/miner-team/pandoc_tex_converter.py
"""
Pandoc MD-to-TeX Converter - Specialist for Miner Manager (V1.0)

This module is responsible for converting a Markdown file to a TeX file using Pandoc.
It validates the structural integrity of the generated TeX file (e.g., presence of
`\documentclass`) and reports success or failure along with relevant outputs and
potential ActionableLeads.

Designed to be imported and used by Miner.py.
Assumes it runs within a Python process where `utils` package is on PYTHONPATH.
Fails violently for critical setup issues (e.g., Pandoc not found, utils not importable).
"""

import sys
import os
import logging
import pathlib
import subprocess # For specific exception types
from typing import List, Optional, Tuple, NamedTuple, Dict, Any

# SDE utilities (expected to be on PYTHONPATH)
from utils.data_model import ActionableLead, SourceContextSnippet # type: ignore
from utils.process_runner import run_script # type: ignore

logger = logging.getLogger(__name__)
if not logger.handlers: # Basic config if not already configured by a parent
    LOG_LEVEL_PTC = logging.DEBUG if os.environ.get("DEBUG", "false").lower() == "true" else logging.INFO
    handler_ptc = logging.StreamHandler(sys.stderr)
    formatter_ptc = logging.Formatter('%(asctime)s - PANDOC_CONVERTER (%(name)s) - %(levelname)s - %(message)s')
    handler_ptc.setFormatter(formatter_ptc)
    logger.addHandler(handler_ptc)
    logger.setLevel(LOG_LEVEL_PTC)
    logger.propagate = False


class PandocConversionResult(NamedTuple):
    """Data class to hold the results of the Pandoc MD-to-TeX conversion."""
    conversion_successful: bool
    generated_tex_content: Optional[str]
    pandoc_raw_log: str
    actionable_lead: Optional[ActionableLead] # Present if conversion_successful is False


def _create_pandoc_failure_lead(
    case_id: str, # Though not strictly needed if DJ isn't passed, good for consistency in leads
    problem_description: str,
    return_code: int,
    full_pandoc_log: str,
    context_snippets: Optional[List[SourceContextSnippet]] = None
) -> ActionableLead:
    """Helper to create an ActionableLead for Pandoc conversion failures."""
    return ActionableLead(
        source_service="Miner", # Attributed to Miner, as this specialist acts on its behalf
        problem_description=problem_description,
        primary_context_snippets=context_snippets if context_snippets else [],
        internal_details_for_oracle={
            "tool_responsible": "pandoc",
            "stage_of_failure": "md-to-tex",
            "return_code": return_code,
            "full_pandoc_log_for_oracle": full_pandoc_log # Ensure Oracle gets the full log
        }
    )

def convert_md_to_tex(
    case_id: str, # For logging and lead attribution consistency
    markdown_file_path: pathlib.Path,
    output_tex_file_path: pathlib.Path,
    # Default Pandoc options for standalone LaTeX. Can be extended.
    pandoc_options: Optional[List[str]] = None
) -> PandocConversionResult:
    """
    Converts the given Markdown file to a TeX file using Pandoc.

    Args:
        case_id: The case ID for logging.
        markdown_file_path: Absolute path to the input Markdown file.
        output_tex_file_path: Absolute path for the generated TeX file.
        pandoc_options: Optional list of additional Pandoc command-line options.

    Returns:
        PandocConversionResult: An object containing success status, TeX content,
                                 Pandoc log, and an ActionableLead if failed.

    Raises:
        FileNotFoundError: If Pandoc executable is not found.
        subprocess.TimeoutExpired: If Pandoc times out.
        AssertionError: For critical precondition failures (e.g., input file missing).
    """
    assert markdown_file_path.is_file(), f"PandocConverter: Input Markdown file not found: {markdown_file_path}"
    assert output_tex_file_path.parent.is_dir(), \
        f"PandocConverter: Output directory for TeX file does not exist: {output_tex_file_path.parent}"

    logger.info(f"[{case_id}] PandocConverter: Starting MD-to-TeX for {markdown_file_path} -> {output_tex_file_path}")

    base_pandoc_cmd = ["pandoc", "-f", "markdown", "-t", "latex", "--standalone"]
    custom_options = pandoc_options if pandoc_options else []
    
    final_pandoc_cmd = base_pandoc_cmd + custom_options + [
        str(markdown_file_path), "-o", str(output_tex_file_path)
    ]

    # run_script from utils.process_runner uses check=True by default,
    # so it will raise CalledProcessError if Pandoc exits non-zero.
    # It also propagates FileNotFoundError and TimeoutExpired.
    # No need for an outer try/except for these in this specialist if we let them propagate to Miner.
    # However, to create a specific ActionableLead, we might catch CalledProcessError.

    log_prefix = f"PandocConverter[{case_id}]"
    process_pandoc: Optional[subprocess.CompletedProcess] = None # Ensure it's defined

    try:
        process_pandoc = run_script(
            command_parts=final_pandoc_cmd,
            timeout=30,
            expect_json_output=False, # Pandoc outputs TeX to file, logs to stderr/stdout
            log_prefix_for_caller=log_prefix,
            set_project_pythonpath=False # Pandoc is an external exe, doesn't need SDE PYTHONPATH
        )
        # If run_script uses check=True and Pandoc exits non-zero, it would have raised CalledProcessError.
        # If we reach here, Pandoc exited 0.
        pandoc_raw_log = (f"Pandoc Command: {' '.join(final_pandoc_cmd)}\nRC: {process_pandoc.returncode}\n"
                          f"Stdout:\n{process_pandoc.stdout}\nStderr:\n{process_pandoc.stderr}")
        logger.debug(f"[{log_prefix}] Pandoc raw log:\n{pandoc_raw_log}")

    except subprocess.CalledProcessError as cpe:
        # Pandoc exited non-zero. run_script (with check=True) caught it.
        logger.error(f"[{log_prefix}] Pandoc execution failed. RC: {cpe.returncode}. Stderr: {cpe.stderr}")
        pandoc_raw_log_on_err = (f"Pandoc Command: {' '.join(final_pandoc_cmd)}\nRC: {cpe.returncode}\n"
                                 f"Stdout:\n{cpe.stdout}\nStderr:\n{cpe.stderr}")
        
        failure_summary = f"Pandoc MD-to-TeX conversion failed. Pandoc exited with RC: {cpe.returncode}."
        context_snippets = None
        if cpe.stderr and cpe.stderr.strip():
            context_snippets = [SourceContextSnippet(source_document_type="md_to_tex_log", snippet_text=cpe.stderr.strip()[:1500])]

        lead = _create_pandoc_failure_lead(
            case_id=case_id, problem_description=failure_summary,
            return_code=cpe.returncode, full_pandoc_log=pandoc_raw_log_on_err,
            context_snippets=context_snippets
        )
        return PandocConversionResult(False, None, pandoc_raw_log_on_err, lead)
    
    # If Pandoc exited 0, proceed to validate the output TeX file
    assert process_pandoc is not None, "process_pandoc should be set if no CalledProcessError occurred."
    assert output_tex_file_path.is_file(), f"Pandoc exited 0, but output TeX file missing: {output_tex_file_path}"
    assert output_tex_file_path.stat().st_size > 0, f"Pandoc exited 0, but output TeX file is empty: {output_tex_file_path}"

    generated_tex_content = output_tex_file_path.read_text(encoding="utf-8", errors="replace")
    
    tex_seems_valid = False
    if generated_tex_content.strip():
        first_few_lines = generated_tex_content.splitlines()[:10]
        for line in first_few_lines:
            if "\\documentclass" in line:
                tex_seems_valid = True
                break
    
    if tex_seems_valid:
        logger.info(f"[{log_prefix}] Pandoc MD-to-TeX conversion successful, TeX output appears valid.")
        return PandocConversionResult(True, generated_tex_content, pandoc_raw_log, None)
    else:
        logger.error(f"[{log_prefix}] Pandoc MD-to-TeX exited 0 but output TeX file does not appear to be a valid standalone document (missing \\documentclass near start).")
        failure_summary = "Pandoc MD-to-TeX conversion seemed to succeed (RC=0), but the output TeX file was not a valid standalone document (e.g., missing '\\documentclass' near start)."
        
        lead = _create_pandoc_failure_lead(
            case_id=case_id, problem_description=failure_summary,
            return_code=0, # Pandoc RC was 0
            full_pandoc_log=pandoc_raw_log,
            context_snippets=[
                SourceContextSnippet(source_document_type="generated_tex_partial_or_invalid", snippet_text=generated_tex_content[:1000])
            ]
        )
        return PandocConversionResult(False, generated_tex_content, pandoc_raw_log, lead)


if __name__ == '__main__':
    # Standalone test for pandoc_tex_converter.py
    # This requires utils.data_model and utils.process_runner to be on PYTHONPATH
    # e.g., run from project root: python -m managers.miner_team.pandoc_tex_converter

    print("Running Pandoc MD-to-TeX Converter Standalone Test...", file=sys.stderr)
    
    if not logging.getLogger().hasHandlers(): # Ensure root logger has a handler for this test
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    test_case_id_standalone = "ptc_standalone_test_01"
    
    with tempfile.TemporaryDirectory(prefix="sde_ptc_test_") as tmpdir_name:
        tmpdir = pathlib.Path(tmpdir_name)
        md_content_ok = "# Hello World\n\nThis is markdown."
        md_content_bad_syntax = "# Bad MD\n\nThis has raw \\ LaTeX that Pandoc might reject without specific flags for native_divs or similar, or just pass through.\n\\mybadcommand"
        
        md_file_ok = tmpdir / "test_ok.md"
        md_file_bad = tmpdir / "test_bad.md"
        tex_out_ok = tmpdir / "test_ok.tex"
        tex_out_bad = tmpdir / "test_bad.tex"

        md_file_ok.write_text(md_content_ok)
        md_file_bad.write_text(md_content_bad_syntax) # This might still convert fine by Pandoc

        print(f"\n--- Test 1: OK Markdown ({md_file_ok}) ---", file=sys.stderr)
        result_ok = convert_md_to_tex(test_case_id_standalone, md_file_ok, tex_out_ok)
        print(f"Conversion Successful: {result_ok.conversion_successful}", file=sys.stderr)
        if result_ok.actionable_lead:
            print(f"Lead: {result_ok.actionable_lead.model_dump_json(indent=2)}", file=sys.stderr)
        else:
            print(f"Generated TeX (first 100 chars): {result_ok.generated_tex_content[:100] if result_ok.generated_tex_content else 'None'}...", file=sys.stderr)
        assert result_ok.conversion_successful and result_ok.generated_tex_content and not result_ok.actionable_lead

        # To test Pandoc failure, we'd need a md file that reliably makes Pandoc exit non-zero,
        # or simulate a Pandoc command failure.
        # For now, this primarily tests the success path and TeX validation.
        # A more complex test might involve a mock `run_script`.

        # Test for Pandoc outputting non-TeX like content (e.g., if Pandoc was misconfigured)
        # This is harder to simulate reliably without a specific Pandoc input that causes it.
        # We can simulate it by writing a non-TeX file and having our validator check it.
        print(f"\n--- Test 2: Pandoc RC=0 but invalid TeX output ---", file=sys.stderr)
        dummy_non_tex_file = tmpdir / "dummy_non_tex.tex"
        dummy_non_tex_file.write_text("This is not a TeX file at all.")
        
        # Temporarily mock subprocess.run to simulate Pandoc success but bad output
        original_subprocess_run = subprocess.run
        def mock_pandoc_success_bad_file(*args, **kwargs):
            # Simulate pandoc writing dummy_non_tex_file to output_tex_file_path
            # The command will be like ['pandoc', ..., 'output_file.tex']
            cmd_list = args[0]
            output_file_arg_idx = -1
            try: output_file_arg_idx = cmd_list.index('-o') + 1
            except ValueError: pass

            if output_file_arg_idx != -1 and output_file_arg_idx < len(cmd_list):
                simulated_output_path = pathlib.Path(cmd_list[output_file_arg_idx])
                simulated_output_path.write_text("This is not TeX but Pandoc exited 0.")

            return subprocess.CompletedProcess(args=cmd_list, returncode=0, stdout="Mock Pandoc success", stderr="")

        try:
            subprocess.run = mock_pandoc_success_bad_file # type: ignore
            md_file_for_mock = tmpdir / "for_mock_test.md"
            md_file_for_mock.write_text("# Mock Test")
            tex_out_for_mock = tmpdir / "for_mock_test.tex"

            result_mock_bad_tex = convert_md_to_tex(test_case_id_standalone, md_file_for_mock, tex_out_for_mock)
            print(f"Conversion Successful: {result_mock_bad_tex.conversion_successful}", file=sys.stderr)
            assert not result_mock_bad_tex.conversion_successful
            assert result_mock_bad_tex.actionable_lead is not None
            print(f"Lead: {result_mock_bad_tex.actionable_lead.model_dump_json(indent=2)}", file=sys.stderr)
            assert "Output file was not a valid standalone TeX document" in result_mock_bad_tex.actionable_lead.problem_description

        finally:
            subprocess.run = original_subprocess_run # Restore original

        print("\nStandalone tests for pandoc_tex_converter completed.", file=sys.stderr)
