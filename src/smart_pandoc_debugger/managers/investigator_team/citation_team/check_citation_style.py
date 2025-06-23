#!/usr/bin/env python3
"""
Citation Style Checker
Validates citation style consistency and package requirements.
"""
import sys
import re
import os
from typing import List, Dict, Optional, Tuple, Set


class CitationStyleValidator:
    """Validates citation style consistency and package usage."""
    
    def __init__(self):
        # Citation command categories
        self.basic_commands = ['cite', 'nocite']
        self.natbib_commands = ['citep', 'citet', 'citeauthor', 'citeyear', 'citealt', 'citealp']
        self.biblatex_commands = ['autocite', 'parencite', 'textcite', 'footcite', 'fullcite', 'citeauthor', 'citetitle']
        
        # All citation commands for detection
        self.all_commands = self.basic_commands + self.natbib_commands + self.biblatex_commands
    
    def extract_citation_commands(self, content: str) -> List[Tuple[str, int, str]]:
        """Extract all citation commands with their line numbers."""
        citations = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Look for all citation commands
            for cmd in self.all_commands:
                pattern = f'\\\\{re.escape(cmd)}\\{{[^}}]+\\}}'
                for match in re.finditer(pattern, line):
                    citations.append((cmd, line_num, line.strip()))
        
        return citations
    
    def check_package_declarations(self, content: str) -> Dict[str, bool]:
        """Check which citation packages are declared."""
        packages = {
            'natbib': bool(re.search(r'\\usepackage(?:\[[^\]]*\])?\{natbib\}', content)),
            'biblatex': bool(re.search(r'\\usepackage(?:\[[^\]]*\])?\{biblatex\}', content)),
            'cite': bool(re.search(r'\\usepackage(?:\[[^\]]*\])?\{cite\}', content)),
        }
        return packages
    
    def analyze_citation_style_usage(self, content: str) -> Dict[str, int]:
        """Analyze which citation styles are being used."""
        citations = self.extract_citation_commands(content)
        
        usage = {
            'basic': 0,
            'natbib': 0,
            'biblatex': 0
        }
        
        for cmd, line_num, line in citations:
            if cmd in self.basic_commands:
                usage['basic'] += 1
            elif cmd in self.natbib_commands:
                usage['natbib'] += 1
            elif cmd in self.biblatex_commands:
                usage['biblatex'] += 1
        
        return usage
    
    def check_missing_packages(self, content: str) -> List[Dict]:
        """Check for citation commands used without proper packages."""
        errors = []
        packages = self.check_package_declarations(content)
        citations = self.extract_citation_commands(content)
        
        for cmd, line_num, line in citations:
            if cmd in self.natbib_commands and not packages['natbib']:
                errors.append({
                    'error_type': 'NatbibCommandWithoutPackage',
                    'line_num': line_num,
                    'command': cmd,
                    'original_line': line
                })
                break  # Only report first occurrence
            elif cmd in self.biblatex_commands and not packages['biblatex']:
                errors.append({
                    'error_type': 'BiblatexCommandWithoutPackage',
                    'line_num': line_num,
                    'command': cmd,
                    'original_line': line
                })
                break  # Only report first occurrence
        
        return errors
    
    def check_style_consistency(self, content: str) -> Optional[Dict]:
        """Check for inconsistent citation style usage."""
        usage = self.analyze_citation_style_usage(content)
        citations = self.extract_citation_commands(content)
        
        if not citations:
            return None
        
        # Count how many different styles are used significantly
        significant_styles = sum(1 for count in usage.values() if count >= 2)
        
        # If multiple styles are used significantly, flag as inconsistent
        if significant_styles > 1:
            # Find the first citation that represents the inconsistency
            style_first_occurrence = {}
            
            for cmd, line_num, line in citations:
                if cmd in self.basic_commands:
                    style = 'basic'
                elif cmd in self.natbib_commands:
                    style = 'natbib'
                elif cmd in self.biblatex_commands:
                    style = 'biblatex'
                else:
                    continue
                
                if style not in style_first_occurrence:
                    style_first_occurrence[style] = (cmd, line_num, line)
            
            # Report the second style encountered (the inconsistent one)
            if len(style_first_occurrence) > 1:
                styles_by_line = sorted(style_first_occurrence.items(), key=lambda x: x[1][1])
                if len(styles_by_line) >= 2:
                    inconsistent_style, (cmd, line_num, line) = styles_by_line[1]
                    return {
                        'error_type': 'InconsistentCitationStyle',
                        'line_num': line_num,
                        'command': cmd,
                        'original_line': line
                    }
        
        return None
    
    def check_conflicting_packages(self, content: str) -> Optional[Dict]:
        """Check for conflicting citation packages."""
        packages = self.check_package_declarations(content)
        
        # natbib and biblatex are incompatible
        if packages['natbib'] and packages['biblatex']:
            # Find the line with the second package declaration
            lines = content.splitlines()
            natbib_line = None
            biblatex_line = None
            
            for line_num, line in enumerate(lines, 1):
                if re.search(r'\\usepackage(?:\[[^\]]*\])?\{natbib\}', line) and natbib_line is None:
                    natbib_line = line_num
                elif re.search(r'\\usepackage(?:\[[^\]]*\])?\{biblatex\}', line) and biblatex_line is None:
                    biblatex_line = line_num
            
            # Report the later declaration as the conflict
            if natbib_line and biblatex_line:
                if biblatex_line > natbib_line:
                    return {
                        'error_type': 'ConflictingCitationPackages',
                        'line_num': biblatex_line,
                        'command': 'biblatex',
                        'original_line': lines[biblatex_line - 1].strip()
                    }
                else:
                    return {
                        'error_type': 'ConflictingCitationPackages',
                        'line_num': natbib_line,
                        'command': 'natbib',
                        'original_line': lines[natbib_line - 1].strip()
                    }
        
        return None
    
    def check_citep_citet_misuse(self, content: str) -> Optional[Dict]:
        """Check for potential misuse of \citep vs \citet."""
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Look for patterns that suggest misuse
            
            # \citep at beginning of sentence (should probably be \citet)
            if re.search(r'^\s*\\citep\{[^}]+\}', line.strip()):
                return {
                    'error_type': 'CitepCitetMisuse',
                    'line_num': line_num,
                    'command': 'citep',
                    'original_line': line.strip()
                }
            
            # \citet in parentheses (should probably be \citep)
            if re.search(r'\(\s*\\citet\{[^}]+\}\s*\)', line):
                return {
                    'error_type': 'CitepCitetMisuse',
                    'line_num': line_num,
                    'command': 'citet',
                    'original_line': line.strip()
                }
        
        return None
    
    def validate_citation_style(self, tex_file: str) -> Optional[Dict]:
        """Validate citation style consistency and package usage."""
        try:
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
        
        # Check for missing packages first
        package_errors = self.check_missing_packages(content)
        if package_errors:
            return package_errors[0]
        
        # Check for conflicting packages
        conflict_error = self.check_conflicting_packages(content)
        if conflict_error:
            return conflict_error
        
        # Check for style consistency
        style_error = self.check_style_consistency(content)
        if style_error:
            return style_error
        
        # Check for specific citep/citet misuse
        misuse_error = self.check_citep_citet_misuse(content)
        if misuse_error:
            return misuse_error
        
        return None


def check_citation_style(tex_file: str) -> Optional[str]:
    """Check for citation style issues in TeX file."""
    validator = CitationStyleValidator()
    
    error = validator.validate_citation_style(tex_file)
    if error:
        # Format: ErrorType:LineNum:Command:Suggestion:ProblemSnippet:OriginalLine
        suggestions = {
            'NatbibCommandWithoutPackage': 'Add \\usepackage{natbib} to document preamble',
            'BiblatexCommandWithoutPackage': 'Add \\usepackage{biblatex} to document preamble',
            'InconsistentCitationStyle': 'Use consistent citation style throughout document',
            'ConflictingCitationPackages': 'Remove one of the conflicting citation packages',
            'CitepCitetMisuse': 'Use \\citep for parenthetical citations, \\citet for textual citations'
        }
        
        suggestion = suggestions.get(error['error_type'], 'Check citation style usage')
        command = error.get('command', '')
        
        # Create appropriate problem snippet
        if error['error_type'] in ['NatbibCommandWithoutPackage', 'BiblatexCommandWithoutPackage']:
            problem_snippet = f"\\{command}{{}}"
        elif error['error_type'] == 'ConflictingCitationPackages':
            problem_snippet = f"\\usepackage{{{command}}}"
        elif error['error_type'] == 'CitepCitetMisuse':
            problem_snippet = f"\\{command}{{}}"
        else:
            problem_snippet = f"\\{command}{{}}"
        
        return f"{error['error_type']}:{error['line_num']}:{command}:{suggestion}:{problem_snippet}:{error['original_line']}"
    
    return None


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <tex_file>", file=sys.stderr)
        sys.exit(2)
    
    result = check_citation_style(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
    
    sys.exit(0)


if __name__ == "__main__":
    main() 