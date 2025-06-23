# Pre-commit Hook Cleanup and Configuration

## 🧹 Problem: Global Hooks with Project-Specific Logic

The original setup had a massive 400+ line pre-commit hook with Smart Pandoc Debugger-specific logic installed globally at `/home/dzack/.githooks`. This is problematic because:

- **Global hooks should be minimal and project-agnostic**
- **Project-specific logic belongs in project-specific hooks**
- **Makes development setup fragile and non-portable**
- **Hard to maintain and debug**

## ✅ Solution: Modular Pre-commit Framework

We've replaced the monolithic hook with a clean, modular setup using the pre-commit framework:

### New Structure

```
.pre-commit-config.yaml           # Main configuration
scripts/hooks/                   # Project-specific hook scripts
├── protect-roadmap.py           # Protect roadmap files (45 lines)
├── check-file-size.py           # Enforce modularity (84 lines)
├── check-alternative-imports.py # Prevent cross-contamination (43 lines)
└── run-tier1-tests.py          # Run MVP tests (95 lines)
.git/hooks/pre-commit            # Simple 17-line hook that delegates
```

### Benefits

- **Modular**: Each concern is a separate, focused script
- **Maintainable**: Individual scripts are small and testable
- **Portable**: Standard pre-commit framework, not custom monolith
- **Project-specific**: No global contamination
- **Size-enforced**: Each hook script follows the same modularity rules

## 🔧 Setup Instructions

### For This Project

```bash
# Run the setup script
./scripts/setup-pre-commit.sh
```

### Manual Setup

```bash
# Install pre-commit framework
uv pip install pre-commit

# Install hooks
pre-commit install

# Make scripts executable
chmod +x scripts/hooks/*.py

# Test the setup
pre-commit run --all-files
```

## 🧹 Global Hooks Cleanup Recommendations

If you have global hooks configured, here's how to clean them up:

### 1. Review Your Global Hooks

```bash
# Check if you have global hooks
git config --global --get core.hooksPath

# Review what's in there
ls -la /home/dzack/.githooks/
```

### 2. Identify Project-Specific Logic

Look for logic that is specific to particular projects:
- File size limits for specific projects
- Project-specific test requirements
- Protection of specific files/directories
- Project-specific style rules

### 3. Move Project-Specific Logic

Move any project-specific logic to individual project configurations:
- Use `.pre-commit-config.yaml` in each project
- Create project-specific hook scripts
- Use local git hook configuration

### 4. Keep Global Hooks Minimal

Your global hooks should only contain:
- Generic security checks (no secrets, no large files)
- Universal style enforcement (basic whitespace, line endings)
- Company-wide policies that apply to ALL repositories

### 5. Example Clean Global Hook

```bash
#!/bin/bash
# Global pre-commit hook - keep minimal!

# Check for secrets
if grep -r "password\|api_key\|secret" --include="*.py" --include="*.js" .; then
    echo "❌ Potential secret found"
    exit 1
fi

# Check for large files
if git diff --cached --name-only | xargs du -h | awk '$1 ~ /M/ {print $2}'; then
    echo "❌ Large files detected"
    exit 1
fi

# Let project-specific hooks handle the rest
exit 0
```

### 6. Remove or Simplify Global Configuration

```bash
# Option 1: Remove global hooks entirely
git config --global --unset core.hooksPath

# Option 2: Keep minimal global hooks
# Move project-specific logic out and keep only universal checks
```

## 🎯 Result

After cleanup:
- **Global hooks**: Minimal, universal policies only
- **Project hooks**: Full project-specific logic using pre-commit framework
- **Maintainability**: Each hook script is focused and under 100 lines
- **Portability**: Standard framework, easy for new developers to understand
- **Testability**: Individual hook scripts can be tested in isolation

## 🔍 Testing Your Setup

```bash
# Test all hooks
pre-commit run --all-files

# Test specific hook
pre-commit run protect-roadmap --all-files

# Test on specific files
pre-commit run check-file-size --files utils/pr_response_helper.py
```

## 📚 Further Reading

- [Pre-commit Framework Documentation](https://pre-commit.com/)
- [Git Hooks Best Practices](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [Smart Pandoc Debugger Development Setup](setup.md)
