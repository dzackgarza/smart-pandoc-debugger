#!/usr/bin/env python3
"""
Protect roadmap files from being modified.
"""

import subprocess
import sys

ROADMAP_FILES = [
    "docs/roadmap/V0.0.md",
    "docs/roadmap/V1.0.md",
    "docs/roadmap/V2.0.md",
    "docs/roadmap/V99.md",
    "docs/roadmap/README.md",
]


def main():
    """Check if any roadmap files are staged for commit."""
    try:
        # Get staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True
        )
        staged_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Check for staged roadmap files
        staged_roadmap_files = [f for f in staged_files if f in ROADMAP_FILES]

        if staged_roadmap_files:
            print("❌ ERROR: Attempting to modify protected roadmap files:")
            for f in staged_roadmap_files:
                print(f"  - {f}")
            print("")
            print("The roadmap files are frozen and should not be modified directly.")
            print("If you need to update the roadmap, please discuss with the team first.")
            print("")
            print("To unstage these files, run:")
            print(f"  git reset -- {' '.join(staged_roadmap_files)}")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"Error checking staged files: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
