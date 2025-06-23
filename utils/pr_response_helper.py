#!/usr/bin/env python3
"""
PR Response Helper for LLMs
============================

This script makes it idiot-proof for LLMs to respond to Codepilot review comments
following the exact protocol described in CONTRIBUTING.md.

Usage:
    python utils/pr_response_helper.py [PR_NUMBER]

The script will:
1. Fetch all review comments from the PR
2. Generate a comprehensive backlink response template
3. Show the exact GitHub CLI command to post the response

Author: Smart Pandoc Debugger Team
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


def run_gh_command(cmd: List[str]) -> Tuple[str, str, int]:
    """Run a GitHub CLI command with proper environment setup."""
    env = {"GH_PAGER": "cat", "GH_PROMPT_DISABLED": "1"}
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={**os.environ, **env},
            input=""  # Provide empty stdin to prevent interactive prompts
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        print("❌ Error: GitHub CLI (gh) not found. Please install it first.")
        sys.exit(1)


def get_pr_info(pr_number: str) -> Dict:
    """Fetch PR information including repository details."""
    print(f"🔍 Fetching PR #{pr_number} information...")

    stdout, stderr, returncode = run_gh_command([
        "gh", "pr", "view", pr_number, "--json",
        "number,title,url,reviews,comments,mergeable,mergeStateStatus,statusCheckRollup"
    ])

    if returncode != 0:
        print(f"❌ Error fetching PR info: {stderr}")
        sys.exit(1)

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing PR data: {e}")
        sys.exit(1)


def check_pr_blockers(pr_info: Dict) -> List[str]:
    """Check for PR blockers like merge conflicts, failing checks, etc."""
    blockers = []

    # Check for merge conflicts
    mergeable = pr_info.get("mergeable")
    if mergeable == "CONFLICTING":
        blockers.append(
            "🚫 **MERGE CONFLICTS**: This branch has conflicts that must be resolved"
        )
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


def get_review_comments(pr_number: str) -> List[Dict]:
    """Fetch all review comments from the PR."""
    print(f"💬 Fetching review comments for PR #{pr_number}...")

    stdout, stderr, returncode = run_gh_command([
        "gh", "api", f"/repos/{{owner}}/{{repo}}/pulls/{pr_number}/comments"
    ])

    if returncode != 0:
        print(f"❌ Error fetching review comments: {stderr}")
        return []

    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return []


def get_issue_comments(pr_number: str) -> List[Dict]:
    """Fetch all issue comments (general PR comments) from the PR."""
    print(f"💭 Fetching issue comments for PR #{pr_number}...")

    stdout, stderr, returncode = run_gh_command([
        "gh", "api", f"/repos/{{owner}}/{{repo}}/issues/{pr_number}/comments"
    ])

    if returncode != 0:
        print(f"❌ Error fetching issue comments: {stderr}")
        return []

    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return []


def extract_comment_info(comment: Dict, comment_type: str) -> Dict:
    """Extract relevant information from a comment."""
    info = {
        "id": comment["id"],
        "html_url": comment["html_url"],
        "body": comment["body"],
        "user": comment["user"]["login"],
        "created_at": comment["created_at"],
        "type": comment_type
    }

    # Add line-specific info for review comments
    if comment_type == "review" and "path" in comment:
        info["path"] = comment.get("path", "")
        info["line"] = comment.get("line", "")
        info["diff_hunk"] = comment.get("diff_hunk", "")

    return info


def is_from_bot(comment: Dict) -> bool:
    """Check if comment is from a bot (like Codepilot)."""
    user_login = comment["user"]["login"]
    return (
        "bot" in user_login.lower() or
        "codepilot" in user_login.lower() or
        comment["user"]["type"] == "Bot"
    )


def format_comment_for_response(comment_info: Dict, index: int) -> str:
    """Format a single comment for the backlink response."""
    comment_type = comment_info["type"]
    user = comment_info["user"]
    html_url = comment_info["html_url"]
    body = comment_info["body"]

    # Truncate long comments for the summary
    body_preview = body[:200] + "..." if len(body) > 200 else body
    body_preview = body_preview.replace("\n", " ").strip()

    response_section = f"### ✅ Comment {index}: {user} ({comment_type})"

    if comment_info["type"] == "review" and comment_info.get("path"):
        response_section += f" on {comment_info['path']}"
        if comment_info.get("line"):
            response_section += f":{comment_info['line']}"

    response_section += f"\n**Link**: {html_url}"
    response_section += f"\n**Comment**: {body_preview}"
    response_section += f"\n**Status**: ⏳ Reviewing..."
    response_section += f"\n**Solution**: [To be filled in after fixing]"

    return response_section


def generate_response_template(pr_number: str, comments: List[Dict]) -> Optional[str]:
    """Generate the comprehensive backlink response template."""
    if not comments:
        return None

    # Sort comments by creation date
    comments.sort(key=lambda x: x["created_at"])

    # Generate the response template
    response_parts = ["## 🔗 Response to Reviewer Comments\n"]

    for i, comment in enumerate(comments, 1):
        response_parts.append(format_comment_for_response(comment, i))
        response_parts.append("")  # Empty line between comments

    response_parts.extend([
        "---",
        "",
        "🔧 **Action Plan:**",
        "1. Address each concern in code",
        "2. Update this comment with commit hashes and solutions",
        "3. Request conversation resolution",
        "",
        "Ready for resolution! Click the links above to resolve each conversation ✅"
    ])

    return "\n".join(response_parts)


def get_latest_commit_hash() -> str:
    """Get the latest commit hash from the current branch."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "[COMMIT_HASH]"


def print_instructions(pr_number: str, response_template: str):
    """Print step-by-step instructions for the LLM."""
    print("\n" + "=" * 80)
    print("🤖 LLM INSTRUCTIONS: How to Respond to PR Comments")
    print("=" * 80)

    print("\n📋 STEP 1: Review Comments")
    print("   Read each comment carefully and understand what needs to be fixed.")

    print("\n🔧 STEP 2: Make Code Changes")
    print("   Address each concern mentioned in the comments with actual code changes.")
    print("   Commit your changes with descriptive commit messages.")

    print("\n💬 STEP 3: Post Comprehensive Response")
    print("   Use this EXACT command (copy and paste):")
    print("\n" + "-" * 40)

    # Escape quotes in the response template for the shell command
    escaped_template = response_template.replace('"', '\\"').replace('`', '\\`')

    print(
        f'GH_PAGER=cat GH_PROMPT_DISABLED=1 gh pr comment {pr_number} --body "{escaped_template}"')
    print("-" * 40)

    print("\n📝 STEP 4: Update Response After Fixing")
    print("   After making fixes, update the comment to include:")
    print("   - Commit hashes for each fix")
    print("   - Specific solutions implemented")
    print("   - Change 'Status: ⏳ Reviewing...' to 'Status: ✅ Fixed in commit [HASH]'")

    print(f"\n🔗 STEP 5: Template for Updates")
    print("   Replace '[To be filled in after fixing]' with specific solutions like:")
    print("   - 'Added missing import in commit abc123'")
    print("   - 'Fixed typo in variable name in commit def456'")
    print("   - 'Added docstring as requested in commit ghi789'")

    print("\n⚠️  CRITICAL RULES:")
    print("   ❌ NEVER reply to individual comment threads")
    print("   ❌ NEVER use --web flag with gh commands")
    print("   ❌ NEVER use gh pr create without proper flags (it becomes interactive!)")
    print("   ✅ ALWAYS use ONE comprehensive response with backlinks")
    print("   ✅ ALWAYS use GH_PAGER=cat GH_PROMPT_DISABLED=1 with gh commands")
    print("   ✅ If gh commands fail with auth, ask user to run the command")

    print("\n🎯 Success Criteria:")
    print("   - All concerns addressed in code")
    print("   - One comprehensive response posted")
    print("   - User can resolve conversations manually")
    print("   - PR becomes ready to merge")


def main():
    """Main function to orchestrate the PR response process."""
    parser = argparse.ArgumentParser(
        description="Generate idiot-proof PR response for LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python utils/pr_response_helper.py 42
  python utils/pr_response_helper.py
        """
    )
    parser.add_argument(
        "pr_number",
        nargs="?",
        help="PR number to analyze (will auto-detect if in PR branch)"
    )
    parser.add_argument(
        "--show-template-only",
        action="store_true",
        help="Only show the response template, don't fetch comments"
    )

    args = parser.parse_args()

    # Auto-detect PR number if not provided
    pr_number = args.pr_number
    if not pr_number:
        try:
            # Try to get PR number from current branch
            result = subprocess.run([
                "gh", "pr", "view", "--json", "number"
            ], capture_output=True, text=True,
                env={**os.environ, "GH_PAGER": "cat", "GH_PROMPT_DISABLED": "1"},
                input="")
            if result.returncode == 0:
                pr_data = json.loads(result.stdout)
                pr_number = str(pr_data["number"])
                print(f"🔍 Auto-detected PR #{pr_number}")
        except Exception:
            pass

    if not pr_number:
        print("❌ Error: No PR number provided and couldn't auto-detect.")
        print("Usage: python utils/pr_response_helper.py [PR_NUMBER]")
        sys.exit(1)

    print(f"🚀 Starting PR response helper for PR #{pr_number}")
    print("=" * 60)

    # Fetch PR info
    pr_info = get_pr_info(pr_number)
    print(f"📄 PR Title: {pr_info['title']}")
    print(f"🔗 PR URL: {pr_info['url']}")

    # Check for PR blockers
    blockers = check_pr_blockers(pr_info)
    if blockers:
        print_blocker_instructions(blockers)
        return

    # Fetch all comments
    review_comments = get_review_comments(pr_number)
    issue_comments = get_issue_comments(pr_number)

    # Process and filter comments
    all_comments = []

    # Add review comments (line-specific)
    for comment in review_comments:
        if is_from_bot(comment):
            all_comments.append(extract_comment_info(comment, "review"))

    # Add issue comments (general PR comments)
    for comment in issue_comments:
        if is_from_bot(comment):
            all_comments.append(extract_comment_info(comment, "issue"))

    print(f"💬 Found {len(all_comments)} bot comments to address")

    if not all_comments:
        print("✅ No bot comments found! Your PR is ready to go.")
        return

    # Generate response template
    response_template = generate_response_template(pr_number, all_comments)

    if response_template:
        print_instructions(pr_number, response_template)
    else:
        print("❌ Error generating response template")
        sys.exit(1)


if __name__ == "__main__":
    import os
    main()
