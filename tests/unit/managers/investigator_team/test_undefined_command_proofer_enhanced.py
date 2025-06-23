#!/usr/bin/env python3
# tests/unit/managers/investigator_team/test_undefined_command_proofer_enhanced.py

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

from smart_pandoc_debugger.managers.investigator_team.undefined_command_proofer import (
    find_undefined_commands,
    suggest_package,
    create_actionable_lead,
    run_undefined_command_proofer
)
from smart_pandoc_debugger.data_model import ActionableLead, SourceContextSnippet

# Test data
SIMPLE_UNDEFINED_CMD = """
! Undefined control sequence.
l.5 \foobar
             
? 
"""

MULTIPLE_UNDEFINED_CMDS = """
! Undefined control sequence.
l.5 \foobar
             
! Undefined control sequence.
l.10 \baz
"""

ALT_FORMAT_ERROR = """
! LaTeX Error: \foobar undefined.
l.5 \foobar
"""

NO_ERROR = """
This is a normal LaTeX log file with no errors.
"""

# Fixtures
@pytest.fixture
def simple_undefined_cmd():
    return SIMPLE_UNDEFINED_CMD

@pytest.fixture
def multiple_undefined_cmds():
    return MULTIPLE_UNDEFINED_CMDS

@pytest.fixture
def alt_format_error():
    return ALT_FORMAT_ERROR

@pytest.fixture
def no_error():
    return NO_ERROR

# Tests
def test_find_undefined_commands_simple(simple_undefined_cmd):
    """Test finding a simple undefined command error."""
    results = find_undefined_commands(simple_undefined_cmd)
    assert len(results) == 1
    assert results[0]['command'] == '\\foobar'
    assert results[0]['line_number'] == 5
    assert results[0]['error_type'] == 'UNDEFINED_CONTROL_SEQUENCE'

def test_find_undefined_commands_multiple(multiple_undefined_cmds):
    """Test finding multiple undefined command errors."""
    results = find_undefined_commands(multiple_undefined_cmds)
    assert len(results) == 2
    commands = {r['command'] for r in results}
    assert '\\foobar' in commands
    assert '\\baz' in commands

def test_find_undefined_commands_alt_format(alt_format_error):
    """Test finding undefined commands in alternate error format."""
    results = find_undefined_commands(alt_format_error)
    assert len(results) == 1
    assert results[0]['command'] == '\\foobar'
    assert results[0]['line_number'] == 5
    assert results[0]['error_type'] == 'UNDEFINED_COMMAND'

def test_find_undefined_commands_no_error(no_error):
    """Test that no errors are found in a clean log."""
    assert find_undefined_commands(no_error) == []

def test_suggest_package_known():
    """Test suggesting a package for a known command."""
    assert suggest_package('\\includegraphics') == 'graphicx'
    assert suggest_package('\\toprule') == 'booktabs'
    assert suggest_package('\\text') == 'amsmath'

def test_suggest_package_unknown():
    """Test suggesting a package for an unknown command."""
    assert suggest_package('\\nonexistentcommand') == ''

def test_create_actionable_lead():
    """Test creating an actionable lead from error info."""
    error_info = {
        'command': '\\includegraphics',
        'line_number': 42,
        'error_type': 'UNDEFINED_CONTROL_SEQUENCE'
    }
    
    lead = create_actionable_lead(error_info, '/path/to/source.tex')
    
    assert isinstance(lead, ActionableLead)
    assert lead.lead_type == 'UNDEFINED_CONTROL_SEQUENCE'
    assert "includegraphics" in lead.description
    assert lead.line_number == 42
    assert lead.source_file == '/path/to/source.tex'
    assert lead.severity == 'error'
    assert lead.confidence == 0.9
    
    # Check that we have a fix suggestion
    assert '\\usepackage' in lead.fix or '\\newcommand' in lead.fix
    
    # Check context
    assert len(lead.context) > 0
    assert any("Undefined command" in snippet.content for snippet in lead.context)

def test_run_undefined_command_proofer_success(tmp_path):
    """Test running the proofer with a log file containing errors."""
    # Create a temporary log file with an error
    log_file = tmp_path / "test.log"
    log_file.write_text(SIMPLE_UNDEFINED_CMD)
    
    # Run the proofer
    leads = run_undefined_command_proofer(str(log_file))
    
    # Check the results
    assert len(leads) == 1
    assert leads[0].lead_type == 'UNDEFINED_CONTROL_SEQUENCE'
    assert "foobar" in leads[0].description
    assert leads[0].line_number == 5

def test_run_undefined_command_proofer_no_file():
    """Test running the proofer with a non-existent log file."""
    leads = run_undefined_command_proofer("/nonexistent/file")
    assert leads == []

def test_main_with_error(monkeypatch, capsys):
    """Test the main function with an error log."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(SIMPLE_UNDEFINED_CMD)
        temp_path = f.name
    
    try:
        with patch('sys.argv', ['undefined_command_proofer.py', '--log-file', temp_path]):
            from smart_pandoc_debugger.managers.investigator_team.undefined_command_proofer import main
            main()
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            
            assert len(output) == 1
            assert output[0]['command'] == '\\foobar'
            assert output[0]['line'] == 5
    finally:
        os.unlink(temp_path)

def test_main_with_source_file(monkeypatch, capsys, tmp_path):
    """Test the main function with a source file."""
    # Create a temporary log file with an error
    log_file = tmp_path / "test.log"
    log_file.write_text(SIMPLE_UNDEFINED_CMD)
    
    # Create a temporary source file
    source_file = tmp_path / "test.tex"
    source_file.write_text("\\documentclass{article}\\n                           \\begin{document}\
                           \\foobar
                           \\end{document}")
    
    try:
        with patch('sys.argv', [
            'undefined_command_proofer.py', 
            '--log-file', str(log_file),
            '--source-file', str(source_file)
        ]):
            from smart_pandoc_debugger.managers.investigator_team.undefined_command_proofer import main
            main()
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            
            # Check that we have a properly formatted ActionableLead
            assert len(output) > 0
            assert 'lead_type' in output[0]
            assert 'foobar' in output[0]['description']
            assert output[0]['line_number'] == 5
            assert output[0]['severity'] == 'error'
            
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")

def test_main_no_error(monkeypatch, capsys):
    """Test the main function with a clean log."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(NO_ERROR)
        temp_path = f.name
    
    try:
        with patch('sys.argv', ['undefined_command_proofer.py', '--log-file', temp_path]):
            from smart_pandoc_debugger.managers.investigator_team.undefined_command_proofer import main
            main()
            
            captured = capsys.readouterr()
            assert captured.out.strip() == '[]'
    finally:
        os.unlink(temp_path)

def test_main_file_not_found(monkeypatch, capsys):
    """Test the main function with a non-existent log file."""
    with patch('sys.argv', ['undefined_command_proofer.py', '--log-file', '/nonexistent/file']):
        from smart_pandoc_debugger.managers.investigator_team.undefined_command_proofer import main
        main()
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert 'error' in output
        assert 'PROCESSING_ERROR' in output.get('error', '')
