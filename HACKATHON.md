# SDE HACKATHON: JUNE 2025

**Motto: "Fail Fast, Fail Loud"**

## DIRECTIVES

1.  You **WILL** use the provided `ptest.sh` script for all tests. It MUST pass before you are done.
2.  You **WILL** commit your changes with descriptive messages after each completed task.
3.  You **WILL** add extensive `logger.debug()` calls to trace execution flow. You **WILL** log all critical variables and decision points.
4.  There will be **NO** `try-catch` blocks. Unhandled exceptions are the goal.
5.  You **WILL** use assertions for all preconditions and invariants.

---

## TASK CHECKLIST (SDE v5.1 -> v5.2)

-   [x] **Task 1: Project Setup** - `COMPLETED`
    -   Goal: Ensure a clean, testable baseline.
    -   Action: Run `./ptest.sh` and confirm all tests fail as expected.

-   [ ] **Task 2: Fix Pandoc Call**
    -   Goal: The `pandoc` call in `pandoc_tex_converter.py` is incorrect for documents with raw LaTeX. It escapes characters (`\(` -> `\\(`) that should be preserved.
    -   Action: Modify the call to use `markdown-raw_tex` instead of `markdown`.
    -   Verify: Test #4 (`ptest.sh 4`) should now pass.

-   [ ] **Task 3: Fix "Undefined Environment" Logic**
    -   Goal: The `undefined_environment_proofer.py` is not being called by the Investigator.
    -   Action: Integrate the proofer into `Investigator.py`'s specialist rotation.
    -   Verify: Test #7 (`ptest.sh 7`) should now pass.

-   [ ] **Task 4: Add "Undefined Command" Test Case**
    -   Goal: The `undefined_command_proofer.py` has no test coverage.
    -   Action: Add a new test case (Test #8) to `./test` that uses a simple, undefined LaTeX command (e.g., `\undefinedcommand`).
    -   Verify: The new Test #8 should fail initially, then pass after the proofer is correctly integrated.

-   [x] **Task 5: Fix "Undefined Command" Proofer**
    -   Goal: The regex in `undefined_command_proofer.py` is faulty and doesn't correctly capture the command.
    -   Action: Fix the regex pattern to correctly extract the undefined command name.
    -   Verify: Test #8 should now pass.
