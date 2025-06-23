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

### 3. Make Changes and Test

1. Make your code changes following the project's coding standards
2. Add tests for new functionality
3. Run tests locally:
   ```bash
   PYTHONPATH=./src pytest tests/ -v
   ```

### 4. Handle Merge Conflicts

When working with feature branches, you might encounter merge conflicts. Here's how to handle them:

1. **Check for conflicts before creating a PR**:
   ```bash
   git fetch origin main
   git merge origin/main
   ```

2. **Resolving conflicts in files**:
   - Open the conflicting file(s) in your editor
   - Look for conflict markers `<<<<<<<`, `=======`, and `>>>>>>>`
   - Edit the file to resolve the conflicts, keeping the desired changes
   - Remove the conflict markers after resolution
   - For complex files like `undefined_environment_proofer.py`, carefully review both versions to ensure no functionality is lost

3. **After resolving conflicts**:
   ```bash
   git add <resolved-file>
   git commit -m "Resolve merge conflicts in <file>"
   git push
   ```

4. **Common conflict scenarios**:
   - When both branches modify the same part of a file differently
   - When a file is modified in one branch but deleted in another
   - When multiple people modify the same file

5. **Best practices**:
   - Pull the latest changes from main frequently
   - Keep your feature branches short-lived
   - Test thoroughly after resolving conflicts
   - Use `git status` to check which files have conflicts

### 5. Commit Your Changes

1. Stage your changes:
   ```bash
   git add <changed-files>
   # Or stage all changes with: git add .
   ```

2. Commit with a descriptive message:
   ```bash
   git commit -m "type(scope): description of changes"
   ```

### 6. Push Changes and Create PR

1. Push your branch to GitHub:
   ```bash
   git push -u origin feature/descriptive-branch-name
   ```

2. Create a pull request using the GitHub web interface or CLI:
   ```bash
   gh pr create --title "type(scope): description" --body "## Description\n\nDetailed description of changes\n\n### Changes\n- [x] Change 1\n- [x] Change 2" --base main
   ```

3. Address any review comments and update the PR as needed

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
