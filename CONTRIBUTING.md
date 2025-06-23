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