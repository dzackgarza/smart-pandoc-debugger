import sys
import json
from smart_pandoc_debugger.data_model import DiagnosticJob, PipelineStatus # Import PipelineStatus

def main():
    if "--process-job" in sys.argv:
        try:
            raw_job = sys.stdin.read()
            if not raw_job:
                # Handle empty stdin if necessary, perhaps output an error or default job
                # For testing purposes, let's assume an empty job is an error for the runner tests
                # or output a job with an error status.
                # However, run_manager expects a DiagnosticJob back.
                # Let's just pass through a default job if input is empty.
                # This scenario should ideally be tested by the test calling run_manager,
                # not by the dummy script itself failing due to empty input.
                # For now, let's assume valid JSON DiagnosticJob is always passed.
                pass # Fall through to json.loads, which will fail on empty string.

            diagnostic_job_dict = json.loads(raw_job)
            # Simulate some processing: change status or add a history item
            # Use a valid status from PipelineStatus enum
            diagnostic_job_dict["status"] = PipelineStatus.ORACLE_ANALYSIS_COMPLETE.value
            diagnostic_job_dict.setdefault("history", []).append("Processed by dummy_manager.py")

            # Ensure it's still a valid DiagnosticJob by parsing before output
            # This helps catch if the dummy script itself makes it invalid
            DiagnosticJob(**diagnostic_job_dict)

            print(json.dumps(diagnostic_job_dict))
            sys.exit(0)
        except json.JSONDecodeError:
            print("Error: Invalid JSON input to dummy_manager.py", file=sys.stderr)
            sys.exit(2) # Exit code for input error
        except Exception as e:
            print(f"Error in dummy_manager.py: {e}", file=sys.stderr)
            sys.exit(1) # General processing error
    else:
        # If --process-job is not provided, perhaps print help or just exit
        print("dummy_manager.py: --process-job flag not provided.", file=sys.stderr)
        sys.exit(3) # Specific exit code for missing flag

if __name__ == "__main__":
    main()
