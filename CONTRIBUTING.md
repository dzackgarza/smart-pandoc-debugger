# Contributing to Smart Pandoc Debugger

Thank you for your interest in contributing! This document outlines the essential steps.

## Quick Start

### 1. Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/smart-pandoc-debugger.git
   cd smart-pandoc-debugger
   ```

2. Set up development environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .[dev]
   ```

### 2. Development Workflow

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Make changes**: Edit code and add tests
3. **Commit**: The pre-commit hook will guide you through all quality checks
4. **Push**: `git push -u origin feature/your-feature-name`
5. **Create PR**: Use GitHub CLI or web interface

## Pre-commit Hook Automation

The pre-commit hook automatically handles:
- ✅ **Code style** (PEP8, line length, formatting)
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

### Quick Response Method

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

## Code Standards

The pre-commit hook enforces all code standards automatically. Just follow:
- Write clear, tested code
- Add docstrings to public functions
- Use type hints
- Keep functions focused and small

## Testing

Add tests for new functionality. The pre-commit hook will:
- Run all MVP tests automatically
- Check test coverage ratios
- Block commits if tests fail

```bash
# Run tests manually:
PYTHONPATH=./src pytest tests/ -v
```

## Questions?

The pre-commit hook provides real-time guidance for most development questions. For complex issues, create a GitHub issue or ask in your PR. 