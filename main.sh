#!/usr/bin/env bash
# smart-pandoc-debugger main.sh — orchestrator that hands off to the Coordinator
#
# Roles and Communication:
#
#   - The **user** provides a Markdown document, expecting to know:
#       * whether it builds cleanly to PDF, and
#       * if not, what went wrong and how to fix it.
#
#   - The **main.sh** script acts as the facilitator.
#     It receives input from the user, sets up a clean workspace,
#     and delegates the actual analysis to the **Coordinator** —
#     a human or automated expert who understands LaTeX syntax deeply.
#
#   - The **Coordinator** inspects the document and reports back:
#       * either that the document compiled successfully, or
#       * a diagnostic report identifying what went wrong and where.
#
# What main.sh does:
#   - Accepts Markdown from stdin and writes it to a file
#   - Creates a temporary workspace for the Coordinator to use
#   - Exports a standard set of environment variables describing file paths
#   - Calls the Coordinator’s entry function: `coordinator_collect_reports`
#   - Forwards the Coordinator’s entire message directly to the user (via stdout)
#   - Exits with the Coordinator’s status code (0 or 1)
#
# What the Coordinator must return (Contract):
#
#   Format of stdout response:
#     * Must be a plain UTF-8 string suitable for immediate display to a user
#     * If successful:
#         - The exact string: "PDF generated successfully."
#         - No extra prefix, newline, or formatting
#     * If failed:
#         - A multiline human-readable diagnostic, beginning with an "Error:" line
#         - Must include:
#             - Approximate source line number(s)
#             - Extracts of the user’s input showing the problem
#             - A short explanation of the issue
#             - If possible, a concrete fix or pointer ("Check your delimiters on line 58")
#
#   Format of exit code:
#     * 0 = build succeeded, no errors found
#     * 1 = build failed, diagnostic has been returned
#
# Coordinator Compliance To-Dos:
#   - Ensure diagnostic output is concise, actionable, and consistent
#   - Include "Error:" prefixes for grepping/highlighting
#   - Always show line numbers and relevant code context
#   - Normalize format: header → line → message → code excerpt → hint
#   - Keep output strictly text-only (no ANSI colors or formatting)
#   - Do not write diagnostics to stderr; everything must go to stdout
#
# Notes:
#   - main.sh does not examine the input or error messages at all
#   - It simply acts as a reliable intermediary between the user and Coordinator
#   - The Coordinator may be automated or human — main.sh does not assume
#
# Communication Summary:
#   1. main.sh prepares and exports:
#        - MDFILE: Markdown input
#        - TMPDIR: working directory
#        - TEXFILE: intermediate .tex file
#        - LOGFILE: compilation log
#        - PDFOUT: final output target
#   2. main.sh invokes `coordinator_collect_reports`
#   3. Coordinator responds via stdout and exit code (0 or 1)
#   4. main.sh relays the exact message to the user, and exits accordingly
#
# This interface ensures clarity and separation of roles:
#   - User: author
#   - main.sh: logistician
#   - Coordinator: diagnostician

set -eo pipefail

# Resolve root directory (where this script lives)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COORDINATOR_BIN="$ROOT/coordinator.sh"

# Create temporary workspace and files
tmpdir=$(mktemp -d)
mdfile="$tmpdir/input.md"
pdfout="$tmpdir/output.pdf"
texfile="$tmpdir/input.tex"
logfile="$tmpdir/pdflatex.log"

# Read Markdown from stdin into temp file
cat > "$mdfile"

# Export environment variables for Coordinator and related tools
export TMPDIR="$tmpdir" MDFILE="$mdfile" PDFOUT="$pdfout" TEXFILE="$texfile" LOGFILE="$logfile"

###############
# Main driver
###############
main() {
  # Invoke Coordinator function and relay output directly
  # Exit code forwarded from Coordinator: 0 = success, 1 = failure
  "$COORDINATOR_BIN" coordinator_collect_reports
  exit $?
}

main

