#!/usr/bin/env python3
# managers/Reporter.py - SDE V5.1.3: Diagnostic Report Builder Manager
#
# Version: 1.0.1 (Aligned with data_model.py V5.4.1)
# Date: 2025-06-25 (Updated from V1.0.0)
# Author: Diagnostic Systems Group
#
# Role (SDE V5.1.3 Manager):
#   - Primary Manager in the SDE V5.1.3 pipeline, called by `coordinator.py` via a runner.
#   - Receives a `DiagnosticJob` Pydantic model instance.
#   - Responsibility:
#       - To analyze the `actionable_leads`, `markdown_remedies`, `final_job_outcome`,
#         and other relevant fields within the input `DiagnosticJob`.
#       - To construct a comprehensive, human-readable `final_user_report_summary` string.
#       - This summary is stored back into `DiagnosticJob.final_user_report_summary`.
#   - Returns the updated `DiagnosticJob` model instance.
#   - FAILS VIOLENTLY: Uses assertions for preconditions.
#
# Interface (as called by manager_runner.py / service_runner.py):
#   - Input: `DiagnosticJob` Pydantic model.
#   - Output: Updated `DiagnosticJob` Pydantic model (with `final_user_report_summary` populated).
#   - Standard CLI: Expects `--process-job` flag.
#
# Environment Assumptions (Asserted):
#   - `utils.data_model` components are importable and correctly defined (V5.4.1).
# --------------------------------------------------------------------------------

import sys
import os
import json
import logging
import argparse
import textwrap

# Attempt to import SDE utilities
try:
    from utils.data_model import DiagnosticJob, ActionableLead, MarkdownRemedy, SourceContextSnippet
except ModuleNotFoundError:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from utils.data_model import DiagnosticJob, ActionableLead, MarkdownRemedy, SourceContextSnippet
    except ModuleNotFoundError as e_inner:
        print(f"CRITICAL REPORTER ERROR: Failed to import SDE utilities. Error: {e_inner}", file=sys.stderr)
        class DiagnosticJob: pass # type: ignore
        class ActionableLead: pass # type: ignore
        class MarkdownRemedy: pass # type: ignore
        class SourceContextSnippet: pass # type: ignore

# --- Logging Setup ---
logger = logging.getLogger(__name__) # Uses "managers.Reporter"
if not logger.handlers:
    DEBUG_ENV_REPORTER = os.environ.get("DEBUG", "false").lower()
    REPORTER_LOG_LEVEL = logging.INFO if DEBUG_ENV_REPORTER == "true" else logging.WARNING # Default to WARNING
    
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(asctime)s - REPORTER (%(name)s) - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(REPORTER_LOG_LEVEL)
    logger.propagate = False

# --- Outcome Constants (for interpreting DiagnosticJob.final_job_outcome) ---
OUTCOME_SUCCESS_PDF_VALID = "CompilationSuccess_PDFShouldBeValid"
OUTCOME_NO_LEADS_MANUAL_REVIEW = "NoActionableLeadsFound_ManualReview"
# Other outcomes like MarkdownError_... or TexCompilationError_... will imply leads/remedies exist.

def format_source_context_snippet_for_report(snippet: SourceContextSnippet) -> str:
    """Formats a SourceContextSnippet for display in the report."""
    # This is a simplified version. Your original format_context_snippet was more detailed.
    # For ActionableLead, we primarily want to show the snippet_text.
    # For MarkdownRemedy's target_source_context, we might want more detail.
    lines = []
    base_indent = "    " # Two spaces for snippet block, two more for text
    if snippet.source_document_type:
        lines.append(f"  Context from: {snippet.source_document_type}")
    if snippet.central_line_number is not None:
        lines.append(f"  Near line: {snippet.central_line_number}")
    if snippet.location_detail:
         lines.append(f"  Detail: {snippet.location_detail}")
    
    lines.append(f"  Snippet:\n{textwrap.indent(snippet.snippet_text, base_indent)}")
    
    if snippet.notes:
        lines.append(f"  Notes on snippet: {snippet.notes}")
    return "\n".join(lines)

def format_actionable_lead_for_report(lead: ActionableLead, index: int) -> str:
    """Formats a single ActionableLead for the report, aligning with data_model.py V5.4.1.
    
    The problem description is made more prominent and includes additional context to help
    users understand the issue better.
    """
    report_lines = []
    report_lines.append(f"\n--- Issue Detected #{index + 1} (Lead ID: {lead.lead_id}) ---")
    report_lines.append(f"Identified by: {lead.source_service}")
    
    # Make the problem description more prominent
    report_lines.append("\nISSUE SUMMARY:")
    report_lines.append(f"  {lead.problem_description}")
    
    # Add confidence score if it's not the default (1.0)
    if hasattr(lead, 'confidence_score') and lead.confidence_score < 1.0:
        report_lines.append(f"  (Confidence: {lead.confidence_score*100:.0f}%)")

    # Add any additional context from internal_details_for_oracle if available
    if lead.internal_details_for_oracle:
        details = []
        if 'tool_responsible' in lead.internal_details_for_oracle:
            details.append(f"Tool: {lead.internal_details_for_oracle['tool_responsible']}")
        if 'stage_of_failure' in lead.internal_details_for_oracle:
            details.append(f"Stage: {lead.internal_details_for_oracle['stage_of_failure']}")
        if details:
            report_lines.append("\n  " + " | ".join(details))

    # Add context snippets if available
    if lead.primary_context_snippets:
        report_lines.append("\nRELEVANT CONTEXT:")
        for i, snippet_model in enumerate(lead.primary_context_snippets):
            assert isinstance(snippet_model, SourceContextSnippet), \
                f"Item in primary_context_snippets for lead {lead.lead_id} is not a SourceContextSnippet."
            report_lines.append(f"  --- Context Snippet {i+1} ---")
            report_lines.append(textwrap.indent(format_source_context_snippet_for_report(snippet_model), "  "))
    
    return "\n".join(report_lines)

def format_markdown_remedy_for_report(remedy: MarkdownRemedy, index: int) -> str:
    """Formats a single MarkdownRemedy for the report, aligning with data_model.py V5.4.1."""
    report_lines = []
    report_lines.append(f"\n--- Suggested Fix #{index + 1} (for Lead ID: {remedy.applies_to_lead_id}) ---")
    report_lines.append(f"Proposed by: {remedy.source_service}") # Usually "Oracle" or "OracleManager(...)"
    
    report_lines.append("\nExplanation & Fix:")
    # Combine explanation and instruction if instruction is generic, or show both if distinct.
    # Assuming remedy.explanation contains the main guidance.
    report_lines.append(textwrap.indent(remedy.explanation, "  "))
    if remedy.instruction_for_markdown_fix and remedy.instruction_for_markdown_fix != remedy.explanation:
        report_lines.append("\nSpecific Instruction for Markdown:")
        report_lines.append(textwrap.indent(remedy.instruction_for_markdown_fix, "  "))


    if remedy.markdown_context_to_change:
        assert isinstance(remedy.markdown_context_to_change, SourceContextSnippet), \
            f"markdown_context_to_change for remedy {remedy.remedy_id} is not a SourceContextSnippet."
        report_lines.append("\nArea in your Markdown to Modify:")
        # Use a more detailed snippet format for remedy context if desired
        report_lines.append(textwrap.indent(format_source_context_snippet_for_report(remedy.markdown_context_to_change), "  "))
    
    if remedy.suggested_markdown_after_fix:
        report_lines.append("\nMarkdown Snippet After Applying Fix (Suggestion):")
        report_lines.append(textwrap.indent(remedy.suggested_markdown_after_fix, "    ")) # Extra indent for code-like block
    
    report_lines.append(f"(Confidence in this fix: {remedy.confidence_score*100:.0f}%)")
    if remedy.notes:
        report_lines.append(f"Notes: {remedy.notes}")
        
    return "\n".join(report_lines)

def build_report_summary(diagnostic_job_model: DiagnosticJob) -> str:
    assert isinstance(diagnostic_job_model, DiagnosticJob), \
        "Reporter.build_report_summary: Input must be a DiagnosticJob model."

    dj = diagnostic_job_model
    report_parts = []

    report_parts.append("========================================")
    report_parts.append("   Smart Diagnostic Engine Report   ")
    report_parts.append("========================================")
    report_parts.append(f"Case ID: {dj.case_id}")
    report_parts.append(f"Timestamp: {dj.timestamp_created}") # Assumes Pydantic model handles datetime to str
    report_parts.append(f"Overall Outcome: {dj.final_job_outcome or 'Undetermined'}")
    report_parts.append("----------------------------------------")

    if dj.final_job_outcome == OUTCOME_SUCCESS_PDF_VALID:
        report_parts.append("\nCongratulations! Document compiled successfully to PDF (as reported by Miner).")
        report_parts.append("No further issues were processed by other diagnostic managers.")
    
    elif dj.actionable_leads: # If there are leads, display them
        report_parts.append("\nIdentified Issues (Leads):")
        for i, lead_model in enumerate(dj.actionable_leads):
            report_parts.append(format_actionable_lead_for_report(lead_model, i))
        
        if dj.markdown_remedies:
            report_parts.append("\n\nProposed Solutions (Markdown Remedies):")
            for i, remedy_model in enumerate(dj.markdown_remedies):
                report_parts.append(format_markdown_remedy_for_report(remedy_model, i))
        else:
            report_parts.append("\n\nProposed Solutions: No specific Markdown remedies were generated by the Oracle manager for the identified issues.")
            report_parts.append("  Please review the leads above and attempt to fix them in your Markdown source.")

    elif dj.final_job_outcome == OUTCOME_NO_LEADS_MANUAL_REVIEW:
        report_parts.append("\nDiagnosis Result: An issue was encountered, but no specific actionable leads could be automatically identified.")
        report_parts.append("  This may indicate a complex or unusual problem.")
        report_parts.append("  Please review the raw logs if available in the full DiagnosticJob for manual investigation.")
        # Show relevant log excerpts more intelligently
        if dj.md_to_tex_conversion_attempted and not dj.md_to_tex_conversion_successful and dj.md_to_tex_raw_log:
            report_parts.append("\nMD-to-TeX Conversion Log (Excerpt from Pandoc):")
            report_parts.append(textwrap.indent(dj.md_to_tex_raw_log[:1000] + ("..." if len(dj.md_to_tex_raw_log) > 1000 else ""), "  "))
        if dj.tex_to_pdf_compilation_attempted and not dj.tex_to_pdf_compilation_successful and dj.tex_compiler_raw_log:
            report_parts.append("\nTeX Compiler Log (Excerpt from pdflatex):")
            report_parts.append(textwrap.indent(dj.tex_compiler_raw_log[-2000:] if len(dj.tex_compiler_raw_log) > 2000 else dj.tex_compiler_raw_log, "  ")) # Show last 2000 chars for TeX errors
            
    else: # Fallback for other outcomes or if no leads but not explicit NO_LEADS_MANUAL_REVIEW
        report_parts.append("\nDiagnostic Summary:")
        report_parts.append(f"  The diagnostic process concluded with outcome: {dj.final_job_outcome or 'Undetermined'}.")
        report_parts.append("  No specific leads or remedies to display in this summary. Please check logs if issues are suspected.")
        # Potentially show log excerpts here too, similar to NO_LEADS_MANUAL_REVIEW case

    report_parts.append("\n========================================")
    report_parts.append("End of Report")
    report_parts.append("========================================")

    return "\n".join(report_parts)

def process_diagnostic_job(diagnostic_job_model: DiagnosticJob) -> DiagnosticJob:
    assert isinstance(diagnostic_job_model, DiagnosticJob), \
        "Reporter.process_diagnostic_job: Input must be a DiagnosticJob model."
    
    logger.info(f"[{diagnostic_job_model.case_id}] Reporter: Starting report generation.")

    report_summary_str = build_report_summary(diagnostic_job_model)
    diagnostic_job_model.final_user_report_summary = report_summary_str

    assert diagnostic_job_model.final_user_report_summary is not None, \
         f"[{diagnostic_job_model.case_id}] Reporter: CRITICAL: final_user_report_summary was not set."

    logger.info(f"[{diagnostic_job_model.case_id}] Reporter: Report generation complete.")
    return diagnostic_job_model

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SDE Reporter Manager V1.0.1: Builds the final user report summary."
    )
    parser.add_argument('--process-job', action='store_true',
                        help="Required flag to process DiagnosticJob JSON from stdin.")
    args = parser.parse_args()

    assert args.process_job, "Reporter.py CRITICAL: Must be called with --process-job flag."

    input_json_str = sys.stdin.read()
    assert input_json_str.strip(), "Reporter.py CRITICAL: Received empty input from stdin."
    
    diagnostic_job_dict_input = json.loads(input_json_str)
    diagnostic_job_model_input = DiagnosticJob(**diagnostic_job_dict_input)
    
    diagnostic_job_model_output = process_diagnostic_job(diagnostic_job_model_input)
    
    output_json_str = diagnostic_job_model_output.model_dump_json(
        indent=2 if os.environ.get("SDE_PRETTY_PRINT_JSON", "false").lower() == "true" else None
    )
    sys.stdout.write(output_json_str)
    sys.stdout.flush()
    
    logger.info(f"[{getattr(diagnostic_job_model_output, 'case_id', 'unknown')}] Reporter: Successfully completed execution.")
    sys.exit(0)
