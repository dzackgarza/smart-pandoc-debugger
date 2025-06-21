# To-Do List for Minor Version Bump (Improving First ~3 V3 Tests)

## I. Coordinator (`coordinator.sh`)

- [x] **Task 1: Add Source Component Debug Line for Proofreader Path.**
    - Action: In `run_diagnostics()`, when `proofreader_error_data` is present, ensure `echo "# DEBUG: SourceComponent: Proofreader"` is printed to stdout before calling `reporter_emit_proofreader_error`.

## II. Proofreader (`proofreader.sh`)

- [x] **Task 2: Enhance `\left`/`\right` to include the problematic snippet in structured output.**
    - Action: Add/modify structured output field(s) (e.g., `PROBLEM_SNIPPET`) to contain the specific problematic text like `\left( x + y`. Update `awk` or processing logic to capture this.
    - *Status: Implemented in `proofreader-team/check_unmatched_left_right.awk` (used by `proofreader.sh` V1.3+). Successfully used by Reporter for V3 message in previous tests.*
- [x] **Task 3: Implement Detection for Unterminated Inline Math (`$...`).**
    - Action: Implement a checker (Python script `check_markdown_unclosed_dollar.py`) to operate directly on Markdown for unclosed `$`. `proofreader.sh` V1.4 delegates to this.
    - Action: Output structured data: `ERROR_TYPE=UnterminatedInlineMathMarkdown`, `LINE_NUMBER`, `PROBLEM_SNIPPET` (e.g., `x + y + z` from the unclosed `$`), `LINE_CONTENT`.
    - *Status: Implemented and successfully detecting error. Reporter update (Task 6) needed for V3 message.*
- [x] **Task 4: Implement Detection for Extra/Unbalanced Braces (`{ }`) within simple math contexts (TeX check).**
    - Action: `proofreader-team/check_unbalanced_braces.awk` (used by `proofreader.sh` V1.3+) implements this.
    - Action: Output structured data: `ERROR_TYPE=UnbalancedBraces`, `LINE_NUMBER`, `PROBLEM_SNIPPET`, `DETAILS` (brace counts), `LINE_CONTENT`.
    - *Status: Implemented. Awaiting test with relevant input and Reporter update (Task 7).*

## III. Reporter (`reporter.sh`)

- [x] **Task 5: Update `reporter_emit_proofreader_error` for "Unclosed `\left`" V3 message.**
    - Action: Modify the `UnmatchedDelimiters` block to use the `PROBLEM_SNIPPET` from Proofreader.
    - Action: Construct the targeted V3 error message.
    - *Status: Implemented in `reporter.sh` V1.6 and successfully producing V3-style message.*
- [ ] **Task 6: Add handler in `reporter_emit_proofreader_error` for `UnterminatedInlineMathMarkdown`.**
    - Action: Add/modify `elif [[ "$error_type" == "UnterminatedInlineMathMarkdown" ]]; then ...` block.
    - Action: Use `PROBLEM_SNIPPET` (which is the content like `x + y + z`) to construct the V3 message: `"Error: Unterminated math mode — started with '$' but no closing '$' found for '$PROBLEM_SNIPPET'. Add a closing '$'."`.
    - Action: Update `Details:` and `Hint:` sections to refer to Markdown source and `$` delimiters.
    - *Status: Implementation attempt in `reporter.sh` V1.6 handled `UnterminatedInlineMath` (TeX); needs update for `UnterminatedInlineMathMarkdown`.*
- [ ] **Task 7: Add handler in `reporter_emit_proofreader_error` for `UnbalancedBraces`/`ExtraClosingBrace` (TeX check).**
    - Action: Ensure the `UnbalancedBraces` handler in `reporter.sh` V1.6 correctly uses `PROBLEM_SNIPPET` and `DETAILS` to construct V3 messages.
    - *Status: Implementation attempt in `reporter.sh` V1.6. Awaiting test verification with relevant input.*

## IV. Investigation (No code changes for this minor bump)

- [ ] **Task 8: Investigate why some errors currently result in "PDF generated successfully."**
    - Action: Review logs and behavior for tests like "Missing \end{align}" where `pdflatex` exits 0.
    - *Status: Partially addressed for "Unterminated inline math" by moving check to Markdown. Other cases may still exist.*
