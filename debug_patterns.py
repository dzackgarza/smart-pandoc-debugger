import re

test_input = """
! Undefined control sequence.
l.5 \begin{testenv}
                   
The control sequence at the end of the top line
of your error message was never \def'ed. If you have
misspelled it (e.g., `\hobx'), type `I' and the correct
spelling (e.g., `I\hbox'). Otherwise just continue,
and I'll forget about whatever was undefined.
"""

print(f"Test input: {test_input!r}")

# Try different patterns
patterns = [
    r'l\.(\d+)\\s*\\begin\{(\w+)\}',
    r'l\.(\d+)\\s*\\\\begin\{(\w+)\}',
    r'l\\.(\\d+)\\\\s*\\\\begin\{(\\w+)\}',
    r'l\\.(\\d+)\\\s*\\\\begin\{(\\w+)\}',
    r'l\\.(\\d+)[\\\\s]*\\\\begin\{(\\w+)\}',
    r'l\\.(\\d+)\\\\s*\\\\begin\{(\\w+)\}',
]

for i, pattern in enumerate(patterns, 1):
    print(f"\nPattern {i}: {pattern}")
    try:
        match = re.search(pattern, test_input, re.DOTALL)
        print(f"  Match: {match}")
        if match:
            print(f"  Groups: {match.groups()}")
    except Exception as e:
        print(f"  Error: {e}")

# Print the raw bytes to see exactly what we're dealing with
print("\nRaw bytes:")
for i, c in enumerate(test_input):
    print(f"{i:2d}: {ord(c):3d} {c!r}")
