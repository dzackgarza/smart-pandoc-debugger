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
import subprocess
import sys
from typing import Dict, List, Optional

from gh_api_client import (auto_detect_pr_number, get_issue_comments,
                           get_pr_info, get_review_comments)
from pr_blockers import check_pr_blockers, print_blocker_instructions


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

    # Add path and line info for review comments
    if comment_type == "review" and "path" in comment:
        info["path"] = comment["path"]
        info["line"] = comment.get("line", comment.get("original_line"))

    return info


def is_from_bot(comment: Dict) -> bool:
    """Check if comment is from a bot or automation."""
    user = comment.get("user", {})
    login = user.get("login", "").lower()

    bot_indicators = ["bot", "codepilot", "github-actions", "dependabot"]
    return any(indicator in login for indicator in bot_indicators)


def format_comment_for_response(comment_info: Dict, index: int) -> str:
    """Format a single comment for the response template."""
    html_url = comment_info["html_url"]
    body = comment_info["body"]
    body_preview = body[:100] + "..." if len(body) > 100 else body

    response_section = f"### {index}. [📝 Resolve Comment #{comment_info['id']}]({html_url})"
    response_section += f"\n**Author**: {comment_info['user']}"

    if comment_info.get("path"):
        response_section += f"\n**File**: {comment_info['path']}"
        if comment_info.get("line"):
            response_section += f" (line {comment_info['line']})"

    response_section += f"\n**Link**: {html_url}"
    response_section += f"\n**Comment**: {body_preview}"
    response_section += "\n**Status**: ⏳ Reviewing..."
    response_section += "\n**Solution**: [To be filled in after fixing]"

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

    print("\n🔗 STEP 5: Template for Updates")
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
        pr_number = auto_detect_pr_number()

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
    blockers = check_pr_blockers(pr_info, pr_number)
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
    main()
