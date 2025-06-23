#!/usr/bin/env python3
"""
Bibliography Checker
Validates bibliography commands and bibliography file integrity.
"""
import sys
import re
import os
from typing import List, Dict, Optional, Tuple


class BibliographyValidator:
    """Validates bibliography setup and file integrity."""
    
    def __init__(self):
        pass
    
    def find_bibliography_commands(self, content: str) -> List[Tuple[str, int, str]]:
        """Find all bibliography-related commands in TeX content."""
        commands = []
        lines = content.splitlines()
        
        patterns = [
            (r'\\bibliography\{([^}]+)\}', 'bibliography'),
            (r'\\bibliographystyle\{([^}]+)\}', 'bibliographystyle'),
            (r'\\addbibresource\{([^}]+)\}', 'addbibresource'),  # biblatex
            (r'\\printbibliography', 'printbibliography'),  # biblatex
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, cmd_type in patterns:
                for match in re.finditer(pattern, line):
                    if cmd_type in ['bibliography', 'addbibresource']:
                        arg = match.group(1)
                    else:
                        arg = match.group(0)
                    commands.append((cmd_type, line_num, arg))
        
        return commands
    
    def check_bibliography_files_exist(self, content: str, tex_dir: str) -> List[Dict]:
        """Check if referenced bibliography files actually exist."""
        errors = []
        commands = self.find_bibliography_commands(content)
        
        for cmd_type, line_num, arg in commands:
            if cmd_type in ['bibliography', 'addbibresource']:
                # Handle multiple files: \bibliography{file1,file2}
                bib_files = [f.strip() for f in arg.split(',')]
                
                for bib_file in bib_files:
                    if not bib_file:
                        continue
                        
                    # Add .bib extension if not present (for \bibliography)
                    if cmd_type == 'bibliography' and not bib_file.endswith('.bib'):
                        bib_file += '.bib'
                    
                    bib_path = os.path.join(tex_dir, bib_file)
                    if not os.path.exists(bib_path):
                        errors.append({
                            'error_type': 'BibliographyFileNotFound',
                            'line_num': line_num,
                            'bib_file': bib_file,
                            'original_line': f"\\{cmd_type}{{{arg}}}"
                        })
        
        return errors
    
    def validate_bibtex_file(self, bib_file: str) -> List[Dict]:
        """Validate the syntax of a BibTeX file."""
        errors = []
        
        try:
            with open(bib_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return [{'error_type': 'BibFileReadError', 'file': bib_file}]
        
        lines = content.splitlines()
        
        # Track brace balance
        brace_balance = 0
        in_entry = False
        entry_start_line = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('%'):
                continue
            
            # Check for entry start
            entry_match = re.match(r'@\w+\s*\{\s*([^,\s]*)\s*,?', stripped, re.IGNORECASE)
            if entry_match:
                if in_entry and brace_balance > 0:
                    # Previous entry wasn't closed properly
                    errors.append({
                        'error_type': 'MalformedBibEntry',
                        'line_num': entry_start_line,
                        'bib_file': os.path.basename(bib_file),
                        'original_line': f"Unclosed entry starting at line {entry_start_line}"
                    })
                
                in_entry = True
                entry_start_line = line_num
                brace_balance = 0
                
                # Check if entry has a key
                key = entry_match.group(1)
                if not key:
                    errors.append({
                        'error_type': 'MalformedBibEntry',
                        'line_num': line_num,
                        'bib_file': os.path.basename(bib_file),
                        'original_line': stripped
                    })
            
            # Count braces
            brace_balance += line.count('{') - line.count('}')
            
            # Check for malformed field syntax
            if in_entry and '=' in stripped and not stripped.startswith('@'):
                # Basic field validation: field = {value} or field = "value"
                field_pattern = r'^\s*\w+\s*=\s*[{"].*[}"]?\s*,?\s*$'
                if not re.match(field_pattern, stripped) and not stripped.endswith(','):
                    # Allow for multi-line values
                    if '{' not in stripped and '"' not in stripped:
                        errors.append({
                            'error_type': 'MalformedBibEntry',
                            'line_num': line_num,
                            'bib_file': os.path.basename(bib_file),
                            'original_line': stripped
                        })
        
        # Check if final entry is properly closed
        if in_entry and brace_balance != 0:
            errors.append({
                'error_type': 'MalformedBibEntry',
                'line_num': entry_start_line,
                'bib_file': os.path.basename(bib_file),
                'original_line': f"Unclosed entry starting at line {entry_start_line}"
            })
        
        return errors
    
    def check_missing_bibliography_setup(self, content: str) -> Optional[Dict]:
        """Check if document has citations but no bibliography setup."""
        # Look for citation commands
        citation_patterns = [
            r'\\cite\{[^}]+\}',
            r'\\citep\{[^}]+\}',
            r'\\citet\{[^}]+\}',
            r'\[@[^\]]+\]',  # Pandoc citations
        ]
        
        has_citations = False
        citation_line = 0
        citation_text = ""
        
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            for pattern in citation_patterns:
                if re.search(pattern, line):
                    has_citations = True
                    citation_line = line_num
                    citation_text = line.strip()
                    break
            if has_citations:
                break
        
        if not has_citations:
            return None
        
        # Check for bibliography setup
        bib_commands = self.find_bibliography_commands(content)
        has_bibliography_setup = bool(bib_commands) or bool(re.search(r'\\bibitem\{', content))
        
        if not has_bibliography_setup:
            return {
                'error_type': 'MissingBibliographyCommand',
                'line_num': citation_line,
                'bib_file': 'refs',  # Suggested filename
                'original_line': citation_text
            }
        
        return None
    
    def validate_bibliography(self, tex_file: str) -> Optional[Dict]:
        """Validate bibliography setup and files."""
        try:
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
            
        tex_dir = os.path.dirname(tex_file)
        
        # Check for missing bibliography setup
        missing_bib = self.check_missing_bibliography_setup(content)
        if missing_bib:
            return missing_bib
        
        # Check if bibliography files exist
        file_errors = self.check_bibliography_files_exist(content, tex_dir)
        if file_errors:
            return file_errors[0]  # Return first file error
        
        # Validate BibTeX files
        commands = self.find_bibliography_commands(content)
        for cmd_type, line_num, arg in commands:
            if cmd_type in ['bibliography', 'addbibresource']:
                bib_files = [f.strip() for f in arg.split(',')]
                
                for bib_file in bib_files:
                    if not bib_file:
                        continue
                        
                    # Add .bib extension if not present
                    if cmd_type == 'bibliography' and not bib_file.endswith('.bib'):
                        bib_file += '.bib'
                    
                    bib_path = os.path.join(tex_dir, bib_file)
                    if os.path.exists(bib_path) and bib_file.endswith('.bib'):
                        bib_errors = self.validate_bibtex_file(bib_path)
                        if bib_errors:
                            # Convert bib file error to our format
                            bib_error = bib_errors[0]
                            return {
                                'error_type': bib_error['error_type'],
                                'line_num': bib_error.get('line_num', line_num),
                                'bib_file': bib_error.get('bib_file', bib_file),
                                'original_line': bib_error.get('original_line', f"\\{cmd_type}{{{arg}}}")
                            }
        
        return None


def check_bibliography(tex_file: str) -> Optional[str]:
    """Check for bibliography issues in TeX file."""
    validator = BibliographyValidator()
    
    error = validator.validate_bibliography(tex_file)
    if error:
        # Format: ErrorType:LineNum:BibFile:Suggestion:ProblemSnippet:OriginalLine
        suggestions = {
            'MissingBibliographyCommand': 'Add \\bibliography{refs} command before \\end{document}',
            'BibliographyFileNotFound': f'Create bibliography file "{error["bib_file"]}" or check filename',
            'MalformedBibEntry': 'Fix BibTeX entry syntax (check braces and commas)',
            'BibFileReadError': 'Check file permissions and encoding'
        }
        
        suggestion = suggestions.get(error['error_type'], 'Check bibliography setup')
        
        # Create appropriate problem snippet
        if error['error_type'] == 'MissingBibliographyCommand':
            problem_snippet = "\\cite{key} without \\bibliography{}"
        elif error['error_type'] == 'BibliographyFileNotFound':
            problem_snippet = f"\\bibliography{{{error['bib_file']}}}"
        else:
            problem_snippet = "BibTeX entry"
        
        return f"{error['error_type']}:{error['line_num']}:{error['bib_file']}:{suggestion}:{problem_snippet}:{error['original_line']}"
    
    return None


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <tex_file>", file=sys.stderr)
        sys.exit(2)
    
    result = check_bibliography(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
    
    sys.exit(0)


if __name__ == "__main__":
    main() 