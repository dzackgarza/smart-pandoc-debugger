# tests/unit/utils/test_manager_runner.py
import pytest
import json
import subprocess # Added for TimeoutExpired and CompletedProcess
import os
import sys
from unittest.mock import patch, MagicMock
import tempfile

from smart_pandoc_debugger.data_model import DiagnosticJob, PipelineStatus
from utils.manager_runner import run_manager
from pydantic import ValidationError

DUMMY_MANAGER_SCRIPT = os.path.join(os.path.dirname(__file__), "dummy_manager.py")

@pytest.fixture
def sample_diagnostic_job():
    return DiagnosticJob(
        original_markdown_content="test content",
        original_markdown_path="dummy_runner_input.md"
    )

@pytest.fixture
def mock_run_process(mocker):
    m = mocker.patch('utils.manager_runner.subprocess.run')
    return m

def test_run_manager_success(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Test run_manager with a successful manager script execution."""
    expected_status_after_dummy_run = PipelineStatus.ORACLE_ANALYSIS_COMPLETE

    job_as_output_by_dummy = sample_diagnostic_job.model_copy(
        update={"status": expected_status_after_dummy_run}
    )
    job_as_output_by_dummy.history.append("Processed by dummy_manager.py")
    output_json_str = job_as_output_by_dummy.model_dump_json()

    mock_run_process.return_value = subprocess.CompletedProcess(
        args=[sys.executable, DUMMY_MANAGER_SCRIPT, "--process-job"],
        returncode=0,
        stdout=output_json_str.encode('utf-8'),
        stderr=b""
    )

    result_job = run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    assert result_job.status == expected_status_after_dummy_run
    assert "Processed by dummy_manager.py" in result_job.history
    mock_run_process.assert_called_once()

def test_run_manager_script_failure(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Test run_manager when the manager script returns a non-zero exit code."""
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=1, stdout=b"", stderr="Script error".encode('utf-8'))

    with pytest.raises(AssertionError) as excinfo:
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    assert f"Manager script '{DUMMY_MANAGER_SCRIPT}' crashed or reported an error" in str(excinfo.value)

def test_run_manager_invalid_json_output(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Test run_manager when manager script outputs invalid JSON."""
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="this is not json".encode('utf-8'), stderr=b"")

    with pytest.raises(ValidationError):
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

def test_run_manager_json_does_not_match_model(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Test when manager outputs valid JSON but not a DiagnosticJob."""
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps({"some_other_data": "value"}).encode('utf-8'), stderr=b"")

    with pytest.raises(ValidationError):
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

def test_run_manager_pythonpath_modification(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Verify PYTHONPATH is correctly modified for the manager script."""
    updated_job_dict = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr=b"")
    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

    assert mock_run_process.call_count == 1
    call_kwargs = mock_run_process.call_args[1]
    assert 'env' in call_kwargs
    called_env = call_kwargs['env']
    assert 'PYTHONPATH' in called_env

    current_script_dir = os.path.dirname(os.path.abspath(run_manager.__code__.co_filename))
    project_root = os.path.dirname(current_script_dir)
    assert project_root in called_env['PYTHONPATH']

    original_pythonpath = os.environ.get('PYTHONPATH', None)
    if original_pythonpath:
        assert original_pythonpath in called_env['PYTHONPATH']

def test_run_manager_process_job_flag(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Verify the --process-job flag is passed to the manager script."""
    updated_job_dict = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr=b"")
    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

    called_cmd_list = mock_run_process.call_args[0][0]
    assert "--process-job" in called_cmd_list

def test_run_manager_stdin_serialization(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Verify DiagnosticJob is correctly serialized to manager's stdin."""
    updated_job_dict_str = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict_str.encode('utf-8'), stderr=b"")
    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

    called_input = mock_run_process.call_args[1].get('input')
    assert json.loads(called_input.decode('utf-8')) == sample_diagnostic_job.model_dump()

def test_run_manager_timeout(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Test manager timeout if run_manager supports it via run_process."""
    mock_run_process.side_effect = subprocess.TimeoutExpired(cmd="cmd", timeout=0.1)
    with pytest.raises(subprocess.TimeoutExpired):
       run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

def test_run_manager_nonexistent_script(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Test trying to run a manager script that doesn't exist."""
    with pytest.raises(AssertionError) as excinfo:
       run_manager("NonExistentManager.py", sample_diagnostic_job)
    assert "Manager script not found" in str(excinfo.value)
    mock_run_process.assert_not_called()

def test_run_manager_empty_diagnostic_job_input(mock_run_process: MagicMock):
    """Test with a completely empty or default DiagnosticJob."""
    empty_job = DiagnosticJob(original_markdown_content="", original_markdown_path="empty.md")
    processed_empty_job_json = empty_job.model_copy(update={"status": PipelineStatus.ORACLE_ANALYSIS_COMPLETE}).model_dump_json()

    mock_run_process.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=processed_empty_job_json.encode('utf-8'),
        stderr=b""
    )
    result_job = run_manager(DUMMY_MANAGER_SCRIPT, empty_job)

    mock_run_process.assert_called_once()
    passed_job_json = mock_run_process.call_args[1].get('input').decode('utf-8')
    passed_job = DiagnosticJob.model_validate_json(passed_job_json)
    assert passed_job.original_markdown_path == "empty.md"
    assert result_job.status == PipelineStatus.ORACLE_ANALYSIS_COMPLETE

def test_run_manager_diagnostic_job_unchanged_if_script_fails_early(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """If script fails before outputting JSON (e.g. Python error in script), run_manager should raise an error."""
    mock_run_process.return_value = subprocess.CompletedProcess(args=[],returncode=0, stdout=b"invalid output", stderr="Python error in script".encode('utf-8'))
    with pytest.raises(ValidationError):
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

def test_run_manager_handles_large_json_io(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Test with DiagnosticJob that results in very large JSON string."""
    large_content = "a" * 10**5
    large_job = DiagnosticJob(original_markdown_content=large_content, original_markdown_path="large.md")

    processed_large_job_json = large_job.model_copy(update={"status": PipelineStatus.ORACLE_ANALYSIS_COMPLETE}).model_dump_json()

    mock_run_process.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=processed_large_job_json.encode('utf-8'),
        stderr=b""
    )
    result_job = run_manager(DUMMY_MANAGER_SCRIPT, large_job)

    mock_run_process.assert_called_once()
    passed_job_json = mock_run_process.call_args[1].get('input').decode('utf-8')
    assert len(passed_job_json) > 10**5
    assert result_job.status == PipelineStatus.ORACLE_ANALYSIS_COMPLETE
    assert result_job.original_markdown_content == large_content

def test_run_manager_correct_script_path_resolution(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Test that the manager_script_path is used as passed."""
    updated_job_dict = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr=b"")

    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

    called_cmd_list = mock_run_process.call_args[0][0]
    assert DUMMY_MANAGER_SCRIPT in called_cmd_list

def test_run_manager_with_different_managers(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Test calling run_manager with different manager script names."""
    job_json = sample_diagnostic_job.model_dump_json().encode('utf-8')
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=job_json, stderr=b"")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=os.path.dirname(DUMMY_MANAGER_SCRIPT)) as tmp_manager1_file, \
         tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=os.path.dirname(DUMMY_MANAGER_SCRIPT)) as tmp_manager2_file:
        manager1_path = tmp_manager1_file.name
        manager2_path = tmp_manager2_file.name
        tmp_manager1_file.write("import sys; sys.exit(0)\n")
        tmp_manager2_file.write("import sys; sys.exit(0)\n")

    try:
        run_manager(manager1_path, sample_diagnostic_job)
        args1, _ = mock_run_process.call_args
        assert manager1_path in args1[0]

        mock_run_process.reset_mock()
        mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=job_json, stderr=b"")
        run_manager(manager2_path, sample_diagnostic_job)
        args2, _ = mock_run_process.call_args
        assert manager2_path in args2[0]
    finally:
        os.remove(manager1_path)
        os.remove(manager2_path)

def test_run_manager_error_propagation_from_run_process(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    """Ensure specific errors from run_process (like permission errors) are handled or propagated."""
    mock_run_process.side_effect = PermissionError("Permission denied")
    with pytest.raises(PermissionError):
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

def test_run_manager_manager_script_stderr_logging(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob, caplog):
    """Test that stderr from the manager script is logged or available."""
    import logging
    processed_job_json = sample_diagnostic_job.model_copy(update={"status": PipelineStatus.ORACLE_ANALYSIS_COMPLETE}).model_dump_json()

    mock_run_process.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=processed_job_json.encode('utf-8'),
        stderr="Some warning from manager".encode('utf-8')
    )
    with caplog.at_level(logging.INFO):
       run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    assert "Some warning from manager" in caplog.text

def test_run_manager_no_process_job_flag_handling(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    updated_job_dict = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr=b"")

    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    args, _ = mock_run_process.call_args
    assert "--process-job" in args[0]

def test_run_manager_malformed_manager_name(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    with pytest.raises(AssertionError) as excinfo:
       run_manager("NotAScript", sample_diagnostic_job)
    assert "Manager script not found" in str(excinfo.value)
    mock_run_process.assert_not_called()

def test_run_manager_pass_through_unknown_kwargs(mock_run_process: MagicMock, sample_diagnostic_job: DiagnosticJob):
    updated_job_dict = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr=b"")

    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    mock_run_process.assert_called_once()
