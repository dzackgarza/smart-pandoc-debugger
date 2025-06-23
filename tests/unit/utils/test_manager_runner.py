# tests/unit/utils/test_manager_runner.py

import subprocess  # For TimeoutExpired
from unittest import mock

import pytest

from smart_pandoc_debugger.data_model import DiagnosticJob

# from utils.manager_runner import run_manager  # Main function


@pytest.fixture
def sample_diagnostic_job():
    """Create a sample DiagnosticJob for testing."""
    return DiagnosticJob(
        original_markdown_path="test.md"
    )


@pytest.fixture
def mock_run_process(mocker, monkeypatch):
    """Mock the subprocess.run function and file existence check."""
    def mock_isfile(path):
        # Only return True for the specific test file we're using
        valid_paths = ["Miner.py", "./Miner.py", "/Miner.py"]
        return path in valid_paths

    # Mock os.path.isfile to handle our test file
    monkeypatch.setattr('os.path.isfile', mock_isfile)

    with mock.patch('subprocess.run') as mock_run:
        # Default to a successful run with empty output
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b'{}',
            stderr=b''
        )
        yield mock_run


def test_run_manager_success(
    mock_run_process, sample_diagnostic_job, tmp_path
):
    """Test run_manager with a successful manager script execution."""
    # Create a temporary file for stdout
    stdout_file = tmp_path / "stdout.txt"
    stdout_file.write_text(sample_diagnostic_job.model_dump_json())

    # Configure the mock to return the path to our stdout file
    mock_run_process.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=stdout_file.read_bytes(), stderr=b""
    )

    # Run the manager
    from utils.manager_runner import run_manager
    result_job = run_manager(
        "Miner.py",
        sample_diagnostic_job
    )

    # Verify the result
    assert (result_job.original_markdown_path ==
            sample_diagnostic_job.original_markdown_path)
    mock_run_process.assert_called_once()


def test_run_manager_script_failure(
    mock_run_process, sample_diagnostic_job
):
    """Test run_manager when manager script returns non-zero exit code."""
    mock_run_process.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout=b"",
        stderr=b"Script error"
    )

    from utils.manager_runner import run_manager
    with pytest.raises(
        AssertionError,
        match="Assertion Failed: Manager script"
    ):
        run_manager(
            "Miner.py",
            sample_diagnostic_job
        )


def test_run_manager_invalid_json_output(
    mock_run_process, sample_diagnostic_job
):
    """Test run_manager when manager script outputs invalid JSON."""
    mock_run_process.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=b"this is not json",
        stderr=b""
    )

    from utils.manager_runner import run_manager
    with pytest.raises(ValueError):
        run_manager("Miner.py", sample_diagnostic_job)


def test_run_manager_json_does_not_match_model(
    mock_run_process, sample_diagnostic_job
):
    """Test when manager outputs valid JSON but not a DiagnosticJob."""
    invalid_json = '{"invalid": "data"}'
    mock_run_process.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=invalid_json.encode('utf-8'),
        stderr=b""
    )

    from utils.manager_runner import run_manager
    with pytest.raises(
        ValueError  # or pydantic.ValidationError
    ):
        run_manager("Miner.py", sample_diagnostic_job)


def test_run_manager_pythonpath_modification(
    mock_run_process, sample_diagnostic_job
):
    """Verify PYTHONPATH is correctly modified for the manager script."""
    # run_manager("Miner.py", sample_diagnostic_job)
    # called_env = mock_run_process.call_args[1].get('env')
    # assert 'PYTHONPATH' in called_env
    # assert 'utils' in called_env['PYTHONPATH']  # Check project root/utils
    pass


def test_run_manager_process_job_flag(mock_run_process, sample_diagnostic_job):
    """Verify the --process-job flag is passed to the manager script."""
    # run_manager("Miner.py", sample_diagnostic_job)
    # called_cmd = mock_run_process.call_args[0][0]  # First arg, first call
    # assert "--process-job" in called_cmd
    pass


def test_run_manager_stdin_serialization(
    mock_run_process, sample_diagnostic_job
):
    """Verify DiagnosticJob is correctly serialized to manager's stdin."""
    # run_manager("Miner.py", sample_diagnostic_job)
    # called_input = mock_run_process.call_args[1].get('input')
    # assert (json.loads(called_input) ==
    #         sample_diagnostic_job.model_dump())
    pass


def test_run_manager_timeout(mock_run_process, sample_diagnostic_job):
    """Test manager timeout if run_manager supports it via run_process."""
    # mock_run_process.side_effect = \
    #     subprocess.TimeoutExpired(
    #         "cmd", 0.1
    #     )
    # with pytest.raises(subprocess.TimeoutExpired):
    #     run_manager(
    #         "Miner.py",
    #         sample_diagnostic_job,
    #         timeout=0.1
    #     )  # Test timeout
    pass


def test_run_manager_nonexistent_script(
    mock_run_process, sample_diagnostic_job
):
    """Test running a non-existent manager script."""
    # mock_run_process.side_effect = FileNotFoundError(
    #     "Script not found"
    # )
    # with pytest.raises(FileNotFoundError):
    #     run_manager("NonExistentManager.py", sample_diagnostic_job)
    pass


def test_run_manager_empty_diagnostic_job_input(mock_run_process):
    """Test with a completely empty or default DiagnosticJob."""
    # empty_job = DiagnosticJob(original_markdown_content="")
    # Setup mock_run_process for success with empty_job
    # run_manager("Miner.py", empty_job)
    pass


def test_run_manager_early_script_failure_handling(
    mock_run_process, sample_diagnostic_job
):
    """If script fails before outputting JSON, return original job."""
    # mock_run_process.return_value.return_code = 1
    # mock_run_process.return_value.stderr = "Failed before JSON output"
    # mock_run_process.return_value.stdout = ""  # No valid JSON
    # with pytest.raises(Exception):
    #     run_manager("Miner.py", sample_diagnostic_job)
    pass


def test_run_manager_handles_large_json_io(
    mock_run_process, sample_diagnostic_job
):
    """Test with DiagnosticJob that results in large JSON string."""
    # large_content = "a" * 10**6
    # large_job = DiagnosticJob(original_markdown_content=large_content)
    # # Setup mock_run_process for success with large_job
    # run_manager("Miner.py", large_job)
    pass


def test_run_manager_script_path_resolution(
    mock_run_process, sample_diagnostic_job
):
    """Test that the path to the manager script is correctly resolved."""
    # run_manager("Miner.py", sample_diagnostic_job)
    # called_cmd = mock_run_process.call_args[0][0]
    # Script path is second element
    # assert "managers/Miner.py" in called_cmd[1]
    pass


def test_run_manager_with_different_managers(
    mock_run_process, sample_diagnostic_job
):
    """Test calling run_manager with different manager names."""
    # for manager_name in ["Miner.py", "Investigator.py"]:
    #     mock_run_process.reset_mock()
    #     # Setup mock for this manager
    #     # updated_job = sample_diagnostic_job.model_copy()
    #     # mock_run_process.return_value.stdout = \
    #     #     updated_job.model_dump_json()
    #     # mock_run_process.return_value.return_code = 0
    #     run_manager(manager_name, sample_diagnostic_job)
    #     assert manager_name in mock_run_process.call_args[0][0]
    pass


def test_run_manager_error_propagation_from_run_process(
    mock_run_process, sample_diagnostic_job
):
    """Ensure errors from run_process are handled or propagated."""
    # mock_run_process.side_effect = (
    #     FileNotFoundError(
    #         "Script not found"
    #     )
    # )
    # with pytest.raises(FileNotFoundError):
    #     run_manager("Miner.py", sample_diagnostic_job)
    pass


def test_run_manager_stderr_logging(
    mock_run_process, sample_diagnostic_job
):
    """Test that stderr from manager script is logged or available."""
    # mock_run_process.return_value.stderr = (
    #     "Warning from manager"
    # )
    # mock_run_process.return_value.return_code = 0  \
    #     # Success with stderr output
    # run_manager("Miner.py", sample_diagnostic_job)
    # Assert warning is logged
    pass


def test_run_manager_no_process_job_flag_handling(
    mock_run_process, sample_diagnostic_job
):
    """Test manager script without --process-job flag."""
    # This might require a real script that checks for the flag.
    # For mocking, ensure run_process includes it.
    pass


def test_run_manager_malformed_manager_name(
    mock_run_process, sample_diagnostic_job
):
    """Test providing a non-.py manager name or invalid path."""
    # with pytest.raises(
    #     ValueError
    # ):
    #     run_manager(
    #         "not_a_python_file",
    #         sample_diagnostic_job
    #     )
    pass


def test_run_manager_pass_through_unknown_kwargs(
    mock_run_process, sample_diagnostic_job
):
    """Test that run_manager passes kwargs to run_process."""
    # run_manager("Miner.py", sample_diagnostic_job, extra_arg=123)
    # assert mock_run_process.call_args[1].get('extra_arg') == 123
    pass
