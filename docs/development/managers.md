# SDE Manager and Specialist Contract (V1)

This document outlines the design philosophy and technical contract that all "Manager" and "Specialist" scripts in the Smart Pandoc Debugger (SDE) project must follow. Adhering to this contract ensures that the system remains modular, testable, and easy to develop for.

## Core Philosophy: A Society of Scripts

The SDE is not a single, monolithic application. It is a collection of independent, specialized scripts that communicate by passing a JSON object through standard Unix pipes (`stdin`/`stdout`).

This "society of scripts" or "pipe-and-filter" architecture has several key advantages for this project:

1.  **Modularity:** Each script has one job and does it well. It knows nothing about the scripts that come before or after it.
2.  **Testability:** Each script can be tested in isolation from the command line using simple file redirection (`cat job.json | python3 manager.py`). This avoids the need for complex mocking frameworks.
3.  **Ease of Development:** The only interface a developer needs to understand is the single, well-defined `DiagnosticJob` data model. There are no complex class hierarchies or APIs to learn.
4.  **Robustness:** Failures are easy to isolate. If a script in the pipeline fails, it exits non-zero, the pipe breaks, and the `Coordinator` knows exactly which stage failed.

## The Pipe-Script Technical Contract

Every manager script (`Miner.py`, `Oracle.py`, etc.) MUST adhere to the following rules.

### 1. Input/Output Contract

-   **Input:** A script MUST read a single JSON object from `stdin`. This JSON object MUST successfully parse and validate as a `utils.data_model.DiagnosticJob` object.
-   **Output:** A script MUST write a single JSON object to `stdout`. This JSON object MUST also be a valid `DiagnosticJob` object. Typically, this is the *modified* input object.
-   **Error Handling:** All logging, debug messages, and error traces MUST be written to `stderr` to avoid corrupting the JSON output on `stdout`.

To simplify this, all managers should use the `utils.base_cli_manager.run_manager_script` utility, which handles this entire lifecycle.

### 2. State Management Contract

The flow of the pipeline is controlled by the `status` field in the `DiagnosticJob` object, which uses the `PipelineStatus` enum.

-   A manager receives a job with a specific status.
-   It performs its designated task.
-   It MUST update the job's `status` field to one of the valid subsequent states before printing the final job object to `stdout`.

This creates a simple, explicit, and robust finite state machine that the `Coordinator` uses to dispatch tasks.

### 3. Import and Path Contract

-   **Imports:** All scripts MUST use absolute imports relative to the project's root directory (e.g., `from managers.miner_team.specialist import ...`). This is made possible by the runner script, which correctly sets the `PYTHONPATH`. Do NOT use relative imports (e.g., `from .specialist import ...`).
-   **Paths:** All paths within the `DiagnosticJob` object should be relative to a temporary working directory created by the `Coordinator` for that specific job. Scripts should not rely on their own location in the file system. 