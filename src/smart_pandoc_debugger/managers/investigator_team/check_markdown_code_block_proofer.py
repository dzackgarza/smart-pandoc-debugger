import re

def find_unclosed_backtick_blocks(file_content):
    """
    Finds unclosed triple-backtick code blocks in Markdown content.

    Args:
        file_content (str): The content of the Markdown file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    and contains 'line_number' and 'message'.
    """
    errors = []
    lines = file_content.splitlines()
    in_code_block = False
    block_start_line = -1
    block_indent_level = 0

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        current_indent_level = len(line) - len(line.lstrip())

        # Matches ``` optionally followed by a language specifier
        if line_stripped.startswith("```"):
            # Potential start or end of a block
            # Check if it's a valid block delimiter (not indented more than the current block's start)
            # Or if we are not in a block, any ``` is a potential starter.

            is_block_delimiter_candidate = re.match(r"```(\s*\w*\s*)?$", line_stripped)

            if is_block_delimiter_candidate:
                if not in_code_block:
                    in_code_block = True
                    block_start_line = i + 1
                    block_indent_level = current_indent_level
                else:
                    # If we are in a code block, a closing ``` should ideally have
                    # an indent less than or equal to the opening indent.
                    # This is a heuristic for simple nesting.
                    # A ``` that is more indented than the block opener is likely content.
                    if current_indent_level <= block_indent_level:
                        in_code_block = False
                        block_start_line = -1
                        block_indent_level = 0 # Reset
                    # Else: it's indented further, so we assume it's part of the code block content.
                    # e.g. an example of a code block within a code block.
            # else: it starts with ``` but has other characters after it, not a valid delimiter.
            # This is treated as content if in_code_block is true.

        # The old elif for "elif in_code_block and line.strip().startswith("```") ..."
        # is now handled by the logic above. If it's not a `is_block_delimiter_candidate`
        # or if it's more indented, it's treated as content.

    if in_code_block:
        errors.append({
            "line_number": block_start_line, # block_start_line refers to the line number of the opening ```
            "message": f"Unclosed triple-backtick code block starting on line {block_start_line}."
        })

    return errors


def find_inconsistent_indentation_code_blocks(file_content):
    """
    Finds 4-space indented code blocks with inconsistent indentation.

    Args:
        file_content (str): The content of the Markdown file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    and contains 'line_number' and 'message'.
    """
    errors = []
    lines = file_content.splitlines()
    in_indented_code_block = False
    block_start_line = -1
    expected_indent = ""

    for i, line in enumerate(lines):
        current_line_stripped = line.strip()

        # Check for start of an indented code block
        # An indented block starts with 4 spaces or a tab, is not blank,
        # and the previous line must be blank or not part of an indented block.
        if (line.startswith("    ") or line.startswith("\t")) and current_line_stripped:
            if not in_indented_code_block:
                # Check if the previous line was blank or not indented
                if i == 0 or not (lines[i-1].startswith("    ") or lines[i-1].startswith("\t")) or lines[i-1].strip() == "":
                    # Heuristic: if the line before is not blank and not indented, this is likely a new block
                    # A more sophisticated check would look at whether the previous non-blank line was part of a list item etc.
                    # For now, we simplify: if a line has >=4 spaces and isn't preceded by an indented line, it's a new block.

                    # This needs to be careful not to trigger inside other constructs like lists.
                    # A simple way: if previous line is blank, it's a code block.
                    # If previous line is not blank and not indented, it's also a code block.
                    # This still has edge cases (e.g. paragraph followed by indented code).
                    # A common pattern is that an indented code block is preceded by a blank line.

                    # Let's refine: A line starts an indented code block if:
                    # 1. It is indented by 4+ spaces (or 1+ tab).
                    # 2. It is not blank.
                    # 3. The *previous non-blank* line was not indented (or it's the first line).
                    # This handles paragraphs followed by indented code.

                    is_new_block = False
                    if i == 0:
                        is_new_block = True
                    else:
                        # Find the previous non-blank line
                        prev_non_blank_line_idx = -1
                        for j in range(i - 1, -1, -1):
                            if lines[j].strip():
                                prev_non_blank_line_idx = j
                                break

                        if prev_non_blank_line_idx == -1: # All previous lines were blank
                            is_new_block = True
                        elif not (lines[prev_non_blank_line_idx].startswith("    ") or lines[prev_non_blank_line_idx].startswith("\t")):
                            is_new_block = True

                    if is_new_block:
                        in_indented_code_block = True
                        block_start_line = i + 1
                        # Determine expected indent (all spaces or all tabs)
                        # For simplicity, let's just check for 4 spaces for now.
                        # A more robust check would handle tab indentation too.
                        if line.startswith("    "):
                            expected_indent = "    "
                        elif line.startswith("\t"):
                             # For now, we will assume tab indented blocks are consistent if they start with a tab.
                             # A deeper check would be needed for mixed tabs/spaces if we want to be strict.
                            expected_indent = "\t"
                        else: # Should not happen due to initial check
                            in_indented_code_block = False
                            block_start_line = -1
                            continue


        elif in_indented_code_block:
            # If the line is blank, it's part of the block
            if not current_line_stripped:
                continue # Allow blank lines within the code block

            # If the line is not indented, the block ends
            if not (line.startswith(expected_indent)):
                # Check if it's a de-indentation or an inconsistent indent
                if line.startswith(" ") or line.startswith("\t"): # It's indented, but not matching expected
                    # It's indented, but not matching the expected prefix.
                    # This could be due to mixed tabs/spaces or wrong indent level.
                    current_line_indent_char_type = None
                    if line.startswith("    "): current_line_indent_char_type = "space"
                    elif line.startswith("\t"): current_line_indent_char_type = "tab"

                    expected_indent_char_type = None
                    if expected_indent.startswith("    "): expected_indent_char_type = "space"
                    elif expected_indent.startswith("\t"): expected_indent_char_type = "tab"

                    message = f"Inconsistent indentation in code block starting on line {block_start_line}. "
                    if expected_indent_char_type and current_line_indent_char_type and expected_indent_char_type != current_line_indent_char_type:
                        message += f"Started with {expected_indent_char_type}-based indent, but line {i+1} uses {current_line_indent_char_type}-based indent. Mixing tabs and spaces for indentation is not allowed."
                    else:
                        message += f"Expected indentation starting with '{expected_indent.replace(' ', '·').replaceঅনেকেই}', but found different indentation."

                    errors.append({
                        "line_number": i + 1,
                        "message": message,
                    })
                # Whether it's inconsistent (and reported) or de-indented (not matching and not indented at all), the current block ends here.
                in_indented_code_block = False
                block_start_line = -1
                expected_indent = ""
            # Else, it is indented correctly, so continue

    # Note: An indented code block doesn't have an explicit "end" marker other than
    # a line that is not indented, or end of file. So no "unclosed" error like backticks.
    # The primary check is for consistency *within* what appears to be a block.

    return errors


# --- Code Block Language Validation ---

# A list of common languages for syntax highlighting.
# This is not exhaustive but covers many common cases.
# Sources: Common highlighters (Pygments, Prism.js, Highlight.js), GitHub/GitLab usage.
COMMON_LANGUAGES = set([
    "python", "py", "javascript", "js", "java", "c", "cpp", "c++", "csharp", "cs",
    "ruby", "rb", "php", "go", "rust", "swift", "kotlin", "scala", "typescript", "ts",
    "html", "css", "xml", "json", "yaml", "yml", "markdown", "md", "sql", "bash", "sh",
    "perl", "lua", "r", "matlab", "powershell", "ps1", "ini", "toml", "dockerfile",
    "plaintext", "text", "diff", "patch", "objectivec", "groovy", "dart", "elixir",
    "erlang", "haskell", "hs", "lisp", "clojure", "fortran", "julia", "pascal",
    "assembly", "asm", "vhdl", "verilog", "makefile", "cmake", "sql", "shell", "console"
])

def validate_code_block_languages(file_content):
    """
    Validates language specifiers in triple-backtick code blocks.

    Args:
        file_content (str): The content of the Markdown file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    (unknown language) and contains 'line_number' and 'message'.
    """
    errors = []
    lines = file_content.splitlines()
    in_code_block = False # To ensure we only look at the opening line of a block

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        if line_stripped.startswith("```"):
            if not in_code_block:
                # This is an opening line of a code block
                in_code_block = True
                match = re.match(r"```\s*(\S+)", line_stripped)
                if match:
                    language = match.group(1).lower()
                    # Further strip any potential non-alpha characters that might cling (like from a copy-paste)
                    # Although the regex \S+ should handle most of this.
                    # Example: ```python, ```python { .numberLines } - we only want 'python'
                    language_cleaned = re.sub(r"[^a-z0-9+#-]", "", language) # Allow c++, c#, etc.

                    if language_cleaned and language_cleaned not in COMMON_LANGUAGES:
                        # Check if it's something like `python {linenos=table}`
                        # We are interested in the part before any space or {
                        language_base = language.split(" ")[0].split("{")[0]
                        language_base_cleaned = re.sub(r"[^a-z0-9+#-]", "", language_base.lower())

                        if language_base_cleaned and language_base_cleaned not in COMMON_LANGUAGES:
                             errors.append({
                                "line_number": i + 1,
                                "message": f"Unknown or uncommon language specifier '{language_base}' for code block. Consider using a common language or ensuring your highlighter supports it."
                            })
            else:
                # This is a closing line
                in_code_block = False

    return errors


# --- Heading Level Validation ---

def validate_heading_levels(file_content):
    """
    Validates heading levels in Markdown content (ATX headings only).
    Checks for jumps in heading levels (e.g., H1 to H3 without H2).

    Args:
        file_content (str): The content of the Markdown file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    and contains 'line_number' and 'message'.
    """
    errors = []
    lines = file_content.splitlines()
    last_heading_level = 0
    last_heading_line_number = 0

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.startswith("#"):
            match = re.match(r"^(#+)\s", stripped_line)
            if match:
                current_level = len(match.group(1))
                current_line_number = i + 1

                if last_heading_level > 0: # If this is not the first heading
                    if current_level > last_heading_level + 1:
                        errors.append({
                            "line_number": current_line_number,
                            "message": f"Heading level jumped from H{last_heading_level} (line {last_heading_line_number}) to H{current_level} (line {current_line_number}). Consider adding intermediate heading levels."
                        })

                last_heading_level = current_level
                last_heading_line_number = current_line_number
            # else: line starts with # but not followed by space, not a valid ATX heading by many parsers.
            # We are only checking valid headings for now.

    return errors


# --- List Consistency Validation ---

def validate_list_consistency(file_content):
    """
    Validates basic list consistency in Markdown content.
    - Checks for consistent bullet style in unordered lists at the same level.
    - Checks for consistent indentation of list items at the same level.
    - Basic check for ordered list numbering (sequential).

    Args:
        file_content (str): The content of the Markdown file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    and contains 'line_number' and 'message'.
    """
    errors = []
    lines = file_content.splitlines()

    # Regex to identify list items (unordered: *, -, +; ordered: 1., 1))
    # It captures indent, bullet/number, and content start
    list_item_regex = re.compile(r"^(\s*)([*+-]|\d+[.)])(\s+.*)?$")

    # Tracks active lists at different indentation levels
    # { indent_level: {"type": "unordered" | "ordered", "bullet_style": "*", "expected_number": 2, "start_line": N} }
    active_lists_stack = []

    for i, line in enumerate(lines):
        match = list_item_regex.match(line)
        line_num = i + 1

        if match:
            indent_str = match.group(1)
            indent_level = len(indent_str)
            bullet_or_num = match.group(2)
            content_present = bool(match.group(3) and match.group(3).strip())

            if not content_present and not (i + 1 < len(lines) and list_item_regex.match(lines[i+1]) and len(lines[i+1].lstrip()) > indent_level ): # allow empty item if it has sublist
                 # Potentially an empty list item that isn't starting a sublist.
                 # CommonMark allows this, but some linters flag it. For now, we'll allow.
                 pass


            # Manage the stack based on indentation
            while active_lists_stack and indent_level < active_lists_stack[-1]["indent_level"]:
                active_lists_stack.pop() # Exiting a deeper list level

            if not active_lists_stack or indent_level > active_lists_stack[-1]["indent_level"]:
                # New list or deeper nested list
                list_type = "unordered" if bullet_or_num in ['*', '+', '-'] else "ordered"
                new_list_info = {
                    "indent_level": indent_level,
                    "type": list_type,
                    "start_line": line_num
                }
                if list_type == "unordered":
                    new_list_info["bullet_style"] = bullet_or_num
                else: # ordered
                    num_match = re.match(r"(\d+)[.)]", bullet_or_num)
                    if num_match:
                        new_list_info["expected_number"] = int(num_match.group(1)) + 1
                        new_list_info["number_style"] = bullet_or_num[-1] # . or )
                    else:
                        # Should not happen due to regex, but as a fallback
                        errors.append({"line_number": line_num, "message": f"Invalid ordered list item format: {bullet_or_num}"})
                        continue
                active_lists_stack.append(new_list_info)
                current_list_info = new_list_info

            elif indent_level == active_lists_stack[-1]["indent_level"]:
                # Continuing an existing list at the same level
                current_list_info = active_lists_stack[-1]

                if current_list_info["type"] == "unordered":
                    if bullet_or_num != current_list_info["bullet_style"]:
                        errors.append({
                            "line_number": line_num,
                            "message": f"Inconsistent bullet style in unordered list. Expected '{current_list_info['bullet_style']}' but got '{bullet_or_num}'. List started on line {current_list_info['start_line']}."
                        })
                else: # ordered
                    num_match = re.match(r"(\d+)[.)]", bullet_or_num)
                    actual_num = -1
                    actual_style = ''
                    if num_match:
                        actual_num = int(num_match.group(1))
                        actual_style = bullet_or_num[-1]

                    if actual_style != current_list_info["number_style"]:
                         errors.append({
                            "line_number": line_num,
                            "message": f"Inconsistent numbering style in ordered list. Expected style ending with '{current_list_info['number_style']}' but got '{actual_style}'. List started on line {current_list_info['start_line']}."
                        })
                    elif actual_num != current_list_info["expected_number"]:
                        # CommonMark allows starting ordered lists with numbers other than 1,
                        # and even non-sequential numbers. However, for "consistency", many prefer sequential.
                        # This check is for strict sequential numbering after the first item.
                        # We could make this optional or less strict. For now, simple sequential.
                        # Let's adjust: the *first* item of a list sets the start, subsequent ones should be sequential *or* restart from 1
                        # For simplicity, this version expects strict sequence from the *previous* number.
                        errors.append({
                            "line_number": line_num,
                            "message": f"Non-sequential numbering in ordered list. Expected '{current_list_info['expected_number']}{current_list_info['number_style']}' but got '{bullet_or_num}'. List started on line {current_list_info['start_line']}."
                        })

                    if num_match : # if valid number format
                        current_list_info["expected_number"] = actual_num + 1
            else:
                # De-indenting to a level not on stack - implies malformed list or end of all lists
                # This case should ideally be handled by the stack pop, but as a safeguard:
                active_lists_stack.clear() # Assume all lists ended

        else: # Not a list item
            if active_lists_stack and line.strip() != "": # Non-blank line ends all lists
                active_lists_stack.clear()
            # If line is blank, list can continue.

    return errors


# --- Table Structure Validation ---

def count_table_columns(row_string):
    """Counts columns in a Markdown table row string."""
    # Normalize: remove leading/trailing pipes if they exist
    if row_string.startswith("|"):
        row_string = row_string[1:]
    if row_string.endswith("|"):
        row_string = row_string[:-1]

    # Split by non-escaped pipes
    # This simple split doesn't handle escaped pipes \| within cells.
    # For a more robust solution, a regex with negative lookbehind would be needed.
    # For now, assuming pipes are delimiters.
    return len(row_string.split("|"))

def validate_table_structure(file_content):
    """
    Validates basic table structure in Markdown content (GFM style).
    - Checks for consistent column counts across rows.
    - Identifies tables by header and separator line.

    Args:
        file_content (str): The content of the Markdown file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    and contains 'line_number' and 'message'.
    """
    errors = []
    lines = file_content.splitlines()

    in_table = False
    expected_columns = 0
    table_start_line = 0
    header_line_num = 0

    # Regex for separator: `|---|---|` or `|:---|---:|` or `|---:|` etc.
    # Must contain at least one pipe and hyphens.
    # Simplified: checks for pipes, hyphens, colons, and spaces.
    separator_regex = re.compile(r"^\s*\|?.*[-:|]{3,}.*\|?\s*$")
    # More precise separator: ensure cells are primarily hyphens
    # Each cell part should be like `\s*:?-+:?\s*`
    cell_separator_part = r"\s*:?\-+:?\s*"
    precise_separator_regex = re.compile(r"^\s*\|?(" + cell_separator_part + r"\|)*" + cell_separator_part + r"\|?\s*$")


    for i, line in enumerate(lines):
        current_line_num = i + 1
        stripped_line = line.strip()

        if not in_table:
            # Try to detect a new table: requires a line that could be a header,
            # followed by a separator line.
            if "|" in stripped_line: # Potential header
                if i + 1 < len(lines):
                    next_line_stripped = lines[i+1].strip()
                    if precise_separator_regex.match(next_line_stripped):
                        # Found a header and separator, start of a table
                        in_table = True
                        table_start_line = current_line_num
                        header_line_num = current_line_num

                        # Count columns from header
                        expected_columns = count_table_columns(stripped_line)

                        # Also count columns from separator to double check, could be more robust
                        separator_columns = count_table_columns(next_line_stripped)
                        if separator_columns != expected_columns:
                            # This can happen if header has empty trailing cells like `| H1 | H2 |  |`
                            # Or if separator is malformed.
                            # Let's trust the separator more for column count if it's a valid separator.
                            # However, GFM allows header to define columns.
                            # For now, we'll use header count, but flag if separator differs significantly.
                            # A common case is `| H1 | H2 |` (2 cols) and `|---|---|---|` (3 cols due to extra pipe)
                            # Let's use the maximum of the two as a heuristic for now, or be stricter with separator.
                            # Using separator count is generally more reliable for GFM.
                            expected_columns = separator_columns

                        # Check first row (header) column count against separator-derived count
                        header_actual_cols = count_table_columns(stripped_line)
                        if header_actual_cols != expected_columns:
                             errors.append({
                                "line_number": current_line_num,
                                "message": f"Table header on line {current_line_num} has {header_actual_cols} columns, but separator line implies {expected_columns} columns."
                            })
                        # Skip the separator line in the next iteration
                        # (already processed, `i` will increment)

        elif in_table: # Already inside a table
            # If line is empty or doesn't contain a pipe, table ends
            if not stripped_line or "|" not in stripped_line:
                if not precise_separator_regex.match(stripped_line): # ensure it's not another separator for some reason
                    in_table = False
                    expected_columns = 0
                    table_start_line = 0
                    header_line_num = 0
                    continue # Move to next line, this one ended the table

            if in_table and current_line_num > header_line_num +1: # Ensure it's a data row, not header or separator
                actual_columns = count_table_columns(stripped_line)
                if actual_columns != expected_columns:
                    errors.append({
                        "line_number": current_line_num,
                        "message": f"Inconsistent column count in table starting on line {table_start_line}. Row {current_line_num} has {actual_columns} columns, expected {expected_columns}."
                    })
    return errors


# --- Image Path Validation ---
import os

def validate_image_paths(file_content, base_dir="."):
    """
    Validates local image paths in Markdown `![alt](path)` syntax.
    Ignores URL paths (http/https).

    Args:
        file_content (str): The content of the Markdown file.
        base_dir (str): The base directory against which relative paths are resolved.
                        Defaults to current directory.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    (missing image file) and contains 'line_number' and 'message'.
    """
    errors = []
    lines = file_content.splitlines()

    # Regex for Markdown images: ![alt](path "title") or ![alt](path)
    # Captures: alt text, path, optional title
    image_regex = re.compile(r"!\[([^]]*)\]\(([^)\s]+)(?:\s*\"([^\"]*)\")?\)")

    for i, line in enumerate(lines):
        for match in image_regex.finditer(line):
            path = match.group(2)
            line_num = i + 1

            # Ignore URLs
            if path.startswith("http://") or path.startswith("https://"):
                continue

            # Handle local paths
            # For testing, base_dir might need to be adjusted or files created.
            # If path is absolute, os.path.join behaves correctly.
            # If path is relative, it's joined with base_dir.
            absolute_path = os.path.abspath(os.path.join(base_dir, path))

            # A more direct way for relative paths from a specific base:
            if os.path.isabs(path):
                resolved_path = path
            else:
                resolved_path = os.path.join(base_dir, path)

            if not os.path.exists(resolved_path):
                errors.append({
                    "line_number": line_num,
                    "message": f"Local image file not found: '{path}'. Resolved to '{os.path.normpath(resolved_path)}'."
                })
    return errors


# --- Empty Section Validation ---

def is_line_whitespace_or_comment(line):
    """Checks if a line is effectively empty (whitespace or common comment types)."""
    stripped_line = line.strip()
    if not stripped_line: # Empty or all whitespace
        return True
    if stripped_line.startswith("<!--") and stripped_line.endswith("-->"): # HTML comment
        return True
    # Add other comment types if necessary, e.g., Markdown extension comments
    # For now, focusing on HTML comments as they are common for "hiding" content.
    return False

def validate_empty_sections(file_content):
    """
    Validates that sections (demarcated by ATX headings) are not empty
    (i.e., contain more than just whitespace or comments).

    Args:
        file_content (str): The content of the Markdown file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    (empty section) and contains 'line_number' (of the heading)
                    and 'message'.
    """
    errors = []
    lines = file_content.splitlines()

    current_section_content = []
    current_section_heading_line = -1
    current_section_heading_text = ""
    current_section_level = 0

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped_line = line.strip()

        heading_match = re.match(r"^(#+)\s+(.*)", stripped_line)

        if heading_match:
            new_heading_level = len(heading_match.group(1))
            new_heading_text = heading_match.group(2).strip()

            # Process previous section (if any) before starting a new one
            if current_section_heading_line != -1:
                is_empty = True
                if not current_section_content: # No lines at all between headings
                    is_empty = True
                else:
                    for content_line in current_section_content:
                        if not is_line_whitespace_or_comment(content_line):
                            is_empty = False
                            break
                if is_empty:
                    errors.append({
                        "line_number": current_section_heading_line,
                        "message": f"Section '{current_section_heading_text}' (H{current_section_level}) starting on line {current_section_heading_line} appears to be empty or contain only comments/whitespace."
                    })

            # Start new section
            current_section_content = []
            current_section_heading_line = line_num
            current_section_heading_text = new_heading_text
            current_section_level = new_heading_level

        elif current_section_heading_line != -1: # If we are inside a section
            current_section_content.append(line)

    # Check the last section after loop finishes
    if current_section_heading_line != -1:
        is_empty = True
        if not current_section_content:
            is_empty = True
        else:
            for content_line in current_section_content:
                if not is_line_whitespace_or_comment(content_line):
                    is_empty = False
                    break
        if is_empty:
            errors.append({
                "line_number": current_section_heading_line,
                "message": f"Section '{current_section_heading_text}' (H{current_section_level}) starting on line {current_section_heading_line} appears to be empty or contain only comments/whitespace."
            })

    return errors


# --- Paragraph Length Validation ---

DEFAULT_MAX_PARAGRAPH_CHARS = 600 # Approx 100-120 words. Roadmap mentions 80, which is very short.

def is_likely_other_markdown_element(line):
    """
    Checks if a line is likely part of another specific Markdown block element.
    This is a helper to avoid misidentifying parts of these as paragraphs.
    """
    stripped_line = line.strip()
    if not stripped_line:
        return True # Blank lines separate paragraphs
    if stripped_line.startswith(("#", ">", "```", "    ", "\t")): # Heading, blockquote, code block fence, indented code
        return True
    if re.match(r"^(\s*)([*+-]|\d+[.)])\s+", stripped_line): # List item
        return True
    if "|" in stripped_line and ("---" in line or (len(stripped_line.split("|")) > 2 and stripped_line.startswith("|")) ): # Table row or separator (heuristic)
        return True
    if stripped_line.startswith("<!--") and stripped_line.endswith("-->"): # HTML comment
        return True
    # Add Setext heading underlines if needed: if re.match(r"^[=-]+$", stripped_line)
    return False

def validate_paragraph_length(file_content, max_chars=DEFAULT_MAX_PARAGRAPH_CHARS):
    """
    Validates that paragraphs do not exceed a maximum character length.

    Args:
        file_content (str): The content of the Markdown file.
        max_chars (int): The maximum allowed characters in a paragraph.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    (long paragraph) and contains 'line_number' (of paragraph start)
                    and 'message'.
    """
    errors = []
    lines = file_content.splitlines()

    current_paragraph_lines = []
    paragraph_start_line = -1

    for i, line in enumerate(lines):
        line_num = i + 1

        if not is_likely_other_markdown_element(line):
            # This line could be part of a paragraph
            if not current_paragraph_lines: # Start of a new potential paragraph
                paragraph_start_line = line_num
            current_paragraph_lines.append(line)
        else:
            # Line is blank or part of another element, so the current paragraph (if any) ends.
            if current_paragraph_lines:
                paragraph_text = " ".join(l.strip() for l in current_paragraph_lines if l.strip()).strip()
                if len(paragraph_text) > max_chars:
                    errors.append({
                        "line_number": paragraph_start_line,
                        "message": f"Paragraph starting on line {paragraph_start_line} is too long ({len(paragraph_text)} chars). Exceeds maximum of {max_chars} chars. Consider breaking it into smaller paragraphs."
                    })
                current_paragraph_lines = []
                paragraph_start_line = -1
            # If the line itself was blank, it just acts as a separator.
            # If it was another element, that element is handled by its own validator.

    # Check any remaining paragraph at the end of the file
    if current_paragraph_lines:
        paragraph_text = " ".join(l.strip() for l in current_paragraph_lines if l.strip()).strip()
        if len(paragraph_text) > max_chars:
            errors.append({
                "line_number": paragraph_start_line,
                "message": f"Paragraph starting on line {paragraph_start_line} is too long ({len(paragraph_text)} chars). Exceeds maximum of {max_chars} chars. Consider breaking it into smaller paragraphs."
            })

    return errors


# --- Problematic Whitespace Validation ---

def validate_problematic_whitespace(file_content):
    """
    Validates for common problematic whitespace issues.
    - Trailing whitespace.
    - Multiple internal spaces (outside of code blocks).
    - Tabs used for mid-line alignment (outside of code blocks).

    Args:
        file_content (str): The content of the Markdown file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an error
                    and contains 'line_number' and 'message'.
    """
    errors = []
    lines = file_content.splitlines(True) # Keep line endings for trailing space check

    in_fenced_code_block = False

    for i, line_with_ending in enumerate(lines):
        line_num = i + 1
        # Remove line ending for content analysis, but keep original for trailing check
        line = line_with_ending.rstrip('\r\n')

        # 1. Trailing whitespace
        if len(line) != len(line.rstrip(" \t")):
            errors.append({
                "line_number": line_num,
                "message": "Line has trailing whitespace."
            })

        # Toggle fenced code block state
        if line.strip().startswith("```"):
            in_fenced_code_block = not in_fenced_code_block
            continue # Skip further whitespace checks on the fence line itself

        if not in_fenced_code_block:
            # 2. Multiple internal spaces (simplified: two or more spaces)
            # This regex looks for a non-space, then two+ spaces, then non-space.
            # It avoids flagging leading spaces used for indentation if line starts with spaces.
            # Or multiple spaces after a list marker, e.g. "-   item" (this is common)

            # A simpler check: find "  " not at the start of the string.
            # We need to be careful not to flag intentional spaces in e.g. tables or poetry.
            # For now, let's use a basic "  " check on stripped content.
            # This is a very broad check and might have false positives.

            # Consider `line.lstrip()` to ignore leading spaces, then check `  `
            line_content_part = line.lstrip()
            if "  " in line_content_part:
                 # Avoid flagging if it's space after list marker, or part of table alignment
                if not (re.match(r"^([*+-]|\d+[.)])\s\s+", line_content_part) or "|" in line):
                    errors.append({
                        "line_number": line_num,
                        "message": "Line contains multiple consecutive internal spaces."
                    })

            # 3. Tabs used for mid-line alignment
            # A tab is problematic if it's not at the beginning of the line (after stripping leading spaces)
            stripped_of_leading_spaces = line.lstrip(" ")
            if "\t" in stripped_of_leading_spaces and not stripped_of_leading_spaces.startswith("\t"):
                errors.append({
                    "line_number": line_num,
                    "message": "Line contains tabs used for mid-line alignment (after initial text or spaces)."
                })

    return errors

if __name__ == '__main__':
    # Example Usage
    test_markdown_ok = """
    # Title

    Some text.

    ```python
    def hello():
        print("Hello")
    ```

    More text.

    ```
    Plain code block
    ```
    """

    test_markdown_error = """
    # Title

    ```ruby
    def world():
        puts "World"
    # Missing closing backticks
    """

    test_markdown_nested_ok = """
    # Title

    ```html
    <div>
        <p>Some HTML</p>
        ```markdown
        This is *Markdown* inside HTML.
        ```
    </div>
    ```

    Final text.
    """

    test_markdown_error_eof = """
    # Title

    Some text.

    ```python
    def hello():
        print("Hello")
    """ # Error: unclosed at EOF

    test_markdown_multiple_ok = """
    ```
    block 1
    ```
    text
    ```
    block 2
    ```
    """

    test_markdown_multiple_error_first = """
    ```
    block 1
    text
    ```
    block 2
    ```
    """ # Error: first block unclosed (assuming ``` inside is content) -> No, this logic is flawed.
      # The current simple logic will treat the second ``` as closing the first.
      # A more robust parser is needed for "``` inside a code block" but that's for step 3.
      # For now, this step focuses on simple unclosed blocks.

    test_markdown_false_positive = """
    This is not a code block ```
    This is still not a code block.
    """

    print("Testing OK markdown:")
    errors_ok = find_unclosed_backtick_blocks(test_markdown_ok)
    assert not errors_ok, f"Found errors in supposedly OK markdown: {errors_ok}"
    print("OK.")

    print("\nTesting ERROR markdown (unclosed block):")
    errors_error = find_unclosed_backtick_blocks(test_markdown_error)
    assert len(errors_error) == 1, f"Expected 1 error, got {len(errors_error)}: {errors_error}"
    assert errors_error[0]["line_number"] == 4, f"Incorrect line number: {errors_error[0]['line_number']}"
    print(f"Found expected error: {errors_error[0]}")
    print("OK.")

    print("\nTesting OK nested markdown (simple case for now):")
    errors_nested_ok = find_unclosed_backtick_blocks(test_markdown_nested_ok)
    # With new indent-aware logic, this should correctly pass.
    # The inner ```markdown and ``` are more indented than the outer ```html block starter.
    assert not errors_nested_ok, f"Found errors in supposedly OK nested markdown: {errors_nested_ok}"
    print("OK (nested with indentation).")

    test_markdown_nested_error = """
    # Title

    ```html
    <div>
        <p>Some HTML</p>
        ```markdown
        This is *Markdown* inside HTML.
        ```
    </div>
    """ # Missing final ``` for the html block
    errors_nested_error = find_unclosed_backtick_blocks(test_markdown_nested_error)
    assert len(errors_nested_error) == 1, f"Expected 1 error for unclosed outer block, got {len(errors_nested_error)}: {errors_nested_error}"
    assert errors_nested_error[0]["line_number"] == 4, f"Incorrect line number for unclosed outer block: {errors_nested_error[0]['line_number']}"
    print(f"Found expected error: {errors_nested_error[0]}")
    print("OK (nested with error).")


    print("\nTesting ERROR markdown (unclosed at EOF):")
    errors_eof = find_unclosed_backtick_blocks(test_markdown_error_eof)
    assert len(errors_eof) == 1, f"Expected 1 error for EOF, got {len(errors_eof)}: {errors_eof}"
    assert errors_eof[0]["line_number"] == 6, f"Incorrect line number for EOF error: {errors_eof[0]['line_number']}"
    print(f"Found expected error: {errors_eof[0]}")
    print("OK.")

    print("\nTesting multiple OK blocks:")
    errors_multiple_ok = find_unclosed_backtick_blocks(test_markdown_multiple_ok)
    assert not errors_multiple_ok, f"Found errors in multiple OK blocks: {errors_multiple_ok}"
    print("OK.")

    print("\nTesting false positive case (inline ```):")
    errors_false_positive = find_unclosed_backtick_blocks(test_markdown_false_positive)
    assert not errors_false_positive, f"Found errors in false positive case: {errors_false_positive}"
    print("OK.")

    print("\nAll basic tests for unclosed backticks passed.")


    print("\n--- Testing Indented Code Blocks ---")

    test_indented_ok = """
    Paragraph.

        def foo():
            print("bar")

        # This is a comment in the block
        Another line
    """
    errors_indented_ok = find_inconsistent_indentation_code_blocks(test_indented_ok)
    assert not errors_indented_ok, f"Found errors in supposedly OK indented markdown: {errors_indented_ok}"
    print("OK (indented basic).")

    test_indented_error = """
    Paragraph.

        def foo():
          print("bar") # Inconsistent indent

        Another line
    """
    errors_indented_error = find_inconsistent_indentation_code_blocks(test_indented_error)
    assert len(errors_indented_error) == 1, f"Expected 1 error for inconsistent indent, got {len(errors_indented_error)}: {errors_indented_error}"
    assert errors_indented_error[0]["line_number"] == 5, f"Incorrect line number for inconsistent indent: {errors_indented_error[0]['line_number']}"
    print(f"Found expected error: {errors_indented_error[0]}")
    print("OK (indented inconsistent).")

    test_indented_tabs_ok = """
    Paragraph.

    \tdef foo():
    \t    print("bar") # Assuming tab width allows this inner indent

    \t# Comment
    \tAnother line
    """
    errors_indented_tabs_ok = find_inconsistent_indentation_code_blocks(test_indented_tabs_ok)
    # Current logic for tabs is very basic: if it starts with \t, it's a tab block.
    # It doesn't currently enforce *only* tabs or consistent tab levels within.
    # This test mostly checks that tab-initiated blocks don't break the parser.
    assert not errors_indented_tabs_ok, f"Found errors in supposedly OK tab-indented markdown: {errors_indented_tabs_ok}"
    print("OK (indented tabs basic).")

    test_indented_mixed_error = """
    Paragraph.

        def foo(): # 4 spaces
    \t    print("bar") # Tab, should be error if previous was space

    """
    # This specific mixed case (4-space start, then tab) should be caught if expected_indent is strictly '    '
    # and \t doesn't start with '    '.
    errors_indented_mixed_error = find_inconsistent_indentation_code_blocks(test_indented_mixed_error)
    assert len(errors_indented_mixed_error) == 1, f"Expected 1 error for mixed indent, got {len(errors_indented_mixed_error)}: {errors_indented_mixed_error}"
    assert errors_indented_mixed_error[0]["line_number"] == 5, f"Incorrect line number for mixed indent: {errors_indented_mixed_error[0]['line_number']}"
    print(f"Found expected error: {errors_indented_mixed_error[0]}")
    print("OK (indented mixed space then tab).")

    test_indented_not_a_block = """
    - List item
        - Nested list item, also indented
          but not a code block.

    Not indented.
        This is a code block.
    """
    errors_indented_not_a_block = find_inconsistent_indentation_code_blocks(test_indented_not_a_block)
    # The heuristic for block start should prevent list items from being treated as code blocks.
    # The line "This is a code block." should be identified.
    # Let's verify no errors are thrown for the list part.
    found_list_error = False
    for error in errors_indented_not_a_block:
        if error["line_number"] < 6: # Errors related to the list part
            found_list_error = True
            break
    assert not found_list_error, f"Erroneously flagged list items as indented code block errors: {errors_indented_not_a_block}"
    print("OK (indented list items not flagged).")

    test_indented_mixed_strict_error = """
    Paragraph.

        def foo(): # 4 spaces
    \t    print("bar") # Tab, should be error
        # Next line with spaces, still part of the same block attempt
            print("baz") # still expecting 4 spaces
    """
    errors_indented_mixed_strict = find_inconsistent_indentation_code_blocks(test_indented_mixed_strict_error)
    assert len(errors_indented_mixed_strict) >= 1, f"Expected at least 1 error for strict mixed indent, got {len(errors_indented_mixed_strict)}: {errors_indented_mixed_strict}"
    error_found = False
    for err in errors_indented_mixed_strict:
        if err["line_number"] == 5 and "Mixing tabs and spaces" in err["message"]:
            error_found = True
            break
    assert error_found, f"Did not find specific mixing error message for line 5: {errors_indented_mixed_strict}"
    print("OK (indented mixed space then tab - strict message).")


    test_indented_tab_then_space_error = """
    Paragraph.

    \tdef foo(): # Tab
            print("bar") # 4 spaces, should be error
    \t    # Next line with tab, still part of the same block attempt
    \t    print("baz") # still expecting tab
    """
    errors_tab_then_space = find_inconsistent_indentation_code_blocks(test_indented_tab_then_space_error)
    assert len(errors_tab_then_space) >= 1, f"Expected at least 1 error for tab then space, got {len(errors_tab_then_space)}: {errors_tab_then_space}"
    error_found_tab = False
    for err in errors_tab_then_space:
        if err["line_number"] == 5 and "Mixing tabs and spaces" in err["message"]:
            error_found_tab = True
            break
    assert error_found_tab, f"Did not find specific mixing error message for line 5 (tab then space): {errors_tab_then_space}"
    print("OK (indented mixed tab then space - strict message).")

    print("\nAll basic tests for indented code blocks passed.")


    print("\n--- Testing Code Block Language Validation ---")
    test_lang_ok = """
    ```python
    x = 1
    ```

    ```javascript { .numberLines }
    var y = 2;
    ```

    ```c++
    int main() { return 0; }
    ```

    ```text
    Just plain text.
    ```

    ```
    No language specified.
    ```
    """
    errors_lang_ok = validate_code_block_languages(test_lang_ok)
    assert not errors_lang_ok, f"Found language errors in supposedly OK markdown: {errors_lang_ok}"
    print("OK (language valid or unspecified).")

    test_lang_error = """
    ```pythn # Misspelled
    x = 1
    ```

    ```mySpecialLang
    data = {}
    ```
    """
    errors_lang_error = validate_code_block_languages(test_lang_error)
    assert len(errors_lang_error) == 2, f"Expected 2 language errors, got {len(errors_lang_error)}: {errors_lang_error}"
    assert errors_lang_error[0]["line_number"] == 2, f"Incorrect line for 'pythn': {errors_lang_error[0]['line_number']}"
    assert errors_lang_error[0]["message"].startswith("Unknown or uncommon language specifier 'pythn'"), f"Incorrect message: {errors_lang_error[0]['message']}"
    assert errors_lang_error[1]["line_number"] == 6, f"Incorrect line for 'mySpecialLang': {errors_lang_error[1]['line_number']}"
    assert errors_lang_error[1]["message"].startswith("Unknown or uncommon language specifier 'myspeciallang'"), f"Incorrect message: {errors_lang_error[1]['message']}" # Note: becomes lowercase
    print(f"Found expected language errors: {errors_lang_error}")
    print("OK (language invalid).")

    test_lang_edge_cases = """
    ```python{linenos=table}
    # complex specifier
    ```
    ```  ruby  { info=string }
    # specifier with spaces around and complex attributes
    ```
    ```
    # empty specifier
    ```
    """
    errors_lang_edge = validate_code_block_languages(test_lang_edge_cases)
    assert not errors_lang_edge, f"Found language errors in edge cases: {errors_lang_edge}"
    print("OK (language edge cases).")

    print("\nAll basic tests for code block language validation passed.")


    print("\n--- Testing Heading Level Validation ---")
    test_headings_ok = """
    # H1
    Some text
    ## H2
    ### H3
    More text
    ## Another H2
    # Another H1
    ## H2 again
    ### H3 again
    #### H4
    """
    errors_headings_ok = validate_heading_levels(test_headings_ok)
    assert not errors_headings_ok, f"Found heading errors in supposedly OK markdown: {errors_headings_ok}"
    print("OK (headings valid).")

    test_headings_jump_error = """
    # H1
    ### H3 (Jump from H1)
    Text
    ## H2 (No jump from H3)
    #### H4 (Jump from H2)
    """
    errors_headings_jump = validate_heading_levels(test_headings_jump_error)
    assert len(errors_headings_jump) == 2, f"Expected 2 heading jump errors, got {len(errors_headings_jump)}: {errors_headings_jump}"

    assert errors_headings_jump[0]["line_number"] == 3, f"Incorrect line for H1->H3 jump: {errors_headings_jump[0]['line_number']}"
    assert "jumped from H1" in errors_headings_jump[0]["message"] and "to H3" in errors_headings_jump[0]["message"], f"Incorrect message: {errors_headings_jump[0]['message']}"

    assert errors_headings_jump[1]["line_number"] == 7, f"Incorrect line for H2->H4 jump: {errors_headings_jump[1]['line_number']}"
    assert "jumped from H2" in errors_headings_jump[1]["message"] and "to H4" in errors_headings_jump[1]["message"], f"Incorrect message: {errors_headings_jump[1]['message']}"
    print(f"Found expected heading jump errors: {errors_headings_jump}")
    print("OK (heading jumps detected).")

    test_headings_no_space = """
    #H1 without space (not considered a heading by this validator)
    ##H2 also no space
    ###H3 no space
    """
    errors_headings_no_space = validate_heading_levels(test_headings_no_space)
    assert not errors_headings_no_space, f"Found heading errors for headings without space: {errors_headings_no_space}"
    print("OK (headings without trailing space ignored).")

    test_headings_start_lower = """
    ## H2 Start
    Text
    ### H3
    Text
    # H1 (Not a jump, decreasing level is fine)
    """
    errors_headings_start_lower = validate_heading_levels(test_headings_start_lower)
    assert not errors_headings_start_lower, f"Erroneously flagged decreasing heading level: {errors_headings_start_lower}"
    print("OK (decreasing heading level is fine).")

    test_headings_sequential_then_jump = """
    # H1
    ## H2
    #### H4 (Jump from H2)
    """
    errors_headings_seq_jump = validate_heading_levels(test_headings_sequential_then_jump)
    assert len(errors_headings_seq_jump) == 1, f"Expected 1 heading jump error, got {len(errors_headings_seq_jump)}: {errors_headings_seq_jump}"
    assert errors_headings_seq_jump[0]["line_number"] == 4
    assert "jumped from H2" in errors_headings_seq_jump[0]["message"] and "to H4" in errors_headings_seq_jump[0]["message"]
    print("OK (sequential then jump detected).")


    print("\nAll basic tests for heading level validation passed.")


    print("\n--- Testing List Consistency Validation ---")
    test_lists_ok = """
    - Item 1
    - Item 2
      * Nested Item A
      * Nested Item B
        1. Deep Nested 1
        2. Deep Nested 2
    - Item 3

    1. Ordered 1
    2. Ordered 2
       - Unordered sub 1
       - Unordered sub 2
    3. Ordered 3

    + Plus Item 1
    + Plus Item 2
    """
    errors_lists_ok = validate_list_consistency(test_lists_ok)
    assert not errors_lists_ok, f"Found list errors in supposedly OK markdown: {errors_lists_ok}"
    print("OK (lists valid).")

    test_lists_mixed_bullets_error = """
    - Item 1
    * Item 2 (Inconsistent bullet)
    - Item 3
    """
    errors_mixed_bullets = validate_list_consistency(test_lists_mixed_bullets_error)
    assert len(errors_mixed_bullets) == 1, f"Expected 1 error for mixed bullets, got {len(errors_mixed_bullets)}: {errors_mixed_bullets}"
    assert errors_mixed_bullets[0]["line_number"] == 3, f"Incorrect line for mixed bullet: {errors_mixed_bullets[0]['line_number']}"
    assert "Inconsistent bullet style" in errors_mixed_bullets[0]["message"], f"Message mismatch: {errors_mixed_bullets[0]['message']}"
    print("OK (mixed bullets detected).")

    test_lists_non_sequential_error = """
    1. Item 1
    3. Item 3 (Non-sequential)
    2. Item 2 (Also non-sequential based on previous)
    """
    errors_non_sequential = validate_list_consistency(test_lists_non_sequential_error)
    assert len(errors_non_sequential) >= 1, f"Expected errors for non-sequential numbering, got {len(errors_non_sequential)}: {errors_non_sequential}"
    # First error should be on line 3 (1. then 3.)
    first_error_on_line_3 = any(e["line_number"] == 3 and "Non-sequential numbering" in e["message"] and "Expected '2.'" in e["message"] for e in errors_non_sequential)
    assert first_error_on_line_3, f"Did not find expected non-sequential error for line 3: {errors_non_sequential}"
    # Second error could be on line 4 (3. then 2.)
    second_error_on_line_4 = any(e["line_number"] == 4 and "Non-sequential numbering" in e["message"] and "Expected '4.'" in e["message"] for e in errors_non_sequential)
    assert second_error_on_line_4, f"Did not find expected non-sequential error for line 4: {errors_non_sequential}"
    print("OK (non-sequential numbering detected).")

    test_lists_mixed_number_style_error = """
    1. Item 1
    2) Item 2 (Inconsistent style: . vs ))
    3. Item 3
    """
    errors_mixed_num_style = validate_list_consistency(test_lists_mixed_number_style_error)
    assert len(errors_mixed_num_style) == 1, f"Expected 1 error for mixed number style, got {len(errors_mixed_num_style)}: {errors_mixed_num_style}"
    assert errors_mixed_num_style[0]["line_number"] == 3, f"Incorrect line for mixed number style: {errors_mixed_num_style[0]['line_number']}"
    assert "Inconsistent numbering style" in errors_mixed_num_style[0]["message"], f"Message mismatch: {errors_mixed_num_style[0]['message']}"
    print("OK (mixed numbering style detected).")

    test_lists_indentation_consistency = """
    - Item 1
      - Nested 1
    - Item 2 (consistent with Item 1)

      * Standalone list (different indent, should be new list)

    1. Ordered 1
      2. Nested Ordered 2 (indent implies new list, but number is off for a *new* list)
         This is a tricky case. Current logic might flag this if it expects a new list at this indent to start with 1.
         Let's test how it behaves.
         A stricter interpretation is that this should be "1." if it's a new list.
         Or, if it's a continuation of the outer list, it should be less indented.
    """
    # For `test_lists_indentation_consistency`, the main check is that `Item 2` does not cause an error relative to `Item 1`.
    # The nested ordered list starting with "2." is indeed a complex case.
    # The current logic: if `indent_level > active_lists_stack[-1]["indent_level"]`, it's a new list.
    # A new ordered list expects its first number to be what it is.
    # Then, if it's `elif indent_level == active_lists_stack[-1]["indent_level"]`, it checks sequence.
    # So, "2. Nested Ordered 2" will start a new list. Its expected_number becomes 3.
    # This part should pass without error by current logic.
    errors_indent_consistency = validate_list_consistency(test_lists_indentation_consistency)
    print(f"DEBUG: errors_indent_consistency: {errors_indent_consistency}")
    # Check that the primary list items don't cause errors due to indentation
    no_errors_for_primary_list = all(not (e["line_number"] in [2,4]) for e in errors_indent_consistency)
    assert no_errors_for_primary_list, f"Found errors related to primary list items that should be consistent: {errors_indent_consistency}"

    # Specifically for the "2. Nested Ordered 2" line (line 9):
    # It will be treated as a new list because its indent (2) is greater than the previous list item's indent (0 for "1. Ordered 1").
    # As a new list, it starts with '2', so its 'expected_number' becomes 3. This is fine.
    error_on_line_9 = any(e["line_number"] == 9 for e in errors_indent_consistency)
    assert not error_on_line_9, f"Erroneously flagged '2. Nested Ordered 2' on line 9: {errors_indent_consistency}"

    print("OK (basic list indentation consistency and tricky nested ordered list start).")


    print("\nAll basic tests for list consistency passed.")


    print("\n--- Testing Table Structure Validation ---")
    test_tables_ok = """
    | Header 1 | Header 2 | Header 3 |
    |----------|:--------:|----------|
    | R1C1     | R1C2     | R1C3     |
    | R2C1     | R2C2     | R2C3     |

    No pipes here, table ended.

    Another table:
    | A   | B   |
    | --- | --- |
    | 1   | 2   |
    """
    errors_tables_ok = validate_table_structure(test_tables_ok)
    assert not errors_tables_ok, f"Found table errors in supposedly OK markdown: {errors_tables_ok}"
    print("OK (tables valid).")

    test_tables_col_mismatch_data = """
    | H1 | H2 |
    |----|----|
    | R1C1 | R1C2 | R1C3 | Too many cols
    | R2C1 |              Too few cols
    """
    errors_col_mismatch_data = validate_table_structure(test_tables_col_mismatch_data)
    assert len(errors_col_mismatch_data) == 2, f"Expected 2 errors for data col mismatch, got {len(errors_col_mismatch_data)}: {errors_col_mismatch_data}"
    assert errors_col_mismatch_data[0]["line_number"] == 4, f"Incorrect line for too many cols: {errors_col_mismatch_data[0]['line_number']}"
    assert "Row 4 has 3 columns, expected 2" in errors_col_mismatch_data[0]["message"]
    assert errors_col_mismatch_data[1]["line_number"] == 5, f"Incorrect line for too few cols: {errors_col_mismatch_data[1]['line_number']}"
    assert "Row 5 has 2 columns, expected 2" in errors_col_mismatch_data[1]["message"] # count_table_columns gives 2 for "| R2C1 |" due to split behavior
    print("OK (table data column mismatch detected).")

    # Adjusting expectation for the "too few cols" case based on how count_table_columns works:
    # "| R2C1 |" -> " R2C1 " -> split by "|" -> [" R2C1 "] one element if no internal pipes.
    # "| R2C1 | |" -> " R2C1 | " -> split -> [" R2C1 ", " "] two elements.
    # The current count_table_columns is simple. For "| R2C1 |", it will be 1 column after stripping pipes.
    # So, let's refine that specific test's expectation.
    # If line is `| R2C1 |`, stripped ` R2C1 `, split `[' R2C1 ']`, len 1.
    # If line is `| R2C1 |   |`, stripped ` R2C1 |   `, split `[' R2C1 ', '   ']`, len 2.
    # The test case `| R2C1 |              Too few cols` has "Too few cols" as part of the cell.
    # `| R2C1 | Too few cols` -> ` R2C1 | Too few cols ` -> split -> [` R2C1 `, ` Too few cols `] -> 2 columns. This is correct.
    # Let's test `| R2C1 |`
    test_tables_col_mismatch_data_strict_few = """
    | H1 | H2 |
    |----|----|
    | R1C1 |
    """ # R1C1 is 1 column if we consider content. count_table_columns will give 1.
    errors_col_mismatch_data_strict_few = validate_table_structure(test_tables_col_mismatch_data_strict_few)
    assert len(errors_col_mismatch_data_strict_few) == 1, f"Expected 1 error for strict few cols, got {len(errors_col_mismatch_data_strict_few)}: {errors_col_mismatch_data_strict_few}"
    assert errors_col_mismatch_data_strict_few[0]["line_number"] == 4
    assert "Row 4 has 1 columns, expected 2" in errors_col_mismatch_data_strict_few[0]["message"]
    print("OK (table data strict single column detected as fewer).")


    test_tables_header_sep_mismatch = """
    | H1 | H2 | H3 | H4 | Four header declared columns
    |----|----|----|     Separator implies 3 columns
    | R1C1 | R1C2 | R1C3 |
    """
    errors_header_sep_mismatch = validate_table_structure(test_tables_header_sep_mismatch)
    # The logic now uses separator count as definitive. Header should match separator.
    # Separator `|----|----|----|` has 3 columns. Header `|H1|H2|H3|H4|` has 4.
    # So, an error on the header line. Then data rows are checked against 3 cols.
    assert len(errors_header_sep_mismatch) == 1, f"Expected 1 error for header/sep mismatch, got {len(errors_header_sep_mismatch)}: {errors_header_sep_mismatch}"
    assert errors_header_sep_mismatch[0]["line_number"] == 2, f"Incorrect line for header/sep mismatch: {errors_header_sep_mismatch[0]['line_number']}"
    assert "header on line 2 has 4 columns, but separator line implies 3 columns" in errors_header_sep_mismatch[0]["message"]
    # The data row R1C1 | R1C2 | R1C3 | has 3 columns, matches separator, so no error there.
    print("OK (table header/separator column mismatch detected).")

    test_tables_no_pipes_in_data = """
    | H1 | H2 |
    |----|----|
    R1C1   R1C2  (This line is not part of the table)
    | R2C1 | R2C2 |
    """
    errors_no_pipes = validate_table_structure(test_tables_no_pipes_in_data)
    # The table ends after the separator. The line "R1C1 R1C2" does not have pipes and is not a separator.
    # Then a new table starts with "| R2C1 | R2C2 |" but it lacks a separator, so it's not detected as a table.
    # So, no errors should be reported by this validator.
    assert not errors_no_pipes, f"Found errors where table should have ended: {errors_no_pipes}"
    print("OK (table ends if data row lacks pipes).")

    test_tables_malformed_separator = """
    | H1 | H2 |
    | -- | -- -- | Missing pipe or too many dashes for a single cell in separator
    | R1 | R2 |
    """
    # The precise_separator_regex should not match the malformed line, so no table is detected.
    errors_malformed_sep = validate_table_structure(test_tables_malformed_separator)
    assert not errors_malformed_sep, f"Detected table with malformed separator: {errors_malformed_sep}"
    print("OK (table not detected with malformed separator).")

    test_tables_optional_outer_pipes = """
    H1 | H2
    ---|---
    R1C1 | R1C2

    | H3 | H4 |
    |----|----|
    | R3C1 | R3C2 |
    """
    errors_optional_pipes = validate_table_structure(test_tables_optional_outer_pipes)
    assert not errors_optional_pipes, f"Found errors with optional outer pipes: {errors_optional_pipes}"
    print("OK (tables with optional outer pipes).")


    print("\nAll basic tests for table structure passed.")


    print("\n--- Testing Image Path Validation ---")
    # Setup a temporary directory for image path testing
    import tempfile
    import shutil
    test_dir = tempfile.mkdtemp()

    # Create some dummy files for testing
    dummy_image_local_path = "dummy_image.png"
    dummy_image_abs_path = os.path.join(test_dir, "abs_dummy_image.png")
    dummy_image_nested_path = os.path.join("assets", "nested_image.jpg")

    with open(os.path.join(test_dir, dummy_image_local_path), "w") as f:
        f.write("dummy")
    with open(dummy_image_abs_path, "w") as f: # abs_dummy_image.png in test_dir
        f.write("dummy_abs")

    os.makedirs(os.path.join(test_dir, "assets"), exist_ok=True)
    with open(os.path.join(test_dir, dummy_image_nested_path), "w") as f:
        f.write("dummy_nested")

    test_images_ok = f"""
    ![Local Image](./{dummy_image_local_path})
    ![Absolute Image]({dummy_image_abs_path})
    ![Nested Image](./assets/nested_image.jpg)
    ![Web Image](http://example.com/image.png)
    ![Web Image Secure](https://example.com/image.jpg)
    Inline ![image](./{dummy_image_local_path}) reference.
    """
    # Test with base_dir = test_dir
    errors_images_ok = validate_image_paths(test_images_ok, base_dir=test_dir)
    assert not errors_images_ok, f"Found image path errors in supposedly OK markdown: {errors_images_ok}"
    print("OK (image paths valid or web).")

    test_images_missing_error = f"""
    ![Missing Local](./missing_image.png)
    ![Missing Nested](./assets/other_missing.gif)
    ![Present Local](./{dummy_image_local_path})
    """
    errors_images_missing = validate_image_paths(test_images_missing_error, base_dir=test_dir)
    assert len(errors_images_missing) == 2, f"Expected 2 errors for missing images, got {len(errors_images_missing)}: {errors_images_missing}"

    found_missing_1 = any(e["line_number"] == 2 and "'./missing_image.png'" in e["message"] for e in errors_images_missing)
    assert found_missing_1, f"Did not find error for './missing_image.png': {errors_images_missing}"

    found_missing_2 = any(e["line_number"] == 3 and "'./assets/other_missing.gif'" in e["message"] for e in errors_images_missing)
    assert found_missing_2, f"Did not find error for './assets/other_missing.gif': {errors_images_missing}"
    print("OK (missing image paths detected).")

    test_images_relative_pathing = f"""
    Text before. ![Image in current dir relative to base_dir]({dummy_image_local_path})
    Subdirectory: ![Image in subdir](./assets/nested_image.jpg)
    Parent directory (will fail if base_dir is root of test_dir): ![Image in parent](../outside_image.png)
    """
    # For the parent directory case, it depends on where 'test_dir' is.
    # If test_dir is e.g. /tmp/sometemp, then ../outside_image.png would be /tmp/outside_image.png
    # This test is more about how os.path.join and os.path.exists resolve it.
    # Let's assume outside_image.png does not exist at `os.path.join(test_dir, "../outside_image.png")`

    errors_images_relative = validate_image_paths(test_images_relative_pathing, base_dir=test_dir)
    # Expect 1 error for ../outside_image.png
    assert len(errors_images_relative) == 1, f"Expected 1 error for parent relative path, got {len(errors_images_relative)}: {errors_images_relative}"
    assert errors_images_relative[0]["line_number"] == 4
    assert "'../outside_image.png'" in errors_images_relative[0]["message"]
    print("OK (image relative pathing, including non-existent parent, handled).")

    # Clean up dummy files and directory
    try:
        shutil.rmtree(test_dir)
        print(f"Cleaned up temp directory: {test_dir}")
    except OSError as e:
        print(f"Error removing temp directory {test_dir}: {e}")

    print("\nAll basic tests for image path validation passed.")


    print("\n--- Testing Empty Section Validation ---")
    test_sections_ok = """
    # Section 1
    This has content.

    ## Section 1.1
    More content.
    <!-- This is a comment, but there's other content -->
    Actual text.

    # Section 2
    Even if it's just one word.
    """
    errors_sections_ok = validate_empty_sections(test_sections_ok)
    assert not errors_sections_ok, f"Found empty section errors in supposedly OK markdown: {errors_sections_ok}"
    print("OK (sections have content).")

    test_sections_empty_error = """
    # Empty Section 1
    <!-- only a comment -->

    ## Empty Section 1.1 (Whitespace only)


    # Section With Content
    Hello.
    ### Empty Sub-Section (no lines at all)
    # Another Section
    Content.
    ## Final Empty Section
    <!-- comment -->
    <!-- another comment -->
    """
    errors_sections_empty = validate_empty_sections(test_sections_empty_error)
    print(f"DEBUG Empty Sections: {errors_sections_empty}")
    assert len(errors_sections_empty) == 4, f"Expected 4 empty section errors, got {len(errors_sections_empty)}: {errors_sections_empty}"

    # Check details of errors (order might vary depending on exact loop/final check logic, so check existence)
    err1_found = any(e["line_number"] == 2 and "Empty Section 1" in e["message"] for e in errors_sections_empty)
    err2_found = any(e["line_number"] == 5 and "Empty Section 1.1" in e["message"] for e in errors_sections_empty)
    err3_found = any(e["line_number"] == 10 and "Empty Sub-Section" in e["message"] for e in errors_sections_empty)
    err4_found = any(e["line_number"] == 13 and "Final Empty Section" in e["message"] for e in errors_sections_empty)

    assert err1_found, "Missing error for 'Empty Section 1'"
    assert err2_found, "Missing error for 'Empty Section 1.1'"
    assert err3_found, "Missing error for 'Empty Sub-Section'"
    assert err4_found, "Missing error for 'Final Empty Section'"
    print("OK (empty sections detected).")

    test_sections_no_content_at_all = """
    # Section One
    # Section Two
    # Section Three
    """
    errors_no_content = validate_empty_sections(test_sections_no_content_at_all)
    assert len(errors_no_content) == 3, f"Expected 3 errors for sections with no lines, got {len(errors_no_content)}: {errors_no_content}"
    assert errors_no_content[0]["line_number"] == 2 and "Section One" in errors_no_content[0]["message"]
    assert errors_no_content[1]["line_number"] == 3 and "Section Two" in errors_no_content[1]["message"]
    assert errors_no_content[2]["line_number"] == 4 and "Section Three" in errors_no_content[2]["message"] # Last section check
    print("OK (sections with no lines between them detected as empty).")

    test_sections_content_then_empty = """
    # Section A
    Has content.
    ## Section B (Empty)
    <!-- just this -->
    ### Section C (Also Empty)
    # Section D
    More Content.
    """
    errors_content_then_empty = validate_empty_sections(test_sections_content_then_empty)
    print(f"DEBUG Content Then Empty: {errors_content_then_empty}")
    assert len(errors_content_then_empty) == 2, f"Expected 2 empty section errors, got {len(errors_content_then_empty)}: {errors_content_then_empty}"
    assert any(e["line_number"] == 4 and "Section B" in e["message"] for e in errors_content_then_empty)
    assert any(e["line_number"] == 6 and "Section C" in e["message"] for e in errors_content_then_empty)
    print("OK (sections with content followed by empty ones detected).")

    print("\nAll basic tests for empty section validation passed.")


    print("\n--- Testing Paragraph Length Validation ---")
    test_para_ok = """
    This is a short paragraph.
    It has two lines.

    This is another short paragraph.
    """
    errors_para_ok = validate_paragraph_length(test_para_ok, max_chars=100) # Max 100 for testing
    assert not errors_para_ok, f"Found paragraph length errors in supposedly OK markdown: {errors_para_ok}"
    print("OK (paragraphs within length limits).")

    test_para_too_long = """
    This is a very long paragraph that is intended to exceed the maximum character limit
    set for testing purposes. It will keep going on and on with more text to ensure that
    it definitely goes over the boundary we have established.
    """ # Approx 200 chars
    errors_para_long = validate_paragraph_length(test_para_too_long, max_chars=150)
    assert len(errors_para_long) == 1, f"Expected 1 error for long paragraph, got {len(errors_para_long)}: {errors_para_long}"
    assert errors_para_long[0]["line_number"] == 2, f"Incorrect line for long paragraph: {errors_para_long[0]['line_number']}"
    assert "is too long" in errors_para_long[0]["message"] and "150 chars" in errors_para_long[0]["message"]
    print("OK (long paragraph detected).")

    test_para_multiple_long = """
    First paragraph, quite long, needs to be over one hundred and fifty characters to trigger the validation error for this specific test case. Yes, still going.

    Second paragraph, also very long, designed to be over the one hundred and fifty character limit to ensure multiple errors can be caught if they exist.
    """
    errors_para_multi_long = validate_paragraph_length(test_para_multiple_long, max_chars=150)
    assert len(errors_para_multi_long) == 2, f"Expected 2 errors for multiple long paragraphs, got {len(errors_para_multi_long)}: {errors_para_multi_long}"
    assert errors_para_multi_long[0]["line_number"] == 2
    assert errors_para_multi_long[1]["line_number"] == 4
    print("OK (multiple long paragraphs detected).")

    test_para_with_other_elements = """
    # Heading
    This paragraph is fine.

    - List item 1
    - List item 2

    > Blockquote text here.
    > And more blockquote.

    This paragraph is also fine and should be checked independently.

    ```python
    def foo():
        pass # code block
    ```

    Final paragraph, which could be long. Let's make this one long as well to test the end-of-file condition for paragraph checking. It must exceed the limit. So more and more text is added here.
    """
    # Calculate length of "Final paragraph..."
    final_para_text = "Final paragraph, which could be long. Let's make this one long as well to test the end-of-file condition for paragraph checking. It must exceed the limit. So more and more text is added here."
    len_final_para = len(final_para_text) # Approx 200

    errors_para_other_elements = validate_paragraph_length(test_para_with_other_elements, max_chars=150)
    # Expected: "This paragraph is fine." (OK)
    # "This paragraph is also fine..." (OK)
    # "Final paragraph..." (Error)
    print(f"DEBUG Paragraphs other elements: {errors_para_other_elements}")
    assert len(errors_para_other_elements) == 1, f"Expected 1 error for long paragraph among others, got {len(errors_para_other_elements)}: {errors_para_other_elements}"
    assert errors_para_other_elements[0]["line_number"] == 16, f"Incorrect line for long paragraph among others: {errors_para_other_elements[0]['line_number']}"
    assert str(len_final_para) in errors_para_other_elements[0]["message"]
    print("OK (paragraphs correctly identified among other Markdown elements).")

    test_para_at_eof_ok = "This is a paragraph right at the end of the file and it's short."
    errors_para_eof_ok = validate_paragraph_length(test_para_at_eof_ok, max_chars=100)
    assert not errors_para_eof_ok, f"Found error for short EOF paragraph: {errors_para_eof_ok}"
    print("OK (short paragraph at EOF is fine).")

    print("\nAll basic tests for paragraph length validation passed.")


    print("\n--- Testing Problematic Whitespace Validation ---")
    test_whitespace_ok = """
    This is a line with no issues.
    - List item with one space.
    * Another list item.
    1. Ordered item.
    Indented line for code (ignored by this check if it were a code block, but here it's just leading space)
        Indented further.
    | Table | Col |
    |-------|-----|
    | A  B  | C   | (Spaces in table cells are fine by this rule)

    ```python
    def foo():
        return "  Hello  \tWorld  " # Inside code block, ignored
    ```
    """
    errors_whitespace_ok = validate_problematic_whitespace(test_whitespace_ok)
    assert not errors_whitespace_ok, f"Found whitespace errors in supposedly OK markdown: {errors_whitespace_ok}"
    print("OK (no problematic whitespace).")

    test_whitespace_errors = """
    Line with trailing space.
    Line with trailing tab.\t
    This  has  double  spaces.
    And this one also  has some.
    A line with a mid-line\t tab.
    Another\tline\twith\ttabs.
        Leading spaces then a\ttab.
    - List  item with  double space.
    """
    # Expected errors:
    # 1. Trailing space (line 2)
    # 2. Trailing tab (line 3)
    # 3. Double spaces (line 4) - 1 error
    # 4. Double spaces (line 5) - 1 error
    # 5. Mid-line tab (line 6) - 1 error
    # 6. Mid-line tabs (line 7) - 1 error (multiple tabs, but one error per line for this rule)
    # 7. Mid-line tab after leading spaces (line 8) - 1 error
    # 8. List item with double space (line 9) - 1 error (current rule for multiple spaces will catch this if not handled by list exclusion)
    # The list exclusion `re.match(r"^([*+-]|\d+[.)])\s\s+"` will prevent error for "-   item" but not for "- item  extra"
    # The line "- List  item with  double space." lstrip() is "List  item with  double space." which contains "  ".
    # The list specific exclusion `if not (re.match(r"^([*+-]|\d+[.)])\s\s+", line_content_part)`
    # `line_content_part` for "List  item with  double space." would be "List  item with  double space."
    # This regex won't match, so it *will* be flagged. This is intended for now.

    errors_ws = validate_problematic_whitespace(test_whitespace_errors)
    print(f"DEBUG Whitespace errors: {errors_ws}")

    num_expected_errors = 8
    assert len(errors_ws) == num_expected_errors, f"Expected {num_expected_errors} whitespace errors, got {len(errors_ws)}: {errors_ws}"

    # Check for specific error types and lines
    assert any(e["line_number"] == 2 and "trailing whitespace" in e["message"] for e in errors_ws), "Missing trailing space error"
    assert any(e["line_number"] == 3 and "trailing whitespace" in e["message"] for e in errors_ws), "Missing trailing tab error"
    assert any(e["line_number"] == 4 and "multiple consecutive internal spaces" in e["message"] for e in errors_ws), "Missing double space error line 4"
    assert any(e["line_number"] == 5 and "multiple consecutive internal spaces" in e["message"] for e in errors_ws), "Missing double space error line 5"
    assert any(e["line_number"] == 6 and "mid-line alignment" in e["message"] for e in errors_ws), "Missing mid-line tab error line 6"
    assert any(e["line_number"] == 7 and "mid-line alignment" in e["message"] for e in errors_ws), "Missing mid-line tab error line 7"
    assert any(e["line_number"] == 8 and "mid-line alignment" in e["message"] for e in errors_ws), "Missing mid-line tab after spaces error line 8"
    assert any(e["line_number"] == 9 and "multiple consecutive internal spaces" in e["message"] for e in errors_ws), "Missing double space in list item line 9"
    print("OK (problematic whitespace detected).")

    test_whitespace_in_code = """
    ```text
    This  line has  double spaces.
    And a trailing space.
    And a mid-line\ttab.
    ```
    Outside code  block now.
    """
    errors_ws_code = validate_problematic_whitespace(test_whitespace_in_code)
    # Expect 1 error for "Outside code  block now." (multiple internal spaces)
    # Plus potentially trailing space on line 3 if not handled by rstrip before check.
    # The current code `line = line_with_ending.rstrip('\r\n')` means trailing check happens on this `line`.
    # So, line 3 `And a trailing space. ` will have trailing space.
    # Line 4 `And a mid-line\ttab.` will have mid-line tab.
    # Line 2 `This  line has  double spaces.` will have double spaces.
    # All these are INSIDE the code block, so they should be IGNORED.

    # The `continue` after toggling `in_fenced_code_block` ensures fence lines themselves aren't checked.
    # The `if not in_fenced_code_block:` ensures content lines inside are not checked.

    print(f"DEBUG WS Code: {errors_ws_code}")
    assert len(errors_ws_code) == 1, f"Expected 1 error outside code block, got {len(errors_ws_code)}: {errors_ws_code}"
    assert errors_ws_code[0]["line_number"] == 6 and "multiple consecutive internal spaces" in errors_ws_code[0]["message"]
    print("OK (whitespace issues correctly ignored inside fenced code blocks).")

    print("\nAll basic tests for problematic whitespace validation passed.")
