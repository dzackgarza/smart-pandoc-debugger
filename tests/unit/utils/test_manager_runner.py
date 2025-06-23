# tests/unit/utils/test_manager_runner.py
import pytest
import json
import subprocess # Added for TimeoutExpired and CompletedProcess
import os # Added
import sys # Added
from unittest.mock import patch # Added
import tempfile # Added, was used later but good to have imports at top

from smart_pandoc_debugger.data_model import DiagnosticJob, PipelineStatus # Corrected Enum name
from utils.manager_runner import run_manager # Assuming this is the main function
from pydantic import ValidationError # Added

DUMMY_MANAGER_SCRIPT = os.path.join(os.path.dirname(__file__), "dummy_manager.py")

@pytest.fixture
def sample_diagnostic_job():
    return DiagnosticJob(
        original_markdown_content="test content",
        original_markdown_path="dummy_runner_input.md"
    )

@pytest.fixture
def mock_run_process(mocker):
    # manager_runner.py imports subprocess and calls subprocess.run
    # So we patch it as it's seen by utils.manager_runner
    return mocker.patch('utils.manager_runner.subprocess.run')


def test_run_manager_success(mock_run_process, sample_diagnostic_job):
    """Test run_manager with a successful manager script execution."""
    # The dummy script now sets status to ORACLE_ANALYSIS_COMPLETE.
    # The mock should reflect what the script (if it were real) would output.
    expected_status_after_dummy_run = PipelineStatus.ORACLE_ANALYSIS_COMPLETE

    # Create the job state as the dummy script would output it
    job_as_output_by_dummy = sample_diagnostic_job.model_copy(
        update={"status": expected_status_after_dummy_run}
    )
    job_as_output_by_dummy.history.append("Processed by dummy_manager.py") # Match dummy script
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
    pass

def test_run_manager_script_failure(mock_run_process, sample_diagnostic_job):
    """Test run_manager when the manager script returns a non-zero exit code."""
    # Ensure stdout is bytes
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=1, stdout=b"", stderr="Script error".encode('utf-8'))

    with pytest.raises(AssertionError) as excinfo:
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    assert f"Manager script '{DUMMY_MANAGER_SCRIPT}' crashed or reported an error" in str(excinfo.value)
    pass

def test_run_manager_invalid_json_output(mock_run_process, sample_diagnostic_job):
    """Test run_manager when manager script outputs invalid JSON."""
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="this is not json".encode('utf-8'), stderr=b"")

    # model_validate_json raises ValidationError for invalid JSON structure or type errors,
    # including when JSON parsing itself fails.
    with pytest.raises(ValidationError):
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    pass

def test_run_manager_json_does_not_match_model(mock_run_process, sample_diagnostic_job):
    """Test when manager outputs valid JSON but not a DiagnosticJob."""
    from pydantic import ValidationError
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps({"some_other_data": "value"}).encode('utf-8'), stderr=b"")

    with pytest.raises(ValidationError):
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    pass

def test_run_manager_pythonpath_modification(mock_run_process, sample_diagnostic_job):
    """Verify PYTHONPATH is correctly modified for the manager script."""
    updated_job_dict = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr=b"")
    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

    assert mock_run_process.call_count == 1
    call_kwargs = mock_run_process.call_args[1]
    assert 'env' in call_kwargs
    called_env = call_kwargs['env']
    assert 'PYTHONPATH' in called_env
    # project_root should be parent of 'utils' dir where manager_runner.py is
    import os
    current_script_dir = os.path.dirname(os.path.abspath(run_manager.__code__.co_filename)) # utils dir
    project_root = os.path.dirname(current_script_dir)
    assert project_root in called_env['PYTHONPATH']
    pass

def test_run_manager_process_job_flag(mock_run_process, sample_diagnostic_job):
    """Verify the --process-job flag is passed to the manager script."""
    updated_job_dict = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr=b"")
    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

    called_cmd_list = mock_run_process.call_args[0][0]
    assert "--process-job" in called_cmd_list
    pass

def test_run_manager_stdin_serialization(mock_run_process, sample_diagnostic_job):
    """Verify DiagnosticJob is correctly serialized to manager's stdin."""
    updated_job_dict_str = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict_str.encode('utf-8'), stderr=b"")
    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)

    called_input = mock_run_process.call_args[1].get('input')
    assert json.loads(called_input.decode('utf-8')) == sample_diagnostic_job.model_dump()
    pass

def test_run_manager_timeout(mock_run_process, sample_diagnostic_job):
    """Test manager timeout if run_manager supports it via run_process."""
    # run_manager itself doesn't directly expose timeout; it's a property of subprocess.run
    # This test would be more about how run_manager *handles* a timeout from subprocess.run
    # For now, assume run_manager doesn't specifically catch TimeoutExpired from subprocess.run
    mock_run_process.side_effect = subprocess.TimeoutExpired(cmd="cmd", timeout=0.1)
    with pytest.raises(subprocess.TimeoutExpired):
       run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    pass

def test_run_manager_nonexistent_script(mock_run_process, sample_diagnostic_job):
    """Test trying to run a manager script that doesn't exist."""
    # run_manager will assert os.path.isfile(manager_script_path)
    with pytest.raises(AssertionError) as excinfo:
       run_manager("NonExistentManager.py", sample_diagnostic_job)
    assert "Manager script not found" in str(excinfo.value)
    pass

def test_run_manager_empty_diagnostic_job_input(mock_run_process):
    """Test with a completely empty or default DiagnosticJob."""
    empty_job = DiagnosticJob(original_markdown_content="", original_markdown_path="empty.md")
    updated_job_dict_str = empty_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict_str.encode('utf-8'), stderr=b"")
    run_manager(DUMMY_MANAGER_SCRIPT, empty_job)
    mock_run_process.assert_called_once()
    pass

def test_run_manager_diagnostic_job_unchanged_if_script_fails_early(mock_run_process, sample_diagnostic_job):
    """If script fails before outputting JSON, original job should be returned or error raised."""
    mock_run_process.return_value = subprocess.CompletedProcess(args=[],returncode=1, stdout=b"", stderr="Failed before JSON output".encode('utf-8'))
    with pytest.raises(AssertionError):
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    pass

def test_run_manager_handles_large_json_io(mock_run_process, sample_diagnostic_job):
    """Test with DiagnosticJob that results in very large JSON string."""
    large_content = "a" * 10**5
    large_job = DiagnosticJob(original_markdown_content=large_content, original_markdown_path="large.md")
    updated_job_dict_str = large_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict_str.encode('utf-8'), stderr=b"")
    run_manager(DUMMY_MANAGER_SCRIPT, large_job)
    mock_run_process.assert_called_once()
    pass

def test_run_manager_correct_script_path_resolution(mock_run_process, sample_diagnostic_job):
    """Test that the path to the manager script is correctly resolved."""
    updated_job_dict = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr=b"")

    # Now uses DUMMY_MANAGER_SCRIPT which is known to exist.
    run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    called_cmd_list = mock_run_process.call_args[0][0]
    assert DUMMY_MANAGER_SCRIPT in called_cmd_list
    pass

def test_run_manager_with_different_managers(mock_run_process, sample_diagnostic_job):
    """Test calling run_manager with different manager script names."""
    # This tests that the manager_script_path argument is correctly used.
    # The original test created temp files. This is a good approach.
    managers_to_test = ["ManagerA_Test.py", "ManagerB_Test.py"]
    for manager_name in managers_to_test:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=os.path.dirname(DUMMY_MANAGER_SCRIPT)) as tmp_script_file:
            # Write minimal content to make it a "valid" script for os.path.isfile
            tmp_script_file.write("import sys; sys.exit(0)\n")
            script_path = tmp_script_file.name

        try:
            mock_run_process.reset_mock()
            updated_job_dict = sample_diagnostic_job.model_dump_json()
            mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr=b"")
            run_manager(script_path, sample_diagnostic_job)
            called_cmd_list = mock_run_process.call_args[0][0]
            assert script_path in called_cmd_list
        finally:
            os.remove(script_path) # Clean up the temporary script
    pass

def test_run_manager_error_propagation_from_run_process(mock_run_process, sample_diagnostic_job):
    """Ensure specific errors from run_process (like permission errors) are handled or propagated."""
    mock_run_process.side_effect = PermissionError("Permission denied")
    with pytest.raises(PermissionError):
        run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    pass

def test_run_manager_manager_script_stderr_logging(mock_run_process, sample_diagnostic_job, caplog):
    """Test that stderr from the manager script is logged or available."""
    import logging
    updated_job_dict = sample_diagnostic_job.model_dump_json()
    mock_run_process.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=updated_job_dict.encode('utf-8'), stderr="Some warning from manager".encode('utf-8'))
    with caplog.at_level(logging.INFO):
       run_manager(DUMMY_MANAGER_SCRIPT, sample_diagnostic_job)
    assert "Some warning from manager" in caplog.text
    pass

def test_run_manager_no_process_job_flag_handling(mock_run_process, sample_diagnostic_job):
    # The current run_manager always adds --process-job.
    # A test for *not* adding it would require changing run_manager or testing a different utility.
    pass

def test_run_manager_malformed_manager_name(mock_run_process, sample_diagnostic_job):
    # run_manager asserts os.path.isfile. This will fail if path is malformed before even calling subprocess.
    with pytest.raises(AssertionError): # As it asserts isfile
       run_manager("NotAScript", sample_diagnostic_job)
    pass

def test_run_manager_pass_through_unknown_kwargs(mock_run_process, sample_diagnostic_job):
    # run_manager does not accept arbitrary **kwargs to pass to subprocess.run
    # This test is not applicable to the current signature of run_manager.
    pass
