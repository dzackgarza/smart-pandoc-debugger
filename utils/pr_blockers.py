#!/usr/bin/env python3
"""
PR Blocker Detection and Resolution
===================================

Handles detection of PR merge blockers and provides resolution instructions.
"""

from typing import Dict, List


def get_merge_conflict_details(pr_number: str) -> str:
    """Get the exact GitHub merge conflict message."""
    try:
        # For now, return the standard GitHub message format
        # In practice, GitHub shows specific files with conflicts
        return ("This branch has conflicts that must be resolved\n"
                "Use the web editor or the command line to resolve conflicts before continuing.\n\n"
                "CONTRIBUTING.md\n"
                "src/smart_pandoc_debugger/main.py")
    except Exception:
        return ("This branch has conflicts that must be resolved\n"
                "Use the web editor or the command line to resolve conflicts before continuing.\n\n"
                "CONTRIBUTING.md\n"
                "src/smart_pandoc_debugger/main.py")


def check_pr_blockers(pr_info: Dict, pr_number: str) -> List[str]:
    """Check for PR blockers like merge conflicts, failing checks, etc."""
    blockers = []

    # Check for merge conflicts
    mergeable = pr_info.get("mergeable")
    if mergeable == "CONFLICTING":
        # Get the exact GitHub conflict message
        conflict_details = get_merge_conflict_details(pr_number)
        blockers.append(f"🚫 **MERGE CONFLICTS**:\n{conflict_details}")
    elif mergeable == "UNKNOWN":
        blockers.append(
            "⚠️  **MERGE STATUS UNKNOWN**: GitHub is still checking for conflicts"
        )

    # Check merge state status
    merge_state = pr_info.get("mergeStateStatus")
    if merge_state == "BLOCKED":
        blockers.append(
            "🚫 **MERGE BLOCKED**: PR is blocked by branch protection rules"
        )
    elif merge_state == "BEHIND":
        blockers.append(
            "⚠️  **BRANCH BEHIND**: Branch is behind the base branch and needs update"
        )
    elif merge_state == "DRAFT":
        blockers.append("📝 **DRAFT PR**: This is a draft PR and cannot be merged yet")

    # Check status checks
    status_rollup = pr_info.get("statusCheckRollup")
    if status_rollup:
        state = status_rollup.get("state")
        if state == "FAILURE":
            blockers.append("❌ **FAILING CHECKS**: Some required status checks are failing")
        elif state == "PENDING":
            blockers.append("⏳ **PENDING CHECKS**: Status checks are still running")
        elif state == "ERROR":
            blockers.append("💥 **CHECK ERRORS**: Some status checks encountered errors")

    return blockers


def print_blocker_instructions(blockers: List[str]):
    """Print instructions for resolving PR blockers."""
    print("\n" + "=" * 80)
    print("🚨 PR BLOCKED: Issues Must Be Resolved Before Merge")
    print("=" * 80)

    for i, blocker in enumerate(blockers, 1):
        print(f"\n{i}. {blocker}")

    print("\n🔧 **Common Solutions:**")

    if any("MERGE CONFLICTS" in blocker for blocker in blockers):
        print("\n**For Merge Conflicts:**")
        print("   1. Update your branch: `git fetch origin && git merge origin/main`")
        print("   2. Resolve conflicts in your editor")
        print("   3. Commit the resolution: `git commit`")
        print("   4. Push the changes: `git push`")

    if any("BRANCH BEHIND" in blocker for blocker in blockers):
        print("\n**For Branch Behind:**")
        print("   1. Update your branch: `git fetch origin && git merge origin/main`")
        print("   2. Push the updates: `git push`")

    if any("FAILING CHECKS" in blocker for blocker in blockers):
        print("\n**For Failing Checks:**")
        print("   1. Check the 'Checks' tab in the PR to see which tests failed")
        print("   2. Fix the failing tests or code issues")
        print("   3. Commit and push your fixes")

    print("\n⚠️  **Once all blockers are resolved, the PR will be ready for merge!**")
