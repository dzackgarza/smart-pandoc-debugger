# AWK script: check_unmatched_inline_math.awk
# Detects unmatched \( and \) on a line.
{
  original_line = $0
  open_c = 0
  close_c = 0
  
  _temp_search_string = original_line
  while ( (pos = index(_temp_search_string, "\\(")) > 0 ) {
    open_c++
    _temp_search_string = substr(_temp_search_string, pos + length("\\("))
  }
  
  _temp_search_string = original_line
  while ( (pos = index(_temp_search_string, "\\)")) > 0 ) {
    close_c++
    _temp_search_string = substr(_temp_search_string, pos + length("\\)"))
  }

  if (open_c != close_c) {
    problem_snippet_for_print = original_line # Default to full line
    if (open_c > close_c) { # More open \(
      # Try to get snippet from first '\('
      if (match(original_line, /\\\(.*/)) { 
        raw_snippet = substr(original_line, RSTART)
        # For Reporter: provide snippet *after* the initial '\('
        problem_snippet_for_print = substr(raw_snippet, length("\\(") + 1) 
      }
    } else { # More close \)
      # Try to get snippet from first '\)'
      if (match(original_line, /\\\).*/)) {
        problem_snippet_for_print = substr(original_line, RSTART)
      }
    }
    # If somehow snippet ended up empty, use original line
    if (problem_snippet_for_print == "") {
        problem_snippet_for_print = original_line 
    }
    print "UnterminatedInlineMath:" NR ":" open_c ":" close_c ":" problem_snippet_for_print ":" original_line
    exit
  }
}
