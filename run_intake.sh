#!/usr/bin/env bash

# Wrapper script to call intake.py and pipe stdin to it.

# Ensure intake.py is executable or python3 is used
if [[ ! -f intake.py ]]; then
  echo "Error: intake.py not found in the current directory." >&2
  exit 1
fi

# Capture all stdin and pipe it to intake.py
exec python3 intake.py
