#!/usr/bin/env python3
"""
Check file size limits to enforce modular code architecture.
"""

import argparse
import sys
from pathlib import Path


def count_code_lines(filename):
    """Count actual code lines (excluding comments and blank lines)."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        code_lines = 0
        in_multiline_string = False

        for line in lines:
            stripped = line.strip()

            # Skip blank lines
            if not stripped:
                continue

            # Skip comment lines (simple heuristic)
            if stripped.startswith("#"):
                continue

            # Simple multiline string detection
            if '"""' in stripped or "'''" in stripped:
                triple_quote_count = stripped.count('"""') + stripped.count("'''")
                if triple_quote_count % 2 == 1:
                    in_multiline_string = not in_multiline_string
                # Count line if it has code besides the quotes
                if not in_multiline_string and any(
                    c not in " \t\"'#" for c in stripped.replace('"""', "").replace("'''", "")
                ):
                    code_lines += 1
            elif not in_multiline_string:
                code_lines += 1

        return code_lines

    except Exception:
        # If anything fails, fall back to total line count (conservative)
        try:
            with open(filename, "r") as f:
                return len(f.readlines())
        except OSError:
            return 0


def main():
    """Check file size limits for Python files."""
    parser = argparse.ArgumentParser(description="Check file size limits")
    parser.add_argument("--max-total-lines", type=int, default=300)
    parser.add_argument("--max-code-lines", type=int, default=200)
    parser.add_argument("files", nargs="*", help="Files to check")

    args = parser.parse_args()

    oversized_files = []

    for filename in args.files:
        if not Path(filename).exists():
            continue

        try:
            with open(filename, "r") as f:
                total_lines = len(f.readlines())
        except OSError:
            continue

        code_lines = count_code_lines(filename)

        # Check limits
        if total_lines > args.max_total_lines or code_lines > args.max_code_lines:
            oversized_files.append((filename, code_lines, total_lines))

    if oversized_files:
        print("❌ Files exceed size limits! Enforce modular design:")
        for filename, code_lines, total_lines in oversized_files:
            print(f"📄 {filename}: {code_lines} code lines ({total_lines} total)")
        print("")
        print("💡 Size limits (to enforce modularity):")
        print(f"   - Maximum {args.max_total_lines} total lines per file")
        print(
            f"   - Maximum {args.max_code_lines} actual code lines (excluding comments/docstrings)"
        )
        print("")
        print("🔧 Refactoring suggestions:")
        print("   - Split large classes into smaller, focused classes")
        print("   - Extract helper functions into separate utility modules")
        print("   - Move related functions into dedicated modules")
        print("   - Consider using composition over large inheritance hierarchies")
        sys.exit(1)
    else:
        print("✅ All files within size limits (good modular design!)")


if __name__ == "__main__":
    main()
