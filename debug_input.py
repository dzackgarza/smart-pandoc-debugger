import re

test_input = r"""
! Undefined control sequence.
l.5 \begin{testenv}
                   
The control sequence at the end of the top line
of your error message was never \def'ed. If you have
misspelled it (e.g., `\hobx'), type `I' and the correct
spelling (e.g., `I\hbox'). Otherwise just continue,
and I'll forget about whatever was undefined.
"""

print(f"Test input: {test_input!r}")

# Try a very simple pattern
pattern = r'l\.(\d+)\\s*\\begin\{(\w+)\}'
match = re.search(pattern, test_input)
print(f"Pattern: {pattern}")
print(f"Match: {match}")
if match:
    print(f"Groups: {match.groups()}")
    print(f"Line number: {match.group(1)}")
    print(f"Environment: {match.group(2)}")
