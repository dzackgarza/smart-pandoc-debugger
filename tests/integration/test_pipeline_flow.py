# tests/integration/test_pipeline_flow.py
import pytest
from unittest.mock import patch, MagicMock, call # Added call
from smart_pandoc_debugger.data_model import DiagnosticJob, StatusEnum, ActionableLead, LeadTypeEnum, MarkdownRemedy
# Assume coordinator.main is the entry point to the pipeline
# from coordinator import main as run_coordinator_pipeline # This needs coordinator.py to be importable

@pytest.fixture
def mock_run_manager(mocker):
    """Mocks the 'run_manager' utility used by Coordinator."""
    # Adjust path to where Coordinator imports run_manager
    # If coordinator.py has `from utils.manager_runner import run_manager`
    return mocker.patch('coordinator.run_manager', create=True) # create=True needed if module not fully loaded

@pytest.fixture
def basic_job_input():
    return DiagnosticJob(case_id="integ_job_01", original_markdown_content="# Title\nTest content.")

@pytest.mark.level1
def test_pipeline_miner_success_no_further_action(mock_run_manager, basic_job_input):
    """Test full pipeline: Miner succeeds, Investigator/Oracle skipped, Reporter runs."""
    # miner_output = basic_job_input.model_copy(update={'status': StatusEnum.COMPILATION_SUCCESS, 'final_pdf_path': 'test.pdf'})
    # reporter_output = miner_output.model_copy(update={'status': StatusEnum.REPORT_GENERATED, 'final_user_report_summary': 'All good!'})

    # def side_effect(manager_name, job_state):
    #     if manager_name == "Miner.py": return miner_output
    #     if manager_name == "Reporter.py": return reporter_output
    #     if manager_name in ["Investigator.py", "Oracle.py"]:
    #         pytest.fail(f"{manager_name} was called unexpectedly.")
    #     return job_state
    # mock_run_manager.side_effect = side_effect

    # from coordinator import main as run_coordinator_pipeline # SUT import
    # final_job = run_coordinator_pipeline(basic_job_input.model_copy())
    #
    # assert mock_run_manager.call_count == 2
    # mock_run_manager.assert_any_call("Miner.py", basic_job_input) # This will be basic_job_input.model_copy()
    # # The actual object passed to Reporter.py would be miner_output.
    # # We need to check the call arguments carefully.
    # # mock_run_manager.assert_any_call("Reporter.py", miner_output) # More accurate
    # assert final_job.status == StatusEnum.REPORT_GENERATED
    # assert final_job.final_user_report_summary == 'All good!'
    pass

@pytest.mark.level2
def test_pipeline_miner_md_fail_oracle_skipped_reporter_runs(mock_run_manager, basic_job_input):
    """Pipeline: Miner fails MD conversion, Investigator/Oracle skipped, Reporter runs."""
    # miner_output = basic_job_input.model_copy(
    #     update={'status': StatusEnum.MINER_MD_TO_TEX_FAILED,
    #             'leads': [ActionableLead(lead_type=LeadTypeEnum.MARKDOWN_SYNTAX, description="Bad MD")]}
    # )
    # reporter_output = miner_output.model_copy(update={'status': StatusEnum.REPORT_GENERATED, 'final_user_report_summary': 'MD Error Report'})

    # def side_effect(manager_name, job_state):
    #     if manager_name == "Miner.py": return miner_output
    #     if manager_name == "Reporter.py": return reporter_output
    #     if manager_name in ["Investigator.py", "Oracle.py"]:
    #         pytest.fail(f"{manager_name} was called unexpectedly.")
    #     return job_state
    # mock_run_manager.side_effect = side_effect
    # from coordinator import main as run_coordinator_pipeline # SUT
    # final_job = run_coordinator_pipeline(basic_job_input.model_copy())
    # assert mock_run_manager.call_count == 2
    # assert final_job.status == StatusEnum.REPORT_GENERATED
    # # Report summary check depends on Reporter's behavior with this job state
    # # assert "Bad MD" in final_job.final_user_report_summary
    pass

@pytest.mark.level2
def test_pipeline_miner_tex_fail_investigator_finds_leads_oracle_gives_remedy_reporter_runs(mock_run_manager, basic_job_input):
    """Full pipeline: Miner TeX fail -> Investigator finds leads -> Oracle gives remedy -> Reporter."""
    # miner_output = basic_job_input.model_copy(update={'status': StatusEnum.MINER_TEX_TO_PDF_FAILED, 'log_file_paths': ['dummy.log']})
    # investigator_output = miner_output.model_copy(
    #     update={'status': StatusEnum.INVESTIGATOR_LEADS_FOUND,
    #             'leads': [ActionableLead(lead_id="L01", lead_type=LeadTypeEnum.LATEX_ERROR, description="TeX error")]}
    # )
    # oracle_output = investigator_output.model_copy(
    #     update={'status': StatusEnum.ORACLE_REMEDIES_GENERATED,
    #             'remedies': [MarkdownRemedy(associated_lead_id="L01", description="Fix it")]}
    # )
    # reporter_output = oracle_output.model_copy(update={'status': StatusEnum.REPORT_GENERATED, 'final_user_report_summary': 'Full Error Report'})

    # call_order_log = []
    # def side_effect(manager_name, job_state):
    #     call_order_log.append(manager_name)
    #     if manager_name == "Miner.py": return miner_output
    #     if manager_name == "Investigator.py": return investigator_output
    #     if manager_name == "Oracle.py": return oracle_output
    #     if manager_name == "Reporter.py": return reporter_output
    #     pytest.fail(f"Unknown manager {manager_name} called.")
    # mock_run_manager.side_effect = side_effect

    # from coordinator import main as run_coordinator_pipeline # SUT
    # final_job = run_coordinator_pipeline(basic_job_input.model_copy())
    #
    # assert call_order_log == ["Miner.py", "Investigator.py", "Oracle.py", "Reporter.py"]
    # assert mock_run_manager.call_count == 4
    # # Check arguments for each call
    # # calls = mock_run_manager.call_args_list
    # # assert calls[0] == call("Miner.py", basic_job_input.model_copy()) # Initial job copy
    # # assert calls[1] == call("Investigator.py", miner_output)
    # # assert calls[2] == call("Oracle.py", investigator_output)
    # # assert calls[3] == call("Reporter.py", oracle_output)
    # assert final_job.status == StatusEnum.REPORT_GENERATED
    # # assert "TeX error" in final_job.final_user_report_summary
    # # assert "Fix it" in final_job.final_user_report_summary
    pass

def test_pipeline_investigator_finds_no_leads_oracle_skipped(mock_run_manager, basic_job_input):
    """Pipeline: Miner TeX fail -> Investigator no leads -> Oracle skipped -> Reporter."""
    # miner_output = basic_job_input.model_copy(update={'status': StatusEnum.MINER_TEX_TO_PDF_FAILED, 'log_file_paths': ['dummy.log']})
    # investigator_output_no_leads = miner_output.model_copy(update={'status': StatusEnum.INVESTIGATOR_NO_LEADS_FOUND, 'leads': []})
    # reporter_output = investigator_output_no_leads.model_copy(update={'status': StatusEnum.REPORT_GENERATED, 'final_user_report_summary': 'No specific leads found report'})

    # call_order_log = []
    # def side_effect(manager_name, job_state):
    #     call_order_log.append(manager_name)
    #     if manager_name == "Miner.py": return miner_output
    #     if manager_name == "Investigator.py": return investigator_output_no_leads
    #     if manager_name == "Reporter.py": return reporter_output
    #     if manager_name == "Oracle.py": pytest.fail("Oracle called when Investigator found no leads.")
    # mock_run_manager.side_effect = side_effect

    # from coordinator import main as run_coordinator_pipeline # SUT
    # final_job = run_coordinator_pipeline(basic_job_input.model_copy())
    # assert call_order_log == ["Miner.py", "Investigator.py", "Reporter.py"]
    # assert mock_run_manager.call_count == 3
    # # assert final_job.final_user_report_summary == 'No specific leads found report'
    pass

def test_pipeline_oracle_finds_no_remedies(mock_run_manager, basic_job_input):
    """Pipeline: ... -> Investigator finds leads -> Oracle no remedies -> Reporter."""
    # miner_output = basic_job_input.model_copy(update={'status': StatusEnum.MINER_TEX_TO_PDF_FAILED, 'log_file_paths': ['dummy.log']})
    # investigator_output = miner_output.model_copy(
    #     update={'status': StatusEnum.INVESTIGATOR_LEADS_FOUND,
    #             'leads': [ActionableLead(lead_id="L01", lead_type=LeadTypeEnum.LATEX_ERROR, description="TeX error")]}
    # )
    # oracle_output_no_remedies = investigator_output.model_copy(update={'status': StatusEnum.ORACLE_NO_REMEDIES_FOUND, 'remedies': []})
    # reporter_output = oracle_output_no_remedies.model_copy(update={'status': StatusEnum.REPORT_GENERATED, 'final_user_report_summary': 'Report with leads but no remedies'})

    # def side_effect(manager_name, job_state):
    #     if manager_name == "Miner.py": return miner_output
    #     if manager_name == "Investigator.py": return investigator_output
    #     if manager_name == "Oracle.py": return oracle_output_no_remedies
    #     if manager_name == "Reporter.py": return reporter_output
    # mock_run_manager.side_effect = side_effect

    # from coordinator import main as run_coordinator_pipeline # SUT
    # final_job = run_coordinator_pipeline(basic_job_input.model_copy())
    # assert mock_run_manager.call_count == 4
    # # assert "TeX error" in final_job.final_user_report_summary
    # # assert "No remedy suggestion available" in final_job.final_user_report_summary
    pass

def test_pipeline_manager_failure_coordinator_handles_gracefully(mock_run_manager, basic_job_input):
    """Test how Coordinator handles a manager (e.g. Miner) raising an exception via run_manager."""
    # reporter_output_on_error = basic_job_input.model_copy(
    #     status=StatusEnum.REPORT_GENERATED,
    #     final_user_report_summary="System error during Miner.py"
    # )
    # def side_effect_miner_crash(manager_name, job_state):
    #     if manager_name == "Miner.py":
    #         raise Exception("Miner Crashed!")
    #     if manager_name == "Reporter.py": # Reporter should still be called
    #         # The job_state passed to Reporter should reflect the error
    #         assert job_state.status == StatusEnum.ERROR
    #         assert "Miner Crashed!" in job_state.leads[0].description # Example error lead
    #         return reporter_output_on_error
    #     pytest.fail(f"Unexpected manager {manager_name} called after crash.")
    # mock_run_manager.side_effect = side_effect_miner_crash

    # from coordinator import main as run_coordinator_pipeline # SUT
    # final_job = run_coordinator_pipeline(basic_job_input.model_copy())
    #
    # assert final_job.status == StatusEnum.REPORT_GENERATED # Reporter still generates a report
    # assert "System error during Miner.py" in final_job.final_user_report_summary
    # assert mock_run_manager.call_count == 2 # Miner (failed), Reporter
    pass

def test_intake_to_coordinator_flow(basic_job_input, mocker):
    """Test interaction between intake.py creating a job and coordinator.py processing it."""
    # mock_coordinator_main = mocker.patch('coordinator.main')
    # # Mock open for intake's file reading
    # mock_builtin_open = mocker.patch('builtins.open', mock_open(read_data=basic_job_input.original_markdown_content))
    #
    # import intake # SUT (intake.py)
    # intake.main(["dummy_file.md"])
    #
    # mock_coordinator_main.assert_called_once()
    # called_job_arg = mock_coordinator_main.call_args[0][0]
    # assert isinstance(called_job_arg, DiagnosticJob)
    # assert called_job_arg.original_markdown_content == basic_job_input.original_markdown_content
    # assert called_job_arg.file_path == "dummy_file.md"
    pass

def test_coordinator_with_real_miner_mock_others(basic_job_input, mocker):
    """Test Coordinator with a more 'real' Miner (less mocking) and other managers mocked."""
    # This is complex. It means `run_manager` for Miner.py would actually execute Miner.py.
    # Requires Miner.py to be executable and its dependencies (like pandoc) available.
    # For now, this is a placeholder for a more involved integration test.
    pass

def test_data_consistency_through_pipeline(mock_run_manager, basic_job_input):
    """Ensure core data like original_markdown_content, job_id are preserved through all stages."""
    # original_job_id = basic_job_input.job_id
    # original_md = basic_job_input.original_markdown_content
    #
    # # Simulate a full successful run for this check
    # miner_out = basic_job_input.model_copy(update={'status': StatusEnum.COMPILATION_SUCCESS})
    # reporter_out = miner_out.model_copy(update={'status': StatusEnum.REPORT_GENERATED})
    #
    # def side_effect(manager_name, job_state):
    #     assert job_state.job_id == original_job_id
    #     assert job_state.original_markdown_content == original_md
    #     if manager_name == "Miner.py": return miner_out
    #     if manager_name == "Reporter.py": return reporter_out
    #     # Should not call others in this success scenario
    #     if manager_name in ["Investigator.py", "Oracle.py"]: pytest.fail("Unexpected call")
    #     return job_state
    # mock_run_manager.side_effect = side_effect
    #
    # from coordinator import main as run_coordinator_pipeline # SUT
    # run_coordinator_pipeline(basic_job_input.model_copy())
    # assert mock_run_manager.call_count == 2
    pass

def test_pipeline_oracle_bypass_integration(mock_run_manager, basic_job_input, mocker):
    """Integration test for HACKATHON_MODE Oracle bypass."""
    # mocker.patch('os.environ.get', side_effect=lambda key, default=None: 'true' if key == 'HACKATHON_MODE' else default)
    #
    # miner_output = basic_job_input.model_copy(update={'status': StatusEnum.MINER_TEX_TO_PDF_FAILED})
    # investigator_output = miner_output.model_copy(update={'status': StatusEnum.INVESTIGATOR_LEADS_FOUND, 'leads': [MagicMock()]})
    # reporter_output = investigator_output.model_copy(update={'status': StatusEnum.REPORT_GENERATED})

    # call_log = []
    # def side_effect(manager_name, job_state):
    #     call_log.append(manager_name)
    #     if manager_name == "Miner.py": return miner_output
    #     if manager_name == "Investigator.py": return investigator_output
    #     if manager_name == "Reporter.py": return reporter_output
    #     if manager_name == "Oracle.py": pytest.fail("Oracle called during HACKATHON_MODE bypass integration test")
    # mock_run_manager.side_effect = side_effect
    #
    # from coordinator import main as run_coordinator_pipeline # SUT
    # run_coordinator_pipeline(basic_job_input.model_copy())
    # assert "Oracle.py" not in call_log
    # assert call_log == ["Miner.py", "Investigator.py", "Reporter.py"]
    pass

def test_pipeline_handles_job_already_in_error_state_at_start(mock_run_manager, basic_job_input):
    """If Coordinator receives a job already marked with a general error."""
    # basic_job_input.status = StatusEnum.ERROR
    # basic_job_input.leads.append(ActionableLead(description="Initial system error"))
    # reporter_output = basic_job_input.model_copy(update={'status':StatusEnum.REPORT_GENERATED, 'final_user_report_summary':'Report for initial error'})

    # def side_effect(manager_name, job_state):
    #    if manager_name == "Reporter.py": return reporter_output
    #    pytest.fail(f"Manager {manager_name} called when job started in error state.")
    # mock_run_manager.side_effect = side_effect

    # from coordinator import main as run_coordinator_pipeline # SUT
    # final_job = run_coordinator_pipeline(basic_job_input)

    # assert mock_run_manager.call_count == 1
    # mock_run_manager.assert_called_once_with("Reporter.py", basic_job_input)
    # assert final_job.final_user_report_summary == 'Report for initial error'
    pass

# ~11 integration stubs
