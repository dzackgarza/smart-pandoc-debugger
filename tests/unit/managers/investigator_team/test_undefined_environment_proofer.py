#!/usr/bin/env python3
# tests/unit/managers/investigator_team/test_undefined_environment_proofer.py

import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from smart_pandoc_debugger.managers.investigator_team.undefined_environment_proofer import (
    find_undefined_environment,
    suggest_package,
    create_actionable_lead,
    main as run_undefined_environment_proofer
)
from smart_pandoc_debugger.data_model import ActionableLead, SourceContextSnippet

# Test data
SIMPLE_ENV_ERROR = r"""
! LaTeX Error: Environment foobar undefined.

See the LaTeX manual or LaTeX Companion for explanation.
Type  H <return>  for immediate help.
 ...                                              
                                              
l.10 \begin{foobar}
                  
? 
"""


ALT_ENV_ERROR = r"""
! Undefined control sequence.
l.5 \begin{testenv}
                   
The control sequence at the end of the top line
of your error message was never \def'ed. If you have
misspelled it (e.g., `\hobx'), type `I' and the correct
spelling (e.g., `I\hbox'). Otherwise just continue,
and I'll forget about whatever was undefined.
"""

NO_ERROR = r"""
This is a normal LaTeX log file with no errors.
"""

# Fixtures
@pytest.fixture
def simple_env_error():
    return SIMPLE_ENV_ERROR

@pytest.fixture
def alt_env_error():
    return ALT_ENV_ERROR

@pytest.fixture
def no_error():
    return NO_ERROR

# Tests
def test_find_undefined_environment_simple(simple_env_error):
    """Test finding a simple undefined environment error."""
    result = find_undefined_environment(simple_env_error)
    assert result is not None
    assert result['environment_name'] == 'foobar'
    assert result['line_number'] == 10
    assert "Environment foobar undefined" in result['raw_error_message']
    assert "Found '\\begin{foobar}' on line 10" in result['context']

def test_find_undefined_environment_alt_format(alt_env_error):
    """Test finding an undefined environment in the alternate format."""
    result = find_undefined_environment(alt_env_error)
    assert result is not None
    assert result['environment_name'] == 'testenv'
    assert result['line_number'] == 5
    assert "Environment testenv undefined" in result['raw_error_message']
    assert "Found '\\begin{testenv}' on line 5" in result['context']

def test_find_undefined_environment_no_error(no_error):
    """Test that no error is found in a clean log."""
    assert find_undefined_environment(no_error) is None

def test_suggest_package_known():
    """Test suggesting a package for a known environment."""
    assert suggest_package('align') == 'amsmath'
    assert suggest_package('theorem') == 'amsthm'
    assert suggest_package('algorithm') == 'algorithm'

def test_suggest_package_unknown():
    """Test suggesting a package for an unknown environment."""
    assert suggest_package('nonexistentenv') == ''

def test_create_actionable_lead():
    """Test creating an actionable lead from error info."""
    error_info = {
        'environment_name': 'testenv',
        'line_number': 42,
        'raw_error_message': 'Environment testenv undefined.',
        'source_file': '/path/to/source.tex'
    }
    
    lead = create_actionable_lead(error_info)
    
    assert isinstance(lead, ActionableLead)
    assert lead.lead_type == 'LATEX_UNDEFINED_ENVIRONMENT'
    assert "testenv" in lead.description
    assert lead.line_number == 42
    assert lead.source_file == '/path/to/source.tex'
    assert lead.severity == 'error'
    assert lead.confidence == 0.9
    
    # Check that we have a fix suggestion
    assert '\\usepackage' in lead.fix or '\\newenvironment' in lead.fix
    
    # Check context
    assert len(lead.context) > 0
    assert any("testenv" in snippet.content for snippet in lead.context)

def test_main_with_error(monkeypatch, capsys):
    """Test the main function with an error log."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(SIMPLE_ENV_ERROR)
        temp_path = f.name
    
    try:
        with patch('sys.argv', ['undefined_environment_proofer.py', '--log-file', temp_path]):
            from smart_pandoc_debugger.managers.investigator_team.undefined_environment_proofer import main
            main()
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            
            assert 'error' in output
            assert output['environment'] == 'foobar'
            assert output['line'] == 10
    finally:
        os.unlink(temp_path)

def test_main_with_source_file(monkeypatch, capsys, tmp_path):
    """Test the main function with a source file."""
    # Create a temporary log file with an error
    log_file = tmp_path / "test.log"
    log_file.write_text(SIMPLE_ENV_ERROR)
    
    # Create a temporary source file
    source_file = tmp_path / "test.tex"
    source_file.write_text("\\begin{document}\\n                           \\begin{foobar}\
                           Test\\end{foobar}\
                           \\end{document}")
    
    try:
        with patch('sys.argv', [
            'undefined_environment_proofer.py', 
            '--log-file', str(log_file),
            '--source-file', str(source_file)
        ]):
            from smart_pandoc_debugger.managers.investigator_team.undefined_environment_proofer import main
            main()
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            
            # Check that we have a properly formatted ActionableLead
            assert 'lead_type' in output
            assert output['lead_type'] == 'LATEX_UNDEFINED_ENVIRONMENT'
            assert 'foobar' in output['description']
            assert output['line_number'] == 10
            assert output['severity'] == 'error'
            
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")

def test_main_no_error(monkeypatch, capsys):
    """Test the main function with a clean log."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(NO_ERROR)
        temp_path = f.name
    
    try:
        with patch('sys.argv', ['undefined_environment_proofer.py', '--log-file', temp_path]):
            from smart_pandoc_debugger.managers.investigator_team.undefined_environment_proofer import main
            main()
            
            captured = capsys.readouterr()
            assert captured.out.strip() == '{}'
    finally:
        os.unlink(temp_path)

def test_main_file_not_found(monkeypatch, capsys):
    """Test the main function with a non-existent log file."""
    with patch('sys.argv', ['undefined_environment_proofer.py', '--log-file', '/nonexistent/file']):
        from smart_pandoc_debugger.managers.investigator_team.undefined_environment_proofer import main
        main()
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert 'error' in output
        assert 'PROCESSING_ERROR' in output.get('error', '')
