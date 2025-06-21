# Smart Diagnostic Engine - V2.4 (Refined 4-Manager Orchestration & Future Work)

**Version:** 2.4.0
**Date:** 2023-10-27 (or current date)

## 1. Overview

The Smart Diagnostic Engine (SDE) is a sophisticated system designed to analyze and diagnose issues in input documents (primarily Markdown) that can prevent successful conversion or compilation, especially to PDF via LaTeX. It employs a modular Python-centric architecture. The primary workflow is orchestrated by `coordinator.py`, which manages a sequence of four core "Manager" modules: `Miner.py`, `Investigator.py`, `Oracle.py`, and `Reporter.py`. These Managers leverage specialized "teams" of scripts and utilize Pydantic models for robust, type-safe data exchange via the `utils/manager_runner.py` utility.

## 2. Core Objectives

*   **Diagnose Conversion/Compilation Failures:** Identify errors in Markdown or intermediate TeX that prevent PDF generation.
*   **Provide Actionable Feedback:** Offer users clear reports and suggestions for fixing identified issues.
*   **Modular Design:** Encapsulate distinct functionalities within core Managers and their specialized support teams/tools.
*   **Extensible Architecture:** Allow for the addition of new diagnostic capabilities and tool integrations.

## 3. Directory Structure

```
smart-pandoc-debugger/
├── archive/                        # Storage for older, potentially useful code versions
│   ├── coordinator.py
│   ├── coordinator.sh
│   └── intake.sh
├── coordinator.py                  # Main Python-based orchestrator script (implements 4-Manager flow)
├── intake.py                       # Python-based entry point for document intake
├── managers/                       # Core logic modules and their specialized teams
│   ├── Converter.py                # Manager: Handles document format conversions (legacy/auxiliary)
│   ├── investigator-team/          # Team: Scripts aiding the Investigator Manager
│   │   └── error_finder.py
│   ├── Investigator.py             # Core Manager: Analyzes logs/artefacts for errors
│   ├── Miner.py                    # Core Manager: Extracts data, handles initial compilation (e.g., Pandoc)
│   ├── oracle-team/                # Team: Scripts aiding the Oracle Manager (e.g., heuristics)
│   │   └── seer.sh
│   ├── Oracle.py                   # Core Manager: Provides insights, suggestions, or remedies
│   ├── reporter-team/              # Team: Scripts for generating specific report sections
│   │   ├── md_report_environment_issues.py
│   │   ├── md_report_unclosed_dollar.py
│   │   ├── receptionist_parse_field_report.py
│   │   ├── tex_report_mismatched_paired_delimiters.py
│   │   ├── tex_report_unbalanced_braces.py
│   │   └── tex_report_unmatched_delimiters.py
│   ├── Reporter.py                 # Core Manager: Assembles and formats final diagnostic reports
│   └── temps/                      # Temporary, utility, or specialized tool scripts
│       ├── Compiler                # (Legacy) Script for compilation (functionality in Miner.py)
│       ├── context_viewer.sh       # Utility: Views context around an issue
│       ├── inspector.sh            # Utility: General purpose inspection/analysis script
│       ├── librarian.sh            # Utility: Manages or extracts information from source/log files
│       ├── proofreader-team/       # Team: Linters and checkers for syntax/style
│       │   ├── check_markdown_unclosed_dollar.py
│       │   ├── check_markdown_unclosed_envs.py
│       │   ├── check_tex_paired_delimiters.py
│       │   ├── check_tex_unbalanced_braces.py
│       │   ├── check_unbalanced_braces.awk
│       │   ├── check_unmatched_inline_math.awk
│       │   └── check_unmatched_left_right.awk
│       ├── proofreader.sh          # Main script for proofreading/linting tasks
│       ├── proofreader2.py         # Alternative/updated Python proofreader script
│       └── sentinel.sh             # Utility: Monitors or guards a process/state
├── readme.md                       # This file
├── test.sh                         # Main testing script for the system
└── utils/                          # Shared utility modules and classes
    ├── __init__.py                 # Makes 'utils' a Python package
    ├── __pycache__/                # Python bytecode cache
    │   ├── ...
    ├── base_cli_manager.py         # Base class supporting CLI for Managers (e.g., --process-job)
    ├── data_model.py               # Pydantic models for data interchange (e.g., DiagnosticJob)
    ├── logger_utils.py             # Centralized logging utilities
    ├── manager_runner.py           # Utility for running Core Manager scripts as distinct processes
    ├── process_runner.py           # Utility for running general external processes/scripts
```

## 4. Component Descriptions

### 4.1. Top-Level Scripts

*   **`intake.py`**: The primary Python-based entry point. It receives user input (e.g., Markdown content), initializes a `DiagnosticJob` Pydantic object, and invokes `coordinator.py` to start the diagnostic pipeline.
*   **`coordinator.py`**: The central Python orchestrator. It implements the primary diagnostic workflow by sequentially invoking the four core Manager scripts (`Miner.py`, `Investigator.py`, `Oracle.py`, `Reporter.py`) using `utils.manager_runner.run_manager()`. It manages the `DiagnosticJob` object as it's passed through and updated by each Manager.
*   **`test.sh`**: The main script for executing automated tests against the system's components and overall workflow. *See To-Do section for desired enhancements.*

### 4.2. `managers/` Directory

This directory houses the SDE's core processing logic, centered around Python "Manager" modules. The primary orchestrated workflow relies on four core Managers. Other Manager files like `Converter.py` exist as part of the broader toolkit but may be legacy or used in auxiliary workflows not directly part of the main `coordinator.py` sequence.

**Core Orchestrated Managers:**

*   **`Miner.py`**: Responsible for initial document processing. This includes attempting Markdown-to-TeX conversion (e.g., via Pandoc, absorbing the role of the legacy `managers/temps/Compiler`), initial fault analysis if MD-to-TeX fails, and attempting TeX-to-PDF compilation.
*   **`Investigator.py`**: If TeX-to-PDF compilation fails, this Manager analyzes TeX compilation logs and related artefacts to identify specific errors. It may leverage scripts from its `investigator-team/` (e.g., `error_finder.py`) for specialized detection. *See To-Do section for clarifying team integration details.*
*   **`Oracle.py`**: Takes `ActionableLead`s (identified by `Miner.py` or `Investigator.py`) and applies heuristics or knowledge-based rules to generate `MarkdownRemedy`s, guiding the user. It may use tools like `oracle-team/seer.sh`.
*   **`Reporter.py`**: The final stage in the main workflow. It gathers all diagnostic information from the `DiagnosticJob` and assembles a comprehensive, user-friendly report, utilizing scripts from `reporter-team/` for formatting specific error types.

**Other Components in `managers/`:**

*   **`Converter.py`**: A Manager for document format conversions. While not part of the primary 4-Manager sequence orchestrated by the current `coordinator.py`, it may serve legacy purposes or be used by other components/workflows.
*   **Team Directories (`investigator-team/`, `oracle-team/`, `reporter-team/`):** Contain specialized scripts (Python, shell) that support their respective parent Manager modules.
*   **`managers/temps/` Subdirectory:** Contains a collection of utility scripts, specialized tools, and potentially experimental or older components. *See To-Do section for clarifying roles of specific scripts.*
    *   **`Compiler`**: (Legacy) Functionality now primarily within `Miner.py`.
    *   **`context_viewer.sh`, `inspector.sh`, `librarian.sh`, `sentinel.sh`**: Various shell utility scripts for specific inspection, extraction, or monitoring tasks.
    *   **`proofreader.sh` / `proofreader2.py` & `proofreader-team/`**: A sub-system for linting and syntax/style checking of Markdown and TeX, comprising a main interface (`proofreader.sh` or `proofreader2.py`) and a collection of specific checker scripts in `proofreader-team/`. These tools might be invoked by one of the core Managers. *See To-Do for clarifying `proofreader.sh` vs `proofreader2.py`.*

### 4.3. `utils/` Directory

This Python package provides shared utilities essential for the SDE's operation.

*   **`data_model.py`**: Defines Pydantic models (e.g., `DiagnosticJob`, `ActionableLead`, `MarkdownRemedy`) that standardize data structures passed between `coordinator.py` and the Manager scripts.
*   **`logger_utils.py`**: Provides centralized logging setup for consistent logging.
*   **`manager_runner.py`**: A crucial utility used by `coordinator.py` to execute the core Manager scripts. It handles:
    *   Serializing the `DiagnosticJob` object to JSON for the Manager's `stdin`.
    *   Deserializing the JSON output from the Manager's `stdout` back into an updated `DiagnosticJob`.
    *   Modifying `PYTHONPATH` for the Manager subprocess, ensuring it can import from the `utils/` package.
    *   Enforcing a contract (e.g., `--process-job` flag, exit codes) with the Manager scripts.
*   **`process_runner.py`**: A general utility for executing external command-line scripts (e.g., shell, AWK) that don't necessarily adhere to the `manager_runner.py`'s strict JSON/`DiagnosticJob` contract. Managers might use this to invoke tools from their "teams" or `temps/`. *See To-Do for clarifying relationship with `manager_runner.py`.*
*   **`base_cli_manager.py`**: Provides base class or utilities that help Manager scripts (e.g., `Miner.py`) parse command-line arguments, particularly the `--process-job` flag required by `manager_runner.py`.

### 4.4. `archive/` Directory

Contains older versions of key scripts, preserved for historical reference, onboarding, or insights during refactoring.

## 5. Workflow Overview (Primary 4-Manager Flow)

The main diagnostic workflow orchestrated by `coordinator.py` involves the following sequence:

1.  **Intake (`intake.py`):** User submits a document. `intake.py` creates an initial `DiagnosticJob` Pydantic object.
2.  **Coordination (`coordinator.py`):** Receives the `DiagnosticJob`.
    a.  **Invoke `Miner.py` (via `manager_runner.py`):**
        *   Attempts MD-to-TeX conversion.
        *   If MD-to-TeX fails: `Miner.py` identifies Markdown-related `ActionableLead`s.
        *   If MD-to-TeX succeeds: `Miner.py` attempts TeX-to-PDF compilation.
    b.  **Invoke `Investigator.py` (via `manager_runner.py`, if TeX-to-PDF failed):**
        *   Analyzes TeX logs, identifies TeX-related `ActionableLead`s.
    c.  **Invoke `Oracle.py` (via `manager_runner.py`, if `ActionableLead`s exist and compilation didn't fully succeed):**
        *   Generates `MarkdownRemedy`s for each lead.
    d.  **Invoke `Reporter.py` (via `manager_runner.py`, always):**
        *   Builds the `final_user_report_summary` within the `DiagnosticJob`.
3.  **Output (`coordinator.py` -> `intake.py` -> user):** The `final_user_report_summary` from the `DiagnosticJob` is printed to `stdout`.

Other tools (e.g., from `managers/temps/proofreader-team/`) may be invoked by one of the core Managers as needed, likely using `utils/process_runner.py`. *See To-Do for workflow example and data flow visualization.*

## 6. Development Focus & Future Direction

*   **Robust 4-Manager Core:** Solidifying the functionality and Pydantic-based data contracts of the four core Managers (`Miner`, `Investigator`, `Oracle`, `Reporter`) as orchestrated by `coordinator.py` and `utils/manager_runner.py`.
*   **Team Specialization:** Further developing the specialized scripts within `*-team/` directories to provide targeted support to their parent Managers.
*   **Pydantic Data Model Refinement:** Continuously improving the `DiagnosticJob` and related Pydantic models in `utils/data_model.py` for clarity and comprehensive data capture.
*   **Enhanced Error Analysis & Remedies:** Expanding the system's ability to detect a wider range of issues and provide more precise, helpful `MarkdownRemedy`s.
*   **Legacy Code Management:** Gradually integrating or retiring components from `managers/temps/` and clarifying the role of auxiliary Managers like `Converter.py`.

## 7. To-Do & Areas for README Improvement

This section outlines areas where this README and the project understanding could be further enhanced. These points are derived from a critical analysis of the available information:

*   **[ ] Clarify Specific Roles in `managers/temps/`:**
    *   Provide more specific, less generic descriptions for the roles of `inspector.sh` and `sentinel.sh`.
    *   Detail the precise relationship and usage differences between `proofreader.sh` and `proofreader2.py` if both are actively maintained or serve distinct purposes.
*   **[ ] Detail Manager-Team Integration Mechanism:**
    *   Specify *how* core Manager modules (e.g., `Investigator.py`) integrate with or invoke scripts from their associated "team" directories (e.g., `investigator-team/error_finder.py`). Is it direct Python import/call, or via `utils/process_runner.py` for shell/external scripts?
*   **[ ] Refine `utils/process_runner.py` vs. `utils/manager_runner.py` Distinction:**
    *   Clearly delineate when one is used over the other. Is `process_runner.py` exclusively for non-Manager scripts, or can Managers also use it for more loosely coupled tools?
*   **[ ] Add `DiagnosticJob` Data Flow Example:**
    *   Include a simplified example (even pseudocode or a list of key field changes) illustrating how the `DiagnosticJob` Pydantic object evolves as it passes through the main 4-Manager pipeline for a common error scenario.
*   **[ ] Enhance `test.sh` Description:**
    *   Specify the *types* of tests `test.sh` performs (e.g., unit, integration, end-to-end) and its primary coverage goals.
*   **[ ] Incorporate a High-Level Architectural Diagram:**
    *   A simple visual (ASCII or linked image) showing the main components (`intake`, `coordinator`, core `Managers`, `utils`) and their primary interactions would greatly aid comprehension.
*   **[ ] Add a "Getting Started / How to Run" Section:**
    *   Provide a minimal example or instructions for developers to run a basic diagnostic task, or point to more detailed developer setup documentation if it exists.
*   **[ ] Maintain Consistency between "Current State" and "Future Direction":**
    *   Ensure that descriptions of components and workflows accurately reflect the current implementation, while "Future Direction" clearly outlines aspirational changes. This is especially important during active refactoring.
*   **[ ] Review and Standardize Terminology:**
    *   While "Manager" is now dominant, ensure any lingering "service" terminology (if not intended for a specific distinction) is harmonized.


