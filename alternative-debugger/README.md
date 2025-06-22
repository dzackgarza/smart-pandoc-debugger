# Alternative Debugger

**IMPORTANT**: This is an alternative implementation that must remain completely separate from the main codebase. It should not be imported by or integrated with any other part of the project.

## Purpose

This directory contains an independent implementation of a Pandoc debugger with its own test suite. It serves as a reference implementation and testing ground for alternative approaches to document debugging.

## Files

- `pandoc-smart-debugger-alternative.py`: The main implementation file
- `test-alternative.py`: Test cases for the alternative implementation
- `README.md`: This file

## Running Tests

To run the tests:

```bash
cd /path/to/alternative-debugger
python test-alternative.py
```

## Isolation

This implementation is intentionally kept separate from the main codebase to:

1. Allow for experimentation without affecting the main code
2. Provide a reference implementation for comparison
3. Enable testing of alternative approaches

Do not import or reference this code from any other part of the project.
