"""
Tests for the PR response helper utility.

This module tests the PR response helper that assists LLMs in responding
to PR comments following the protocol described in CONTRIBUTING.md.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the utils directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "utils"))

try:
    import pr_response_helper
except ImportError:
    pytest.skip("PR response helper not available", allow_module_level=True)


class TestPRResponseHelper:
    """Test cases for the PR response helper functions."""
    
    def test_is_from_bot(self):
        """Test bot detection logic."""
        # Test bot user
        bot_comment = {
            "user": {"login": "github-copilot-bot", "type": "Bot"}
        }
        assert pr_response_helper.is_from_bot(bot_comment)
        
        # Test regular user
        human_comment = {
            "user": {"login": "regular-user", "type": "User"}
        }
        assert not pr_response_helper.is_from_bot(human_comment)
        
        # Test codepilot user
        codepilot_comment = {
            "user": {"login": "codepilot-assistant", "type": "Bot"}
        }
        assert pr_response_helper.is_from_bot(codepilot_comment)
    
    def test_extract_comment_info(self):
        """Test comment information extraction."""
        sample_comment = {
            "id": 12345,
            "html_url": "https://github.com/user/repo/pull/1#comment-12345",
            "body": "This is a test comment",
            "user": {"login": "test-bot"},
            "created_at": "2024-01-01T00:00:00Z",
            "path": "test.py",
            "line": 42
        }
        
        result = pr_response_helper.extract_comment_info(sample_comment, "review")
        
        assert result["id"] == 12345
        assert result["type"] == "review"
        assert result["path"] == "test.py"
        assert result["line"] == 42
        assert "test-bot" in result["user"]
    
    def test_format_comment_for_response(self):
        """Test comment formatting for response."""
        comment_info = {
            "type": "review",
            "user": "test-bot",
            "html_url": "https://github.com/user/repo/pull/1#comment-12345",
            "body": "Please fix this issue",
            "path": "src/main.py",
            "line": 25
        }
        
        result = pr_response_helper.format_comment_for_response(comment_info, 1)
        
        assert "Comment 1: test-bot" in result
        assert "src/main.py:25" in result
        assert "https://github.com/user/repo/pull/1#comment-12345" in result
        assert "Please fix this issue" in result
        assert "⏳ Reviewing..." in result
    
    def test_generate_response_template_empty(self):
        """Test response template generation with no comments."""
        result = pr_response_helper.generate_response_template("123", [])
        assert result is None
    
    def test_generate_response_template_with_comments(self):
        """Test response template generation with comments."""
        comments = [
            {
                "type": "review",
                "user": "test-bot",
                "html_url": "https://github.com/user/repo/pull/1#comment-1",
                "body": "Fix this",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        result = pr_response_helper.generate_response_template("123", comments)
        
        assert result is not None
        assert "🔗 Response to Reviewer Comments" in result
        assert "Comment 1: test-bot" in result
        assert "Ready for resolution!" in result
    
    @patch('subprocess.run')
    def test_run_gh_command(self, mock_run):
        """Test GitHub CLI command execution."""
        mock_result = MagicMock()
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        stdout, stderr, returncode = pr_response_helper.run_gh_command(["gh", "version"])
        
        assert stdout == "test output"
        assert returncode == 0
        mock_run.assert_called_once()
    
    def test_get_latest_commit_hash(self):
        """Test getting the latest commit hash."""
        # This should work in any git repository
        result = pr_response_helper.get_latest_commit_hash()
        
        # Should either return a hash or the placeholder
        assert isinstance(result, str)
        assert len(result) > 0


class TestMainFunctionality:
    """Integration tests for main functionality."""
    
    @patch('pr_response_helper.get_pr_info')
    @patch('pr_response_helper.get_review_comments')
    @patch('pr_response_helper.get_issue_comments')
    def test_main_with_no_comments(self, mock_issue_comments, mock_review_comments, mock_pr_info):
        """Test main function with no bot comments."""
        mock_pr_info.return_value = {
            "number": 123,
            "title": "Test PR",
            "url": "https://github.com/user/repo/pull/123",
            "repository": {"url": "https://github.com/user/repo"}
        }
        mock_review_comments.return_value = []
        mock_issue_comments.return_value = []
        
        # Mock sys.argv to simulate command line usage
        with patch('sys.argv', ['pr_response_helper.py', '123']):
            with patch('builtins.print') as mock_print:
                try:
                    pr_response_helper.main()
                except SystemExit:
                    pass  # Expected when no comments found
                
                # Should print that no bot comments were found
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any("No bot comments found" in call for call in print_calls)


if __name__ == "__main__":
    pytest.main([__file__]) 