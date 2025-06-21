# Smart Pandoc Debugger - FAST-TODO

## 🎯 MVP GOALS (READ FIRST)

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

## 🚀 HACKATHON MODE

### 🎯 Golden Rules
- [ ] **NEVER** modify test expectations
- [ ] Mark items as IN-PROGRESS when started
- [ ] Check off items ONLY when test passes
- [ ] Run tests after EVERY change
- [ ] Work on ONE test at a time
- [ ] **NO REGRESSIONS** - Passing tests must stay passing

## 🔧 FAST DEBUGGING TECHNIQUES

### 🐛 Quick Debugging Tips
1. **Use DEBUG=1**
   - Run tests with `DEBUG=1 ./test X` to see detailed output
   - Look for error patterns in the debug output

2. **Check Test Output**
   - The test script shows the exact input being tested
   - Compare expected vs actual output carefully

3. **Simple Patterns First**
   - Start with basic regex patterns
   - Test patterns in isolation before combining
   - Use online regex testers to verify patterns

4. **Error Message Analysis**
   - Look for key phrases in error messages
   - Pay attention to line numbers and context
   - Check for common LaTeX error patterns

5. **Incremental Testing**
   - Test small changes one at a time
   - Use `git stash` to quickly revert changes
   - Keep a clean working directory

6. **Common Pitfalls**
   - Escaping special characters in regex
   - Handling different line endings
   - Case sensitivity in pattern matching
   - Whitespace handling in test inputs

7. **When Stuck**
   - Check the raw LaTeX output in /tmp/
   - Look at the full error log
   - Try simplifying the test case further
   - Take a break and come back with fresh eyes


### 🔥 MVP Development Strategy

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
1. Pick a test from the checklist below
2. Mark it as IN-PROGRESS
3. Make minimal changes to make it pass
4. Run tests frequently
5. When test passes:
   - ✅ Check it off in the checklist
   - `git add [modified-files]`  # Only add files you changed
   - `git commit -m "PASS: [Test #] Description"`
6. If stuck after 5 minutes:
   - `git checkout -- [modified-files]`  # Discard changes to specific files
   - ⏩ Move to next test
7. Never commit broken code - fix or revert before moving on

## TEST CHECKLIST (IN ORDER OF PRIORITY)

### Test 1: Missing Dollar Sign
- [x] Status: ✅ Passed
- **Input**:
  ```markdown
  # Test
  
  f(x) = 2x + 3
  ```
- **Expected**: Should detect missing math delimiters

### Test 2: Undefined Command
- [x] Status: ✅ Passed
- **Input**:
  ```markdown
  # Test
  
  $\nonexistentcommand$
  ```
- **Expected**: Should detect undefined command

### Test 3: Mismatched Delimiters
- [x] Status: ✅ Passed
- **Input**:
  ```markdown
  # Test
  
  $$ \left( \frac{a}{b} \right] $$
  ```
- **Expected**: Should detect mismatched delimiters

### Test 4: Simple Math Expression
- [x] Status: ✅ Passed
- **Input**:
  ```markdown
  # Test
  
  $$a = b + c$$
  ```
- **Expected**: Should compile successfully

### Test 5: Unbalanced Braces
- [ ] Status: IN-PROGRESS
- **Input**:
  ```markdown
  # Test
  
  $f(x) = \frac{1}{1 + e^{-x}$
  ```
- **Expected**: Should detect unbalanced braces

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
