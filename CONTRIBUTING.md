# Contributing to Smart Pandoc Debugger

Thank you for your interest in contributing to Smart Pandoc Debugger! This document outlines the process for contributing to the project.

## Development Workflow

### 1. Setup

1. Fork the repository to your GitHub account
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/smart-pandoc-debugger.git
   cd smart-pandoc-debugger
   ```
3. Set up the development environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .[dev]
   ```

### 2. Create a Feature Branch

Always create a new branch for your changes:

```bash
git checkout -b feature/descriptive-branch-name
```

Branch naming conventions:
- `feature/` - New features or improvements
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions or improvements
- `refactor/` - Code refactoring

### 3. Make Changes

1. Make your code changes following the project's coding standards
2. Add tests for new functionality with proper assertions
3. Run tests locally:
   ```bash
   PYTHONPATH=./src pytest tests/ -v
   ```
4. The project includes a pre-commit hook that will:
   - Run tests automatically
   - Check for untracked files and potential issues
   - Remind you of important checks before committing

### 4. Repository Cleanliness

Before committing, ensure:

- 🧹 Remove all temporary and debug files
- 📂 Organize test/debug files in appropriate directories
- 🚫 Never commit sensitive information (API keys, credentials, etc.)
- 📏 Avoid committing large files (>5MB). Use git-lfs if necessary
- 🔍 Review all changes with `git diff --cached` before committing

Common files/directories to exclude (add to `.gitignore` if needed):
- `*.pyc`, `__pycache__/`, `*.swp`, `*.swo`
- Virtual environments: `venv/`, `.venv/`, `env/`
- Build artifacts: `dist/`, `build/`, `*.egg-info/`
- Local configuration files
- Log files and databases

### 5. Commit Your Changes

1. Review your changes:
   ```bash
   git status
   git diff --cached
   ```

2. Stage your changes:
   ```bash
   # Stage specific files
   git add <changed-files>
   
   # Or stage all changes
   # git add .
   ```

3. Commit with a descriptive message:
   ```bash
   git commit -m "feat(scope): Add new feature"
   ```
   
   #### Commit Message Format:
   ```
   type(scope): description
   
   Detailed description if needed
   
   - Bullet points for important changes
   - Reference issues with #123
   ```
   
   ##### Types:
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style changes
   - `refactor`: Code refactoring
   - `test`: Test related changes
   - `chore`: Maintenance tasks
   
   ##### Scope Examples:
   - `feat(api)`: API-related feature
   - `fix(cli)`: CLI-related bug fix
   - `docs(readme)`: README updates

### 6. Push Changes to Remote

1. Push your branch to GitHub:
   ```bash
   # First push to a new branch
   git push -u origin feature/descriptive-branch-name
   
   # Subsequent pushes
   # git push
   ```
   
   **Important**: 
   - You must be the one to push changes to the remote repository.
   - The automated assistant can help with local changes but will not push to remote.
   - Ensure all tests pass before pushing.

### 7. Create a Pull Request

1. Create a pull request from your fork to the main repository using the GitHub CLI:
   ```bash
   # Note: Do NOT use --web flag as it causes browser issues
   GH_PAGER=cat gh pr create --title "feat(scope): Your descriptive title" --body """
   ## 🎯 [Brief Description of Changes]
   
   [Detailed description of what this PR does and why it's needed]
   
   ### ✅ Features Implemented
   - [ ] Feature 1
   - [ ] Feature 2
   
   ### 🧪 Testing
   - [ ] All tests pass
   - [ ] New tests added for new features
   - [ ] Test coverage maintained or improved
   
   ### 📝 Documentation
   - [ ] Code is well-documented
   - [ ] README/CHANGELOG updated if needed
   - [ ] Project documentation (roadmap, etc.) updated to reflect completed work
   """
   ```
   
   Or create the PR through the GitHub web interface.

2. Update the project documentation to mark your branch as completed in the roadmap or relevant documentation

## Handling Reviewer Comments

### Finding Reviewer Comments

After creating your PR, automated reviewers (like Copilot) and human reviewers will provide feedback. Here's how to find and read all comments:

#### 1. List Your Pull Requests
```bash
# Always set GH_PAGER=cat to avoid pager issues
GH_PAGER=cat gh pr list
```

#### 2. View PR Details and Comments
```bash
# View the full PR description and inline comments
GH_PAGER=cat gh pr view [PR_NUMBER]
```

#### 3. Extract Detailed Reviewer Feedback
```bash
# Get structured JSON data about reviews and comments
GH_PAGER=cat gh pr view [PR_NUMBER] --json reviews

# For more detailed comment extraction (if needed):
GH_PAGER=cat gh pr view [PR_NUMBER] --json comments,reviews --jq '.reviews[] | {body, comments: .comments[].body, path: .comments[].path, line: .comments[].line}'
```

### Responding to Reviewer Comments

#### Example Process (Based on PR #12 - Branch 6 Implementation)

**Step 1: Identify the Comments**
From the PR view, I identified 2 nitpick-level comments:
- **Comment 1**: `tex_proofer.py:133` - Expand docstring for `_run_citation_proofer`
- **Comment 2**: `citation_proofer.py:55` - Replace `assert` with graceful error handling

**Step 2: Address Each Comment Systematically**

For **Comment 1** (Docstring Enhancement):
```python
# Before:
def _run_citation_proofer(tex_file_path: str) -> Optional[ActionableLead]:
    """Run the comprehensive citation proofer and return parsed result."""

# After:
def _run_citation_proofer(tex_file_path: str) -> Optional[ActionableLead]:
    """
    Run the comprehensive citation proofer and return parsed result.
    
    Args:
        tex_file_path: Path to the TeX file to validate for citation issues.
        
    Returns:
        ActionableLead if citation issues are found, None otherwise.
        
    Expected Output Format:
        The citation proofer script returns structured output on stdout when issues are found:
        - Exit code 1 with stdout indicates validation error found
        - First line: "Citation issue found: <description>"
        - Subsequent lines: Additional context and location information
        - Exit code 0 indicates no issues found
        - Non-zero exit code (other than 1) indicates script execution failure
    """
```

For **Comment 2** (Graceful Error Handling):
```python
# Before:
def _run_specialist_script(script_path: str, tex_file: str) -> Optional[str]:
    """Runs a specialist script and returns its stdout if it finds an error."""
    assert os.path.exists(script_path), f"Specialist script not found: {script_path}"

# After:
def _run_specialist_script(script_path: str, tex_file: str) -> Optional[str]:
    """Runs a specialist script and returns its stdout if it finds an error."""
    if not os.path.exists(script_path):
        logger.warning(f"Specialist script not found: {script_path}")
        return None
```

**Step 3: Test the Changes**
```bash
# Always test after making changes
PYTHONPATH=./src pytest tests/unit/managers/investigator_team/test_citation_proofer.py -v
```

**Step 4: Commit and Push the Fixes**
```bash
git add .
git commit -m "fix(citations): Address reviewer feedback from PR #12

- Expand docstring for _run_citation_proofer with detailed output format
- Replace assert with graceful error handling in _run_specialist_script
- Both changes improve maintainability and robustness as requested"

# Push to update the PR (user must do this step)
git push
```

### Best Practices for Reviewer Responses

1. **Address ALL Comments**: Even nitpick-level comments should be addressed
2. **Test After Changes**: Always run relevant tests to ensure fixes don't break functionality
3. **Clear Commit Messages**: Reference the PR number and describe what was fixed
4. **Explain Your Changes**: If the fix isn't obvious, add comments explaining the reasoning
5. **Be Responsive**: Address feedback promptly to keep the review process moving

### Finding Blocking Conversations

Sometimes the PR merge will be blocked by unresolved conversations. Here's how to identify and address them:

#### A) Identifying Blocking Issues

**Check the PR Status:**
```bash
# Check for merge blocking reasons
GH_PAGER=cat gh pr view [PR_NUMBER] --json mergeable,mergeStateStatus
```

Look for messages like:
- "Merging is blocked"
- "A conversation must be resolved before this pull request can be merged"
- "This branch is out-of-date with the base branch"

**Common Blocking Reasons:**
1. **Unresolved Conversations**: Technical concerns that need addressing
2. **Out-of-date Branch**: Need to merge latest changes from main
3. **Failed Checks**: Tests or CI/CD pipeline failures
4. **Required Reviews**: Missing required approvals

#### B) Addressing Technical Concerns

**Example: BibTeX Multiline Field Handling (PR #12)**

**Problem Identified:**
- Reviewer comment: "does not handle multiline BibTeX field values accurately; consider using a dedicated BibTeX parser or enhancing the regex to robustly support multiline values."

**Solution Process:**
1. **Identify the Code**: Located the issue in `extract_bib_keys_from_bibtex()` method
2. **Analyze the Problem**: Simple regex pattern couldn't handle multiline field values or comments
3. **Implement Robust Solution**: 
   - Replace simple regex with proper brace counting
   - Add comment removal that preserves quoted strings
   - Implement entry boundary detection for multiline support
   - Include fallback to simple regex for error resilience
4. **Add Test Coverage**: Create test with complex multiline BibTeX entries
5. **Verify Fix**: Ensure all existing tests pass and new test validates the fix

**Implementation:**
```python
# Before (problematic):
pattern = r'@\w+\s*\{\s*([^,\s]+)\s*,'
for match in re.finditer(pattern, content, re.IGNORECASE):
    keys.add(match.group(1))

# After (robust):
# Comprehensive parser with comment removal, brace counting,
# and proper multiline field support (see actual implementation)
```

#### C) Updating Out-of-Date Branches

```bash
# Fetch latest changes
git fetch origin

# Merge main into your feature branch
git merge origin/main

# Resolve any conflicts if they occur
# (use git status to see conflicted files)

# Commit the merge
git commit -m "Merge latest changes from main"
```

### Common Reviewer Comment Types

- **[nitpick]**: Minor improvements, style issues, or documentation enhancements
- **[suggestion]**: Optional improvements that could enhance code quality
- **[issue]**: Problems that should be addressed before merging
- **[question]**: Clarifications needed about implementation choices
- **Technical Concerns**: Complex issues requiring algorithmic or architectural changes

### GitHub CLI Environment Setup

**Important**: Always set the `GH_PAGER=cat` environment variable when using GitHub CLI commands to avoid pager issues:

```bash
# Correct way to use gh commands:
GH_PAGER=cat gh pr list
GH_PAGER=cat gh pr view 12
GH_PAGER=cat gh pr create [options]

# Never use --web flag in this environment:
# gh pr create --web  # ❌ This causes browser errors
```

### Pre-commit Hook

The project includes a pre-commit hook that will:
- Run tests automatically
- Check for untracked files and potential issues
- Remind you of important checks before committing

To install the pre-commit hook (if not already installed):
```bash
chmod +x .git/hooks/pre-commit
```

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use type hints for all function signatures
- Keep lines under 100 characters
- Include docstrings for all public functions and classes

## Testing

- Write tests for all new functionality
- Run tests before pushing code
- Maintain or improve test coverage
- Use descriptive test names that explain what's being tested

## Review Process

1. All PRs require at least one approval
2. Address all review comments (including nitpick-level feedback)
3. Update the PR with any requested changes
4. Once approved, a maintainer will merge your PR

## Reporting Issues

When reporting issues, please include:
- A clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE) file. 