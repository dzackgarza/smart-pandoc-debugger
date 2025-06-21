#!/usr/bin/env bash
# test2.sh - SDE V5.1.3 Test Suite - HACKATHON MODE
#
# HACKATHON MODE: Short-circuited tests with milestone checkpoints
#
# Usage: 
#   ./test2.sh                     # Run all tests
#   ./test2.sh MILESTONE_1        # Run specific milestone test
#   DEBUG=true ./test2.sh         # With verbose SDE logs

# Always run in hackathon mode by default
RUN_HACKATHON_TESTS=1
RUN_ORIGINAL_TESTS=0

# Check for --original flag
if [[ "$1" == "--original" ]]; then
    RUN_HACKATHON_TESTS=0
    RUN_ORIGINAL_TESTS=1
fi


# Determine SCRIPT_DIR and PROJECT_ROOT relative to this test.sh script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}" # Assuming test.sh is at the project root

# Path to the main SDE entry point
# Assumes 'smart-pandoc-debugger' is in the system PATH
SDE_EXECUTABLE="smart-pandoc-debugger" # <<< --- THIS IS THE CHANGE ---

# --- Helper to run a single SDE invocation ---
# $1: Test Name
# $2: Input Markdown string
# $3: Brief description of what this test targets
run_sde_test() {
    local test_name="$1"
    local input_md="$2"
    local description="$3"

    echo -e "\n\n--- TEST: ${test_name} ---"
    echo -e "Description: ${description}"
    echo -e "Input Markdown:\n${input_md}"
    echo -e "--------------------------------------------------"

    local sde_command_output
    sde_command_output=$(printf '%s' "${input_md}" | "${SDE_EXECUTABLE}" 2>&1)
    local sde_exit_status=$?

    echo -e "SDE Output (stdout & stderr, exit status: ${sde_exit_status}):"
    echo "${sde_command_output}" | sed 's/^/  /'
    echo -e "--- END TEST: ${test_name} ---\n"

    if echo "${sde_command_output}" | grep -E -q "CRITICAL|AssertionError|Traceback (most recent call last)"; then
        echo -e "\033[0;31mPOTENTIAL ISSUE DETECTED IN ABOVE TEST (CRITICAL/Assertion/Traceback found).\033[0m"
    elif [[ ${sde_exit_status} -ne 0 && "${description}" == *"should succeed"* ]]; then
        echo -e "\033[0;31mPOTENTIAL ISSUE: Test expected success but SDE exited non-zero (${sde_exit_status}).\033[0m"
    elif [[ ${sde_exit_status} -eq 0 && "${description}" == *"should fail"* && "${sde_command_output}" != *"CompilationSuccess"* ]]; then
        if echo "${sde_command_output}" | grep -q "NoActionableLeadsFound_ManualReview"; then
             echo -e "\033[0;33mNOTE: Test expected failure, SDE reported 'NoActionableLeadsFound' (exit 0).\033[0m"
        elif echo "${sde_command_output}" | grep -qE "MarkdownError_RemediesProvided|TexCompilationError_RemediesProvided"; then
            echo -e "\033[0;32mNOTE: Test expected failure, SDE reported specific errors (exit 0).\033[0m"
        else
            echo -e "\033[0;33mPOTENTIAL ISSUE: Test expected failure, SDE exited 0 but outcome unclear.\033[0m"
        fi
    fi
}

# --- Milestone Test Function ---
run_milestone_test() {
    local milestone_id="$1"
    local test_name="$2"
    local input_md="$3"
    local description="$4"
    local expected_outcome="$5"
    
    echo -e "\n\n=== MILESTONE ${milestone_id}: ${test_name} ==="
    echo -e "Description: ${description}"
    echo -e "Input Markdown:\n${input_md}"
    echo -e "--------------------------------------------------"
    
    local sde_command_output
    sde_command_output=$(printf '%s' "${input_md}" | "${SDE_EXECUTABLE}" 2>&1)
    local sde_exit_status=$?
    
    echo -e "SDE Output (exit status: ${sde_exit_status}):"
    echo "${sde_command_output}" | head -n 20  # Show first 20 lines only
    
    if echo "${sde_command_output}" | grep -q "${expected_outcome}"; then
        echo -e "\n✅ MILESTONE ${milestone_id} PASSED: Found '${expected_outcome}'"
        return 0
    else
        echo -e "\n❌ MILESTONE ${milestone_id} FAILED: Expected '${expected_outcome}' not found"
        return 1
    fi
}

# --- Test Suite ---

echo "======================================================================"
echo "🚀 SDE Test Suite - HACKATHON MODE"
echo "Target SDE Entry Point: ${SDE_EXECUTABLE}"
echo "DEBUG mode: ${DEBUG:-false}"
echo "MODE: ${RUN_ORIGINAL_TESTS:+ORIGINAL TESTS}${RUN_HACKATHON_TESTS:+HACKATHON TESTS}"
echo "======================================================================"

# --- Milestone Tests ---

# Milestone 1: Basic Pipeline
run_milestone_test "1" "Basic Pipeline" \
    "# Hello World" \
    "Basic markdown should process without errors" \
    "CompilationSuccess_PDFShouldBeValid"

# Milestone 2: Undefined Command
run_milestone_test "2" "Undefined Command" \
    "# Test\n\n\$\\nonexistentcommand\$" \
    "Should detect undefined LaTeX command" \
    "Undefined control sequence"

# Milestone 3: Mismatched Delimiters
run_milestone_test "3" "Mismatched Delimiters" \
    "# Test\n\n\$\$ \\left( \\frac{a}{b} \\right] \$\$" \
    "Should detect mismatched LaTeX delimiters" \
    "Mismatched delimiters"

echo -e "\n======================================================================"
echo "✅ TEST SESSION COMPLETE"
echo "Review the milestone results above."
echo "======================================================================" 