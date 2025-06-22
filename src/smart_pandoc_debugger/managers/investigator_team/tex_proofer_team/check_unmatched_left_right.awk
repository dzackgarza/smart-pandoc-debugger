# AWK script: check_unmatched_left_right.awk
# Detects unmatched \left and \right on a line.
# Output (if error): ErrorType:LineNum:LeftCount:RightCount:ProblemSnippet:OriginalLine
{
  original_line = $0
  
  _temp_line_left = original_line;  lc = gsub(/\\left/,  "&", _temp_line_left)
  _temp_line_right = original_line; rc = gsub(/\\right/, "&", _temp_line_right)
  
  if (lc != rc) {
    problem_snippet = original_line 
    if (lc > rc) { 
      match(original_line, /\\left([(\[]).*/) 
      if (RSTART > 0) problem_snippet = substr(original_line, RSTART)
    } else { 
      match(original_line, /\\right([)\]]).*/) 
      if (RSTART > 0) problem_snippet = substr(original_line, RSTART)
    }
    print "UnmatchedDelimiters:" NR ":" lc ":" rc ":" problem_snippet ":" original_line
    exit # Exit awk after finding the first error on any line
  }
}
