# AWK script: check_unbalanced_braces.awk
# Detects unbalanced { and } on lines heuristically identified as containing math.
# Output (if error): ErrorType:LineNum:OpenBraceCount:CloseBraceCount:ProblemSnippet:OriginalLine
/\\\(|\\\[|\\left|\\right|\\begin\{equation\}|\\frac|\\sqrt|\\sum|\\int|\\text\{|\\label\{/ {
  original_line = $0
  
  _temp_line_open_b = original_line; open_b_c = gsub(/\{/, "&", _temp_line_open_b);
  _temp_line_close_b = original_line; close_b_c = gsub(/\}/, "&", _temp_line_close_b);

  if (open_b_c != close_b_c) {
    problem_snippet = original_line 
    print "UnbalancedBraces:" NR ":" open_b_c ":" close_b_c ":" problem_snippet ":" original_line
    exit # Exit awk after finding the first error on any line
  }
}
