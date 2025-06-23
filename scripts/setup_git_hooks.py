#!/usr/bin/env python3
"""
Set up Git hooks for the repository.
"""
import os
import shutil
import stat
import sys
from pathlib import Path

def setup_pre_commit_hook():
    """Set up the pre-commit hook."""
    # Paths
    repo_root = Path(__file__).parent.parent
    hooks_dir = repo_root / ".git" / "hooks"
    pre_commit_path = hooks_dir / "pre-commit"
    check_branch_script = repo_root / "scripts" / "check_branch.py"
    
    # Create hooks directory if it doesn't exist
    hooks_dir.mkdir(exist_ok=True, parents=True)
    
    # Get the absolute path to the Python interpreter
    python_path = sys.executable
    
    # Create the pre-commit hook
    with open(pre_commit_path, 'w') as f:
        f.write("#!/bin/sh\n")
        f.write("# Auto-generated pre-commit hook\n")
        f.write("# This hook ensures branch naming conventions and runs tests before commit\n\n")
        f.write(f"{python_path} {check_branch_script.absolute()}")
    
    # Make the hook executable
    pre_commit_path.chmod(0o755)  # rwxr-xr-x
    
    print(f"✅ Pre-commit hook installed at {pre_commit_path}")
    print(f"   Using Python: {python_path}")
    print(f"   Checking with: {check_branch_script.absolute()}")

def main():
    """Main function."""
    if not (Path(__file__).parent.parent / ".git").exists():
        print("❌ Error: This script must be run from the root of a Git repository.")
        sys.exit(1)
    
    setup_pre_commit_hook()
    print("\n🎉 Git hooks have been set up successfully!")
    print("The pre-commit hook will now check branch names and run tests before each commit.")

if __name__ == "__main__":
    main()
