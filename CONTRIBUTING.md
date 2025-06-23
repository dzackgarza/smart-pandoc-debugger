# Contributing to Smart Pandoc Debugger

Thank you for your interest in contributing to Smart Pandoc Debugger! This document outlines the process for contributing to the project.

## PR Status Messages

### Checking for Merge Conflicts

When creating or reviewing a PR, always check for these important status messages:

1. **Merge Conflict Warning**
   ```
   This branch has conflicts that must be resolved
   Use the web editor or the command line to resolve conflicts before continuing.
   ```
   - This appears when there are conflicts with the target branch
   - Common files that might have conflicts include:
     - `src/smart_pandoc_debugger/managers/investigator_team/undefined_environment_proofer.py`
     - Other files modified in both branches

2. **How to check for conflicts locally**
   ```bash
   # From your feature branch
   git fetch origin main
   git merge-base --is-ancestor origin/main HEAD || git merge origin/main
   ```
   - If there are conflicts, resolve them before pushing

3. **Required Status Checks**
   - Check that all required status checks are passing
   - Look for any failing tests or linting errors

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
