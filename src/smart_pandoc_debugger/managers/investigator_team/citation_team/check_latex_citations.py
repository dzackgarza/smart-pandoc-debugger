#!/usr/bin/env python3
"""
LaTeX Citation Checker
Validates LaTeX-style citations \cite{key} against available bibliography entries.
"""
import sys
import re
import os
from typing import List, Dict, Optional, Tuple, Set


class LatexCitationValidator:
    """Validates LaTeX citations and bibliography references."""
    
    def __init__(self):
        # Common citation commands
        self.citation_commands = [
            r'\\cite\{([^}]+)\}',
            r'\\citep\{([^}]+)\}',
            r'\\citet\{([^}]+)\}',
            r'\\citeauthor\{([^}]+)\}',
            r'\\citeyear\{([^}]+)\}',
            r'\\nocite\{([^}]+)\}',
            r'\\autocite\{([^}]+)\}',
            r'\\parencite\{([^}]+)\}',
            r'\\textcite\{([^}]+)\}'
        ]
        
        # natbib-specific commands
        self.natbib_commands = ['citep', 'citet', 'citeauthor', 'citeyear']
        
        # biblatex-specific commands  
        self.biblatex_commands = ['autocite', 'parencite', 'textcite']
    
    def extract_latex_citations(self, content: str) -> List[Tuple[str, int, str, str]]:
        """Extract all LaTeX citations with their line numbers and commands."""
        citations = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.citation_commands:
                for match in re.finditer(pattern, line):
                    citation_keys = match.group(1)
                    command = match.group(0).split('{')[0].lstrip('\\')
                    
                    # Handle multiple citations: \cite{key1,key2}
                    keys = [k.strip() for k in citation_keys.split(',')]
                    for key in keys:
                        if key:  # Skip empty keys
                            citations.append((key, line_num, line.strip(), command))
        
        return citations
    
    def extract_bib_entries(self, content: str) -> Set[str]:
        """Extract bibliography entries from TeX content."""
        entries = set()
        
        # Look for \bibitem{key} entries
        bibitem_pattern = r'\\bibitem\{([^}]+)\}'
        for match in re.finditer(bibitem_pattern, content):
            entries.add(match.group(1))
        
        return entries
    
    def find_bib_files_in_content(self, content: str, tex_dir: str) -> List[str]:
        """Find bibliography files referenced in TeX content."""
        bib_files = []
        
        # Look for \bibliography{filename} commands
        bib_pattern = r'\\bibliography\{([^}]+)\}'
        for match in re.finditer(bib_pattern, content):
            bib_names = match.group(1).split(',')
            for bib_name in bib_names:
                bib_name = bib_name.strip()
                # Add .bib extension if not present
                if not bib_name.endswith('.bib'):
                    bib_name += '.bib'
                
                bib_path = os.path.join(tex_dir, bib_name)
                if os.path.exists(bib_path):
                    bib_files.append(bib_path)
        
        return bib_files
    
    def extract_bib_keys_from_bibtex(self, bib_file: str) -> Set[str]:
        """Extract citation keys from a BibTeX file."""
        keys = set()
        try:
            with open(bib_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Pattern to match BibTeX entries: @article{key,
            pattern = r'@\w+\s*\{\s*([^,\s]+)\s*,'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                keys.add(match.group(1))
                
        except Exception:
            pass
        return keys
    
    def get_all_bibliography_keys(self, content: str, tex_dir: str) -> Set[str]:
        """Get all citation keys from bibliography sources."""
        all_keys = set()
        
        # Get keys from inline \bibitem entries
        all_keys.update(self.extract_bib_entries(content))
        
        # Get keys from external .bib files
        bib_files = self.find_bib_files_in_content(content, tex_dir)
        for bib_file in bib_files:
            all_keys.update(self.extract_bib_keys_from_bibtex(bib_file))
        
        return all_keys
    
    def check_package_usage(self, content: str) -> List[Dict]:
        """Check for citation command usage without proper packages."""
        errors = []
        lines = content.splitlines()
        
        has_natbib = bool(re.search(r'\\usepackage.*\{natbib\}', content))
        has_biblatex = bool(re.search(r'\\usepackage.*\{biblatex\}', content))
        
        for line_num, line in enumerate(lines, 1):
            # Check for natbib commands without package
            if not has_natbib:
                for cmd in self.natbib_commands:
                    if f'\\{cmd}{{' in line:
                        errors.append({
                            'error_type': 'NatbibCommandWithoutPackage',
                            'line_num': line_num,
                            'command': cmd,
                            'original_line': line.strip()
                        })
                        break
            
            # Check for biblatex commands without package
            if not has_biblatex:
                for cmd in self.biblatex_commands:
                    if f'\\{cmd}{{' in line:
                        errors.append({
                            'error_type': 'BiblatexCommandWithoutPackage',
                            'line_num': line_num,
                            'command': cmd,
                            'original_line': line.strip()
                        })
                        break
        
        return errors
    
    def check_citation_style_consistency(self, content: str) -> Optional[Dict]:
        """Check for inconsistent citation style usage."""
        citations = self.extract_latex_citations(content)
        
        # Count different citation styles
        natbib_usage = sum(1 for _, _, _, cmd in citations if cmd in self.natbib_commands)
        biblatex_usage = sum(1 for _, _, _, cmd in citations if cmd in self.biblatex_commands)
        basic_cite_usage = sum(1 for _, _, _, cmd in citations if cmd == 'cite')
        
        # If multiple styles are used significantly, flag as inconsistent
        styles_used = sum(1 for count in [natbib_usage, biblatex_usage, basic_cite_usage] if count > 0)
        
        if styles_used > 1 and min(natbib_usage, biblatex_usage, basic_cite_usage) > 2:
            first_citation = citations[0] if citations else None
            if first_citation:
                return {
                    'error_type': 'InconsistentCitationStyle',
                    'line_num': first_citation[1],
                    'command': first_citation[3],
                    'original_line': first_citation[2]
                }
        
        return None
    
    def find_unused_bib_entries(self, content: str, tex_dir: str) -> List[str]:
        """Find bibliography entries that are defined but never cited."""
        all_bib_keys = self.get_all_bibliography_keys(content, tex_dir)
        cited_keys = set()
        
        citations = self.extract_latex_citations(content)
        for key, _, _, _ in citations:
            cited_keys.add(key)
        
        # Also check for \nocite{*} which cites all entries
        if re.search(r'\\nocite\{\*\}', content):
            return []  # All entries are considered used
        
        unused_keys = all_bib_keys - cited_keys
        return list(unused_keys)
    
    def validate_citations(self, tex_file: str) -> Optional[Dict]:
        """Validate all LaTeX citations in the TeX file."""
        try:
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
            
        tex_dir = os.path.dirname(tex_file)
        
        # Check for package usage issues first
        package_errors = self.check_package_usage(content)
        if package_errors:
            return package_errors[0]  # Return first package error
        
        # Check for citation style consistency
        style_error = self.check_citation_style_consistency(content)
        if style_error:
            return style_error
        
        # Get all valid citation keys
        valid_keys = self.get_all_bibliography_keys(content, tex_dir)
        
        # Check for missing bibliography command
        has_bibliography = bool(re.search(r'\\bibliography\{', content)) or bool(re.search(r'\\bibitem\{', content))
        citations = self.extract_latex_citations(content)
        
        if citations and not has_bibliography:
            first_citation = citations[0]
            return {
                'error_type': 'MissingBibliographyCommand',
                'line_num': first_citation[1],
                'citation_key': first_citation[0],
                'original_line': first_citation[2]
            }
        
        # Check each citation for undefined keys
        for citation_key, line_num, original_line, command in citations:
            if valid_keys and citation_key not in valid_keys:  # Only check if we have a bibliography
                return {
                    'error_type': 'UndefinedLatexCitation',
                    'line_num': line_num,
                    'citation_key': citation_key,
                    'original_line': original_line
                }
            elif not valid_keys and has_bibliography:  # Has bibliography command but no valid keys found
                return {
                    'error_type': 'UndefinedLatexCitation',
                    'line_num': line_num,
                    'citation_key': citation_key,
                    'original_line': original_line
                }
        
        # Check for unused bibliography entries
        unused_keys = self.find_unused_bib_entries(content, tex_dir)
        if unused_keys:
            # Return info about first unused key
            return {
                'error_type': 'UnusedBibEntry',
                'line_num': 1,  # No specific line for unused entries
                'citation_key': unused_keys[0],
                'original_line': f"Unused bibliography entry: {unused_keys[0]}"
            }
        
        return None


def check_latex_citations(tex_file: str) -> Optional[str]:
    """Check for LaTeX citation issues in TeX file."""
    validator = LatexCitationValidator()
    
    error = validator.validate_citations(tex_file)
    if error:
        # Format: ErrorType:LineNum:CitationKey:Suggestion:ProblemSnippet:OriginalLine
        suggestions = {
            'UndefinedLatexCitation': f'Add "{error.get("citation_key", "key")}" to bibliography or check spelling',
            'UnusedBibEntry': f'Remove unused entry "{error.get("citation_key", "key")}" or add \\cite{{{error.get("citation_key", "key")}}}',
            'MissingBibliographyCommand': 'Add \\bibliography{filename} command to document',
            'NatbibCommandWithoutPackage': 'Add \\usepackage{natbib} to document preamble',
            'BiblatexCommandWithoutPackage': 'Add \\usepackage{biblatex} to document preamble',
            'InconsistentCitationStyle': 'Use consistent citation style (natbib, biblatex, or basic \\cite)'
        }
        
        suggestion = suggestions.get(error['error_type'], 'Check citation format')
        
        # Determine the key/command field
        key_field = error.get('citation_key', error.get('command', ''))
        
        # Create appropriate problem snippet
        if error['error_type'] in ['NatbibCommandWithoutPackage', 'BiblatexCommandWithoutPackage']:
            problem_snippet = f"\\{error.get('command', 'cite')}{{}}"
        elif error['error_type'] == 'UnusedBibEntry':
            problem_snippet = f"@article{{{error.get('citation_key', 'key')},...}}"
        else:
            problem_snippet = f"\\cite{{{error.get('citation_key', 'key')}}}"
        
        return f"{error['error_type']}:{error['line_num']}:{key_field}:{suggestion}:{problem_snippet}:{error['original_line']}"
    
    return None


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <tex_file>", file=sys.stderr)
        sys.exit(2)
    
    result = check_latex_citations(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
    
    sys.exit(0)


if __name__ == "__main__":
    main() 