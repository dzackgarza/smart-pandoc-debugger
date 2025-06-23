import re

test_input = """
! Undefined control sequence.
l.5 \begin{testenv}
                   
The control sequence at the end of the to...and the correct
spelling (e.g., `I\hbox'). Otherwise just continue,
and I'll forget about whatever was undefined.
"""

# Try different patterns
patterns = [
    r'! Undefined control sequence\..*?l\.(\d+)\\s*\\begin\{(\w+)\}',
    r'! Undefined control sequence\..*?l\.(\d+)\\s*\\\\begin\{(\w+)\}',
    r'! Undefined control sequence\..*?l\.(\d+)\\s*\\begin\{(\w+)\}',
    r'! Undefined control sequence\..*?l\.(\d+)\\s*\\\\begin\{(\w+)\}',
    r'l\.(\d+)\\s*\\begin\{(\w+)\}',
    r'l\.(\d+)\\s*\\\\begin\{(\w+)\}',
]

for i, pattern in enumerate(patterns, 1):
    print(f"\nPattern {i}: {pattern}")
    try:
        match = re.search(pattern, test_input, re.DOTALL)
        if match:
            print(f"  Match found! Groups: {match.groups()}")
            print(f"  Line number: {match.group(1)}")
            print(f"  Environment: {match.group(2)}")
        else:
            print("  No match")
    except Exception as e:
        print(f"  Error: {e}")
