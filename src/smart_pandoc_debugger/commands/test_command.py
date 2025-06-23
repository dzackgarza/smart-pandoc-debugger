"""
Test command for SPD (Smart Pandoc Debugger)

This module provides commands to check the test status of different branches
as defined in the V1.0 roadmap.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from enum import Enum

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich import box

class TestStatus(Enum):
    """Status of a test."""
    PASSED = "✅"
    FAILED = "❌"
    XFAIL = "⚠️"
    NOT_IMPLEMENTED = "⏳"

# Map of branch keys to test names and their expected status
BRANCH_TESTS = {
    "branch1_text_validation": {
        "test_name": "TestV1RoadmapCompliance.test_branch1_special_chars_escaped",
        "status": "incomplete",
        "description": "Basic text validation (special chars, URLs, etc.)"
    },
    "branch2_math_validation": {
        "test_name": "TestV1RoadmapCompliance.test_branch2_math_mode_validation",
        "status": "complete",
        "description": "Math mode and equation validation"
    },
    "branch3_environment_command_validation": {
        "test_name": "TestV1RoadmapCompliance.test_branch3_environment_validation",
        "status": "partial",
        "description": "Environment and command validation"
    },
    "branch4_code_block_validation": {
        "test_name": "TestV1RoadmapCompliance.test_branch4_code_block_validation",
        "status": "incomplete",
        "description": "Code block and structure validation"
    },
    "branch11_documentation_updates": {
        "test_name": "TestV1RoadmapCompliance.test_branch11_documentation_updates",
        "status": "complete",
        "description": "Documentation and contribution guidelines updates"
    },
    "branch5_references": {
        "test_name": "TestV1RoadmapCompliance.test_branch5_reference_validation",
        "status": "incomplete",
        "description": "References and cross-references"
    },
    "branch6_citations": {
        "test_name": "TestV1RoadmapCompliance.test_branch6_citation_validation",
        "status": "incomplete",
        "description": "Citations and bibliography"
    },
    "branch7_tables": {
        "test_name": "TestV1RoadmapCompliance.test_branch7_table_validation",
        "status": "incomplete",
        "description": "Table and layout validation"
    },
    "branch8_brackets": {
        "test_name": "TestV1RoadmapCompliance.test_branch8_bracket_matching",
        "status": "incomplete",
        "description": "Bracket and delimiter matching"
    },
    "branch9_error_reporting": {
        "test_name": "TestV1RoadmapCompliance.test_branch9_error_reporting",
        "status": "incomplete",
        "description": "Enhanced error reporting and integration"
    },
}

def get_branch_name(branch_key: str) -> str:
    """Convert branch key to display name."""
    names = {
        "branch1_text_validation": "1. Basic Text & Character Validation",
        "branch2_math_validation": "2. Math Mode & Equations",
        "branch3_environment_command_validation": "3. Environment & Command Validation",
        "branch4_code_block_validation": "4. Code Block & Structure Validation",
        "branch5_references": "5. References & Cross-References",
        "branch6_citations": "6. Citations & Bibliography",
        "branch7_tables": "7. Table & Layout Validation",
        "branch8_brackets": "8. Bracket & Delimiter Matching",
        "branch9_error_reporting": "9. Enhanced Error Reporting & Integration",
    }
    return names.get(branch_key, branch_key)

def run_test(test_name: str) -> Tuple[TestStatus, str]:
    """Run a specific test and return its status."""
    try:
        # Construct the full path to the test file - relative to project root
        test_file = project_root / "tests" / "unit" / "test_v1_roadmap_compliance.py"
        if not test_file.exists():
            # Try alternative path (relative to project root)
            test_file = Path("tests/unit/test_v1_roadmap_compliance.py").resolve()
            if not test_file.exists():
                return TestStatus.FAILED, f"Test file not found. Tried:\n- {project_root / 'tests/unit/test_v1_roadmap_compliance.py'}\n- {test_file}"
        
        # Note: Test discovery is handled by pytest directly
            
        # Format the test name for pytest (extract class and method name)
        parts = test_name.split('.')
        if len(parts) >= 2:
            # Format: TestClass.test_method -> TestClass::test_method
            class_name = parts[-2]
            method_name = parts[-1]
            test_path = f"{test_file}::{class_name}::{method_name}"
        else:
            # Fallback to just the method name
            method_name = parts[-1]
            test_path = f"{test_file}::{method_name}"
        
        # Run pytest with the specific test
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_path,
            "-v"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        print(f"Looking for test method: {method_name}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Debug output
        print(f"Test output for {test_name}:")
        print("=" * 50)
        print(result.stdout)
        if result.stderr:
            print("Error:")
            print(result.stderr)
        print("=" * 50)
        
        # Check the output to determine test result
        if "PASSED" in result.stdout or "passed" in result.stdout.lower() or result.returncode == 0:
            return TestStatus.PASSED, ""
        elif "XFAIL" in result.stdout:
            return TestStatus.XFAIL, "Expected failure"
        elif "FAILED" in result.stdout or "failed" in result.stdout.lower() or result.returncode != 0:
            return TestStatus.FAILED, result.stderr or "Test failed"
        else:
            return TestStatus.NOT_IMPLEMENTED, f"Test not found or did not run as expected. Output: {result.stdout[:500]}"
            
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
        return TestStatus.FAILED, error_msg

def get_status_emoji(status: str) -> str:
    """Get emoji for status."""
    return {
        "complete": "✅",
        "partial": "🔄",
        "incomplete": "❌",
    }.get(status, "❓")

def test_v1(console: Optional[Console] = None) -> int:
    """Run tests for V1 roadmap branches and display results.
    
    Args:
        console: Optional rich console instance. If not provided, a new one will be created.
        
    Returns:
        int: Number of failed tests (0 means success)
    """
    if console is None:
        console = Console()
    
    console.print("[bold blue]Smart Pandoc Debugger - V1.0 Roadmap Status[/bold blue]\n")
    
    # Create a table for the results
    table = Table(
        show_header=True, 
        header_style="bold magenta", 
        box=box.ROUNDED,
        show_lines=True
    )
    table.add_column("Branch", style="cyan", width=5, justify="center")
    table.add_column("Feature", style="cyan", width=40)
    table.add_column("Status", width=15, justify="center")
    table.add_column("Details", style="white")
    
    total_branches = len(BRANCH_TESTS)
    completed_branches = 0
    in_progress_branches = 0
    not_started_branches = 0
    
    for branch_key, branch_info in BRANCH_TESTS.items():
        branch_num = branch_key.replace("branch", "").split("_")[0]
        status = branch_info["status"]
        description = branch_info["description"]
        
        # Update counters
        if status == "complete":
            completed_branches += 1
            status_display = f"[green]✅ Complete[/green]"
        elif status == "partial":
            in_progress_branches += 1
            status_display = f"[yellow]🔄 In Progress[/yellow]"
        else:  # incomplete
            not_started_branches += 1
            status_display = f"[red]❌ Not Started[/red]"
        
        # Add row to the table
        table.add_row(
            branch_num,
            description,
            status_display,
            ""  # Empty details for now
        )
    
    # Print the table
    console.print(table)
    
    # Print summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  ✅ [green]Completed: {completed_branches}/{total_branches} branches")
    console.print(f"  🔄 [yellow]In Progress: {in_progress_branches} branches")
    console.print(f"  ❌ [red]Not Started: {not_started_branches} branches")
    
    # Calculate and print progress
    progress = (completed_branches / total_branches) * 100
    console.print(f"\n[bold]Overall Progress:[/bold] {progress:.1f}%")
    
    # Simple progress bar
    console.print("\n[bold]Progress:[/bold]")
    bar_length = 30
    filled_length = int(bar_length * progress / 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    console.print(f"[{bar}] {progress:.1f}%")
    console.print()  # Add a newline for better spacing
    
    # Return 0 if all branches are complete, 1 otherwise
    return 0 if completed_branches == total_branches else 1

def test_branch(branch_number: int, console: Optional[Console] = None) -> int:
    """Run tests for a specific branch.
    
    Args:
        branch_number: Branch number (1-9, 11+ for additional branches)
        console: Optional rich console instance
        
    Returns:
        int: 0 if tests pass, 1 otherwise
    """
    if console is None:
        console = Console()
    
    branch_key = f"branch{branch_number}_"
    matching_branches = [k for k in BRANCH_TESTS.keys() if k.startswith(branch_key)]
    
    if not matching_branches:
        console.print(f"[red]❌ No branch found with number {branch_number}[/red]")
        return 1
    
    branch_key = matching_branches[0]
    test_info = BRANCH_TESTS[branch_key]
    test_name = test_info["test_name"]
    
    console.print(f"[bold blue]Testing {get_branch_name(branch_key)}...[/bold blue]\n")
    
    status, details = run_test(test_name)
    
    if status == TestStatus.PASSED:
        console.print(f"[green]✅ {get_branch_name(branch_key)}: PASSED[/green]")
        return 0
    elif status == TestStatus.XFAIL:
        console.print(f"[yellow]⚠️  {get_branch_name(branch_key)}: EXPECTED FAILURE[/yellow]")
        if details:
            console.print(f"[yellow]Details: {details}[/yellow]")
        return 0
    else:
        console.print(f"[red]❌ {get_branch_name(branch_key)}: FAILED[/red]")
        if details:
            console.print(f"[red]Details: {details}[/red]")
        return 1
