#!/usr/bin/env bash
# h1_tests.sh - SDE Hackathon 1 Test Suite
#
# Tests for tasks 6-10 as defined in FAST-TODO.md.
#
# Usage: ./h1_tests.sh         # Run all H1 tests
#        ./h1_tests.sh 6 8     # Run tests 6 and 8
#        DEBUG=1 ./h1_tests.sh # Run with debug output

# --- CONFIGURATION ---
SDE_EXECUTABLE="smart-pandoc-debugger"
FAIL_FAST=${FAIL_FAST:-0}

# --- Test Runner ---
run_test() {
    local test_num="$1"
    local test_name=""
    local input_md=""
    local expected_outcome=""
    
    case "$test_num" in
        6) test_name="Runaway Argument"
           input_md="# Test\n\n\$\\frac{1{1 + e^{-x}}\$"
           expected_outcome="Runaway argument" ;;
        7) test_name="Undefined Environment"
           input_md="# Test\n\n\\begin{nonexistent_env}\ncontent\n\\end{nonexistent_env}"
           expected_outcome="Environment nonexistent_env undefined" ;;
        8) test_name="Missing End Environment"
           input_md="# Test\n\n\\begin{align*}\na &= b + c \\\\\nd &= e + f"
           expected_outcome="ended before \\end{align*} was complete" ;;
        9) test_name="Math Mode in Text"
           input_md="# Test\n\nThis \$should not be in math mode"
           expected_outcome="Missing \\$ inserted" ;;
        10) test_name="Multiple Errors"
            input_md="# Test\n\n\$f(x) = \\frac{1}{1 + e^{-x}}\$\n\$\\nonexistentcommand\$"
            expected_outcome="Unbalanced braces" # We expect it to find the *first* error
            ;;
        *) echo "ERROR: Invalid test number: $test_num" >&2; return 2 ;;
    esac
    
    echo -e "\n=== H1 TEST ${test_num}: ${test_name} ==="
    echo -e "Input Markdown:\n${input_md}"
    echo -e "--------------------------------------------------"
    
    local output
    output=$(printf '%s' "${input_md}" | "${SDE_EXECUTABLE}" 2>&1)
    
    if [[ "${DEBUG:-0}" == "1" ]]; then
        echo -e "SDE Output (Full):"
        echo "${output}" | sed 's/^/  /'
    fi
    
    if echo "${output}" | grep -q "${expected_outcome}"; then
        echo -e "✅ H1 TEST ${test_num} PASSED: Found '${expected_outcome}'"
        return 0
    else
        echo -e "❌ H1 TEST ${test_num} FAILED: Expected '${expected_outcome}' not found in output:"
        echo "${output}" | head -n 20 | sed 's/^/  /'
        return 1
    fi
}

# --- Main Logic ---
main() {
    if ! command -v "${SDE_EXECUTABLE}" >/dev/null 2>&1; then
        echo -e "\033[0;31mERROR: SDE executable '${SDE_EXECUTABLE}' not found in PATH.\033[0m" >&2
        exit 1
    fi
    
    local tests_to_run=()
    local failed_tests=()
    
    if [[ $# -eq 0 ]]; then
        tests_to_run=(6 7 8 9 10)
    else
        tests_to_run=("$@")
    fi
    
    echo "🚀 Running Hackathon 1 Test Suite (Tasks 6-10)..."
    
    for test_num in "${tests_to_run[@]}"; do
        if ! run_test "$test_num"; then
            failed_tests+=("$test_num")
            if [[ "$FAIL_FAST" -eq 1 ]]; then
                break
            fi
        fi
    done
    
    echo -e "\n\n=== H1 SUMMARY ==="
    if [[ ${#failed_tests[@]} -eq 0 ]]; then
        echo -e "\033[0;32m✅ ALL H1 TESTS PASSED\033[0m"
        return 0
    else
        echo -e "\033[0;31m❌ FAILED H1 TESTS: ${failed_tests[*]}\033[0m"
        return 1
    fi
}

main "$@" 