#!/usr/bin/env python3
"""
Prevent imports from alternative-debugger in the main codebase.
"""

import subprocess
import sys


def main():
    """Check for imports from alternative-debugger in staged files."""
    try:
        # Get staged Python files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
        )
        staged_files = (
            [f for f in result.stdout.strip().split("\n") if f.endswith(".py")]
            if result.stdout.strip()
            else []
        )

        # Check each file for alternative-debugger imports
        problematic_files = []
        for filename in staged_files:
            try:
                with open(filename, "r") as f:
                    content = f.read()
                    if (
                        "alternative-debugger" in content or "alternative_debugger" in content
                    ) and "check-alternative-imports" not in filename:
                        problematic_files.append(filename)
            except FileNotFoundError:
                continue  # File was deleted

        if problematic_files:
            print("❌ ERROR: Found import from alternative-debugger in staged files!")
            for f in problematic_files:
                print(f"  - {f}")
            print("")
            print(
                "The alternative-debugger must remain completely separate from the main codebase."
            )
            print("")
            print("To unstage these changes, run:")
            print(f"  git reset -- {' '.join(problematic_files)}")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"Error checking staged files: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
