#!/usr/bin/env python3
"""
Smart Pandoc Debugger - Dead Simple CLI Interface

Usage:
    spd doc.md              # Process file and output report to stdout
    cat doc.md | spd        # Process stdin and output report to stdout  
    spd test                # Run internal tiered tests (dev command)
    spd test-doc doc.md     # Test/analyze a document
    spd respond-to-pr [PR_NUMBER]     # Help respond to PR comments (for LLMs)
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Optional
import argparse

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def colorize(text: str, color: str) -> str:
    """Add color to text if stdout is a terminal."""
    if sys.stdout.isatty():
        return f"{color}{text}{RESET}"
    return text


def process_document(input_file: Optional[str] = None) -> int:
    """Process a markdown document and output diagnostic report.
    
    Args:
        input_file: Path to markdown file. If None, reads from stdin.
        
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    try:
        # For now, output a simple placeholder report
        # TODO: Integrate with actual diagnostic pipeline
        
        if input_file:
            if not Path(input_file).exists():
                print(f"Error: File '{input_file}' not found", file=sys.stderr)
                return 1
            
            content = Path(input_file).read_text(encoding='utf-8')
            print(f"📄 Analyzing: {input_file}")
        else:
            # Read from stdin
            content = sys.stdin.read()
            print("📄 Analyzing stdin input")
        
        # Simple analysis placeholder
        print()
        print("🔍 DIAGNOSTIC REPORT")
        print("=" * 50)
        
        # Basic checks
        lines = content.split('\n')
        word_count = len(content.split())
        
        print(f"📊 Document Stats:")
        print(f"   • Lines: {len(lines)}")
        print(f"   • Words: {word_count}")
        print(f"   • Characters: {len(content)}")
        print()
        
        # Check for common issues
        issues = []
        
        if '$' in content and content.count('$') % 2 != 0:
            issues.append("❌ Unmatched dollar signs (potential math mode issue)")
            
        if '\\begin{' in content:
            begin_count = content.count('\\begin{')
            end_count = content.count('\\end{')
            if begin_count != end_count:
                issues.append(f"❌ Unmatched LaTeX environments ({begin_count} begins, {end_count} ends)")
        
        if '{' in content:
            open_count = content.count('{')
            close_count = content.count('}')
            if open_count != close_count:
                issues.append(f"❌ Unmatched braces ({open_count} open, {close_count} close)")
        
        if issues:
            print("🚨 Issues Found:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("✅ No obvious issues detected")
        
        print()
        print("💡 For detailed analysis, the full diagnostic pipeline is under development.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        return 1


def test_document(input_file: str) -> int:
    """Test/analyze a document with detailed output.
    
    Args:
        input_file: Path to markdown file to test.
        
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    try:
        if not Path(input_file).exists():
            print(f"❌ Error: File '{input_file}' not found", file=sys.stderr)
            return 1
        
        content = Path(input_file).read_text(encoding='utf-8')
        print(f"🧪 Testing Document: {input_file}")
        print("=" * 50)
        
        # More detailed analysis for testing
        lines = content.split('\n')
        word_count = len(content.split())
        
        # Test results tracking
        tests_passed = 0
        tests_total = 0
        
        print(f"📊 Document Analysis:")
        print(f"   • File size: {len(content)} characters")
        print(f"   • Line count: {len(lines)}")
        print(f"   • Word count: {word_count}")
        print()
        
        # Test 1: Dollar sign matching
        tests_total += 1
        dollar_count = content.count('$')
        if dollar_count == 0:
            print("✅ Math delimiters: No math found")
            tests_passed += 1
        elif dollar_count % 2 == 0:
            print(f"✅ Math delimiters: {dollar_count//2} pairs matched")
            tests_passed += 1
        else:
            print(f"❌ Math delimiters: Unmatched $ (total: {dollar_count})")
        
        # Test 2: LaTeX environment matching
        tests_total += 1
        begin_count = content.count('\\begin{')
        end_count = content.count('\\end{')
        if begin_count == 0 and end_count == 0:
            print("✅ LaTeX environments: None found")
            tests_passed += 1
        elif begin_count == end_count:
            print(f"✅ LaTeX environments: {begin_count} pairs matched")
            tests_passed += 1
        else:
            print(f"❌ LaTeX environments: Unmatched ({begin_count} begins, {end_count} ends)")
        
        # Test 3: Brace matching
        tests_total += 1
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces == close_braces:
            print(f"✅ Brace matching: {open_braces} pairs matched")
            tests_passed += 1
        else:
            print(f"❌ Brace matching: Unmatched ({open_braces} open, {close_braces} close)")
        
        # Test 4: Basic markdown structure
        tests_total += 1
        has_headers = any(line.strip().startswith('#') for line in lines)
        if has_headers:
            print("✅ Document structure: Headers found")
            tests_passed += 1
        else:
            print("⚠️  Document structure: No headers detected")
        
        print()
        print("=" * 50)
        
        # Summary
        percentage = (tests_passed / tests_total) * 100 if tests_total > 0 else 0
        if tests_passed == tests_total:
            color = GREEN
            status = "PASSED"
        else:
            color = RED  
            status = "FAILED"
        
        print(f"📋 Test Results: {colorize(f'{tests_passed}/{tests_total} ({percentage:.0f}%) - {status}', color)}")
        
        return 0 if tests_passed == tests_total else 1
        
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        return 1


def run_tiered_tests() -> int:
    """Run internal tests in tiers, only proceeding if previous tier passes 100%.
    
    Returns:
        int: Exit code (0 if all tiers pass, non-zero otherwise)
    """
    print("🧪 Running Internal Tiered Tests")
    print("=" * 50)
    
    # Define test tiers
    tiers = [
        {
            'name': 'Tier 1: Core Data Models',
            'pattern': 'tests/unit/utils/test_data_model.py',
            'description': 'Basic data structure validation'
        },
        {
            'name': 'Tier 2: User Expectations',
            'pattern': 'tests/unit/user_expectations/',
            'description': 'Functionality users expect (development roadmap)'
        },
        {
            'name': 'Tier 3: Manager Units', 
            'pattern': 'tests/unit/managers/',
            'description': 'Individual manager functionality'
        },
        {
            'name': 'Tier 4: Integration',
            'pattern': 'tests/integration/',
            'description': 'Cross-component integration'
        },
        {
            'name': 'Tier 5: End-to-End',
            'pattern': 'tests/e2e/',
            'description': 'Full pipeline testing'
        }
    ]
    
    overall_success = True
    failed_tier = None
    
    def get_tier_test_count(pattern):
        """Get the total number of tests for a tier pattern."""
        try:
            cmd = ['python', '-m', 'pytest', pattern, '--collect-only', '-q', '--cov-report=', '--cov-config=/dev/null']
            result = subprocess.run(cmd, capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            # Look for line like "N tests collected" or "N items collected"
            import re
            for line in lines:
                if 'collected' in line:
                    # Try different formats: "20 tests collected", "20 items collected"
                    match = re.search(r'(\d+)\s+(?:tests?|items?)\s+collected', line)
                    if match:
                        return int(match.group(1))
                    # Also try "collected N items"
                    match = re.search(r'collected\s+(\d+)\s+(?:tests?|items?)', line)
                    if match:
                        return int(match.group(1))
            return 1  # Default fallback
        except Exception:
            return 1  # Default fallback
    
    for i, tier in enumerate(tiers, 1):
        print(f"\n🔄 {tier['name']}")
        print(f"   {tier['description']}")
        
        # If a previous tier failed, show this tier as not reached
        if failed_tier is not None:
            total = get_tier_test_count(tier['pattern'])
            status_text = f"❌ 0/{total}, 0%"
            print(f"   {colorize(status_text, RED)}")
            continue
        
        try:
            # Run pytest for this tier with coverage files in temp directory
            import tempfile
            import os
            temp_dir = tempfile.mkdtemp(prefix='spd_coverage_')
            coverage_file = os.path.join(temp_dir, '.coverage')
            
            cmd = ['python', '-m', 'pytest', tier['pattern'], '-v', '--tb=short', '--disable-warnings', 
                   f'--cov-report=', f'--cov-config=/dev/null', f'--cov-append', f'--cov-fail-under=0']
            
            # Set coverage data file location via environment
            env = os.environ.copy()
            env['COVERAGE_FILE'] = coverage_file
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            # Clean up temp coverage directory
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass  # Ignore cleanup errors
            
            # Parse results - look for the summary line
            lines = result.stdout.split('\n')
            summary_line = None
            for line in lines:
                if '=' in line and ('passed' in line or 'failed' in line):
                    summary_line = line.strip()
                    break
            
            if summary_line:
                # Extract passed/total from summary
                # Handle formats like: "48 passed, 1 warning" or "5 failed, 3 passed"
                import re
                
                # Extract numbers followed by "passed" and "failed"
                passed_match = re.search(r'(\d+)\s+passed', summary_line)
                failed_match = re.search(r'(\d+)\s+failed', summary_line)
                error_match = re.search(r'(\d+)\s+error', summary_line)
                
                passed = int(passed_match.group(1)) if passed_match else 0
                failed = int(failed_match.group(1)) if failed_match else 0
                errors = int(error_match.group(1)) if error_match else 0
                
                total = passed + failed + errors
                percentage = round((passed / total * 100)) if total > 0 else 0
                success = (failed == 0 and errors == 0)
            else:
                # No clear summary, check return code
                success = result.returncode == 0
                passed = 1 if success else 0
                total = 1
                percentage = 100 if success else 0
            
            # Display results
            if success and percentage == 100:
                status_color = GREEN
                status_text = f"✅ {passed}/{total}, {percentage}%"
            else:
                status_color = RED
                status_text = f"❌ {passed}/{total}, {percentage}%"
                overall_success = False
                failed_tier = i
            
            print(f"   {colorize(status_text, status_color)}")
            
            # If this tier failed, mark it but continue to show remaining tiers
            if not success or percentage != 100:
                if result.stderr and 'coverage' not in result.stderr.lower():
                    print(f"\nError output:\n{result.stderr}")
                
        except Exception as e:
            print(f"   {colorize(f'❌ Error running tests: {e}', RED)}")
            overall_success = False
            failed_tier = i
    
    print(f"\n{'='*50}")
    if overall_success:
        print(colorize("🎉 All tiers passed!", GREEN))
        print(colorize("✓ You can now commit your changes and submit a PR!", GREEN))
        return 0
    else:
        print(colorize(f"❌ Failed at tier {failed_tier}", RED))
        # Special message if only Tier 1 passed
        if failed_tier == 2:
            print(colorize("✓ Tier 1 passed! You can commit your changes and submit a PR.", GREEN))
        return 1


def run_pr_response_helper() -> int:
    """
    Run the PR response helper to assist LLMs in responding to reviewer comments.
    
    This command implements the exact protocol described in CONTRIBUTING.md
    for responding to Codepilot and other reviewer comments with proper backlinks.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        import subprocess
        import sys
        import os
        
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        helper_script = os.path.join(project_root, "utils", "pr_response_helper.py")
        
        if not os.path.exists(helper_script):
            print("❌ Error: PR response helper script not found.")
            print(f"Expected at: {helper_script}")
            return 1
        
        # Pass through all command line arguments except the 'respond-to-pr' command
        args = sys.argv[2:]  # Skip 'spd' and 'respond-to-pr'
        cmd = [sys.executable, helper_script] + args
        
        # Run the helper script
        result = subprocess.run(cmd)
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running PR response helper: {e}")
        return 1


def main():
    """Main entry point for the Smart Pandoc Debugger CLI."""
    parser = argparse.ArgumentParser(
        description="Smart Pandoc Debugger: Analyze and fix Pandoc markdown documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  spd document.md                    # Analyze a markdown file
  echo "# Test" | spd               # Process stdin
  spd test-doc                      # Run tiered tests
  spd respond-to-pr [PR_NUMBER]     # Help respond to PR comments (for LLMs)

For more help: https://github.com/dzackgarza/smart-pandoc-debugger
        """
    )
    
    parser.add_argument('command', nargs='?', default='analyze',
                       help='Command to run: analyze (default), test-doc, or respond-to-pr')
    parser.add_argument('target', nargs='?', 
                       help='Target file for analysis or PR number for respond-to-pr')
    parser.add_argument('--version', action='version', version='Smart Pandoc Debugger v0.1.0')
    
    # Handle case where no arguments are provided
    if len(sys.argv) == 1:
        parser.print_help()
        return 1
    
    args, unknown = parser.parse_known_args()
    
    if args.command == 'test-doc':
        return run_tiered_tests()
    elif args.command == 'respond-to-pr':
        return run_pr_response_helper()
    elif args.command == 'analyze' or args.target:
        # Handle both 'spd analyze file.md' and 'spd file.md'
        target_file = args.target if args.target else args.command
        if target_file == 'analyze':
            # stdin mode: spd analyze
            return process_document()
        else:
            # file mode: spd file.md or spd analyze file.md
            return process_document(target_file)
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
