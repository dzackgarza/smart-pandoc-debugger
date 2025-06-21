## MVP Checklist to Pass Basic Tests (SDE)

*   **[ ] `managers/miner-team/pandoc_tex_converter.py`:** Modify the Pandoc command to minimize problematic label/hypertarget generation (e.g., try `-f markdown-auto_identifiers`). This is to prevent the common "Undefined control sequence" errors from Pandoc's default TeX output.
*   **[ ] `managers/Investigator.py` (and/or `investigator-team/error_finder.py`):** Implement TeX log parsing to identify common LaTeX errors from `DiagnosticJob.tex_compiler_raw_log`. For each error found, create and append a populated `ActionableLead` object to `DiagnosticJob.actionable_leads`.
*   **[ ] `managers/Miner.py`:** Ensure that if `pandoc_tex_converter.py` reports a Pandoc tool failure (non-zero RC from Pandoc itself), `Miner.py` correctly sets `DiagnosticJob.md_to_tex_conversion_successful = False` and `DiagnosticJob.final_job_outcome = "MarkdownError_MdToTexConversionFailed"` (or similar), and provides the lead from the specialist. This is to correctly handle tests like T1.1 and T1.2.
*   **[ ] `utils/data_model.py` & `managers/Reporter.py`:** Address the `AttributeError: 'MarkdownRemedy' object has no attribute 'confidence_score'` in `Reporter.py`. Either add `confidence_score: Optional[float] = Field(None, ge=0, le=1)` to the `MarkdownRemedy` Pydantic model in `data_model.py` (and ensure `Oracle.py` can set it) OR remove the line attempting to access `remedy.confidence_score` in `Reporter.py`.
*   **[ ] `managers/Oracle.py` (and/or `oracle-team/seer.py`):** Implement basic logic to consume at least one type of `ActionableLead` (e.g., from a TeX error identified by `Investigator`) and generate a corresponding `MarkdownRemedy` object. This is to ensure the `Reporter.py` has remedies to process once its attribute error is fixed.

---

This condensed list targets the primary blockers observed in the test results, aiming to get the core pipeline (MD Proofing -> MD-to-TeX -> TeX-to-PDF -> TeX Error Investigation -> Basic Oracle -> Reporting) to function correctly for these scenarios.
