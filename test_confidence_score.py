#!/usr/bin/env python3
"""
Test script to verify the confidence_score field in ActionableLead.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from utils.data_model import ActionableLead, SourceContextSnippet

def test_confidence_score():
    """Test that confidence_score is properly initialized and validated."""
    # Test default value
    lead = ActionableLead(
        source_service="Test",
        problem_description="Test problem",
        primary_context_snippets=[]
    )
    assert lead.confidence_score == 1.0, "Default confidence_score should be 1.0"
    
    # Test custom value
    lead = ActionableLead(
        source_service="Test",
        problem_description="Test problem",
        primary_context_snippets=[],
        confidence_score=0.75
    )
    assert lead.confidence_score == 0.75, "Custom confidence_score should be 0.75"
    
    # Test validation
    try:
        lead = ActionableLead(
            source_service="Test",
            problem_description="Test problem",
            primary_context_snippets=[],
            confidence_score=1.5  # Should raise ValueError
        )
        assert False, "Should have raised ValueError for confidence_score > 1.0"
    except ValueError:
        pass
    
    try:
        lead = ActionableLead(
            source_service="Test",
            problem_description="Test problem",
            primary_context_snippets=[],
            confidence_score=-0.1  # Should raise ValueError
        )
        assert False, "Should have raised ValueError for confidence_score < 0.0"
    except ValueError:
        pass
    
    print("✅ All confidence_score tests passed!")

if __name__ == "__main__":
    test_confidence_score()
