# Development Setup

This guide will help you set up the development environment for the Smart Pandoc Debugger using `uv` for package management and virtual environments.

## Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
  ```bash
  # Install uv (requires Python 3.8+)
  curl -sSf https://astral.sh/uv/install.sh | sh
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/smart-pandoc-debugger.git
   cd smart-pandoc-debugger
   ```

2. Create and activate a virtual environment using `uv`:
   ```bash
   # Create a new virtual environment
   uv venv
   
   # Activate the environment
   # On Unix/macOS:
   source .venv/bin/activate
   # On Windows:
   # .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   # Install all dependencies
   uv pip install -r requirements.txt
   
   # Install the package in development mode
   uv pip install -e ".[dev]"
   ```

## Development Tools

We use several tools to maintain code quality, all specified in `requirements.txt`:

- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Static type checking
- `pytest` - Testing framework

## Using uv for Package Management

### Installing Packages

To add a new package:

```bash
uv pip install package_name

# Add to requirements.txt (recommended for project dependencies)
uv pip install package_name && uv pip freeze | grep -i package_name >> requirements.txt
```

### Syncing Dependencies

To ensure all developers have the same environment:

```bash
# Update the virtual environment to match requirements.txt
uv pip sync requirements.txt
```

### Updating Dependencies

```bash
# Update a specific package
uv pip install --upgrade package_name

# Update all packages
uv pip list --outdated | awk 'NR>2 {print $1}' | xargs -n1 uv pip install -U
```

## Building Documentation

Documentation is built using MkDocs. To build and serve the documentation locally:

```bash
# Install documentation dependencies
uv pip install mkdocs mkdocs-material mkdocstrings

# Serve the documentation
mkdocs serve
```

Then open http://localhost:8000 in your browser.

## Pre-commit Hooks

We use pre-commit to run code quality checks before each commit. To set it up:

```bash
# Install pre-commit
uv pip install pre-commit

# Install git hooks
pre-commit install
```

Now the checks will run automatically on each commit.
