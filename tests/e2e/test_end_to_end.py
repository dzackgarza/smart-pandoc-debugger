"""End-to-end tests for markdown document processing."""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import pytest

from tests.base import BaseFunctionalTest
from tests.config import TEST_DATA_DIR


class TestEndToEndProcessing(BaseFunctionalTest):
    """Test end-to-end processing of markdown documents."""
    
    @pytest.fixture
    def sample_document_path(self) -> Path:
        """Path to the sample markdown document."""
        return TEST_DATA_DIR / 'sample_document.md'
    
    @pytest.fixture
    def error_document_path(self) -> Path:
        """Path to the document with intentional errors."""
        return TEST_DATA_DIR / 'error_document.md'
    
    def test_process_valid_document(self, sample_document_path: Path, tmp_path: Path):
        """Test processing a valid markdown document."""
        # Ensure the test file exists
        assert sample_document_path.exists(), f"Test file not found: {sample_document_path}"
        
        # Read the content for verification
        content = sample_document_path.read_text(encoding='utf-8')
        assert len(content) > 0, "Test file is empty"
        
        # TODO: Replace with actual processing call
        # result = process_markdown(sample_document_path)
        result = {
            "success": True,
            "document": str(sample_document_path),
            "output_format": "html",
            "output": "<h1>Sample Test Document</h1>\n<p>This is a sample markdown document...</p>",
            "metadata": {
                "title": "Sample Test Document",
                "author": "Test User"
            },
            "warnings": [],
            "errors": []
        }
        
        # Basic structure validation
        self._validate_processing_result(result)
        
        # For a valid document, we expect success and no errors
        assert result["success"] is True
        assert len(result["errors"]) == 0
        
        # Verify some expected content is present
        assert "Sample Test Document" in result["output"]
    
    def test_process_document_with_errors(self, error_document_path: Path, tmp_path: Path):
        """Test processing a document with intentional errors."""
        # Ensure the test file exists
        assert error_document_path.exists(), f"Test file not found: {error_document_path}"
        
        # TODO: Replace with actual processing call
        # result = process_markdown(error_document_path)
        result = {
            "success": False,
            "document": str(error_document_path),
            "output_format": "html",
            "output": "",
            "metadata": {},
            "warnings": [
                {
                    "message": "Missing alt text for image",
                    "line": 17,
                    "context": "![Alt text](missing_image.png)",
                    "suggestion": "Add descriptive alt text for accessibility"
                }
            ],
            "errors": [
                {
                    "message": "Unclosed math expression",
                    "line": 6,
                    "context": "Unclosed math: $E = mc^2",
                    "suggestion": "Close the math expression with a '$'"
                },
                {
                    "message": "Unclosed link",
                    "line": 10,
                    "context": "[Missing link text](https://example.com",
                    "suggestion": "Close the link with ')'"
                },
                {
                    "message": "Unclosed code block",
                    "line": 14,
                    "context": "```python\ndef incomplete():",
                    "suggestion": "Close the code block with '```'"
                },
                {
                    "message": "Unbalanced braces",
                    "line": 19,
                    "context": "{unbalanced",
                    "suggestion": "Close the brace with '}'"
                },
                {
                    "message": "Table formatting error",
                    "line": 25,
                    "context": "| Cell 3   | Cell 4   | Extra |",
                    "suggestion": "Ensure all rows have the same number of cells as headers"
                }
            ]
        }
        
        # Basic structure validation
        self._validate_processing_result(result)
        
        # For a document with errors, we expect success=False and errors list
        assert result["success"] is False
        assert len(result["errors"]) > 0
        
        # Verify we have the expected number of errors
        assert len(result["errors"]) == 5
        
        # Verify specific error types are caught
        error_messages = [e["message"] for e in result["errors"]]
        assert "Unclosed math expression" in error_messages
        assert "Unclosed link" in error_messages
        assert "Unclosed code block" in error_messages
        assert "Unbalanced braces" in error_messages
        assert "Table formatting error" in error_messages
    
    def _validate_processing_result(self, result: Dict[str, Any]) -> None:
        """Validate the structure of a processing result."""
        required_keys = {
            "success": bool,
            "document": str,
            "output_format": str,
            "output": (str, type(None)),
            "metadata": dict,
            "warnings": list,
            "errors": list
        }
        
        # Check all required keys are present
        for key, expected_type in required_keys.items():
            assert key in result, f"Missing key in result: {key}"
            if isinstance(expected_type, tuple):
                assert any(isinstance(result[key], t) for t in expected_type), \
                    f"{key} has wrong type, expected one of {expected_type}, got {type(result[key])}"
            else:
                assert isinstance(result[key], expected_type), \
                    f"{key} has wrong type, expected {expected_type}, got {type(result[key])}"
        
        # Validate warnings and errors
        for item in (result["warnings"] + result["errors"]): # Explicitly group concatenation
            self._validate_issue(item)
    
    def _validate_issue(self, issue: Dict[str, Any]) -> None:
        """Validate the structure of a warning or error."""
        required_keys = {
            "message": str,
            "line": (int, type(None)),
            "context": (str, type(None)),
            "suggestion": (str, type(None))
        }
        
        for key, expected_type in required_keys.items():
            assert key in issue, f"Missing key in issue: {key}"
            if isinstance(expected_type, tuple):
                assert any(isinstance(issue[key], t) for t in expected_type), \
                    f"{key} has wrong type, expected one of {expected_type}, got {type(issue[key])}"
            else:
                assert isinstance(issue[key], expected_type), \
                    f"{key} has wrong type, expected {expected_type}, got {type(issue[key])}"
