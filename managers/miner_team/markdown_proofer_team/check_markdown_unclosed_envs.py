#!/usr/bin/env python3
import sys
import re

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_markdown_unclosed_envs.py <markdown_file>", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]
    
    # Regex to find \begin{env} or \end{env}
    # Assumes they are on their own lines, possibly with leading/trailing whitespace.
    # Captures 'env_name'.
    # For \begin{...} and \end{...}
    env_pattern = re.compile(r"^\s*\\(begin|end)\s*\{\s*([a-zA-Z0-9_*]+)\s*\}") # Allows * in env name e.g. align*

    env_stack = [] # Stores tuples of (env_name, line_number, line_content)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line_content_raw in enumerate(f):
                line_number = i + 1
                line_content = line_content_raw.rstrip('\n')
                
                match = env_pattern.match(line_content)
                if match:
                    action = match.group(1) # "begin" or "end"
                    env_name = match.group(2) # e.g., "align", "itemize"

                    if action == "begin":
                        env_stack.append({
                            "name": env_name, 
                            "line_num": line_number, 
                            "content": line_content.strip(), # The \begin{...} line
                            "line_content_raw": line_content_raw # Full original line
                        })
                    elif action == "end":
                        if not env_stack:
                            # Found an \end without a matching \begin
                            error_type = "MismatchedMarkdownEnvironment" # Or "UnexpectedEndEnvironment"
                            problem_snippet = line_content.strip() # The \end{...} line
                            # VAL1: expected env (N/A), VAL2: found env (env_name)
                            print(f"{error_type}:{line_number}:N/A:{env_name}:{problem_snippet}:{line_content_raw}")
                            sys.exit(0) # Report and exit

                        opened_env = env_stack.pop()
                        if opened_env["name"] != env_name:
                            # Mismatched \end, e.g., \begin{foo} \end{bar}
                            error_type = "MismatchedMarkdownEnvironment"
                            problem_snippet = f"{opened_env['content']} ... {line_content.strip()}"
                            # VAL1: opened_env["name"], VAL2: env_name (the \end{env_name} found)
                            print(f"{error_type}:{opened_env['line_num']}:{opened_env['name']}:{env_name}:{problem_snippet}:{opened_env['line_content_raw']}")
                            sys.exit(0) # Report and exit
            
            # End of file processing
            if env_stack: # If stack is not empty, there are unclosed environments
                oldest_unclosed_env = env_stack[0] # Report the first one that wasn't closed
                error_type = "UnclosedMarkdownEnvironment"
                problem_snippet = oldest_unclosed_env["content"] # The \begin{...} line
                # VAL1: env_name, VAL2: N/A (no closing found)
                print(f"{error_type}:{oldest_unclosed_env['line_num']}:{oldest_unclosed_env['name']}:N/A:{problem_snippet}:{oldest_unclosed_env['line_content_raw']}")
                sys.exit(0) # Report and exit

    except FileNotFoundError:
        print(f"Error: Markdown file not found: {filepath}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error processing file {filepath}: {e}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0) # No errors found

if __name__ == "__main__":
    main()
