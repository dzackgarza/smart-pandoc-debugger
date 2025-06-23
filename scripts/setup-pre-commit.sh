#!/bin/bash
#
# Setup script for Smart Pandoc Debugger pre-commit hooks
# This script configures project-specific hooks instead of relying on global ones
#

set -e

echo "🔧 Setting up Smart Pandoc Debugger pre-commit hooks..."

# Change to repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Check if user has global hooks configured
GLOBAL_HOOKS_PATH=$(git config --global --get core.hooksPath 2>/dev/null || echo "")
if [[ -n "$GLOBAL_HOOKS_PATH" ]]; then
    echo "⚠️  WARNING: You have global git hooks configured at: $GLOBAL_HOOKS_PATH"
    echo ""
    echo "🧹 RECOMMENDATION: Clean up your global hooks setup!"
    echo "   Global hooks should be minimal and project-agnostic."
    echo "   Project-specific logic belongs in project-specific hooks."
    echo ""
    echo "🔧 To clean up global hooks:"
    echo "   1. Review what's in: $GLOBAL_HOOKS_PATH"
    echo "   2. Move project-specific logic to individual projects"
    echo "   3. Keep only generic, reusable hooks globally"
    echo "   4. Consider: git config --global --unset core.hooksPath"
    echo ""
    echo "For this project, we'll use local hooks only."
    echo ""
fi

# Temporarily unset global hooks for this project
echo "📝 Configuring project-specific hooks..."
git config core.hooksPath ".git/hooks"

# Install pre-commit if not available
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    if command -v uv &> /dev/null; then
        uv pip install pre-commit
    elif [[ -n "$VIRTUAL_ENV" ]]; then
        pip install pre-commit
    else
        echo "❌ Error: Please activate a virtual environment or install uv"
        exit 1
    fi
fi

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

# Make hook scripts executable
echo "🔨 Making hook scripts executable..."
chmod +x scripts/hooks/*.py

echo ""
echo "✅ Pre-commit setup complete!"
echo ""
echo "📋 What was configured:"
echo "   ✓ Project-specific hook configuration"
echo "   ✓ Pre-commit framework installed"
echo "   ✓ Hook scripts made executable"
echo "   ✓ Local .git/hooks/pre-commit configured"
echo ""
echo "🧪 Test your setup:"
echo "   pre-commit run --all-files"
echo ""
echo "💡 Next steps:"
echo "   1. Consider cleaning up your global hooks ($GLOBAL_HOOKS_PATH)"
echo "   2. Move any project-specific logic from global to local"
echo "   3. Keep global hooks minimal and generic"
