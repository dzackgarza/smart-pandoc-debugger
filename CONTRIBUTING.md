# Contributing to Smart Pandoc Debugger

Thank you for your interest in contributing to Smart Pandoc Debugger! This document outlines the process for contributing to the project.

## PR Status Messages

### Checking for Merge Conflicts

#### Via GitHub Web Interface
1. When viewing a PR, look for the merge conflict banner:
   ```
   This branch has conflicts that must be resolved
   Use the web editor or the command line to resolve conflicts before continuing.
   ```
2. Check the "Conversation" tab for any automated messages about merge conflicts
3. Look for the "Resolve conflicts" button near the bottom of the PR page

#### Via GitHub CLI

1. **Check merge conflict status**
   ```bash
   # Check if PR has conflicts (returns 'true' if conflicts exist)
   gh pr view 13 --json mergeable,mergeableState | jq '.mergeable == false and .mergeableState == "dirty"'
   ```

2. **View detailed PR status**
   ```bash
   # Get detailed PR information including merge status
   gh pr view 13 --json mergeable,mergeableState,mergeStateStatus,mergeCommit,autoMergeRequest
   ```

3. **Check which files have conflicts**
   ```bash
   # Get list of files with conflicts
   git diff --name-only --diff-filter=U
   ```

#### Common Conflict Scenarios
- Files modified in both branches:
  - `src/smart_pandoc_debugger/managers/investigator_team/undefined_environment_proofer.py`
  - Other files modified in both the PR and target branch

#### Required Status Checks
- Check that all required status checks are passing
- Look for any failing tests or linting errors
- Ensure the branch is up to date with the target branch

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

### 3. Make Changes and Test

1. Make your code changes following the project's coding standards
2. Add tests for new functionality
3. Run tests locally:
   ```bash
   PYTHONPATH=./src pytest tests/ -v
   ```

### 4. Push Changes and Create PR

1. Push your branch to GitHub:
   ```bash
   git push -u origin feature/descriptive-branch-name
   ```

2. Create a pull request using the GitHub web interface or CLI:
   ```bash
   gh pr create --title "type(scope): description" --body "## Description\n\nDetailed description of changes\n\n### Changes\n- [x] Change 1\n- [x] Change 2" --base main
   ```

3. **Check for PR Status Messages**
   - Look for any conflict warnings or required checks
   - Address any issues before requesting review

4. Address any review comments and update the PR as needed

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
2. Address all review comments
3. Update the PR with any requested changes
4. Once approved, a maintainer will merge your PR
