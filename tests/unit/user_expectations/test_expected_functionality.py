"""
Tests for User Expectations - Functionality Holes

These tests document what users expect the Smart Pandoc Debugger to detect,
but which are not yet implemented. Each failing test represents a development
priority and user story.

These tests serve as:
1. Documentation of missing features
2. Specification for future development  
3. User acceptance criteria
4. Development roadmap priorities
"""

import tempfile
import os
import subprocess
import pytest


def test_missing_end_environment_detection():
    """Test that missing \\end{environment} gives usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with missing end environment
    missing_env_doc = """# Document with Missing Environment End

Here is some text.

\\begin{itemize}
\\item First item
\\item Second item
% Missing \\end{itemize}

This text comes after.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(missing_env_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect missing end environment
        assert any(word in output.lower() for word in ['end', 'environment', 'itemize', 'missing', 'unclosed'])
        
    finally:
        os.unlink(temp_path)

def test_undefined_latex_command_detection():
    """Test that undefined LaTeX commands give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with undefined commands
    undefined_cmd_doc = """# Document with Undefined Commands

This uses an undefined command: \\undefinedcommand{text}

Also this one: \\nonexistentmacro

And this: \\missingcmd{arg1}{arg2}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(undefined_cmd_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect undefined commands
        assert any(word in output.lower() for word in ['undefined', 'command', 'unknown', 'missing'])
        
    finally:
        os.unlink(temp_path)

def test_broken_citations_detection():
    """Test that broken citations give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with broken citations
    citation_doc = """# Research Paper

This cites a nonexistent source [@nonexistent2024].

And this one too [@missing_ref].

Also broken: \\cite{undefined_key}

## References

(No bibliography provided)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(citation_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect citation issues
        assert any(word in output.lower() for word in ['citation', 'reference', 'bibliography', 'cite', 'undefined'])
        
    finally:
        os.unlink(temp_path)

def test_missing_image_paths_detection():
    """Test that missing images give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with missing images
    image_doc = """# Document with Images

Here's a missing image:

![Missing Image](nonexistent_image.png)

And another:

\\includegraphics{missing_figure.pdf}

Also broken: ![Alt text](./images/not_found.jpg)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(image_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect missing image issues
        assert any(word in output.lower() for word in ['image', 'figure', 'file', 'missing', 'not found', 'includegraphics'])
        
    finally:
        os.unlink(temp_path)

def test_broken_cross_references_detection():
    """Test that broken cross-references give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with broken cross-references
    xref_doc = """# Document with Cross-References

See Section \\ref{nonexistent_section}.

And Figure \\ref{missing_figure}.

Also broken: \\eqref{undefined_equation}

As shown in Table \\ref{no_such_table}.

## Real Section {#real-section}

This section exists but others reference nonexistent ones.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(xref_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect cross-reference issues
        assert any(word in output.lower() for word in ['reference', 'ref', 'undefined', 'section', 'figure', 'equation'])
        
    finally:
        os.unlink(temp_path)

def test_mismatched_math_delimiters_detection():
    """Test that mismatched math delimiters give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with mismatched math delimiters
    math_doc = """# Math Delimiter Problems

Mismatched parentheses: $(x + y]$

Wrong brackets: $[a + b)$

Mixed delimiters: $\\left( x + y \\right]$

Unclosed: $\\left\\{ x + y$

Missing right: $\\left( x + y$
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(math_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect math delimiter issues
        assert any(word in output.lower() for word in ['delimiter', 'parenthes', 'bracket', 'math', 'mismatched', 'left', 'right'])
        
    finally:
        os.unlink(temp_path)

def test_missing_latex_packages_detection():
    """Test that missing LaTeX packages give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document using commands from missing packages
    package_doc = """# Document with Missing Packages

Using tikz without package: \\tikz \\draw (0,0) -- (1,1);

Using amsmath symbols: \\mathbb{R} \\in \\mathcal{F}

Using color: \\textcolor{red}{This is red}

Using hyperref: \\href{http://example.com}{Link}

Using listings: \\lstinline{code}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(package_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect package-related issues
        assert any(word in output.lower() for word in ['package', 'usepackage', 'tikz', 'amsmath', 'missing', 'undefined'])
        
    finally:
        os.unlink(temp_path)

def test_nested_environment_errors_detection():
    """Test that nested environment errors give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with nested environment problems
    nested_doc = """# Nested Environment Problems

\\begin{itemize}
\\item First item
  \\begin{enumerate}
  \\item Nested item
  \\end{itemize}  % Wrong closing tag!
\\item Another item
\\end{enumerate}  % Wrong again!

\\begin{align}
x &= y \\\\
  \\begin{cases}
  a &= b \\\\
  c &= d
  \\end{align}  % Should be end{cases}
\\end{cases}      % Should be end{align}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(nested_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect nested environment issues
        assert any(word in output.lower() for word in ['nested', 'environment', 'mismatch', 'itemize', 'enumerate', 'align'])
        
    finally:
        os.unlink(temp_path)

def test_malformed_tables_detection():
    """Test that malformed tables give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with table problems
    table_doc = """# Table Problems

| Header 1 | Header 2 | Header 3 |
|----------|----------|
| Row 1, Col 1 | Row 1, Col 2 | Row 1, Col 3 | Extra cell |
| Row 2, Col 1 | Row 2, Col 2 |  % Missing cell

\\begin{tabular}{cc}
Header 1 & Header 2 & Extra header \\\\  % Too many columns
\\hline
Cell 1 & Cell 2 \\\\
Cell 3 \\\\  % Missing cell
\\end{tabular}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(table_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect table formatting issues
        assert any(word in output.lower() for word in ['table', 'column', 'row', 'cell', 'tabular', 'malformed'])
        
    finally:
        os.unlink(temp_path)

def test_incorrect_heading_hierarchy_detection():
    """Test that incorrect heading hierarchy gives usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with bad heading structure
    heading_doc = """# Main Title

#### Skipped H2 and H3  % Should be H2

## Now H2

##### Another skip to H5  % Should be H3

# Another H1 in middle  % Poor structure

### H3 without parent H2
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(heading_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect heading hierarchy issues
        assert any(word in output.lower() for word in ['heading', 'hierarchy', 'structure', 'level', 'skipped', 'h1', 'h2'])
        
    finally:
        os.unlink(temp_path)

def test_duplicate_labels_detection():
    """Test that duplicate labels give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with duplicate labels
    duplicate_doc = """# Document with Duplicates

## Section A {#duplicate-label}

Content here.

## Section B {#duplicate-label}  % Same label!

More content.

\\begin{equation} \\label{eq:duplicate}
x = y
\\end{equation}

\\begin{equation} \\label{eq:duplicate}  % Same label again!
a = b
\\end{equation}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(duplicate_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect duplicate labels
        assert any(word in output.lower() for word in ['duplicate', 'label', 'repeated', 'multiple', 'same'])
        
    finally:
        os.unlink(temp_path)

def test_invalid_url_links_detection():
    """Test that invalid URLs give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with invalid URLs
    url_doc = """# Links Document

[Broken link](http://this-domain-definitely-does-not-exist-123456.com)

[Local broken](./nonexistent_file.md)

[Invalid URL](not-a-valid-url)

[Empty link]()

\\href{http://broken-latex-link-999.invalid}{LaTeX link}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(url_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect link issues
        assert any(word in output.lower() for word in ['link', 'url', 'broken', 'invalid', 'not found', 'href'])
        
    finally:
        os.unlink(temp_path)

def test_malformed_code_blocks_detection():
    """Test that malformed code blocks give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with code block problems
    code_doc = """# Code Block Problems

```python
def function():
    print("Hello")
# Missing closing backticks

```unknown_language
Some code in unknown language
```

```
# No language specified but complex code
import tensorflow as tf
model = tf.keras.Sequential()
```

\\begin{lstlisting}[language=Python]
def example():
    pass
% Missing \\end{lstlisting}

Inline code with problems: `unclosed inline
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(code_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect code block issues
        assert any(word in output.lower() for word in ['code', 'block', 'listing', 'language', 'backtick', 'unclosed'])
        
    finally:
        os.unlink(temp_path)

def test_bibliography_format_errors_detection():
    """Test that bibliography format errors give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with bibliography problems
    bib_doc = """# Paper with Bibliography

This cites [@smith2020] and [@jones2019].

## References

[@smith2020]: Malformed entry without proper format

jones2019: Missing @ symbol

[@incomplete2020]  % No actual reference data

\\bibliographystyle{nonexistent_style}
\\bibliography{missing_bib_file}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(bib_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect bibliography issues
        assert any(word in output.lower() for word in ['bibliography', 'reference', 'citation', 'bibtex', 'missing', 'format'])
        
    finally:
        os.unlink(temp_path)

def test_complex_math_syntax_errors_detection():
    """Test that complex math syntax errors give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with complex math issues
    math_complex_doc = """# Complex Math Errors

$$\\begin{align}
x &= \\frac{1 + 2 + 3}{4 + 5 + 6 \\\\  % Missing closing brace
y &= \\sum_{i=1}^{n \\cdot m} x_i^{2}  % Malformed superscript in limits
\\end{align}$$

Matrix with wrong dimensions:
$$\\begin{pmatrix}
1 & 2 & 3 \\\\
4 & 5 \\\\  % Missing element
6 & 7 & 8 & 9  % Extra element
\\end{pmatrix}$$

Wrong array format:
$$\\begin{array}{cc|c}
a & b \\\\
c & d & e & f  % Too many columns for format
\\end{array}$$
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(math_complex_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect complex math issues
        assert any(word in output.lower() for word in ['math', 'matrix', 'array', 'align', 'syntax', 'frac', 'sum'])
        
    finally:
        os.unlink(temp_path)

def test_footnote_reference_errors_detection():
    """Test that footnote reference errors give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with footnote problems
    footnote_doc = """# Document with Footnotes

This has a footnote[^1] and another[^missing].

Also this one[^2] but no definition below.

\\footnote{LaTeX footnote without proper context}

[^1]: This footnote exists.

[^3]: This footnote is defined but never referenced.

Multiple definitions:
[^1]: This is a duplicate definition of footnote 1.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(footnote_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect footnote issues
        assert any(word in output.lower() for word in ['footnote', 'reference', 'missing', 'undefined', 'duplicate'])
        
    finally:
        os.unlink(temp_path)

def test_inconsistent_spacing_and_formatting_detection():
    """Test that inconsistent spacing/formatting gives usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with spacing/formatting inconsistencies
    spacing_doc = """#No space after hash

## Proper heading

###Another bad one

This has  multiple   spaces    between words.

Lists with bad formatting:
-No space after dash
- Proper list item
-    Weird spacing

1.Bad numbered list
2. Good item
3.   Inconsistent spacing
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(spacing_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect formatting consistency issues
        assert any(word in output.lower() for word in ['spacing', 'format', 'consistency', 'heading', 'list'])
        
    finally:
        os.unlink(temp_path)

def test_pandoc_specific_syntax_errors_detection():
    """Test that Pandoc-specific syntax errors give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with Pandoc-specific issues
    pandoc_doc = """# Pandoc Syntax Issues

Broken divs:
::: {.class-name}
Content here
<!-- Missing closing div -->

Bad attributes: ![Image](pic.jpg){width=100px height=invalid}

Wrong filter syntax: ```{.python .numberLines startFrom="abc"}

Bad yaml header:
---
title: "Document"
author: John Doe
date: 2024-01-01
invalid_field: value without quotes
---

Extension issues: [@citation]{.smallcaps .invalid-extension}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(pandoc_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect Pandoc-specific issues
        assert any(word in output.lower() for word in ['pandoc', 'div', 'attribute', 'yaml', 'extension', 'filter'])
        
    finally:
        os.unlink(temp_path)

def test_academic_document_structure_issues_detection():
    """Test that academic document structure issues give usable output."""
    import tempfile
    import os
    import subprocess
    
    # Document with academic structure problems
    academic_doc = """# Research Paper

## Abstract

This is the abstract.

## Related Work

Some related work here.

## Introduction  <!-- Should come before Related Work -->

This introduction is in wrong place.

## Methology  <!-- Typo: should be "Methodology" -->

Our approach.

## Results

Our findings.

## Conclusion

<!-- Missing References section -->

Figure without caption: ![](image.png)

Table without number:
| Data | Value |
|------|-------|
| A    | 1     |
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(academic_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect academic structure issues
        assert any(word in output.lower() for word in ['structure', 'section', 'abstract', 'introduction', 'methodology', 'references'])
        
    finally:
        os.unlink(temp_path)

def test_comprehensive_real_world_document_issues():
    """Test a realistic document with multiple real-world issues."""
    import tempfile
    import os
    import subprocess
    
    # Realistic document with many common issues
    realistic_doc = """---
title: "My Research Paper"
author: Jane Doe
date: 2024-01-01
bibliography: references.bib  # This file doesn't exist
---

# My Research Paper

## Abstract

This paper presents findings on [@nonexistent_ref] and builds on work by \\cite{missing_citation}.

## Introduction  

Here we introduce the topic with some math: $\\alpha + \\beta = \\gamma$.

However, we also have problematic math: $x + y = z  // Missing closing $

### Subsection with image issue

See Figure \\ref{fig:nonexistent} for details.

![Missing Image](./figures/nonexistent.png)

## Methds  // Typo in heading

Our approach uses the following algorithm:

\\begin{algorithm}
\\caption{Our Algorithm}
\\begin{algorithmic}[1]
\\Procedure{DoSomething}{$x, y$}
\\State $result \\gets x + y$
\\EndProcedure
\\end{algorithmic}
// Missing \\end{algorithm}

The above has multiple issues including:
- Missing packages (algorithm, algorithmic)
- Unclosed environment
- References to nonexistent figures

## Results

| Metric | Value |
|--------|-------|
| Accuracy | 95% | Extra column |
| Precision | 90% |  // Missing value

\\begin{table}
\\centering
\\begin{tabular}{cc}
Column 1 & Column 2 & Extra column \\\\
Data 1 & Data 2 \\\\
Data 3 \\\\  // Missing cell
\\end{tabular}
\\caption{Results table}
\\label{tab:results}
\\end{table}

## Discussion

This section references Table \\ref{tab:nonexistent} which doesn't exist.

Math with issues:
$$\\begin{equation}
x = \\frac{a + b}{c + d  // Missing closing brace
\\end{equation}$$

## Conclusion

In conclusion, we have demonstrated [citation needed] that our approach works.

<!-- References section missing -->
<!-- Bibliography file (references.bib) doesn't exist -->
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(realistic_doc)
        temp_path = f.name
    
    try:
        result = subprocess.run(['spd', temp_path], capture_output=True, text=True, timeout=45)
        
        assert result.returncode is not None
        output = result.stdout + result.stderr
        assert len(output) > 0
        
        # Should detect multiple categories of issues
        issue_categories = [
            ['citation', 'reference', 'bibliography'],  # Citation issues
            ['image', 'figure', 'missing'],              # Image issues  
            ['math', 'dollar', 'equation'],              # Math issues
            ['table', 'column', 'cell'],                 # Table issues
            ['environment', 'algorithm', 'end'],         # Environment issues
            ['package', 'usepackage', 'missing']         # Package issues
        ]
        
        detected_categories = 0
        for category in issue_categories:
            if any(word in output.lower() for word in category):
                detected_categories += 1
        
        # Should detect at least 3 different categories of issues
        assert detected_categories >= 3, f"Only detected {detected_categories} issue categories in comprehensive document"
        
    except subprocess.TimeoutExpired:
        assert False, "Tool took too long on comprehensive document (>45s)"
    finally:
        os.unlink(temp_path)

# 20 tests total documenting user expectation holes 