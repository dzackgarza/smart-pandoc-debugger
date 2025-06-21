#!/usr/bin/env python3
# managers/miner-team/pandoc_tex_converter.py
"""
Pandoc MD-to-TeX Converter - Specialist for Miner Manager (V1.1.0 - Simplified TeX for Debugging)

This module converts a Markdown file to TeX using Pandoc. For debugging purposes,
it attempts to generate simpler TeX by disabling automatic section identifiers,
which can be a source of "Undefined control sequence" errors in pdflatex.
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
from typing import List, Optional, NamedTuple, Dict, Any # Removed Tuple as not directly used

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
    # case_id: str, # Not strictly needed if lead_id is auto-generated
    problem_description: str,
    return_code: int, # Pandoc's return code
    full_pandoc_log: str,
    context_snippets: Optional[List[SourceContextSnippet]] = None,
    internal_details_extra: Optional[Dict[str, Any]] = None
) -> ActionableLead:
    """Helper to create an ActionableLead for Pandoc conversion failures."""
    internal_details = {
        "tool_responsible": "pandoc",
        "stage_of_failure": "md-to-tex",
        "return_code": return_code,
        "full_pandoc_log_for_oracle": full_pandoc_log
    }
    if internal_details_extra:
        internal_details.update(internal_details_extra)

    return ActionableLead(
        source_service="Miner", 
        problem_description=problem_description,
        primary_context_snippets=context_snippets if context_snippets else [],
        internal_details_for_oracle=internal_details
    )

def convert_md_to_tex(
    case_id: str, 
    markdown_file_path: pathlib.Path,
    output_tex_file_path: pathlib.Path,
    # pandoc_options is kept for advanced overrides, but default behavior is now simplified
    pandoc_options_override: Optional[List[str]] = None 
) -> PandocConversionResult:
    """
    Converts Markdown to TeX using Pandoc, aiming for simpler output for debugging.
    It attempts to disable automatic section identifiers to reduce label-related errors.
    """
    assert markdown_file_path.is_file(), f"PandocConverter: Input MD file not found: {markdown_file_path}"
    assert output_tex_file_path.parent.is_dir(), \
        f"PandocConverter: Output directory for TeX file does not exist: {output_tex_file_path.parent}"

    log_prefix = f"PandocConverter[{case_id}]"
    logger.info(f"[{log_prefix}] Starting MD-to-TeX for {markdown_file_path} -> {output_tex_file_path} (Simplified TeX mode).")

    # --- MODIFIED PANDOC COMMAND ---
    # Use 'markdown-auto_identifiers' to try and disable automatic section labels from GFM-like markdown.
    # Keep essential extensions for TeX math, raw TeX pass-through, and figures.
    # This aims to reduce "Undefined control sequence" errors from complex labels during debugging.
    pandoc_format_string = "markdown-auto_identifiers+raw_tex+tex_math_dollars+implicit_figures"
    # Consider adding +footnotes, +pipe_tables etc. if they are common and safe.
    # The goal is to minimize auto-generated LaTeX macros that might be problematic.

    base_pandoc_cmd_parts = [
        "pandoc",
        "-f", pandoc_format_string,
        "-t", "latex",
        "--standalone" # Essential for a complete TeX document
    ]
    
    # If pandoc_options_override is provided, it replaces the default command construction logic.
    # This allows advanced users or specific test cases to use different Pandoc flags.
    if pandoc_options_override:
        final_pandoc_cmd = ["pandoc"] + pandoc_options_override + [
            str(markdown_file_path), "-o", str(output_tex_file_path)
        ]
        logger.info(f"[{log_prefix}] Using overridden Pandoc options.")
    else:
        final_pandoc_cmd = base_pandoc_cmd_parts + [
            str(markdown_file_path), "-o", str(output_tex_file_path)
        ]
    # --- END MODIFIED PANDOC COMMAND ---

    process_pandoc: Optional[subprocess.CompletedProcess] = None
    pandoc_raw_log_content = ""

    try:
        process_pandoc = run_script(
            command_parts=final_pandoc_cmd, timeout=30,
            expect_json_output=False, 
            log_prefix_for_caller=log_prefix,
            set_project_pythonpath=False 
        )
        pandoc_raw_log_content = (f"Pandoc Command: {' '.join(final_pandoc_cmd)}\nRC: {process_pandoc.returncode}\n"
                                  f"Stdout:\n{process_pandoc.stdout}\nStderr:\n{process_pandoc.stderr}")
        logger.debug(f"[{log_prefix}] Pandoc successfully exited 0. Raw log captured.")

    except subprocess.CalledProcessError as cpe:
        logger.error(f"[{log_prefix}] Pandoc execution failed. RC: {cpe.returncode}. Stderr: {cpe.stderr.strip() if cpe.stderr else 'N/A'}")
        pandoc_raw_log_content = (f"Pandoc Command: {' '.join(final_pandoc_cmd)}\nRC: {cpe.returncode}\n"
                                  f"Stdout:\n{cpe.stdout}\nStderr:\n{cpe.stderr}")
        
        failure_summary = f"Pandoc MD-to-TeX conversion failed. Pandoc exited with RC: {cpe.returncode}."
        context_snippets_list: List[SourceContextSnippet] = []
        if cpe.stderr and cpe.stderr.strip():
            context_snippets_list.append(SourceContextSnippet(source_document_type="md_to_tex_log", snippet_text=cpe.stderr.strip()[:1500]))

        lead = _create_pandoc_failure_lead(
            problem_description=failure_summary, return_code=cpe.returncode,
            full_pandoc_log=pandoc_raw_log_content, context_snippets=context_snippets_list
        )
        return PandocConversionResult(False, None, pandoc_raw_log_content, lead)
    # FileNotFoundError and TimeoutExpired from run_script will propagate up to Miner.py

    assert process_pandoc is not None, f"[{log_prefix}] process_pandoc object is None after successful run."
    assert output_tex_file_path.is_file(), f"[{log_prefix}] Pandoc exited 0, but output TeX file missing: {output_tex_file_path}"
    assert output_tex_file_path.stat().st_size > 0, f"[{log_prefix}] Pandoc exited 0, but output TeX file is empty: {output_tex_file_path}"

    generated_tex_content = output_tex_file_path.read_text(encoding="utf-8", errors="replace")
    
    tex_seems_valid = False
    if generated_tex_content.strip():
        first_few_lines = generated_tex_content.splitlines()[:10]
        for line in first_few_lines:
            if "\\documentclass" in line:
                tex_seems_valid = True
                break
    
    if tex_seems_valid:
        logger.info(f"[{log_prefix}] Pandoc MD-to-TeX successful, TeX output appears valid (found \\documentclass).")
        return PandocConversionResult(True, generated_tex_content, pandoc_raw_log_content, None)
    else:
        logger.error(f"[{log_prefix}] Pandoc MD-to-TeX exited 0 but output TeX file ({output_tex_file_path}) does not appear to be a valid standalone document (missing \\documentclass near start).")
        failure_summary = "Pandoc MD-to-TeX conversion seemed to succeed (RC=0), but the output TeX file was not a valid standalone document (e.g., missing '\\documentclass' near start)."
        
        lead = _create_pandoc_failure_lead(
            problem_description=failure_summary, return_code=0, 
            full_pandoc_log=pandoc_raw_log_content,
            context_snippets=[
                SourceContextSnippet(source_document_type="generated_tex_partial_or_invalid", snippet_text=generated_tex_content[:1000])
            ],
            internal_details_extra={"reason": "InvalidTeXLatexDocumentStructure"}
        )
        return PandocConversionResult(False, generated_tex_content, pandoc_raw_log_content, lead)


if __name__ == '__main__':
    # (Standalone test block - updated to reflect new Pandoc command strategy)
    print("Running Pandoc MD-to-TeX Converter Standalone Test (V1.1.0)...", file=sys.stderr)
    
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    test_case_id_standalone = "ptc_standalone_test_v110"
    
    with tempfile.TemporaryDirectory(prefix="sde_ptc_test_") as tmpdir_name:
        tmpdir = pathlib.Path(tmpdir_name)
        # This content with a header would previously generate a label.
        # With "markdown-auto_identifiers", it should not.
        md_content_ok = "# Hello World with Sections\n\nThis is markdown.\n\n## A Subsection\n\nMore content."
        md_file_ok = tmpdir / "test_ok.md"
        tex_out_ok = tmpdir / "test_ok.tex"
        md_file_ok.write_text(md_content_ok)

        print(f"\n--- Test 1: OK Markdown with new Pandoc command ({md_file_ok}) ---", file=sys.stderr)
        result_ok = convert_md_to_tex(test_case_id_standalone, md_file_ok, tex_out_ok)
        print(f"Conversion Successful: {result_ok.conversion_successful}", file=sys.stderr)
        
        if result_ok.generated_tex_content:
            print(f"Generated TeX (first 200 chars): {result_ok.generated_tex_content[:200]}...", file=sys.stderr)
            # Check if \label or \hypertarget related to section IDs are absent (or fewer)
            if "\\label{hello-world-with-sections}" in result_ok.generated_tex_content or \
               "\\hypertarget{hello-world-with-sections}" in result_ok.generated_tex_content:
                print("WARNING: TeX output still contains auto-generated section labels/hypertargets. The 'markdown-auto_identifiers' flag might not be effective or overridden.", file=sys.stderr)
            else:
                print("INFO: Auto-generated section labels/hypertargets seem to be correctly suppressed.", file=sys.stderr)
        
        if result_ok.actionable_lead:
            print(f"Lead: {result_ok.actionable_lead.model_dump_json(indent=2)}", file=sys.stderr)
        
        assert result_ok.conversion_successful and result_ok.generated_tex_content and not result_ok.actionable_lead

        # (Test 2 for "Pandoc RC=0 but invalid TeX output" can remain similar, using mock if needed)

        print("\nStandalone tests for pandoc_tex_converter (V1.1.0) completed.", file=sys.stderr)
