# Smart Pandoc Debugger - FAST-TODO

## 📚 INSTRUCTIONS

### 🎯 MVP GOALS (READ FIRST)

### 🚨 CORE PRINCIPLES
1. **USER DEBUGGING IS KING**
   - Show clear, actionable debug info to users
   - Error messages should help users fix issues directly
   - Prefer simple, direct solutions over complex ones

2. **START SIMPLE, THEN REFINE**
   - Make tests pass with the simplest possible solution first
   - Fake it till you make it - hardcode responses if needed
   - Add complexity ONLY after basic tests pass

3. **ORACLE IS OPTIONAL**
   - Bypass the Oracle if it gets in the way
   - Direct error detection > Oracle-based detection for MVP
   - Keep error handling simple and direct

### 🚀 HACKATHON MODE: RULES
1. **NEVER** modify test expectations
2. Mark items as IN-PROGRESS when started
3. Check off items ONLY when test passes
4. Run tests after EVERY change
5. Work on ONE test at a time
6. **NO REGRESSIONS** - Passing tests must stay passing

### 🛠️ DEVELOPMENT WORKFLOW
1. **Start Simple**
   - Make the minimal change to pass the test
   - Use hardcoded values if needed
   - Comment out complex logic initially

2. **Test Frequently**
   - Run tests after every change
   - Use `./test X` to run specific tests
   - Check debug output with `DEBUG=1 ./test X`

3. **Commit Often**
   - Commit after each passing test
   - Use descriptive commit messages
   - Keep commits focused on one change

### 🐛 DEBUGGING QUICK REFERENCE

#### Common Error Patterns
1. **Missing Math Delimiters**
   - Pattern: `f(x)`, `x = 2` without `$`
   - Fix: Add pattern to `ERROR_SIGNATURES`

2. **Mismatched Delimiters**
   - Pattern: `\left(` with `\right]`
   - Fix: Add regex for `\\left\\(.*?\\right[^)]`

3. **Undefined Commands**
   - Look for: `! Undefined control sequence`
   - Fix: Add command to whitelist or error patterns

#### Quick Commands
```bash
# Run specific test with debug
DEBUG=1 ./test 3

# View latest LaTeX output
cat $(ls -td /tmp/sde_miner_* | head -1)/pandoc_output.tex

# View test input
grep -A 5 "3)" test | head -n 10
```

---

## ✅ TODO LIST

### 🔥 MVP TASKS

## 🔧 PROJECT-SPECIFIC DEBUGGING PATHS

### 🎯 Critical Debugging Files
1. **`managers/investigator-team/error_finder.py`**
   - Main file for error detection patterns
   - Look for `ERROR_SIGNATURES` dictionary to add new patterns
   - `find_primary_error()` is where most pattern matching happens

2. **`test` Script**
   - Run specific tests: `./test 3` (for test #3)
   - Debug mode: `DEBUG=1 ./test 3`
   - Check the exact test input in the test case definitions

3. **Temporary Files**
   - LaTeX output and logs are in `/tmp/sde_miner_*/`
   - Look for `pandoc_output.tex` to see generated LaTeX
   - Check `pandoc_output.log` for compilation errors

### 🎯 MVP Development Strategy

#### 1. DEBUGGING FIRST
- Add debug output before writing logic
- Log all decision points
- Show intermediate states

#### 2. FAKE IT TILL YOU MAKE IT
```python
# Example: Hardcoded response for Test 1 (Missing $)
if "f(x) = 2x + 3" in content:
    return "Missing math delimiters"

# Example: Bypass Oracle
def get_oracle_advice(error):
    # TODO: Implement proper Oracle integration
    return "Try fixing the syntax error"  # Generic fallback
```

### 🔥 Development Rules
- [ ] **EXTENSIVE LOGGING**
  - Add debug logs at every step
  - Use `logger.debug()` for detailed execution flow
  - Log variable states and important decisions
  - Use unique identifiers for log messages (e.g., `[MISSING_$]` for missing dollar sign detection)

- [ ] **SHORT-CIRCUIT LIBERALLY**
  - Comment out or stub complex code blocks
  - Return hardcoded values to make tests pass first
  - Use feature flags to enable/disable functionality
  - Example:
    ```python
    # TODO: Implement proper detection
    if "f(x) = 2x + 3" in input_text:
        return "Missing math delimiters"
    ```

- [ ] **FAIL FAST AND LOUD**
  - Use assertions aggressively
  - No try-catch unless absolutely necessary
  - Use `assert` for preconditions and invariants
  - If something unexpected happens, raise an exception immediately
  - Example:
    ```python
    def process_math(content: str) -> str:
        assert content is not None, "Content cannot be None"
        if not content.strip():
            raise ValueError("Empty content provided")
        # Rest of the function
    ```

### Workflow
1. **Before starting**: Run `./h1_test` to establish a baseline
2. Pick a test from the checklist below
3. Mark it as IN-PROGRESS
4. Make minimal changes to make it pass
5. **Validation**:
   - Run `./h1_test` after each change
   - A test is only considered passing if `h1_test` shows it as passing
   - Check for any regressions in previously passing tests
6. **When test passes**:
   - ✅ Check it off in the checklist
   - `git add [modified-files]`  # Only add files you changed
   - `git commit -m "PASS: [Test #] Description"`
7. **If stuck after 5 minutes**:
   - `git checkout -- [modified-files]`  # Discard changes to specific files
   - ⏩ Move to next test
8. **Handling Regressions**:
   - If a change breaks a previously passing test:
     1. Revert the change immediately
     2. Investigate why it caused a regression
     3. Find an alternative approach that doesn't break existing functionality
9. **Never commit broken code** - fix or revert before moving on
10. **Before final commit**:
    - Run `./h1_test` to verify all tests still pass
    - Check for any console warnings or errors

## TEST CHECKLIST (IN ORDER OF PRIORITY)

### Test 1: Runaway Argument
- [ ] Status: IN-PROGRESS
- **Input**:
  ```markdown
  # Test
  
  $\frac{1}{1 + e^{-x}$
  ```
- **Expected**: Should detect runaway argument

### Test 2: Undefined Environment
- [ ] Status: PENDING
- **Input**:
  ```markdown
  # Test
  
  \begin{nonexistent_env}
  content
  \end{nonexistent_env}
  ```
- **Expected**: Should detect undefined environment

### Test 3: Missing End Environment
- [ ] Status: PENDING
- **Input**:
  ```markdown
  # Test
  
  \begin{align*}
  a &= b + c \\
  d &= e + f
  ```
- **Expected**: Should detect missing \end{align*}

### Test 4: Math Mode in Text
- [ ] Status: PENDING
- **Input**:
  ```markdown
  # Test
  
  This $should not be in math mode
  ```
- **Expected**: Should detect math mode in text

### Test 5: Multiple Errors
- [ ] Status: PENDING
- **Input**:
  ```markdown
  # Test
  
  $f(x) = \frac{1}{1 + e^{-x}$
  $\nonexistentcommand$
  ```
- **Expected**: Should detect both unbalanced braces and undefined command

### Test 6: Table Environment
- [ ] Status: PENDING
- **Input**:
  ```markdown
  # Test
  
  \begin{tabular}{|l|c|r|}
  \hline
  Left & Center & Right \\
  \hline
  A & B & C \\
  \hline
  \end{tabular}
  ```
- **Expected**: Should properly handle tabular environment

### Test 7: Math Operators
- [ ] Status: PENDING
- **Input**:
  ```markdown
  # Test
  
  $\sin x + \log y = \sqrt{z}$
  ```
- **Expected**: Should properly render math operators

## 🚀 NEXT HACKATHON (30m Sprint)

Here are the next set of prioritized goals. Claim a task by adding your name and moving it to "IN-PROGRESS".

### PRIORITY 1: Fix Regressions & Remove Hacks
- [ ] **Task 6: Fix "Missing Dollar" Regression**
  - **Goal**: The `./test` script shows the "Missing Dollar" test is failing. Implement a robust fix that passes both `./test` and `./test2.sh`.
  - **Files**: `managers/investigator-team/error_finder.py` or a new specialist.
  - **Owner**:

- [ ] **Task 7: Refactor Miner Hacks**
  - **Goal**: Remove the hardcoded `if "..." in dj.original_markdown_content:` blocks from `managers/Miner.py` for "Mismatched Delimiters" and "Unbalanced Braces". The system should rely on the Investigator pipeline for these.
  - **Files**: `managers/Miner.py`
  - **Owner**:

- [ ] **Task 8: Robust "Unbalanced Braces" Detection**
  - **Goal**: Create a proper, non-hacky detection mechanism for unbalanced braces that passes both `./test` and `./test2.sh`. This replaces the hack removed in Task #7.
  - **Files**: `managers/investigator-team/error_finder.py`
  - **Owner**:

- [ ] **Task 9: Robust "Mismatched Delimiters" Detection**
  - **Goal**: The current detection is a hack in `Miner.py`. Implement the *real* detection logic in the Investigator pipeline. This is the final step for the hack removed in Task #7.
  - **Files**: `managers/investigator-team/error_finder.py`
  - **Owner**:

### PRIORITY 2: Expand Test Coverage
- [ ] **Task 10: Add Test Case for "Runaway Argument"**
  - **Goal**: Add a new test case to `./test` for a `Runaway argument?` LaTeX error (e.g., from a command with a missing closing brace).
  - **Files**: `test`, `test_cases/`
  - **Owner**:

- [ ] **Task 11: Add Test Case for "Undefined Environment"**
  - **Goal**: Add a new test case to `./test` for an undefined environment error (e.g., `\begin{nonexistent_env}`).
  - **Files**: `test`, `test_cases/`
  - **Owner**:

### PRIORITY 3: Enhance Managers & Data Model
- [ ] **Task 12: Enhance Oracle Remedies**
  - **Goal**: Improve the `OracleManager_HackathonMode` to provide specific, helpful remedies for at least three distinct error signatures (e.g., `LATEX_UNDEFINED_CONTROL_SEQUENCE`, `LATEX_UNBALANCED_BRACES`).
  - **Files**: `managers/Oracle.py`
  - **Owner**:

- [ ] **Task 13: Improve Reporter Formatting**
  - **Goal**: Modify the `Reporter` to include the `problem_description` from the `ActionableLead` in the final report, giving users more context.
  - **Files**: `managers/Reporter.py` and its specialists.
  - **Owner**:

- [ ] **Task 14: Add Confidence Score**
  - **Goal**: Add an optional `confidence_score: float` field to the `ActionableLead` Pydantic model. This will be used in the future to prioritize leads.
  - **Files**: `utils/data_model.py`
  - **Owner**:

- [ ] **Task 15: Isolate Specialist Logic**
  - **Goal**: Create a new specialist script, e.g., `managers/investigator-team/undefined_command_proofer.py`, and move the "Undefined control sequence" logic out of `error_finder.py` and into this new file. The goal is to make `error_finder.py` a simple dispatcher.
  - **Files**: `managers/investigator-team/error_finder.py`, new specialist script.
  - **Owner**:

### PRIORITY 5: Table & Complex Environments
- [ ] **Task 23: Add Test Case for Table Environment**
  - **Goal**: Test handling of tabular environments, a common source of LaTeX errors.
  - **Files**: `test`, `test_cases/`
  - **Owner**:

- [ ] **Task 24: Add Test Case for Math Operators**
  - **Goal**: Test proper handling of math operators (e.g., `$\sin x$` vs `$sin x$`).
  - **Files**: `test`, `test_cases/`
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
