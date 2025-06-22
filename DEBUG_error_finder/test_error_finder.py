#!/usr/bin/env python3

import sys
import json
import os

def run_test(test_name, log_content, tex_content, expected_signature):
    print(f"\n=== {test_name} ===")
    
    # Write test files
    with open("test.log", "w") as f:
        f.write(log_content)
    with open("test.tex", "w") as f:
        f.write(tex_content)
    
    # Run error_finder.py
    cmd = f"python3 managers/investigator-team/error_finder.py --log-file test.log --tex-file test.tex"
    result = os.popen(cmd).read()
    
    try:
        result_data = json.loads(result)
        print("Result:", json.dumps(result_data, indent=2))
        
        if result_data.get("error_signature") == expected_signature:
            print("✅ Test passed")
            return True
        else:
            print(f"❌ Test failed: Expected {expected_signature}, got {result_data.get('error_signature')}")
            return False
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON output:")
        print(result)
        return False

# Test 1: Missing dollar sign
test1_log = """This is a test log
! Missing $ inserted.
<inserted text> 
                $
<to be read again> 
                   \\ 
l.27 \\end{align}
               
? 
"""
test1_tex = """\documentclass{article}
\begin{document}
Some math: a = b + c
\end{document}"""

# Test 2: Unbalanced braces
test2_log = """This is a test log
! Extra }, or forgotten $.
<inserted text> 
                }
<to be read again> 
                   \\ 
l.27 \\end{align}
               
? 
"""
test2_tex = """\documentclass{article}
\begin{document}
Some math: $f(x) = \\frac{1}{1 + e^{-x}}}$
\end{document}"""

# Test 3: Successful compilation
test3_log = """This is a test log
Output written on test.pdf (1 page, 12345 bytes).
Transcript written on test.log.
"""
test3_tex = """\documentclass{article}
\begin{document}
Hello, world!
\end{document}"""

# Run tests
passed = 0
total = 0

print("Running tests...")

if run_test("Missing Dollar Sign", test1_log, test1_tex, "LATEX_MISSING_DOLLAR"):
    passed += 1
total += 1

if run_test("Unbalanced Braces", test2_log, test2_tex, "LATEX_UNBALANCED_BRACES"):
    passed += 1
total += 1

if run_test("Successful Compilation", test3_log, test3_tex, "LATEX_NO_ERROR_MESSAGE_IDENTIFIED"):
    passed += 1
total += 1

print(f"\nSummary: {passed}/{total} tests passed")
