#!/usr/bin/env bash
# miner.sh — Miner role: build runner and lead generator (Markdown + LaTeX)
#
# Version: 4.0
# Role: Lead Generator
#
# Responsibilities:
#   - Run builds:
#       • Markdown → PDF (pandoc)
#       • Markdown → TeX (pandoc -t latex)
#       • TeX → PDF (pdflatex)
#   - Collect all logs in $TMPDIR
#   - Emit structured LEADS as JSON: high-signal, low-noise pointers to problems
#
# Notes:
#   - Miner never interprets, fixes, or guesses error causes
#   - It emits only minimal “this failed” signals
#   - It NEVER parses logs for detailed information — that’s Investigator’s job
#
# Required environment:
#   TMPDIR   — temp directory for logs and outputs
#   MDFILE   — input Markdown file
#   TEXFILE  — output LaTeX file
#   LOGFILE  — pdflatex log file
#   PDFOUT   — output PDF path
#
# Commands:
#   $0 run_pandoc_tex    → generate TeX from Markdown
#   $0 run_pandoc_pdf    → generate PDF from Markdown
#   $0 run_pdflatex      → compile TeX into PDF
#
# Output:
#   - Writes to:
#       • $TMPDIR/pandoc_stdout.log
#       • $TMPDIR/pandoc_stderr.log
#       • $TMPDIR/pandoc_tex_stderr.log
#       • $LOGFILE (from pdflatex)
#       • $TMPDIR/miner_leads.json (structured diagnostic stubs)
#
#   - Format of miner_leads.json (example):
#     [
#       {
#         "tool": "pandoc",
#         "stage": "pdf",
#         "file": "paper.md",
#         "summary": "pandoc PDF build failed",
#         "severity": "error"
#       },
#       {
#         "tool": "pdflatex",
#         "stage": "compile",
#         "file": "paper.tex",
#         "summary": "pdflatex compilation failed",
#         "severity": "error"
#       }
#     ]
#
# Exit codes:
#   0 = success
#   1 = failure (build step failed, leads generated)
#   2 = configuration error (bad usage or missing env)
#

set -eo pipefail

# Validate environment
for var in TMPDIR MDFILE PDFOUT TEXFILE LOGFILE; do
  if [[ -z "${!var}" ]]; then
    echo "miner.sh: Missing required environment variable: $var" >&2
    exit 2
  fi
done

OUT_LEADS="$TMPDIR/miner_leads.json"

emit_lead() {
  local tool="$1"
  local stage="$2"
  local file="$3"
  local summary="$4"
  local severity="$5"

  jq -n --arg tool "$tool" \
        --arg stage "$stage" \
        --arg file "$file" \
        --arg summary "$summary" \
        --arg severity "$severity" \
        '{
          tool: $tool,
          stage: $stage,
          file: $file,
          summary: $summary,
          severity: $severity
        }'
}

append_lead() {
  local lead="$1"
  if [[ -f "$OUT_LEADS" ]]; then
    jq ". += [$lead]" "$OUT_LEADS" >"$OUT_LEADS.tmp" && mv "$OUT_LEADS.tmp" "$OUT_LEADS"
  else
    echo "[$lead]" >"$OUT_LEADS"
  fi
}

run_pandoc_pdf() {
  local outlog="$TMPDIR/pandoc_stdout.log"
  local errlog="$TMPDIR/pandoc_stderr.log"

  if ! pandoc --verbose "$MDFILE" -o "$PDFOUT" >"$outlog" 2>"$errlog"; then
    emit_lead "pandoc" "pdf" "$MDFILE" "pandoc PDF build failed" "error" | append_lead
    return 1
  fi
  return 0
}

run_pandoc_tex() {
  local errlog="$TMPDIR/pandoc_tex_stderr.log"

  if ! pandoc -t latex --standalone "$MDFILE" -o "$TEXFILE" 2>"$errlog"; then
    emit_lead "pandoc" "latex" "$MDFILE" "pandoc TeX generation failed" "error" | append_lead
    return 1
  fi
  return 0
}

run_pdflatex() {
  if ! pdflatex -interaction=nonstopmode -halt-on-error -file-line-error \
        -output-directory="$TMPDIR" "$TEXFILE" >"$LOGFILE" 2>&1; then
    emit_lead "pdflatex" "compile" "$TEXFILE" "pdflatex compilation failed" "error" | append_lead
    return 1
  fi
  return 0
}

case "$1" in
  run_pandoc_pdf) run_pandoc_pdf ;;
  run_pandoc_tex) run_pandoc_tex ;;
  run_pdflatex) run_pdflatex ;;
  *)
    echo "Usage: $0 {run_pandoc_pdf|run_pandoc_tex|run_pdflatex}" >&2
    exit 2
    ;;
esac

