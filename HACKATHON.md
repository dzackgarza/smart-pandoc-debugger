# Smart Pandoc Debugger - HACKATHON DIRECTIVES

## 1. CORE DIRECTIVES (NON-NEGOTIABLE)

### 1.1. OBSESS OVER USER DEBUGGING
- Your primary goal is to provide **clear, actionable debug information**.
- Error messages **MUST** tell the user exactly how to fix their document.
- **ALWAYS** implement the simplest, most direct solution. Complexity is the enemy.

### 1.2. METHODOLOGY: SIMPLE, THEN REFINE
- **First, make the test pass.** Use the simplest possible code.
- **Hardcode if necessary.** "Faking it" is mandatory to establish a baseline.
- **DO NOT** add complexity until the basic test passes and is committed.

### 1.3. ORACLE IS A LIABILITY
- **Bypass the Oracle by default.** It is not part of the MVP.
- **Direct error detection is the ONLY approved method** for this hackathon.
- All error handling **WILL BE** simple and direct.

---

## 2. HACKATHON RULES OF ENGAGEMENT

- **RULE 1: TEST EXPECTATIONS ARE IMMUTABLE.** You will not modify them for any reason.
- **RULE 2: CLAIM YOUR TASK.** Before starting, mark your task as "IN-PROGRESS".
- **RULE 3: PASS THE TEST.** A task is only done when its test passes.
- **RULE 4: TEST AFTER EVERY CHANGE.** No exceptions.
- **RULE 5: ONE TASK AT A TIME.** Do not work on multiple tests simultaneously.
- **RULE 6: ZERO REGRESSIONS.** A passing test must never fail. If it does, you **WILL** revert your changes immediately.

---

## 3. WORKFLOW PROTOCOL

- **STEP 1: BASELINE.** Run `./test` and `./h1_tests.sh` to confirm the current state.
- **STEP 2: SELECT.** Pick one, and only one, task from the checklist.
- **STEP 3: IMPLEMENT.** Make the minimal change required to pass the corresponding test.
- **STEP 4: VALIDATE.** Run the relevant test script after every file modification.
- **STEP 5: COMMIT.** When the test passes with no regressions, commit with the message `PASS: [Test #] Description`.
- **STEP 6: RESET IF STUCK.** If you are stuck for more than 5 minutes, you **WILL** run `git checkout -- .` and rethink your approach. Do not waste time on a failing strategy.

---

## 4. CODE OF CONDUCT

### 4.1. LOGGING IS MANDATORY
- You **WILL** add extensive `logger.debug()` calls to trace execution flow.
- You **WILL** log all critical variables and decision points.

### 4.2. SHORT-CIRCUIT AGGRESSIVELY
- To make tests pass, you **WILL** comment out or stub complex code.
- You **WILL** return hardcoded values as a first-pass solution.

### 4.3. FAIL FAST, FAIL LOUD, FAIL ALWAYS
- You **WILL** use assertions for all preconditions and invariants. There are no excuses.
- There will be **NO** `try-catch` blocks. Unhandled exceptions are the goal.

---
## 5. TEST CHECKLIST (IN ORDER OF PRIORITY)

### PRIORITY 1: Fix Regressions & Remove Hacks
- [x] **Task 6: Fix "Missing Dollar" Regression**
  - **Goal**: The `./test` script shows the "Missing Dollar" test is failing. Implement a robust fix that passes both `./test` and `./test2.sh`.
  - **Files**: `managers/investigator-team/error_finder.py` or a new specialist.
  - **Owner**: Gemini (COMPLETED)

- [x] **Task 7: Refactor Miner Hacks**
  - **Goal**: Remove the hardcoded `if "..." in dj.original_markdown_content:` blocks from `managers/Miner.py` for "Mismatched Delimiters" and "Unbalanced Braces". The system should rely on the Investigator pipeline for these.
  - **Files**: `managers/Miner.py`
  - **Owner**: Gemini (COMPLETED - Functionality already exists)

- [x] **Task 8: Robust "Unbalanced Braces" Detection**
  - **Goal**: Create a proper, non-hacky detection mechanism for unbalanced braces that passes both `./test` and `./test2.sh`. This replaces the hack removed in Task #7.
  - **Files**: `managers/investigator-team/error_finder.py`
  - **Owner**: Gemini (COMPLETED)

- [x] **Task 9: Robust "Mismatched Delimiters" Detection**
  - **Goal**: The current detection is a hack in `Miner.py`. Implement the *real* detection logic in the Investigator pipeline. This is the final step for the hack removed in Task #7.
  - **Files**: `managers/investigator-team/error_finder.py`
  - **Owner**: Gemini (COMPLETED)

### PRIORITY 2: Expand Test Coverage
- [x] **Task 10: Add Test Case for "Runaway Argument"**
  - **Goal**: Add a new test case to the `./test` script (Test #6) that specifically fails with a "Runaway argument?" error from a TeX compilation.
  - **Files**: `./test`
  - **Owner**: Gemini (COMPLETED)

- [x] **Task 11: Add Test Case for "Undefined Environment"**
  - **Goal**: Add a new test case to `./test` for an undefined environment error (e.g., `\begin{nonexistent_env}`).
  - **Files**: `test`, `test_cases/`
  - **Owner**: Gemini (COMPLETED)

### PRIORITY 3: Enhance Managers & Data Model
- [x] **Task 12: Enhance Oracle Remedies**
  - **Goal**: Improve the `OracleManager_HackathonMode` to provide specific, helpful remedies for at least three distinct error signatures (e.g., `LATEX_UNDEFINED_CONTROL_SEQUENCE`, `LATEX_UNBALANCED_BRACES`).
  - **Files**: `managers/Oracle.py`
  - **Owner**: Gemini (COMPLETED)

- [x] **Task 13: Improve Reporter Formatting**
  - **Goal**: Modify the `Reporter` to include the `problem_description` from the `ActionableLead` in the final report, giving users more context.
  - **Files**: `managers/Reporter.py` and its specialists.
  - **Owner**: Gemini (COMPLETED - Functionality already exists)

- [x] **Task 14: Add Confidence Score**
  - **Goal**: Add an optional `confidence_score: float` field to the `ActionableLead` Pydantic model. This will be used in the future to prioritize leads.
  - **Files**: `utils/data_model.py`
  - **Owner**: Cascade (COMPLETED - Field already exists with proper implementation)

- [x] **Task 15: Isolate Specialist Logic**
  - **Goal**: Create a new specialist script, e.g., `managers/investigator-team/undefined_command_proofer.py`, and move the "Undefined control sequence" logic out of `error_finder.py` and into this new file. The goal is to make `error_finder.py` a simple dispatcher.
  - **Files**: `managers/investigator-team/error_finder.py`, new specialist script.
  - **Owner**: Gemini (COMPLETED)

### PRIORITY 5: Table & Complex Environments
- [ ] **Task 16: Add Test Case for Table Environment**
  - **Goal**: Test handling of tabular environments, a common source of LaTeX errors.
  - **Files**: `test`, `test_cases/`
  - **Owner**:

- [ ] **Task 17: Add Test Case for Math Operators**
  - **Goal**: Test proper handling of math operators (e.g., `$\sin x$` vs `$sin x$`).
  - **Files**: `test`, `test_cases/`
  - **Owner**:

- [ ] **Task 18: Handle Nested Math Environments**
  - **Goal**: Properly detect and handle nested math environments like `$a_{b_c}$`
  - **Files**: `managers/investigator-team/error_finder.py`
  - **Owner**:

- [ ] **Task 19: Support Complex Tables**
  - **Goal**: Add support for complex table structures with merged cells
  - **Files**: `managers/investigator-team/error_finder.py`
  - **Owner**:

- [ ] **Task 20: Math Operator Validation**
  - **Goal**: Validate proper usage of math operators and functions
  - **Files**: `managers/investigator-team/error_finder.py`
  - **Owner**:

## 🛠️ Test Commands
```bash
# Run all tests
./test

# Run specific test (1-5)
./test 1  # Test missing dollar sign
./test 3  # Test mismatched delimiters
./test 4  # Test align environment
./test 5  # Test unbalanced braces
```
