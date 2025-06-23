# Contributing to Smart Pandoc Debugger

Thank you for your interest in contributing to Smart Pandoc Debugger! This document outlines the process for contributing to the project.

## Table of Contents
- [Development Workflow](#development-workflow)
- [Branch Naming](#branch-naming)
- [Commit Messages](#commit-messages)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Dependencies](#dependencies)
- [Pull Requests](#pull-requests)
- [Code Review](#code-review)
- [PR Status Messages](#pr-status-messages)

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

Follow the [branch naming](#branch-naming) conventions when creating a new branch:

```bash
git checkout -b type/descriptive-branch-name
```

### 3. Make Changes and Test

1. Make your code changes following the [code style guidelines](#code-style)
2. Add tests for new functionality following [testing guidelines](#testing)
3. Run tests and linters:
   ```bash
   # Run all tests
   PYTHONPATH=./src pytest tests/ -v
   
   # Run linters
   flake8 src/
   black --check src/ tests/
   ```
4. Update documentation as needed

### 4. Commit Your Changes

Follow the [commit message guidelines](#commit-messages) when committing:

```bash
git add .
git commit -m "type(scope): brief description of changes"
```

## Branch Naming

Use the following prefix for branch names:

- `feature/` - New features or enhancements
- `bugfix/` - Bug fixes
- `hotfix/` - Critical production fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test-related changes

Examples:
- `feature/add-tex-validation`
- `bugfix/fix-citation-parsing`
- `docs/update-contributing-guide`

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): brief description

Detailed description of changes

- Change 1
- Change 2
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style/formatting
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for all function signatures
- Keep lines under 100 characters
- Include docstrings for all public functions and classes following Google style:
  ```python
  def example_function(param1: str, param2: int) -> bool:
      """Short description of the function.

      Args:
          param1: Description of param1.
          param2: Description of param2.

      Returns:
          Description of return value.
      """
  ```

## Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Group related tests in classes
- Use descriptive test names that explain what's being tested
- Mock external dependencies in unit tests
- Use fixtures for common test data

### Running Tests

```bash
# Run all tests
PYTHONPATH=./src pytest tests/ -v

# Run a specific test file
PYTHONPATH=./src pytest tests/unit/test_module.py -v

# Run tests with coverage
PYTHONPATH=./src pytest --cov=src tests/ -v
```

## Documentation

- Update documentation when adding new features or changing behavior
- Keep docstrings up to date
- Document public APIs thoroughly
- Include examples in docstrings when appropriate
- Update README.md for user-facing changes

## Dependencies

- Add new dependencies only when necessary
- Use the latest stable version of packages
- Add dependencies to `pyproject.toml` under `[project.dependencies]`
- Add development dependencies to `pyproject.toml` under `[project.optional-dependencies].dev`
- Document the reason for adding each new dependency

## Pull Requests

1. Push your branch to GitHub:
   ```bash
   git push -u origin your-branch-name
   ```

2. Create a pull request using the GitHub web interface or CLI:
   ```bash
   gh pr create --title "type(scope): description" --body "## Description\n\nDetailed description of changes\n\n### Changes\n- [x] Change 1\n- [x] Change 2" --base main
   ```

3. Ensure all CI checks pass
4. Address any review comments
5. Update the PR with requested changes
6. Once approved, a maintainer will merge your PR

## Code Review

### As a Contributor
- Address all review comments
- Keep commits focused and atomic
- Rebase on main if there are merge conflicts
- Update documentation as needed

### As a Reviewer
- Check code quality and style
- Verify tests cover new functionality
- Ensure documentation is updated
- Check for potential security issues
- Look for performance implications

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

3. **Automatically detect conflicting files**
   ```bash
   # Get list of all modified files in the PR
   PR_FILES=$(gh pr view 13 --json files --jq '.files[].path')
   
   # Check each file for conflicts
   for file in $PR_FILES; do
     if ! git diff --quiet --diff-filter=U -- "$file" 2>/dev/null; then
       echo "Conflict found in: $file"
     fi
   done
   ```

4. **One-command conflict check**
   ```bash
   # Single command to list all conflicting files in the PR
   gh pr view 13 --json files --jq '.files[].path' | while read -r file; do git diff --name-only --diff-filter=U -- "$file" 2>/dev/null; done | grep -v '^$'
   ```

5. **Check specific PR for conflicts (replace PR_NUMBER)**
   ```bash
   # Function to check conflicts for a PR
   check_pr_conflicts() {
     local pr=$1
     echo "Checking PR #$pr for conflicts..."
     if gh pr view $pr --json mergeable,mergeableState | jq -e '.mergeable == false and .mergeableState == "dirty"' >/dev/null; then
       echo "❌ Conflicts detected in PR #$pr"
       echo "Files with conflicts:"
       gh pr view $pr --json files --jq '.files[].path' | while read -r file; do 
         git diff --name-only --diff-filter=U -- "$file" 2>/dev/null; 
       done | grep -v '^$' | sort | uniq | sed 's/^/  - /'
     else
       echo "✅ No conflicts detected in PR #$pr"
     fi
   }
   
   # Example usage:
   # check_pr_conflicts 13
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

### 4. Development Workflow

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Make changes**: Edit code and add tests
3. **Commit**: The pre-commit hook will guide you through all quality checks
4. **Push**: `git push -u origin feature/your-feature-name`
5. **Create PR**: Use GitHub CLI or web interface

## Pre-commit Hook Automation

The pre-commit hook automatically handles:
- ✅ **Code style** (PEP8, line length, formatting)
- ✅ **Modular design** (max 300 total lines OR 200 code lines per file)
- ✅ **Test coverage** requirements 
- ✅ **Quality checks** (type hints, docstrings)
- ✅ **Test execution** (all MVP tests must pass)
- ✅ **Repository cleanliness** checks
- ✅ **Reviewer response** protocol reminders

**Just focus on writing good code - the hook will tell you everything else you need to know!**

## Branch Naming

- `feature/` - New features 
- `fix/` - Bug fixes
- `docs/` - Documentation 
- `test/` - Tests
- `refactor/` - Code refactoring

## Commit Messages

```
type(scope): description

feat(citations): Add bibliography validation
fix(parser): Handle malformed BibTeX files  
docs(readme): Update installation instructions
```

## Handling Reviewer Comments

### 🤖 Idiot-Proof Method for LLMs

**Use the automated PR response helper:**

```bash
spd respond-to-pr [PR_NUMBER]
```

This command will:
- ✅ Automatically fetch all reviewer comments from the PR
- ✅ Generate the exact backlink response template 
- ✅ Show you the precise GitHub CLI command to post it
- ✅ Provide step-by-step instructions for fixing issues
- ✅ Enforce the correct response protocol automatically
- ✅ Check for merge conflicts and other PR blockers

**No more manual template construction or guessing!**

### Manual Method (Advanced Users)

1. **Find comments**: `GH_PAGER=cat gh pr view [PR_NUMBER]`
2. **Fix issues**: Address each concern in code
3. **Respond with backlinks**: Create ONE comprehensive response comment linking to each individual comment
4. **Never reply to individual threads** - use the backlink method

**The pre-commit hook shows the exact response format after each commit.**

### Example Response Format
```bash
gh pr comment [PR_NUMBER] --body "## 🔗 Response to Reviewer Comments

### ✅ Comment 1: [Description]  
**Link**: [DIRECT_GITHUB_URL_TO_COMMENT]
**Status**: Fixed in commit [HASH]
**Solution**: [What you changed]

---

Ready for resolution! Click the links above to resolve each conversation ✅"
```

## GitHub CLI Setup

Always use `GH_PAGER=cat` to avoid pager issues:
```bash
GH_PAGER=cat gh pr create --title "feat: Your title" --body "Description"
GH_PAGER=cat gh pr view [PR_NUMBER]
```

**Never use `--web` flag** - it causes browser errors in this environment.

## Merge Blocked? Troubleshooting Guide

When your PR shows `BLOCKED` status, follow this systematic troubleshooting:

### 1. Check Technical Issues First

```bash
# Check if branch is out of date
GH_PAGER=cat gh pr view [PR_NUMBER] | grep -i "out-of-date\|behind"

# Update if needed
git fetch origin && git merge origin/main
```

### 2. Check for Unresolved Conversations

```bash
# View PR status
GH_PAGER=cat gh pr view [PR_NUMBER] --json mergeStateStatus,mergeable
```

**Common blocking patterns:**
- `"mergeStateStatus": "BLOCKED"` + `"mergeable": "MERGEABLE"` = **Unresolved conversations**
- `"mergeable": "CONFLICTING"` = **Merge conflicts need resolution**

### 3. Verify Your Backlink Responses

**Check you've posted the comprehensive response:**
1. Did you use the **backlink method** with direct GitHub URLs?
2. Did you reference specific commit hashes for each fix?
3. Are all reviewer concerns addressed?

### 4. Prompt User to Resolve Conversations

**If conversations are unresolved, the user must manually resolve them:**

```
🚨 MERGE BLOCKED: Unresolved conversations detected

I've addressed all reviewer concerns with commits [HASH1], [HASH2].
Please resolve the conversation threads to unblock merge:

1. Go to: https://github.com/[USER]/smart-pandoc-debugger/pull/[PR_NUMBER]
2. Click on each reviewer comment thread
3. Click "Resolve conversation" after reviewing the fixes
4. Merge should auto-unblock once all conversations resolved

All technical issues are fixed - just need manual conversation resolution! ✅
```

### 5. Verify Unblock

```bash
# Confirm merge is now available
GH_PAGER=cat gh pr view [PR_NUMBER] | grep -E "(Ready to merge|Merge pull request)"
```

**This is the exact workflow we use** - address concerns with code, respond with backlinks, then prompt user to resolve conversations for auto-merge activation.

## Code Standards

The pre-commit hook enforces all code standards automatically. Just follow:
- Write clear, tested code
- Add docstrings to public functions
- Use type hints
- Keep files modular (≤200 actual code lines, ≤300 total lines)
- Keep functions focused and small

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
