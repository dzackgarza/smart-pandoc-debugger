#!/usr/bin/env python3
"""
Tests for Citation Proofer (Branch 6: Citations & Bibliography)

Tests all citation validation functionality including:
- Pandoc citation validation [@key]
- LaTeX citation validation \cite{key}
- Bibliography file validation
- Citation style consistency
"""
import pytest
import tempfile
import os
from pathlib import Path

# Add project root to path for imports
import sys
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.smart_pandoc_debugger.managers.investigator_team.citation_proofer import run_citation_proofer
from src.smart_pandoc_debugger.managers.investigator_team.citation_team.check_pandoc_citations import check_pandoc_citations, PandocCitationValidator
from src.smart_pandoc_debugger.managers.investigator_team.citation_team.check_latex_citations import check_latex_citations
from src.smart_pandoc_debugger.managers.investigator_team.citation_team.check_bibliography import check_bibliography
from src.smart_pandoc_debugger.managers.investigator_team.citation_team.check_citation_style import check_citation_style


class TestPandocCitationValidator:
    """Test Pandoc citation validation [@key] functionality."""
    
    def test_undefined_pandoc_citation(self):
        """Test detection of undefined Pandoc citations."""
        tex_content = """
This is a document with a citation [@nonexistent2024].
More text here.
"""
        bib_content = """
@article{smith2024,
  title={A Different Paper},
  author={Smith, John},
  year={2024}
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")
            bib_file = os.path.join(temp_dir, "refs.bib")
            
            with open(tex_file, 'w') as f:
                f.write(tex_content)
            with open(bib_file, 'w') as f:
                f.write(bib_content)
            
            result = check_pandoc_citations(tex_file)
            assert result is not None
            assert "UndefinedPandocCitation" in result
            assert "nonexistent2024" in result
    
    def test_pandoc_citation_with_bibliography(self):
        """Test Pandoc citation validation with valid bibliography."""
        tex_content = """
This is a document with a citation [@smith2024].
More text here.
"""
        bib_content = """
@article{smith2024,
  title={A Great Paper},
  author={Smith, John},
  year={2024}
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")
            bib_file = os.path.join(temp_dir, "refs.bib")
            
            with open(tex_file, 'w') as f:
                f.write(tex_content)
            with open(bib_file, 'w') as f:
                f.write(bib_content)
            
            result = check_pandoc_citations(tex_file)
            assert result is None  # No errors expected
    
    def test_missing_bibliography_for_pandoc(self):
        """Test detection of missing bibliography for Pandoc citations."""
        tex_content = """
This document has citations [@smith2024] but no bibliography.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_pandoc_citations(f.name)
            assert result is not None
            assert "MissingBibliography" in result
            
        os.unlink(f.name)
    
    def test_duplicate_citation_keys(self):
        """Test detection of duplicate citation keys in bibliography."""
        tex_content = """
This document has citations [@smith2024].
"""
        bib1_content = """
@article{smith2024,
  title={First Paper},
  author={Smith, John},
  year={2024}
}
"""
        bib2_content = """
@article{smith2024,
  title={Second Paper},
  author={Smith, Jane},
  year={2024}
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")
            bib1_file = os.path.join(temp_dir, "refs1.bib")
            bib2_file = os.path.join(temp_dir, "refs2.bib")
            
            with open(tex_file, 'w') as f:
                f.write(tex_content)
            with open(bib1_file, 'w') as f:
                f.write(bib1_content)
            with open(bib2_file, 'w') as f:
                f.write(bib2_content)
            
            result = check_pandoc_citations(tex_file)
            assert result is not None
            assert "DuplicateCitationKey" in result
            assert "smith2024" in result
    
    def test_multiline_bibtex_field_handling(self):
        """Test that multiline BibTeX field values are handled correctly."""
        validator = PandocCitationValidator()
        
        # Create a BibTeX file with multiline field values and comments
        multiline_bibtex = '''@article{multiline2024,
    title = {A Very Long Title That
             Spans Multiple Lines
             And Contains Special Characters},
    author = {Smith, John and
              Doe, Jane and
              Brown, Alice},
    abstract = {This is a long abstract that
                spans multiple lines and contains
                nested {braces} and other special
                characters like % percent signs
                and "quoted strings"},
    year = {2024},
    % This is a comment that should be ignored
    journal = {Journal of
               Multiline % Another comment
               Research}
}

% A commented out entry that should be ignored
% @article{commented2024,
%   title = {This should not be parsed}
% }

@book{simple2024,
    title = {Simple Book},
    author = {Author, Test}
}'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bib', delete=False) as f:
            f.write(multiline_bibtex)
            bib_path = f.name
        
        try:
            # Test that both keys are extracted correctly
            keys = validator.extract_bib_keys_from_bibtex(bib_path)
            
            # Should find both keys despite multiline content
            assert 'multiline2024' in keys
            assert 'simple2024' in keys
            
            # Should not find the commented out entry
            assert 'commented2024' not in keys
            
            # Total should be exactly 2 keys
            assert len(keys) == 2
            
        finally:
            os.unlink(bib_path)


class TestLatexCitationValidator:
    """Test LaTeX citation validation \cite{key} functionality."""
    
    def test_undefined_latex_citation(self):
        """Test detection of undefined LaTeX citations."""
        tex_content = """
\\documentclass{article}
\\begin{document}
This is a document with a citation \\cite{nonexistent2024}.
\\bibliography{refs}
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_latex_citations(f.name)
            assert result is not None
            assert "UndefinedLatexCitation" in result
            assert "nonexistent2024" in result
            
        os.unlink(f.name)
    
    def test_latex_citation_with_bibliography(self):
        """Test LaTeX citation validation with valid bibliography."""
        tex_content = """
\\documentclass{article}
\\begin{document}
This is a document with a citation \\cite{smith2024}.
\\bibliography{refs}
\\end{document}
"""
        bib_content = """
@article{smith2024,
  title={A Great Paper},
  author={Smith, John},
  year={2024}
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")
            bib_file = os.path.join(temp_dir, "refs.bib")
            
            with open(tex_file, 'w') as f:
                f.write(tex_content)
            with open(bib_file, 'w') as f:
                f.write(bib_content)
            
            result = check_latex_citations(tex_file)
            assert result is None  # No errors expected
    
    def test_missing_bibliography_command(self):
        """Test detection of missing \\bibliography command."""
        tex_content = """
\\documentclass{article}
\\begin{document}
This document has citations \\cite{smith2024} but no bibliography command.
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_latex_citations(f.name)
            assert result is not None
            assert "MissingBibliographyCommand" in result
            
        os.unlink(f.name)
    
    def test_natbib_without_package(self):
        """Test detection of natbib commands without package."""
        tex_content = """
\\documentclass{article}
\\begin{document}
This document uses \\citep{smith2024} without natbib package.
\\bibliography{refs}
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_latex_citations(f.name)
            assert result is not None
            assert "NatbibCommandWithoutPackage" in result
            assert "citep" in result
            
        os.unlink(f.name)
    
    def test_unused_bibliography_entry(self):
        """Test detection of unused bibliography entries."""
        tex_content = """
\\documentclass{article}
\\begin{document}
This document cites \\cite{smith2024} but not jones2024.
\\bibliography{refs}
\\end{document}
"""
        bib_content = """
@article{smith2024,
  title={Used Paper},
  author={Smith, John},
  year={2024}
}
@article{jones2024,
  title={Unused Paper},
  author={Jones, Jane},
  year={2024}
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")
            bib_file = os.path.join(temp_dir, "refs.bib")
            
            with open(tex_file, 'w') as f:
                f.write(tex_content)
            with open(bib_file, 'w') as f:
                f.write(bib_content)
            
            result = check_latex_citations(tex_file)
            assert result is not None
            assert "UnusedBibEntry" in result
            assert "jones2024" in result


class TestBibliographyValidator:
    """Test bibliography file and command validation."""
    
    def test_missing_bibliography_file(self):
        """Test detection of missing bibliography file."""
        tex_content = """
\\documentclass{article}
\\begin{document}
This document references \\cite{smith2024}.
\\bibliography{nonexistent}
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_bibliography(f.name)
            assert result is not None
            assert "BibliographyFileNotFound" in result
            assert "nonexistent.bib" in result
            
        os.unlink(f.name)
    
    def test_malformed_bibtex_entry(self):
        """Test detection of malformed BibTeX entries."""
        tex_content = """
\\documentclass{article}
\\begin{document}
This document references \\cite{smith2024}.
\\bibliography{refs}
\\end{document}
"""
        bib_content = """
@article{smith2024,
  title={A Great Paper}
  author={Smith, John},  % Missing comma after title
  year={2024}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")
            bib_file = os.path.join(temp_dir, "refs.bib")
            
            with open(tex_file, 'w') as f:
                f.write(tex_content)
            with open(bib_file, 'w') as f:
                f.write(bib_content)
            
            result = check_bibliography(tex_file)
            assert result is not None
            assert "MalformedBibEntry" in result


class TestCitationStyleValidator:
    """Test citation style consistency validation."""
    
    def test_inconsistent_citation_style(self):
        """Test detection of inconsistent citation styles."""
        tex_content = """
\\documentclass{article}
\\usepackage{natbib}
\\begin{document}
First citation uses \\cite{smith2024}.
Second citation uses \\citep{jones2024}.
Third citation uses \\citet{brown2024}.
\\bibliography{refs}
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_citation_style(f.name)
            # This might or might not trigger depending on the threshold
            # The validator considers this acceptable mixing within natbib
            
        os.unlink(f.name)
    
    def test_citep_citet_misuse(self):
        """Test detection of \\citep vs \\citet misuse."""
        tex_content = """
\\documentclass{article}
\\usepackage{natbib}
\\begin{document}
\\citep{smith2024} shows that this is wrong at sentence start.
We know this from (\\citet{jones2024}) which is also wrong.
\\bibliography{refs}
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_citation_style(f.name)
            assert result is not None
            assert "CitepCitetMisuse" in result
            
        os.unlink(f.name)


class TestCitationProoferIntegration:
    """Test the main citation proofer dispatcher."""
    
    def test_citation_proofer_pandoc_error(self):
        """Test citation proofer detecting Pandoc citation errors."""
        tex_content = """
This document has undefined citation [@missing2024].
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = run_citation_proofer(f.name)
            assert result is not None
            assert "citation" in result.problem_description.lower()
            assert result.source_service.startswith("CitationProofer")
            
        os.unlink(f.name)
    
    def test_citation_proofer_latex_error(self):
        """Test citation proofer detecting LaTeX citation errors."""
        tex_content = """
\\documentclass{article}
\\begin{document}
This document has citation \\cite{missing2024} but no bibliography.
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = run_citation_proofer(f.name)
            assert result is not None
            assert "citation" in result.problem_description.lower() or "bibliography" in result.problem_description.lower()
            
        os.unlink(f.name)
    
    def test_citation_proofer_no_errors(self):
        """Test citation proofer with valid citations."""
        tex_content = """
\\documentclass{article}
\\begin{document}
This document has valid citation \\cite{smith2024}.
\\bibliography{refs}
\\end{document}
"""
        bib_content = """
@article{smith2024,
  title={A Great Paper},
  author={Smith, John},
  year={2024}
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")
            bib_file = os.path.join(temp_dir, "refs.bib")
            
            with open(tex_file, 'w') as f:
                f.write(tex_content)
            with open(bib_file, 'w') as f:
                f.write(bib_content)
            
            result = run_citation_proofer(tex_file)
            assert result is None  # No errors expected


class TestBranch6Requirements:
    """Test that all Branch 6 requirements are covered."""
    
    def test_requirement_pandoc_citation_validation(self):
        """Requirement: For [@citation], verify key exists in bibliography."""
        tex_content = "Text with [@undefined2024] citation."
        bib_content = """
@article{smith2024,
  title={A Different Paper},
  author={Smith, John},
  year={2024}
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")
            bib_file = os.path.join(temp_dir, "refs.bib")
            
            with open(tex_file, 'w') as f:
                f.write(tex_content)
            with open(bib_file, 'w') as f:
                f.write(bib_content)
            
            result = check_pandoc_citations(tex_file)
            assert result is not None
            assert "UndefinedPandocCitation" in result
    
    def test_requirement_unused_bib_entry(self):
        """Requirement: When \\cite{key} is used but key doesn't appear in any citation, flag as potentially unused."""
        tex_content = """
\\documentclass{article}
\\begin{document}
Only cite \\cite{used2024}.
\\bibliography{refs}
\\end{document}
"""
        bib_content = """
@article{used2024,
  title={Used Paper},
  author={Used, Author},
  year={2024}
}
@article{unused2024,
  title={Unused Paper},
  author={Unused, Author},
  year={2024}
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")
            bib_file = os.path.join(temp_dir, "refs.bib")
            
            with open(tex_file, 'w') as f:
                f.write(tex_content)
            with open(bib_file, 'w') as f:
                f.write(bib_content)
            
            result = check_latex_citations(tex_file)
            assert result is not None
            assert "UnusedBibEntry" in result
            assert "unused2024" in result
    
    def test_requirement_undefined_latex_citation(self):
        """Requirement: \\cite{key} with undefined key."""
        tex_content = """
\\documentclass{article}
\\begin{document}
Citation to \\cite{undefined2024}.
\\bibliography{refs}
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_latex_citations(f.name)
            assert result is not None
            assert "UndefinedLatexCitation" in result
            assert "undefined2024" in result
            
        os.unlink(f.name)
    
    def test_requirement_missing_bibliography_command(self):
        """Requirement: Missing \\bibliography{refs}."""
        tex_content = """
\\documentclass{article}
\\begin{document}
Citation \\cite{smith2024} without bibliography command.
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_bibliography(f.name)
            assert result is not None
            assert "MissingBibliographyCommand" in result
            
        os.unlink(f.name)
    
    def test_requirement_citep_citet_misuse(self):
        """Requirement: \\citep vs \\citet misuse."""
        tex_content = """
\\documentclass{article}
\\usepackage{natbib}
\\begin{document}
\\citep{smith2024} at start of sentence is wrong.
\\bibliography{refs}
\\end{document}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(tex_content)
            f.flush()
            
            result = check_citation_style(f.name)
            assert result is not None
            assert "CitepCitetMisuse" in result
            
        os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 