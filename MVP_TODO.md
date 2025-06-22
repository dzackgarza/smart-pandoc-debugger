# Smart Pandoc Debugger - MVP TODO List

This document outlines the specific, actionable tasks needed to achieve a Minimum Viable Product (MVP) for the Smart Pandoc Debugger. The tasks are organized by priority and component.

## High Priority Tasks

### 1. Core Infrastructure Setup

- [ ] **Create a system-wide executable script**
  - Create a shell script named `smart-pandoc-debugger` in the project root
  - Make it executable with `chmod +x smart-pandoc-debugger`
  - Script should invoke `intake.py` with proper environment variables
  - Add symlink to a directory in PATH or update PATH to include the project directory

- [ ] **Set up proper Python module structure**
  - Ensure all necessary `__init__.py` files exist in module directories
  - Fix import paths in all modules to ensure proper module resolution

### 2. Miner Manager Implementation

- [ ] **Implement `managers/miner_team/markdown_proofer.py`**
  - Create this file if it doesn't exist
  - Implement the `run_markdown_checks()` function to detect basic Markdown errors
  - Focus on detecting missing dollar signs, mismatched delimiters, and unbalanced braces

- [ ] **Implement `managers/miner_team/pandoc_tex_converter.py`**
  - Create this file if it doesn't exist
  - Implement the `convert_md_to_tex()` function to handle Markdown to TeX conversion
  - Use Pandoc with options to minimize problematic label/hypertarget generation (e.g., `-f markdown-auto_identifiers`)
  - Properly handle and report Pandoc errors

- [ ] **Implement `managers/miner_team/tex_compiler.py`**
  - Create this file if it doesn't exist
  - Implement the `compile_tex_to_pdf()` function to handle TeX to PDF compilation
  - Properly capture and store the LaTeX compilation log
  - Handle and report pdflatex errors

### 3. Investigator Manager Implementation

- [ ] **Move `DEBUG_error_finder/error_finder.py` to `managers/investigator-team/`**
  - Ensure the file is properly integrated with the Investigator Manager
  - Update imports and paths as needed

- [ ] **Enhance `error_finder.py` to detect common LaTeX errors**
  - Implement detection for "Undefined control sequence" errors
  - Implement detection for "Missing dollar sign" errors
  - Implement detection for "Mismatched delimiters" errors
  - Implement detection for "Unbalanced braces" errors
  - Implement detection for "Runaway argument" errors
  - Implement detection for "Undefined environment" errors

- [ ] **Fix the Investigator Manager to properly use `error_finder.py`**
  - Ensure proper handling of the TeX compilation log
  - Correctly transform error_finder output into ActionableLead objects

### 4. Oracle Manager Implementation

- [ ] **Implement basic Oracle functionality**
  - Focus on direct error detection as specified in HACKATHON.md
  - Implement hardcoded remedies for common error types
  - Ensure proper generation of MarkdownRemedy objects for each ActionableLead

- [ ] **Fix the confidence_score issue**
  - Address the `AttributeError: 'MarkdownRemedy' object has no attribute 'confidence_score'` in Reporter.py
  - Either add the field to the MarkdownRemedy model or remove the reference in Reporter.py

### 5. Reporter Manager Implementation

- [ ] **Enhance the Reporter to generate clear, actionable reports**
  - Format the report to clearly show each error and its remedy
  - Include relevant context from the original Markdown document
  - Ensure the report is user-friendly and provides clear instructions

## Medium Priority Tasks

### 1. Testing Infrastructure

- [ ] **Fix the test script to work with the new executable**
  - Update the test script to use the correct path to the executable
  - Ensure all tests can be run individually and as a group

- [ ] **Add comprehensive test cases**
  - Implement test cases for all supported error types
  - Include edge cases and complex scenarios

### 2. Error Detection Enhancements

- [ ] **Implement detection for additional LaTeX errors**
  - Add support for table-related errors
  - Add support for math operator errors
  - Add support for nested math environment errors

### 3. Documentation

- [ ] **Create user documentation**
  - Document how to install and use the system
  - Provide examples of common errors and their solutions

- [ ] **Create developer documentation**
  - Document the system architecture and component interactions
  - Provide guidelines for adding new error detection capabilities

## Low Priority Tasks (Future Enhancements)

- [ ] **Implement a web interface**
  - Create a simple web UI for uploading Markdown documents
  - Display the diagnostic report in a user-friendly format

- [ ] **Add support for additional document formats**
  - Extend the system to handle other input formats (e.g., RST, AsciiDoc)
  - Support additional output formats beyond PDF

- [ ] **Implement an interactive mode**
  - Allow users to interactively fix errors and rerun the diagnostic process
  - Provide real-time feedback on fixes

## Implementation Notes

1. **Follow the HACKATHON.md directives:**
   - Focus on making tests pass with the simplest possible code
   - Hardcode solutions if necessary to establish a baseline
   - Add extensive logging for debugging
   - Fail fast and loud - use assertions liberally

2. **Prioritize the core workflow:**
   - Ensure the basic pipeline (MD Proofing -> MD-to-TeX -> TeX-to-PDF -> TeX Error Investigation -> Basic Oracle -> Reporting) works correctly
   - Focus on the most common error types first

3. **Maintain backward compatibility:**
   - Ensure changes don't break existing functionality
   - Follow the existing data model and component interfaces

4. **Testing strategy:**
   - Test after every change
   - Ensure no regressions in existing functionality
   - Focus on one task at a time