#!/usr/bin/env python3
"""
GitHub API Client for PR Operations
===================================

Handles all GitHub CLI interactions for PR response helper.
"""

import json
import os
import subprocess
import sys
from typing import Dict, List, Tuple


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


def auto_detect_pr_number() -> str:
    """Try to auto-detect PR number from current branch."""
    try:
        stdout, stderr, returncode = run_gh_command([
            "gh", "pr", "view", "--json", "number"
        ])
        if returncode == 0:
            pr_data = json.loads(stdout)
            pr_number = str(pr_data["number"])
            print(f"🔍 Auto-detected PR #{pr_number}")
            return pr_number
    except Exception:
        pass
    return ""
