#!/usr/bin/env python3
"""
Pandoc Citation Checker
Validates Pandoc-style citations [@key] against available bibliography files.
"""
import sys
import re
import os
from typing import List, Dict, Optional, Tuple, Set


class PandocCitationValidator:
    """Validates Pandoc citations and bibliography references."""
    
    def __init__(self):
        # Common bibliography file extensions
        self.bib_extensions = ['.bib', '.yaml', '.yml', '.json']
        
    def find_bibliography_files(self, tex_file_dir: str) -> List[str]:
        """Find bibliography files in the same directory as the TeX file."""
        bib_files = []
        # Look for common bibliography file names
        common_bib_names = ['refs', 'references', 'bibliography', 'bib', 'citations']
        
        for base_name in common_bib_names:
            for ext in self.bib_extensions:
                filename = base_name + ext
                filepath = os.path.join(tex_file_dir, filename)
                if os.path.exists(filepath):
                    bib_files.append(filepath)
        
        # Also look for any .bib files (most common case)
        try:
            for filename in os.listdir(tex_file_dir):
                if filename.endswith('.bib') and filename not in [os.path.basename(f) for f in bib_files]:
                    # Only include .bib files, not other extensions to avoid false positives
                    bib_files.append(os.path.join(tex_file_dir, filename))
        except OSError:
            pass
            
        return bib_files
    
    def extract_pandoc_citations(self, content: str) -> List[Tuple[str, int, str]]:
        """Extract all Pandoc citations [@key] with their line numbers."""
        citations = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Find all [@citation] patterns
            citation_pattern = r'\[@([^\]]+)\]'
            for match in re.finditer(citation_pattern, line):
                citation_key = match.group(1)
                # Handle multiple citations: [@key1; @key2]
                keys = [k.strip().lstrip('@') for k in citation_key.split(';')]
                for key in keys:
                    if key:  # Skip empty keys
                        citations.append((key, line_num, line.strip()))
        
        return citations
    
    def extract_bib_keys_from_bibtex(self, bib_file: str) -> Set[str]:
        """
        Extract citation keys from a BibTeX file.
        
        Uses a robust parser that handles multiline field values by parsing
        entry boundaries with proper brace counting.
        """
        keys = set()
        try:
            with open(bib_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Remove comments (lines starting with %)
            lines = content.splitlines()
            cleaned_lines = []
            for line in lines:
                # Remove inline comments but preserve quoted strings
                in_string = False
                escape_next = False
                cleaned_line = ""
                for char in line:
                    if escape_next:
                        cleaned_line += char
                        escape_next = False
                    elif char == '\\':
                        cleaned_line += char
                        escape_next = True
                    elif char == '"' and not escape_next:
                        in_string = not in_string
                        cleaned_line += char
                    elif char == '%' and not in_string:
                        break  # Rest of line is comment
                    else:
                        cleaned_line += char
                cleaned_lines.append(cleaned_line)
            
            content = '\n'.join(cleaned_lines)
            
            # Find BibTeX entries with proper brace matching for multiline support
            # Pattern matches: @entrytype{key,
            entry_pattern = r'@(\w+)\s*\{\s*([^,\s}]+)\s*,'
            
            pos = 0
            while pos < len(content):
                match = re.search(entry_pattern, content[pos:], re.IGNORECASE)
                if not match:
                    break
                    
                # Extract the citation key
                entry_type = match.group(1)
                citation_key = match.group(2)
                keys.add(citation_key)
                
                # Skip past this entry to find the next one
                # Find the start of the entry content (after the key and comma)
                start_pos = pos + match.end()
                
                # Count braces to find the end of this entry
                brace_count = 1  # We're inside the opening brace
                current_pos = start_pos
                
                while current_pos < len(content) and brace_count > 0:
                    char = content[current_pos]
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                    current_pos += 1
                
                # Move past this entry for next iteration
                pos = current_pos
                
        except Exception:
            # Fallback to simple regex if robust parsing fails
            try:
                with open(bib_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                pattern = r'@\w+\s*\{\s*([^,\s]+)\s*,'
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    keys.add(match.group(1))
            except Exception:
                pass
        return keys
    
    def extract_bib_keys_from_yaml(self, bib_file: str) -> Set[str]:
        """Extract citation keys from a YAML bibliography file."""
        keys = set()
        try:
            with open(bib_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for YAML entries with id: or key: fields
            # This is a simple pattern - real YAML parsing would be more robust
            patterns = [
                r'^\s*-?\s*id:\s*["\']?([^"\'\s]+)["\']?',
                r'^\s*-?\s*key:\s*["\']?([^"\'\s]+)["\']?'
            ]
            
            for pattern in patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    keys.add(match.group(1))
                    
        except Exception:
            pass
        return keys
    
    def get_all_bibliography_keys(self, bib_files: List[str]) -> Set[str]:
        """Get all citation keys from all bibliography files."""
        all_keys = set()
        
        for bib_file in bib_files:
            if bib_file.endswith('.bib'):
                all_keys.update(self.extract_bib_keys_from_bibtex(bib_file))
            elif bib_file.endswith(('.yaml', '.yml')):
                all_keys.update(self.extract_bib_keys_from_yaml(bib_file))
            # JSON bibliography parsing could be added here
                
        return all_keys
    
    def check_duplicate_keys(self, bib_files: List[str]) -> Optional[Dict]:
        """Check for duplicate citation keys across bibliography files."""
        key_files = {}  # key -> list of files containing it
        
        for bib_file in bib_files:
            if bib_file.endswith('.bib'):
                keys = self.extract_bib_keys_from_bibtex(bib_file)
            elif bib_file.endswith(('.yaml', '.yml')):
                keys = self.extract_bib_keys_from_yaml(bib_file)
            else:
                continue
                
            for key in keys:
                if key not in key_files:
                    key_files[key] = []
                key_files[key].append(bib_file)
        
        # Find duplicates
        for key, files in key_files.items():
            if len(files) > 1:
                return {
                    'error_type': 'DuplicateCitationKey',
                    'key': key,
                    'files': files
                }
        
        return None
    
    def validate_citations(self, tex_file: str) -> Optional[Dict]:
        """Validate all Pandoc citations in the TeX file."""
        try:
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
            
        tex_dir = os.path.dirname(tex_file)
        bib_files = self.find_bibliography_files(tex_dir)
        
        # Get citations first to check if we need a bibliography
        citations = self.extract_pandoc_citations(content)
        
        if not bib_files:
            # Check if there are any citations that would need a bibliography
            if citations:
                first_citation = citations[0]
                return {
                    'error_type': 'MissingBibliography',
                    'line_num': first_citation[1],
                    'citation_key': first_citation[0],
                    'original_line': first_citation[2]
                }
            return None
        
        # Check for duplicate keys
        duplicate_error = self.check_duplicate_keys(bib_files)
        if duplicate_error:
            return {
                'error_type': duplicate_error['error_type'],
                'line_num': 1,  # No specific line for duplicates
                'citation_key': duplicate_error['key'],
                'original_line': f"Duplicate key in files: {', '.join(duplicate_error['files'])}"
            }
        
        # Get all valid citation keys
        valid_keys = self.get_all_bibliography_keys(bib_files)
        
        # Check each citation
        for citation_key, line_num, original_line in citations:
            if citation_key not in valid_keys:
                return {
                    'error_type': 'UndefinedPandocCitation',
                    'line_num': line_num,
                    'citation_key': citation_key,
                    'original_line': original_line
                }
        
        return None


def check_pandoc_citations(tex_file: str) -> Optional[str]:
    """Check for Pandoc citation issues in TeX file."""
    validator = PandocCitationValidator()
    
    error = validator.validate_citations(tex_file)
    if error:
        # Format: ErrorType:LineNum:CitationKey:Suggestion:ProblemSnippet:OriginalLine
        suggestions = {
            'UndefinedPandocCitation': f'Add "{error["citation_key"]}" to bibliography or check spelling',
            'MissingBibliography': 'Add a bibliography file (.bib, .yaml) to the document directory',
            'DuplicateCitationKey': 'Remove duplicate key from one of the bibliography files'
        }
        
        suggestion = suggestions.get(error['error_type'], 'Check citation format')
        problem_snippet = f"[@{error['citation_key']}]"
        
        return f"{error['error_type']}:{error['line_num']}:{error['citation_key']}:{suggestion}:{problem_snippet}:{error['original_line']}"
    
    return None


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <tex_file>", file=sys.stderr)
        sys.exit(2)
    
    result = check_pandoc_citations(sys.argv[1])
    if result:
        print(result)
        sys.exit(0)
    
    sys.exit(0)


if __name__ == "__main__":
    main() 