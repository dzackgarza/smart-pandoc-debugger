import io
import sys
import os
from contextlib import redirect_stdout, redirect_stderr

# Import the main function from the alternative debugger
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pandoc_smart_debugger_alternative import run_pandoc_analysis_pipe

# Define the test cases with their markdown content and target output format
test_cases = {
    "Test Case 1: Malformed Markdown Snippet (Unclosed code string)": {
        "content": '# Heading\n\n- List Item\n  Not a list item\n```python\nprint(\'hello)\n```\n',
        "format": "markdown"
    },
    "Test Case 2: LaTeX Error (Missing Brace)": {
        "content": '\\documentclass{article}\\begin{document}Hello\\end{document} Missing brace: \\section{',
        "format": "pdf"
    },
    "Test Case 3: Valid Markdown Document (Successful Conversion)": {
        "content": '# My Sample Document\n\nThis is a generic markdown document.\n\n## Section 1\nThis is the first section.\n\n## Section 2\nThis is the second section.\n\n- Item 1\n- Item 2\n- Item 3\n\n```python\nprint("Hello world!")\n```\n\n**Bold text** and *italic text*.\n\n[Link to Google](https://www.google.com)\n',
        "format": "html"
    },
    "Test Case 4: Unknown Pandoc Error (Invalid YAML Metadata)": {
        "content": '---\nmetadata: {invalid: ]}\n---\n# Test\n',
        "format": "markdown"
    },
    "Test Case 5: Unreadable Image Link": {
        "content": '![Broken Image](file:///path/to/nonexistent/image.png)\n',
        "format": "markdown"
    },
    "Test Case 6: Malformed Custom Filter Call": {
        "content": '---\nfilters: [non-existent-filter]\n---\n# Doc\n',
        "format": "markdown"
    },
    "Test Case 7: LaTeX Document with Unicode Issues": {
        "content": '\\documentclass{article}\\usepackage[utf8]{inputenc}\\begin{document}Grüße\\end{document}\n',
        "format": "pdf"
    },
    "Test Case 8: Complex Table Syntax": {
        "content": '| Header 1 | Header 2 |\n|---|---|\n| Cell 1 | Cell 2\n',
        "format": "markdown"
    },
    "Test Case 9: Template-Related Issue": {
        "content": '---\ntemplate: bad-template.html\n---\nHello\n',
        "format": "html"
    },
}

print("--- Starting Automated Test Suite for pandoc-smart-debugger-alternative.py ---")
print("----------------------------------------------------------------------------")

for test_name, test_data in test_cases.items():
    print(f"\n===== Running {test_name} =====", file=sys.stderr) # Use stderr for test progress
    
    # Create string buffers for stdout and stderr capture
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Redirect stdout and stderr
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        try:
            # Call the main analysis function from the script
            # Note: This assumes run_pandoc_analysis_pipe is defined in this scope
            run_pandoc_analysis_pipe(test_data["content"], test_data["format"])
        except Exception as e:
            # Catch unexpected Python errors from the script itself (e.g., FileNotFoundError for pandoc)
            print(f"!!! Script crashed during {test_name}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)

    # Print captured stdout (the report)
    report_output = stdout_capture.getvalue()
    if report_output:
        print(f"\n--- Output Report for {test_name} (stdout) ---")
        print(report_output.strip())
    else:
        print(f"\n--- No Report Output (stdout) for {test_name} (Expected for clean success) ---")
    
    # Print captured stderr (operational messages from script/Pandoc)
    operational_messages = stderr_capture.getvalue()
    if operational_messages:
        print(f"\n--- Operational Messages for {test_name} (stderr) ---")
        print(operational_messages.strip())
    
    print(f"===== Finished {test_name} =====\n", file=sys.stderr) # Use stderr for test progress

print("\n--- Automated Test Suite Completed ---")
print("--------------------------------------")
