# Smart Pandoc Debugger - Fast Track TODOs

## 🔄 Workflow Instructions
1. Work on ONE task at a time
2. After each change, run: `./test`
3. If tests pass, check off the item ✅
4. If tests fail, fix before moving on
5. Commit working changes before next task

---

## 🚨 Critical Path (In Order)

### 1. Fix Crashes in Reporter
- [ ] **Task**: Add missing `notes` field
  - File: `utils/data_model.py`
  - Add to `MarkdownRemedy` class:
    ```python
    notes: Optional[str] = Field(
        None,
        description="Optional notes about this remedy"
    )
    ```
  - Run: `./test`
  - Expected: No more AttributeError for 'notes'

- [ ] **Task**: Bypass Reporter formatting
  - File: `managers/Reporter.py`
  - Add at start of `format_diagnostic_report`:
    ```python
    def format_diagnostic_report(job: DiagnosticJob) -> str:
        # DEBUG: Return raw JSON
        return job.model_dump_json()
    ```
  - Run: `./test`
  - Expected: Tests run further before failing

### 2. Fix Error Detection
- [ ] **Task**: Simplify error_finder.py
  - File: `managers/investigator-team/error_finder.py`
  - Replace `find_primary_error` with:
    ```python
    def find_primary_error(log_content: str) -> dict:
        return {
            "error_found": True,
            "primary_error": "TeX_Compilation_Error",
            "context": log_content[:300]
        }
    ```
  - Run: `./test`
  - Expected: Should detect errors generically

### 3. Add One Error Type
- [ ] **Task**: Enable basic error matching
  - File: `managers/oracle-team/seer_rules.yaml`
  - Uncomment the first error pattern
  - Run: `./test test_cases/mismatched_delimiters.md`
  - Expected: Should match the test case

---

## 📊 Progress Tracker
- [ ] Step 1: Crashes fixed
- [ ] Step 2: Basic error detection working
- [ ] Step 3: One error type handled

## ⚠️ Current Limitations
- [ ] Reporter bypassed (raw JSON output)
- [ ] Basic error detection only
- [ ] One error type implemented

## 🕒 Time Check
- Start: 10:50 AM
- Target: MVP by 11:20 AM
- Time left: [ 30 minutes ]

## 🧪 Test Command
```bash
# Full test suite
./test

# Single test case
./test test_cases/mismatched_delimiters.md
```
