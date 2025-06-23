#!/usr/bin/env python3
"""
Script to respond to a specific GitHub PR comment.
"""

import os
import sys
import json
import requests
from typing import Dict, Any

def get_github_token() -> str:
    """Get GitHub token from environment variable."""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    return token

def post_comment_reply(comment_id: int, body: str) -> None:
    """Post a reply to a specific comment."""
    token = get_github_token()
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    
    # GitHub API endpoint for creating a reply to a review comment
    url = f"https://api.github.com/repos/dzackgarza/smart-pandoc-debugger/pulls/comments/{comment_id}/replies"
    
    response = requests.post(
        url,
        headers=headers,
        json={'body': body}
    )
    
    if response.status_code == 201:
        print(f"Successfully posted reply to comment {comment_id}")
        print(f"View at: https://github.com/dzackgarza/smart-pandoc-debugger/pull/11#discussion_r{comment_id}")
    else:
        print(f"Failed to post reply. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <comment_id> <message>")
        print("Example: python3 respond_to_comment.py 12345678 'Addressed in commit abc123'")
        sys.exit(1)
    
    comment_id = sys.argv[1]
    message = sys.argv[2]
    
    # Get the latest commit hash
    commit_hash = os.popen('git rev-parse HEAD').read().strip()
    full_message = f"{message} (commit {commit_hash})"
    
    post_comment_reply(comment_id, full_message)
