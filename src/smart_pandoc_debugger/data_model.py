"""
Data models for the Smart Pandoc Debugger.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, NamedTuple
from pydantic import BaseModel, Field
import uuid
import pathlib
from enum import Enum
import time


class StatusEnum(str, Enum):
    PENDING = "pending"
    MINER_PROCESSING = "miner_processing"
    MINER_MD_TO_TEX_SUCCESS = "miner_md_to_tex_success"
    MINER_MD_TO_TEX_FAILED = "miner_md_to_tex_failed"
    MINER_TEX_TO_PDF_SUCCESS = "miner_tex_to_pdf_success"
    MINER_TEX_TO_PDF_FAILED = "miner_tex_to_pdf_failed"
    COMPILATION_SUCCESS = "compilation_success"
    INVESTIGATOR_PROCESSING = "investigator_processing"
    INVESTIGATOR_LEADS_FOUND = "investigator_leads_found"
    INVESTIGATOR_NO_LEADS_FOUND = "investigator_no_leads_found"
    INVESTIGATOR_LOG_MISSING = "investigator_log_missing"
    INVESTIGATOR_CORRUPT_LOG = "investigator_corrupt_log"
    INVESTIGATOR_LOG_PERMISSION_ERROR = "investigator_log_permission_error"
    ORACLE_PROCESSING = "oracle_processing"
    ORACLE_REMEDIES_GENERATED = "oracle_remedies_generated"
    ORACLE_NO_REMEDIES_FOUND = "oracle_no_remedies_found"
    ORACLE_TIMEOUT = "oracle_timeout"
    REPORTER_PROCESSING = "reporter_processing"
    REPORT_GENERATED = "report_generated"
    REPORT_GENERATION_FAILED = "report_generation_failed"
    ERROR = "error"

class LeadTypeEnum(str, Enum):
    MARKDOWN_LINT = "markdown_lint"
    MARKDOWN_SYNTAX = "markdown_syntax"
    LATEX_ERROR = "latex_error"
    LATEX_WARNING = "latex_warning"
    LATEX_UNDEFINED_CONTROL_SEQUENCE = "latex_undefined_control_sequence"
    LATEX_UNDEFINED_ENVIRONMENT = "latex_undefined_environment"
    LATEX_MISSING_DOLLAR = "latex_missing_dollar"
    LATEX_UNBALANCED_BRACES = "latex_unbalanced_braces"
    LATEX_MISMATCHED_DELIMITERS = "latex_mismatched_delimiters"
    LATEX_RUNAWAY_ARGUMENT = "latex_runaway_argument"
    GENERAL_ERROR = "general_error"

class UrgencyEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProcessOutput(BaseModel):
    """Represents the output of an external process call."""
    stdout: str
    stderr: str
    return_code: int

    def is_success(self) -> bool:
        return self.return_code == 0

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
    confidence_score: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="A confidence score between 0.0 and 1.0 indicating how confident the system is "
                    "that this lead represents a real issue that needs to be fixed. "
                    "Higher values indicate higher confidence."
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

# --- Enums for Job State ---

class PipelineStatus(str, Enum):
    """
    Represents the state of the pipeline, determining the next action.
    """
    READY_FOR_MINER = "Ready for Miner"
    MINER_FAILURE_PANDOC = "Miner Failure: Pandoc could not convert Markdown to TeX"
    MINER_SUCCESS_GATHERED_TEX_LOGS = "Miner Success: TeX compilation failed as expected, logs gathered"
    ORACLE_ANALYSIS_COMPLETE = "Oracle Analysis Complete"
    REPORTER_SUMMARY_COMPLETE = "Reporter Summary Complete"

# --- Data Structures for Specialist Results ---

PandocConversionResult = NamedTuple("PandocConversionResult", [
    ("conversion_successful", bool),
    ("output_tex_file_path", Optional[pathlib.Path]),
    ("generated_tex_content", Optional[str]),
    ("pandoc_raw_log", Optional[str])
])

TexCompilationResult = NamedTuple("TexCompilationResult", [
    ("compilation_successful", bool),
    ("pdf_file_path", Optional[pathlib.Path]),
    ("tex_compiler_raw_log", Optional[str])
])

# --- Main Job State Model ---

class DiagnosticJob(BaseModel):
    """
    Core data model for a single debugging job.
    This object is created by the Coordinator and passed through the pipeline,
    evolving as each manager completes its task.
    """
    # Core Identification
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_markdown_path: str
    status: PipelineStatus = PipelineStatus.READY_FOR_MINER

    # --- Artifacts & Data (Paths are relative to a job-specific work directory) ---
    
    # Populated by Miner
    markdown_proofer_errors: List[str] = Field(default_factory=list)
    generated_tex_path: Optional[str] = None
    tex_compilation_log_path: Optional[str] = None
    synctex_path: Optional[str] = None
    generated_pdf_path: Optional[str] = None

    # Populated by Oracle
    actionable_leads: List[ActionableLead] = Field(default_factory=list)

    # Populated by Reporter
    markdown_remedies: List[MarkdownRemedy] = Field(default_factory=list)
    final_report_path: Optional[str] = None

    # --- Internal Metadata ---
    timestamp: float = Field(default_factory=time.time)
    history: List[str] = Field(default_factory=list)

    def log_message(self, message: str):
        """Appends a timestamped message to the job's history log."""
        self.history.append(f"{time.time()}: {message}")

    class Config:
        validate_assignment = True
