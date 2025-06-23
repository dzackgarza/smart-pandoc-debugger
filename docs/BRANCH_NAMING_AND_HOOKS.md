# Branch Naming Conventions and Git Hooks

This document outlines the branch naming conventions and Git hooks used in the Smart Pandoc Debugger project to maintain code quality and consistency.

## Branch Naming Conventions

### For V1.0 Roadmap Branches

Branches for V1.0 roadmap features must be named according to the branch number in the roadmap:

```
branchN-description
# or
feature/branchN-description
# or
N-description
# or
feature/N-description
```

Where:
- `N` is the branch number from the V1.0 roadmap (1-9)
- `description` is a short, kebab-case description of the changes

Examples:
- `branch1-special-chars`
- `feature/branch2-math-validation`
- `3-environment-validation`
- `feature/4-code-blocks`

### For Other Branches

For branches not part of the V1.0 roadmap, use:
- `fix/description` for bug fixes
- `feature/description` for new features
- `docs/description` for documentation changes
- `chore/description` for maintenance tasks

## Git Hooks

This repository includes pre-commit hooks to ensure code quality and test coverage. These hooks will:

1. Verify that your branch name follows the correct convention
2. Run tests for the specific branch you're working on before allowing a commit

### Setting Up Git Hooks

1. Make sure you have Python 3.8+ installed
2. Install the project in development mode:
   ```bash
   pip install -e .
   ```
3. Run the setup script:
   ```bash
   python scripts/setup_git_hooks.py
   ```

### How It Works

- When you try to commit changes, the pre-commit hook will:
  1. Check if your branch name follows the required pattern
  2. If it's a V1.0 roadmap branch, it will run the specific tests for that branch
  3. If any checks fail, the commit will be aborted

### Bypassing Hooks (When Necessary)

In rare cases, you might need to bypass the pre-commit hooks. You can do this with:

```bash
git commit --no-verify -m "Your commit message"
```

However, this should be used sparingly and only when absolutely necessary.

## Troubleshooting

If you encounter issues with the Git hooks:

1. Make sure you've run `pip install -e .` to install the package in development mode
2. Check that the pre-commit hook is executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```
3. Run the setup script again:
   ```bash
   python scripts/setup_git_hooks.py
   ```
4. If you still have issues, you can temporarily disable the hooks with:
   ```bash
   git config --local core.hooksPath /dev/null
   ```
   And re-enable them later with:
   ```bash
   git config --local --unset core.hooksPath
   ```
