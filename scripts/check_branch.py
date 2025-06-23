#!/usr/bin/env python3
"""
Check branch name and test status before allowing commits.
"""
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        # First check if we're in a git repository
        check_git = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True
        )
        
        if check_git.returncode != 0:
            print("ℹ️  Not in a Git repository. Skipping branch checks.")
            return ""
            
        # Get the current branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting current branch: {e}", file=sys.stderr)
        print(f"Command output: {e.output}")
        print(f"Command stderr: {e.stderr}")
        return ""

def check_branch_name(branch_name: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Check if branch name follows the required pattern.
    
    Returns:
        Tuple of (is_valid, error_message, branch_number)
    """
    # Pattern for feature branches: feature/branchN-description or branchN/description
    pattern = r'^(feature/)?(branch(\d+)(?:[-_/].*)?|(\d+)[-_/].*)$'
    match = re.match(pattern, branch_name, re.IGNORECASE)
    
    if not match:
        return False, "❌ Branch name must be in format 'branchN-description' or 'feature/branchN-description' where N is the branch number", None
    
    # Extract branch number from either group 3 or 4 of the regex
    branch_num = match.group(3) or match.group(4)
    if not branch_num:
        return False, "❌ Could not determine branch number from branch name", None
    
    return True, None, int(branch_num)

def run_branch_tests(branch_num: int) -> bool:
    """Run tests for the specified branch number."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Get the path to the main module
    main_module = project_root / "src" / "smart_pandoc_debugger" / "main.py"
    
    if not main_module.exists():
        print(f"❌ Error: Could not find main module at {main_module}")
        return False
    
    print(f"\n🔍 Running tests for branch {branch_num}...")
    
    try:
        # Run the test using the Python module directly
        result = subprocess.run(
            [sys.executable, str(main_module), "test-v1", str(branch_num)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        # Print the test output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            print(f"\n❌ Tests failed for branch {branch_num} (exit code: {result.returncode})")
            return False
            
        print(f"\n✅ All tests passed for branch {branch_num}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running tests: {e}", file=sys.stderr)
        if e.output:
            print(f"Command output: {e.output}")
        if e.stderr:
            print(f"Command stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error running tests: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def main():
    # Get current branch
    branch_name = get_current_branch()
    
    # If not in a Git repository, exit successfully
    if not branch_name:
        print("ℹ️  Not in a Git repository. Exiting...")
        sys.exit(0)
    
    # Skip checks for main/master branches
    if branch_name in ["main", "master"]:
        print("ℹ️  Skipping checks for main/master branch")
        sys.exit(0)
    
    print(f"🔍 Checking branch: {branch_name}")
    
    # Check branch name
    is_valid, error_msg, branch_num = check_branch_name(branch_name)
    if not is_valid:
        print(error_msg, file=sys.stderr)
        print("\nBranch name must follow one of these patterns:")
        print("  - branchN-description")
        print("  - feature/branchN-description")
        print("  - N-description")
        print("  - feature/N-description")
        print("\nWhere N is the branch number from the V1.0 roadmap")
        print("\nExample: branch1-special-chars or feature/2-math-validation")
        sys.exit(1)
    
    print(f"✅ Branch name is valid (branch {branch_num})")
    
    # Run tests for this branch
    print(f"\n🚀 Running tests for branch {branch_num}...")
    if not run_branch_tests(branch_num):
        print(f"\n❌ Commit aborted: Tests failed for branch {branch_num}")
        print("Please fix the test failures before committing.")
        sys.exit(1)
    
    print("\n✨ All checks passed! You can now commit your changes.")
    sys.exit(0)

if __name__ == "__main__":
    main()
