# utils/data_model.py
# Version 5.4.2 - Specialist Result Models Added
#
# This module defines the Pydantic models used to represent the state and
# data flowing through the Smart Diagnostic Engine (SDE). The primary goal of the
# SDE is to help users diagnose and fix issues in their Markdown documents that
# prevent successful compilation to PDF, typically via a LaTeX intermediate.
#
# The core model, `DiagnosticJob`, encapsulates the entire state of a diagnostic
# task, evolving as it passes through different service stages. Other models
# represent more granular pieces of information like contextual code/log snippets,
# identified problems ("leads"), proposed solutions ("remedies"), and structured
# results from specialist tools.
#
# Key Principles Reflected in this Model:
# 1.  Markdown-Centric Fixes: All proposed remedies guide the user to modify
#     their original Markdown file.
# 2.  MD-to-TeX Short-Circuit: If the initial conversion from Markdown to TeX fails,
#     this indicates a likely structural Markdown issue. The diagnostic process
#     focuses on this first, bypassing deeper TeX analysis until the Markdown
#     can be successfully converted to TeX.
# 3.  Actionable Output: The system aims to provide concrete, actionable advice
#     that helps the user achieve a compilable Markdown document.
# 4.  Context is Key: Identifying the precise location of an issue (in Markdown,
#     generated TeX, or logs) is crucial for both automated analysis (by an "Oracle"
#     service) and for user understanding.

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any 
import datetime
import uuid
import pathlib # For pathlib.Path type hint

# --- Atomic Data Structures ---

class SourceContextSnippet(BaseModel):
    """
    Represents a snippet of text from one of the source documents (Markdown or
    generated TeX) or a relevant log file, pinpointing an area of interest or
    the location of a potential error. This is used to provide context for
    identified leads and proposed remedies.
    """
    source_document_type: str = Field(
        ...,
        description="Type of the source document or log from which this snippet originates. "
                    "Examples: 'markdown', 'generated_tex', 'md_to_tex_log', 'tex_compilation_log', 'generated_tex_partial_or_invalid'."
    )
    central_line_number: Optional[int] = Field(
        None,
        description="The primary line number of interest within the source_document_type. "
                    "For logs, this might be the line number within that specific log file."
    )
    snippet_text: str = Field(
        ...,
        description="The actual text of the snippet, which may be multi-line. "
                    "This provides the direct context around the point of interest."
    )
    location_detail: Optional[str] = Field(
        None,
        description="Optional, more specific location detail. For example, for Markdown, "
                    "this could be a character offset if determinable, or a section title."
    )
    notes: Optional[str] = Field(
        None,
        description="Optional annotations or comments about this specific snippet, perhaps "
                    "highlighting why it's relevant or what to look for."
    )

class ActionableLead(BaseModel):
    """
    Represents a specific issue, problem, or "lead" identified by a diagnostic
    Manager (e.g., Miner, Investigator) or one of its specialist tools. This lead is
    considered actionable, meaning it's something the system believes is contributing
    to the compilation failure and for which a remedy might be proposed.
    """
    lead_id: str = Field(
        default_factory=lambda: f"lead_{uuid.uuid4().hex[:8]}",
        description="A unique identifier for this specific lead."
    )
    source_service: str = Field( 
        ...,
        description="The name of the SDE Manager that identified or is reporting this lead. "
                    "Examples: 'Miner', 'Investigator', 'Oracle'. "
                    "Specialist tools create leads that are attributed to their calling Manager."
    )
    problem_description: str = Field(
        ...,
        description="A brief, human-readable description of the problem identified. "
                    "This summary helps categorize the issue."
    )
    primary_context_snippets: List[SourceContextSnippet] = Field(
        default_factory=list,
        description="A list of one or more SourceContextSnippet objects that provide "
                    "the essential evidence or illustrate this lead."
    )
    internal_details_for_oracle: Optional[Dict[str, Any]] = Field(
        None,
        description="A dictionary for structured data primarily intended for programmatic use "
                    "by the 'Oracle' manager. "
                    "Example: {'tool_responsible': 'pandoc', 'stage_of_failure': 'md-to-tex', 'return_code': 1}."
    )

class MarkdownRemedy(BaseModel):
    """
    Represents a specific, actionable instruction to modify the ORIGINAL MARKDOWN
    document. The aim of this remedy is to address an identified ActionableLead
    and help make the Markdown document successfully compilable to PDF.
    """
    remedy_id: str = Field(
        default_factory=lambda: f"remedy_{uuid.uuid4().hex[:8]}",
        description="A unique identifier for this specific remedy."
    )
    applies_to_lead_id: str = Field(
        ...,
        description="The lead_id of the ActionableLead that this remedy is intended to address."
    )
    source_service: str = Field( # Typically "Oracle"
        ...,
        description="The name of the SDE Manager that proposed this remedy."
    )
    explanation: str = Field(
        ...,
        description="A human-readable explanation of why the problem (identified in the lead) "
                    "occurs and how this proposed remedy is expected to resolve it."
    )
    instruction_for_markdown_fix: str = Field(
        ...,
        description="Clear, step-by-step instructions detailing what changes the user "
                    "should make IN THEIR ORIGINAL MARKDOWN document."
    )
    markdown_context_to_change: Optional[SourceContextSnippet] = Field(
        None,
        description="An optional SourceContextSnippet taken from the original Markdown document, "
                    "showing the specific area where the fix should be applied."
    )
    suggested_markdown_after_fix: Optional[str] = Field(
        None,
        description="An optional textual representation of what the relevant Markdown snippet "
                    "(referenced by markdown_context_to_change) should look like *after* "
                    "the fix has been applied. This could be a direct snippet or a 'diff-like' description."
    )
    confidence_score: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="A confidence score between 0.0 and 1.0 indicating how confident the system is "
                    "that this remedy will fix the issue. Higher values indicate higher confidence."
    )
    notes: Optional[str] = Field(
        None,
        description="Optional notes about this remedy"
    )

# --- NEW: Specialist Result Models ---

class PandocConversionResult(BaseModel):
    """
    Holds the results of the Pandoc MD-to-TeX conversion performed by
    the pandoc_tex_converter.py specialist.
    """
    conversion_successful: bool = Field(
        ...,
        description="True if Pandoc exited successfully AND the generated TeX "
                    "passed basic structural validation (e.g., contains \\documentclass)."
    )
    generated_tex_content: Optional[str] = Field(
        None,
        description="The full content of the generated .tex file if conversion was successful "
                    "and the file was read. May also contain partial/invalid content on failure."
    )
    pandoc_raw_log: Optional[str] = Field(
        None,
        description="The full, verbatim log output (stdout and stderr combined) from the Pandoc process."
    )
    actionable_lead: Optional[ActionableLead] = Field(
        None,
        description="An ActionableLead object if the Pandoc conversion process itself failed "
                    "(e.g., Pandoc exited non-zero, or output TeX was structurally invalid). "
                    "This lead is generated by the pandoc_tex_converter specialist."
    )
    # output_tex_file_path could be added if Miner needs the specialist to report back the exact path it used.
    # For now, Miner provides this path to the specialist.
    # output_tex_file_path: Optional[pathlib.Path] = Field(None, description="Path to .tex file")

    class Config:
        arbitrary_types_allowed = True # In case pathlib.Path or other complex types are used in future

class TexCompilationResult(BaseModel):
    """
    Holds the results of the TeX-to-PDF compilation performed by
    the tex_compiler.py specialist.
    """
    compilation_successful: bool = Field(
        ...,
        description="True if pdflatex (after all runs) exited successfully AND a valid, "
                    "non-empty PDF file was produced."
    )
    pdf_file_path: Optional[pathlib.Path] = Field(
        None,
        description="Absolute path to the generated .pdf file if compilation was successful."
    )
    tex_compiler_raw_log: Optional[str] = Field(
        None,
        description="The full, verbatim content of the LaTeX .log file from the compilation attempts."
    )
    # This lead is for failures of the compilation *process* itself (e.g., tool timeout, pdflatex not found),
    # NOT for specific TeX content errors found *within* the log (that's Investigator's job).
    actionable_lead: Optional[ActionableLead] = Field(
        None,
        description="An ActionableLead object if the pdflatex compilation process itself failed "
                    "(e.g., pdflatex executable not found, or timed out). This lead is generated "
                    "by the tex_compiler specialist."
    )

    class Config:
        arbitrary_types_allowed = True # To allow pathlib.Path

# --- Main Job State Model ---

class DiagnosticJob(BaseModel):
    """
    The central Pydantic model representing the complete state of a single diagnostic
    task. An instance of this model is created when a new diagnostic job begins
    and is progressively populated and modified as it passes through the various
    SDE Managers. It carries all necessary information from input
    (original Markdown) through intermediate stages (TeX conversion,
    compilation attempts) to final outputs (identified leads, proposed remedies,
    and a summary report).
    """
    case_id: str = Field(
        ...,
        description="A unique identifier for this diagnostic case or job, often derived "
                    "from a temporary filename or generated at the start of processing."
    )
    timestamp_created: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + "Z", # Ensure UTC 'Z'
        description="An ISO 8601 formatted timestamp (UTC) indicating when this diagnostic job was initiated."
    )

    # --- Input ---
    original_markdown_content: str = Field(
        ...,
        description="The full content of the user's original Markdown document that is "
                    "to be diagnosed."
    )

    # --- Stage 1: MD-to-TeX Conversion (e.g., by Pandoc, handled by Miner manager) ---
    md_to_tex_conversion_attempted: bool = Field(
        False,
        description="Flag indicating whether an attempt was made to convert the "
                    "original_markdown_content to TeX."
    )
    md_to_tex_conversion_successful: bool = Field(
        False,
        description="Flag indicating if the MD-to-TeX conversion was successful. "
                    "If False, the diagnostic pipeline will typically focus on analyzing "
                    "the Markdown content for errors and skip TeX compilation."
    )
    md_to_tex_raw_log: Optional[str] = Field(
        None,
        description="The raw, verbatim log output (stdout/stderr) from the MD-to-TeX "
                    "conversion tool (e.g., Pandoc). This log is crucial for diagnosing "
                    "conversion failures."
    )
    generated_tex_content: Optional[str] = Field(
        None,
        description="The TeX content generated from the Markdown. This field is populated "
                    "only if md_to_tex_conversion_successful is True."
    )

    # --- Stage 2: TeX-to-PDF Compilation (e.g., by pdflatex, handled by Miner manager) ---
    # This stage is SKIPPED if md_to_tex_conversion_successful is False.
    tex_to_pdf_compilation_attempted: bool = Field(
        False,
        description="Flag indicating whether an attempt was made to compile the "
                    "generated_tex_content to PDF."
    )
    tex_to_pdf_compilation_successful: bool = Field(
        False,
        description="Flag indicating if the TeX-to-PDF compilation resulted in a "
                    "successfully generated PDF document. If True, the SDE's primary "
                    "goal is achieved for this run."
    )
    tex_compiler_raw_log: Optional[str] = Field(
        None,
        description="The raw, verbatim .log file output from the LaTeX compiler "
                    "(e.g., pdflatex, lualatex). This log is the primary source for "
                    "identifying TeX-level compilation errors if tex_to_pdf_compilation_successful is False."
    )
    
    # --- Aggregated Diagnostics & Remedies ---
    actionable_leads: List[ActionableLead] = Field(
        default_factory=list,
        description="A list of ActionableLead objects. These represent specific problems "
                    "identified during the diagnostic process, either from Markdown analysis "
                    "(if MD->TeX fails, by Miner) or from TeX compilation log analysis (by Investigator)."
    )
    markdown_remedies: List[MarkdownRemedy] = Field(
        default_factory=list,
        description="A list of MarkdownRemedy objects. Each remedy provides specific "
                    "instructions for modifying the original_markdown_content to address "
                    "a corresponding ActionableLead (proposed by Oracle)."
    )
    
    # --- Workflow & Final Outcome ---
    current_pipeline_stage: str = Field(
        "Initialized", 
        description="A string indicating the current high-level stage of processing in "
                    "the SDE pipeline. Examples: 'Initialized', 'Miner_Processing', "
                    "'Investigator_Processing', 'Oracle_Processing', 'Reporter_Processing'."
    )
    final_job_outcome: Optional[str] = Field(
        None, 
        description="A summary string indicating the final outcome of this diagnostic job. "
                    "This field is populated by managers or the coordinator as processing concludes. "
                    "Examples: 'MarkdownError_LeadsProvided', "
                    "'TexCompilationError_RemediesProvided', "
                    "'CompilationSuccess_PDFShouldBeValid', "
                    "'NoActionableLeadsFound_ManualReview', 'InternalToolFailure_Miner', etc."
    )
    final_user_report_summary: Optional[str] = Field(
        None,
        description="The assembled human-readable diagnostic report or summary of advice "
                    "to be presented to the user. This is typically constructed by the Reporter manager "
                    "from the markdown_remedies and other relevant job information."
    )
    
    # --- Internal Data Store ---
    internal_tool_outputs_verbatim: Dict[str, str] = Field(
        default_factory=dict,
        description="A dictionary for storing raw, verbatim outputs from various internal "
                    "tools or sub-processes used during diagnostics (e.g., specific linter outputs, "
                    "Pandoc's direct md->pdf log if attempted). This data is primarily for "
                    "debugging the SDE itself or for use by highly specialized Oracle components, "
                    "and not typically part of the final user report."
    )

    class Config:
        validate_assignment = True 
        # extra = 'forbid'
