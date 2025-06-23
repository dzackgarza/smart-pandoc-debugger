#!/bin/bash
#
# Cleanup script for removing Smart Pandoc Debugger-specific logic from global hooks
# This script safely backs up and cleans global hooks that shouldn't be global
#

set -e

echo "🧹 Smart Pandoc Debugger: Global Hooks Cleanup"
echo "================================================"
echo ""

# Check if global hooks directory exists
GLOBAL_HOOKS_DIR="/home/dzack/.githooks"
if [[ ! -d "$GLOBAL_HOOKS_DIR" ]]; then
    echo "✅ No global hooks directory found at $GLOBAL_HOOKS_DIR"
    echo "   Nothing to clean up!"
    exit 0
fi

echo "📂 Found global hooks directory: $GLOBAL_HOOKS_DIR"
echo ""

# Create backup directory with timestamp
BACKUP_DIR="$HOME/.githooks-backup-$(date +%Y%m%d-%H%M%S)"
echo "💾 Creating backup at: $BACKUP_DIR"
cp -r "$GLOBAL_HOOKS_DIR" "$BACKUP_DIR"
echo "✅ Backup created successfully"
echo ""

# Check what's in the global pre-commit hook
PRE_COMMIT_HOOK="$GLOBAL_HOOKS_DIR/pre-commit"
if [[ -f "$PRE_COMMIT_HOOK" ]]; then
    echo "🔍 Analyzing global pre-commit hook..."

    # Check if it contains Smart Pandoc Debugger specific logic
    if grep -q "smart-pandoc-debugger\|roadmap\|V0.0.md\|V1.0.md\|V2.0.md" "$PRE_COMMIT_HOOK"; then
        echo "❌ Found Smart Pandoc Debugger-specific logic in global hook!"
        echo "   This belongs in the project, not globally."
        echo ""
        echo "📋 Smart Pandoc Debugger-specific items found:"
        grep -n "smart-pandoc-debugger\|roadmap\|V0.0.md\|V1.0.md\|V2.0.md" "$PRE_COMMIT_HOOK" | head -5
        echo ""

        # Offer to clean it up
        echo "🔧 RECOMMENDED ACTION: Remove project-specific global hooks"
        echo ""
        echo "Options:"
        echo "  1. Remove the entire global hooks setup (RECOMMENDED)"
        echo "  2. Create a minimal universal global hook"
        echo "  3. Skip cleanup (keep existing contaminated setup)"
        echo ""

        # For automation, default to option 1 since user said things don't apply to other projects
        echo "🎯 Since you mentioned the global hooks don't apply to other projects,"
        echo "   proceeding with OPTION 1: Complete removal"
        echo ""

        # Remove global hooks configuration
        echo "🗑️  Removing global hooks configuration..."
        git config --global --unset core.hooksPath || echo "   (core.hooksPath was not set globally)"

        # Remove or rename the global hooks directory
        mv "$GLOBAL_HOOKS_DIR" "${GLOBAL_HOOKS_DIR}-disabled-$(date +%Y%m%d)"

        echo "✅ Global hooks cleaned up successfully!"
        echo ""
        echo "📋 Summary of changes:"
        echo "   ✓ Backup created: $BACKUP_DIR"
        echo "   ✓ Global core.hooksPath unset"
        echo "   ✓ Global hooks directory disabled: ${GLOBAL_HOOKS_DIR}-disabled-$(date +%Y%m%d)"
        echo ""
        echo "🎉 Your git setup is now clean!"
        echo "   - Project-specific hooks stay in projects (using pre-commit framework)"
        echo "   - No more global contamination"
        echo "   - Other projects unaffected"

    else
        echo "✅ Global pre-commit hook looks generic (no Smart Pandoc Debugger specifics found)"
        echo "   You may want to review it manually to ensure it's truly universal"
    fi
else
    echo "ℹ️  No global pre-commit hook found"
fi

echo ""
echo "💡 Next steps:"
echo "   1. Test that Smart Pandoc Debugger hooks still work: pre-commit run --all-files"
echo "   2. Verify other projects still work as expected"
echo "   3. If you need universal hooks later, create minimal ones that apply to ALL repos"
echo ""
echo "📖 See docs/development/pre-commit-cleanup.md for detailed guidance"
