#!/usr/bin/env bash
# smart-pandoc-debugger inspector.sh — Quality Inspector: PDF validation agent
#
# Version: 1.0
# Date: 2025-06-20
# Author: Diagnostic Systems Group
#
# ────────────────────────────────────────────────────────────────────────────────
# Role Overview — The QUALITY INSPECTOR
#
#   Invoked by the Coordinator to validate final PDF output.
#   Ensures the generated PDF is non-empty and readable.
#
#   Responsibilities:
#     • Check that $PDFOUT exists
#     • Verify that it contains extractable text (i.e. not blank or corrupt)
#
#   May be extended to perform metadata validation, size checks, or page count.
#
# ────────────────────────────────────────────────────────────────────────────────
# Interface Contract with Coordinator
#
#   coordinator.sh invokes:
#     "$INSPECTOR_BIN" check_pdf_valid
#
#   Required environment variable:
#     PDFOUT : Path to the expected PDF output file
#
#   Output:
#     - stdout only
#     - No output on success
#     - No color or formatting codes
#
#   Exit codes:
#     0 - PDF is valid and non-empty
#     1 - PDF is missing or empty
#     2 - CLI misuse (unknown command or missing env var)
#
# ────────────────────────────────────────────────────────────────────────────────

set -eo pipefail

check_pdf_valid() {
  if [[ -z "$PDFOUT" ]]; then
    echo "Error: PDFOUT environment variable is not set." >&2
    exit 2
  fi

  if [[ ! -f "$PDFOUT" ]]; then
    exit 1
  fi

  # Check for non-empty visible content using pdftotext
  if ! pdftotext "$PDFOUT" - | grep -q '[^[:space:]]'; then
    exit 1
  fi

  exit 0
}

# Entrypoint
case "${1:-}" in
  check_pdf_valid)
    check_pdf_valid
    ;;
  *)
    echo "Usage: $0 check_pdf_valid" >&2
    exit 2
    ;;
esac

