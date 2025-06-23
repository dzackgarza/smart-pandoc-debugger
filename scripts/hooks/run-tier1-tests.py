#!/usr/bin/env python3
"""
Run Tier 1 (MVP) tests before allowing commits.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Run tier 1 tests and block commit if they fail."""
    # Change to repository root
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)

    # Check if this is a docs-only commit
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True
        )
        staged_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # If only docs files are changed, skip tests
        docs_only = all(
            f.endswith((".md", ".txt", ".rst")) or f.startswith("docs/") for f in staged_files if f
        )

        if docs_only:
            print("📝 Documentation-only commit detected - skipping test execution")
            print("✅ Commit approved for documentation changes")
            return

    except subprocess.CalledProcessError:
        pass  # Continue with tests if we can't determine file types

    print("🔍 Running Tier 1 (MVP) tests before commit...")
    print("━" * 60)

    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)

    # Try to activate virtual environment if available
    venv_paths = [repo_root / ".venv" / "bin" / "activate", repo_root / "venv" / "bin" / "activate"]

    for venv_path in venv_paths:
        if venv_path.exists():
            print(f"📦 Using virtual environment: {venv_path.parent.parent}")
            break

    # Run tier 1 tests
    try:
        print("🧪 Running Tier 1 tests...")
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/unit/test_error_finder_consolidated.py",
                "-m",
                "tier1",
                "-v",
                "--tb=short",
            ],
            cwd=repo_root,
            env=env,
            check=False,
        )

        if result.returncode == 0:
            print("━" * 60)
            print("✅ All Tier 1 tests passed! Commit allowed.")
            print("")
            print("📋 REMINDER: Reviewer Response Protocol")
            print("━" * 60)
            print("When addressing PR reviewer comments:")
            print("")
            print("🤖 IDIOT-PROOF METHOD (Recommended for LLMs):")
            print("   spd respond-to-pr [PR_NUMBER]")
            print("   ↳ Automatically generates correct backlink response!")
            print("")
            print("✅ Manual Method: Create ONE comprehensive response with backlinks")
            print("❌ DON'T: Try to reply to individual comment threads")
            print("")
            print("📖 Full protocol: See CONTRIBUTING.md → 'Handling Reviewer Comments'")
            print("━" * 60)
        else:
            print("━" * 60)
            print("❌ Tier 1 tests failed! Commit blocked.")
            print("")
            print("🛠️  Fix the failing Tier 1 (MVP) tests before committing:")
            print("   - test_undefined_control_sequence")
            print("   - test_missing_dollar")
            print("   - test_unbalanced_braces")
            print("")
            print("💡 Run tests manually with:")
            print("   pytest tests/unit/test_error_finder_consolidated.py -m tier1 -v")
            print("━" * 60)
            sys.exit(1)

    except FileNotFoundError:
        print("❌ Error: pytest not found. Please install test dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()
