# tests/unit/scripts/test_coordinator.py
import pytest
from unittest.mock import patch, MagicMock, call
from smart_pandoc_debugger.data_model import DiagnosticJob, StatusEnum, ActionableLead, LeadTypeEnum, MarkdownRemedy, UrgencyEnum, SourceContextSnippet
# import coordinator # Assuming coordinator.py is in src/smart_pandoc_debugger

# Test importability
def test_coordinator_module_importable():
    """Test if coordinator.py can be imported as a module."""
    # import smart_pandoc_debugger.Coordinator as coordinator # SUT
    # assert coordinator is not None
    pass

@pytest.fixture
def initial_diagnostic_job():
    """A fresh DiagnosticJob as if from intake.py."""
    # Assuming DiagnosticJob needs original_markdown_path now
    return DiagnosticJob(case_id="coord_test_job_01", original_markdown_content="# Test Content", original_markdown_path="dummy.md")

@pytest.fixture
def mock_manager_runner(mocker):
    """Mocks the relevant run_manager function used by coordinator."""
    return mocker.patch('smart_pandoc_debugger.Coordinator.run_manager', create=True)

def test_coordinator_runs_miner_first(mock_manager_runner, initial_diagnostic_job):
    """Test that Miner.py is the first manager called."""
    # mock_manager_runner.return_value = initial_diagnostic_job.model_copy()
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # current_job = initial_diagnostic_job.model_copy()
    # run_coordinator_pipeline(current_job)
    # mock_manager_runner.assert_any_call('Miner.py', current_job)
    # if mock_manager_runner.call_args_list:
    #    assert mock_manager_runner.call_args_list[0].args[0] == 'Miner.py'
    pass

def test_coordinator_runs_investigator_if_miner_fails_tex_compilation(mock_manager_runner, initial_diagnostic_job):
    """Test Investigator.py is called if Miner indicates TeX-to-PDF failure."""
    # current_job = initial_diagnostic_job.model_copy()
    # miner_output_job = current_job.model_copy(
    #     update={
    #         'final_job_outcome': StatusEnum.MINER_TEX_TO_PDF_FAILED.value,
    #         'md_to_tex_conversion_successful': True,
    #         'tex_to_pdf_compilation_successful': False,
    #         'current_pipeline_stage': StatusEnum.MINER_PROCESSING.value
    #         }
    # )
    # investigator_output_job = miner_output_job.model_copy(update={'final_job_outcome': StatusEnum.INVESTIGATOR_LEADS_FOUND.value, 'current_pipeline_stage': StatusEnum.INVESTIGATOR_PROCESSING.value})
    # reporter_output_job = investigator_output_job.model_copy(update={'final_job_outcome': StatusEnum.REPORT_GENERATED.value, 'current_pipeline_stage': StatusEnum.REPORTER_PROCESSING.value})

    # def manager_runner_side_effect(manager_script, job_input):
    #     if manager_script == 'Miner.py': return miner_output_job
    #     if manager_script == 'Investigator.py': return investigator_output_job
    #     if manager_script == 'Oracle.py': return investigator_output_job # Oracle might run
    #     if manager_script == 'Reporter.py': return reporter_output_job
    #     return job_input
    # mock_manager_runner.side_effect = manager_runner_side_effect
    #
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # run_coordinator_pipeline(current_job)
    #
    # mock_manager_runner.assert_any_call('Miner.py', current_job)
    # mock_manager_runner.assert_any_call('Investigator.py', miner_output_job)
    pass

def test_coordinator_skips_investigator_if_miner_succeeds_or_md_fails(mock_manager_runner, initial_diagnostic_job):
    """Test Investigator is skipped if Miner succeeds or fails only at MD conversion."""
    # for outcome_status_val, md_success, tex_success in [
    #     (StatusEnum.COMPILATION_SUCCESS.value, True, True),
    #     (StatusEnum.MINER_MD_TO_TEX_FAILED.value, False, False)
    # ]:
    #     mock_manager_runner.reset_mock()
    #     current_job_state = initial_diagnostic_job.model_copy()

    #     miner_output_job = current_job_state.model_copy(
    #         update={
    #             'final_job_outcome': outcome_status_val,
    #             'md_to_tex_conversion_successful': md_success,
    #             'tex_to_pdf_compilation_successful': tex_success,
    #             'current_pipeline_stage': StatusEnum.MINER_PROCESSING.value
    #         }
    #     )
    #     reporter_input_job = miner_output_job
    #     reporter_output_job = reporter_input_job.model_copy(update={'final_job_outcome': StatusEnum.REPORT_GENERATED.value, 'current_pipeline_stage': StatusEnum.REPORTER_PROCESSING.value})

    #     def side_effect(manager_script, job_input):
    #         if manager_script == 'Miner.py': return miner_output_job
    #         if manager_script == 'Reporter.py': return reporter_output_job
    #         if manager_script in ['Investigator.py', 'Oracle.py']:
    #             pytest.fail(f"{manager_script} was called unexpectedly for outcome {outcome_status_val}")
    #         return job_input
    #     mock_manager_runner.side_effect = side_effect
    #
    #     from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    #     run_coordinator_pipeline(current_job_state)
    #
    #     investigator_called = any(c.args[0] == 'Investigator.py' for c in mock_manager_runner.call_args_list)
    #     assert not investigator_called
    #     oracle_called = any(c.args[0] == 'Oracle.py' for c in mock_manager_runner.call_args_list)
    #     assert not oracle_called
    pass

def test_coordinator_runs_oracle_if_leads_exist_and_not_success(mock_manager_runner, initial_diagnostic_job):
    """Test Oracle.py is called if leads are present and compilation wasn't a full success."""
    # current_job = initial_diagnostic_job.model_copy()
    # miner_job = current_job.model_copy(update={'final_job_outcome': StatusEnum.MINER_TEX_TO_PDF_FAILED.value, 'md_to_tex_conversion_successful': True, 'tex_to_pdf_compilation_successful': False, 'current_pipeline_stage': StatusEnum.MINER_PROCESSING.value})
    # investigator_job = miner_job.model_copy(
    #     update={'final_job_outcome': StatusEnum.INVESTIGATOR_LEADS_FOUND.value,
    #             'actionable_leads': [ActionableLead(lead_type=LeadTypeEnum.LATEX_ERROR, problem_description="Err", source_service="Investigator", lead_id="L01")],
    #             'current_pipeline_stage': StatusEnum.INVESTIGATOR_PROCESSING.value
    #            }
    # )
    # oracle_job = investigator_job.model_copy(update={'final_job_outcome': StatusEnum.ORACLE_REMEDIES_GENERATED.value, 'current_pipeline_stage': StatusEnum.ORACLE_PROCESSING.value})
    # reporter_job = oracle_job.model_copy(update={'final_job_outcome': StatusEnum.REPORT_GENERATED.value, 'current_pipeline_stage': StatusEnum.REPORTER_PROCESSING.value})

    # def side_effect(manager_script, job_input):
    #     if manager_script == 'Miner.py': return miner_job
    #     if manager_script == 'Investigator.py': return investigator_job
    #     if manager_script == 'Oracle.py': return oracle_job
    #     if manager_script == 'Reporter.py': return reporter_job
    #     return job_input
    # mock_manager_runner.side_effect = side_effect
    #
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # run_coordinator_pipeline(current_job)
    # mock_manager_runner.assert_any_call('Oracle.py', investigator_job)
    pass

def test_coordinator_skips_oracle_if_no_leads(mock_manager_runner, initial_diagnostic_job):
    """Test Oracle.py is skipped if there are no leads."""
    # current_job = initial_diagnostic_job.model_copy()
    # miner_job = current_job.model_copy(update={'final_job_outcome': StatusEnum.MINER_TEX_TO_PDF_FAILED.value, 'md_to_tex_conversion_successful':True, 'tex_to_pdf_compilation_successful': False, 'current_pipeline_stage': StatusEnum.MINER_PROCESSING.value})
    # investigator_job_no_leads = miner_job.model_copy(update={'final_job_outcome': StatusEnum.INVESTIGATOR_NO_LEADS_FOUND.value, 'actionable_leads': [], 'current_pipeline_stage': StatusEnum.INVESTIGATOR_PROCESSING.value})
    # reporter_job = investigator_job_no_leads.model_copy(update={'final_job_outcome': StatusEnum.REPORT_GENERATED.value, 'current_pipeline_stage': StatusEnum.REPORTER_PROCESSING.value})

    # def side_effect(manager_script, job_input):
    #     if manager_script == 'Miner.py': return miner_job
    #     if manager_script == 'Investigator.py': return investigator_job_no_leads
    #     if manager_script == 'Reporter.py': return reporter_job
    #     if manager_script == 'Oracle.py': pytest.fail("Oracle called when no leads present")
    #     return job_input
    # mock_manager_runner.side_effect = side_effect
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # run_coordinator_pipeline(current_job)
    # oracle_called = any(c.args[0] == 'Oracle.py' for c in mock_manager_runner.call_args_list)
    # assert not oracle_called
    pass

def test_coordinator_skips_oracle_if_compilation_succeeded_despite_leads(mock_manager_runner, initial_diagnostic_job):
    """Test Oracle is skipped if compilation succeeded (e.g. only warnings were found)."""
    # current_job = initial_diagnostic_job.model_copy()
    # miner_job_success_with_warnings = current_job.model_copy(
    #     update={
    #         'final_job_outcome': StatusEnum.COMPILATION_SUCCESS.value,
    #         'md_to_tex_conversion_successful': True,
    #         'tex_to_pdf_compilation_successful': True,
    #         'actionable_leads': [ActionableLead(lead_type=LeadTypeEnum.LATEX_WARNING, problem_description="Warn", source_service="Investigator", lead_id="W01")],
    #         'current_pipeline_stage': StatusEnum.MINER_PROCESSING.value
    #     }
    # )
    # reporter_job = miner_job_success_with_warnings.model_copy(update={'final_job_outcome': StatusEnum.REPORT_GENERATED.value, 'current_pipeline_stage': StatusEnum.REPORTER_PROCESSING.value})
    #
    # def side_effect(manager_script, job_input):
    #     if manager_script == 'Miner.py': return miner_job_success_with_warnings
    #     if manager_script == 'Investigator.py':
    #         pytest.fail("Investigator should be skipped on full success from Miner")
    #         return job_input
    #     if manager_script == 'Reporter.py': return reporter_job
    #     if manager_script == 'Oracle.py': pytest.fail("Oracle called on full success")
    #     return job_input
    # mock_manager_runner.side_effect = side_effect
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # run_coordinator_pipeline(current_job)
    # oracle_called = any(c.args[0] == 'Oracle.py' for c in mock_manager_runner.call_args_list)
    # assert not oracle_called
    pass


def test_coordinator_always_runs_reporter(mock_manager_runner, initial_diagnostic_job):
    """Test that Reporter.py is always the final manager called."""
    # current_job = initial_diagnostic_job.model_copy()
    # job_state_before_reporter = current_job.model_copy(update={'final_job_outcome': StatusEnum.ORACLE_REMEDIES_GENERATED.value, 'current_pipeline_stage': StatusEnum.ORACLE_PROCESSING.value})
    # final_reported_job = job_state_before_reporter.model_copy(update={'final_job_outcome': StatusEnum.REPORT_GENERATED.value, 'final_user_report_summary': "Report", 'current_pipeline_stage': StatusEnum.REPORTER_PROCESSING.value})

    # def side_effect(manager_script, job_input):
    #     if manager_script == 'Reporter.py': return final_reported_job
    #     return job_input.model_copy(update={'current_pipeline_stage': StatusEnum.ORACLE_PROCESSING.value, 'final_job_outcome': StatusEnum.ORACLE_REMEDIES_GENERATED.value})
    # mock_manager_runner.side_effect = side_effect
    #
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # final_job = run_coordinator_pipeline(current_job)
    #
    # reporter_call_args = None
    # for call_item in mock_manager_runner.call_args_list:
    #     if call_item.args[0] == 'Reporter.py':
    #         reporter_call_args = call_item
    #         break
    # assert reporter_call_args is not None, "Reporter.py was not called"
    # assert final_job.final_job_outcome == StatusEnum.REPORT_GENERATED.value
    # assert mock_manager_runner.call_args_list[-1].args[0] == 'Reporter.py'
    pass

def test_coordinator_passes_updated_job_between_managers(mock_manager_runner, initial_diagnostic_job):
    """Verify the DiagnosticJob state is correctly passed from one manager to the next."""
    # current_job = initial_diagnostic_job.model_copy()
    # miner_out = current_job.model_copy(update={'current_pipeline_stage': StatusEnum.MINER_PROCESSING.value, 'generated_tex_content': "TeX from Miner", 'md_to_tex_conversion_successful': True, 'tex_to_pdf_compilation_successful': False, 'final_job_outcome': StatusEnum.MINER_TEX_TO_PDF_FAILED.value})
    # invest_out = miner_out.model_copy(update={'current_pipeline_stage': StatusEnum.INVESTIGATOR_PROCESSING.value, 'actionable_leads': [ActionableLead(problem_description="Lead from Invest", source_service="Investigator", lead_type=LeadTypeEnum.LATEX_ERROR, lead_id="L01")] , 'final_job_outcome': StatusEnum.INVESTIGATOR_LEADS_FOUND.value})
    # oracle_out = invest_out.model_copy(update={'current_pipeline_stage': StatusEnum.ORACLE_PROCESSING.value, 'markdown_remedies': [MarkdownRemedy(associated_lead_id="L01", explanation="Fix", instruction_for_markdown_fix="Do this", source_service="Oracle", applies_to_lead_id="L01", remedy_id="R01")] , 'final_job_outcome': StatusEnum.ORACLE_REMEDIES_GENERATED.value})
    # reporter_out = oracle_out.model_copy(update={'final_job_outcome': StatusEnum.REPORT_GENERATED.value, 'current_pipeline_stage': StatusEnum.REPORTER_PROCESSING.value})

    # def side_effect(manager_script, job_input):
    #     if manager_script == 'Miner.py':
    #         assert job_input.current_pipeline_stage == "Initialized" # or initial_diagnostic_job.current_pipeline_stage
    #         return miner_out
    #     if manager_script == 'Investigator.py':
    #         assert job_input.generated_tex_content == "TeX from Miner"
    #         return invest_out
    #     if manager_script == 'Oracle.py':
    #         assert len(job_input.actionable_leads) == 1
    #         return oracle_out
    #     if manager_script == 'Reporter.py':
    #         assert len(job_input.markdown_remedies) == 1
    #         return reporter_out
    #     return job_input
    # mock_manager_runner.side_effect = side_effect
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # run_coordinator_pipeline(current_job)
    pass

def test_coordinator_returns_final_diagnostic_job(mock_manager_runner, initial_diagnostic_job):
    """Test that the coordinator returns the DiagnosticJob after Reporter has run."""
    # current_job = initial_diagnostic_job.model_copy()
    # final_reported_job = current_job.model_copy(update={'final_user_report_summary': "Report text", 'final_job_outcome': StatusEnum.REPORT_GENERATED.value})
    #
    # def side_effect_reporter(manager_script, job_input):
    #     if manager_script == 'Reporter.py':
    #         return final_reported_job
    #     return job_input.model_copy(update={'final_job_outcome': StatusEnum.COMPILATION_SUCCESS.value, 'md_to_tex_conversion_successful':True, 'tex_to_pdf_compilation_successful':True, 'current_pipeline_stage': StatusEnum.ORACLE_PROCESSING.value})
    # mock_manager_runner.side_effect = side_effect_reporter
    #
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # result_job = run_coordinator_pipeline(current_job)
    # assert result_job.final_user_report_summary == "Report text"
    # assert result_job.final_job_outcome == StatusEnum.REPORT_GENERATED.value
    pass

def test_coordinator_handles_manager_runner_exception(mock_manager_runner, initial_diagnostic_job, caplog):
    """Test coordinator's behavior if manager_runner.run_manager raises an exception."""
    # current_job = initial_diagnostic_job.model_copy()
    #
    # def side_effect_crash(manager_script, job_input):
    #     if manager_script == "Miner.py":
    #         raise Exception("Miner Crashed!")
    #     if manager_script == "Reporter.py":
    #         assert job_input.final_job_outcome == StatusEnum.ERROR.value
    #         assert any("Miner Crashed!" in lead.problem_description for lead in job_input.actionable_leads)
    #         return job_input.model_copy(update={'final_user_report_summary': "Report of crash.", 'final_job_outcome': StatusEnum.REPORT_GENERATED.value})
    #     pytest.fail(f"Manager {manager_script} called after Miner crash path was not Reporter")
    #     return job_input
    #
    # mock_manager_runner.side_effect = side_effect_crash
    # import logging
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    #
    # final_job = run_coordinator_pipeline(current_job)
    #
    # assert f"Failed to run Miner.py for job {current_job.case_id}" in caplog.text
    # assert final_job.final_job_outcome == StatusEnum.REPORT_GENERATED.value
    # assert "Report of crash" in final_job.final_user_report_summary
    # called_scripts = [c.args[0] for c in mock_manager_runner.call_args_list]
    # assert called_scripts == ["Miner.py", "Reporter.py"]
    pass

def test_coordinator_logging_of_pipeline_steps(mock_manager_runner, initial_diagnostic_job, caplog):
    """Test that coordinator logs which manager it's about to call."""
    # import logging
    # current_job = initial_diagnostic_job.model_copy()
    # def side_effect_log(manager_script, job_input):
    #     update_data = {'current_pipeline_stage': f"{manager_script}_done"}
    #     if manager_script == "Miner.py":
    #         update_data.update({'final_job_outcome': StatusEnum.MINER_TEX_TO_PDF_FAILED.value, 'md_to_tex_conversion_successful':True, 'tex_to_pdf_compilation_successful':False})
    #     elif manager_script == "Investigator.py":
    #         update_data.update({'final_job_outcome': StatusEnum.INVESTIGATOR_LEADS_FOUND.value, 'actionable_leads': [ActionableLead(problem_description="Test", source_service="Investigator", lead_type=LeadTypeEnum.LATEX_ERROR, lead_id="LTest")]})
    #     elif manager_script == "Oracle.py":
    #          update_data.update({'final_job_outcome': StatusEnum.ORACLE_REMEDIES_GENERATED.value})
    #     elif manager_script == "Reporter.py":
    #         update_data['final_job_outcome'] = StatusEnum.REPORT_GENERATED.value
    #     return job_input.model_copy(update=update_data)
    # mock_manager_runner.side_effect = side_effect_log
    #
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # with caplog.at_level(logging.INFO):
    #    run_coordinator_pipeline(current_job)
    #
    # assert f"Invoking Miner.py for job {initial_diagnostic_job.case_id}" in caplog.text
    # assert f"Invoking Investigator.py for job {initial_diagnostic_job.case_id}" in caplog.text
    # assert f"Invoking Oracle.py for job {initial_diagnostic_job.case_id}" in caplog.text
    # assert f"Invoking Reporter.py for job {initial_diagnostic_job.case_id}" in caplog.text
    pass

def test_coordinator_main_function_entry_point(mock_manager_runner, initial_diagnostic_job):
    """Test the main function if it's the primary entry point used by intake."""
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # run_coordinator_pipeline(initial_diagnostic_job.model_copy())
    # mock_manager_runner.assert_called()
    pass

def test_coordinator_timeout_overall_if_implemented(mock_manager_runner, initial_diagnostic_job):
    """If coordinator has an overall timeout for the entire pipeline."""
    pass

def test_coordinator_oracle_bypass_hackathon_mode(mock_manager_runner, initial_diagnostic_job, mocker):
    """Test HACKATHON_MODE bypass for Oracle as per HACKATHON.md."""
    # mocker.patch('os.environ.get', side_effect=lambda key, default=None: 'true' if key == 'HACKATHON_MODE' else default)
    # current_job = initial_diagnostic_job.model_copy()
    # miner_job = current_job.model_copy(update={'final_job_outcome': StatusEnum.MINER_TEX_TO_PDF_FAILED.value, 'md_to_tex_conversion_successful':True, 'tex_to_pdf_compilation_successful': False, 'current_pipeline_stage': StatusEnum.MINER_PROCESSING.value})
    # investigator_job = miner_job.model_copy(
    #     update={'final_job_outcome': StatusEnum.INVESTIGATOR_LEADS_FOUND.value,
    #             'actionable_leads': [ActionableLead(lead_type=LeadTypeEnum.LATEX_ERROR, problem_description="Err", source_service="Investigator", lead_id="L01")],
    #             'current_pipeline_stage': StatusEnum.INVESTIGATOR_PROCESSING.value
    #             }
    # )
    # reporter_job = investigator_job.model_copy(update={'final_job_outcome': StatusEnum.REPORT_GENERATED.value, 'current_pipeline_stage': StatusEnum.REPORTER_PROCESSING.value})

    # call_log = []
    # def side_effect(manager_script, job_input):
    #     call_log.append(manager_script)
    #     if manager_script == 'Miner.py': return miner_job
    #     if manager_script == 'Investigator.py': return investigator_job
    #     if manager_script == 'Reporter.py': return reporter_job
    #     if manager_script == 'Oracle.py': pytest.fail("Oracle was called in Hackathon mode bypass")
    #     return job_input
    # mock_manager_runner.side_effect = side_effect
    # from smart_pandoc_debugger.Coordinator import main as run_coordinator_pipeline # SUT
    # run_coordinator_pipeline(current_job)
    # assert "Oracle.py" not in call_log
    # assert call_log == ["Miner.py", "Investigator.py", "Reporter.py"]
    pass

# ~15 stubs for coordinator.py
