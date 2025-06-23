# Contributing to Smart Pandoc Debugger

Thank you for your interest in contributing to Smart Pandoc Debugger! This document outlines the process for contributing to the project.

## Development Workflow

### 1. Setup

1. Fork the repository to your GitHub account
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/smart-pandoc-debugger.git
   cd smart-pandoc-debugger
   ```
3. Set up the development environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .[dev]
   ```

### 2. Create a Feature Branch

Always create a new branch for your changes:

```bash
git checkout -b feature/descriptive-branch-name
```

Branch naming conventions:
- `feature/` - New features or improvements
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions or improvements
- `refactor/` - Code refactoring

### 3. Make Changes

1. Make your code changes following the project's coding standards
2. Add tests for new functionality
3. Run tests locally:
   ```bash
   PYTHONPATH=./src pytest tests/ -v
   ```
4. The project includes a pre-commit hook that will run tests automatically before each commit

### 4. Commit Your Changes

1. Stage your changes:
   ```bash
   git add <changed-files>
   ```
2. Commit with a descriptive message:
   ```bash
   git commit -m "feat: Add new feature"
   ```
   
   Commit message format:
   ```
   type(scope): description
   
   Detailed description if needed
   ```
   
   Types:
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style changes
   - `refactor`: Code refactoring
   - `test`: Test related changes
   - `chore`: Maintenance tasks

### 5. Push Changes to Remote

1. Push your branch to GitHub:
   ```bash
   git push -u origin feature/descriptive-branch-name
   ```
   
   **Important**: You must be the one to push changes to the remote repository. The automated assistant can help with local changes but will not push to remote.

### 6. Create a Pull Request

1. Create a pull request from your fork to the main repository
2. Update the project documentation to mark your branch as completed in the roadmap or relevant documentation
3. Use the following PR template:

   ```markdown
   ## 🎯 [Brief Description of Changes]
   
   [Detailed description of what this PR does and why it's needed]
   
   ### ✅ Features Implemented
   - Feature 1
   - Feature 2
   
   ### 🧪 Testing
   - [ ] All tests pass
   - [ ] New tests added for new features
   - [ ] Test coverage maintained or improved
   
   ### 📝 Documentation
   - [ ] Code is well-documented
   - [ ] README/CHANGELOG updated if needed
   - [ ] Project documentation (roadmap, etc.) updated to reflect completed work
   ```

3. After creating the PR, get the automated Copilot review by running:
   ```bash
   GH_PAGER=cat gh pr view --json reviews
   ```
   
   This will display the automated review from Copilot. You must:
   - Address all points raised in the review
   - Make necessary changes locally
   - Push the updates to your branch
   - The PR will only be accepted once all review comments are resolved

4. Request review from maintainers after addressing all automated review comments

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use type hints for all function signatures
- Keep lines under 100 characters
- Include docstrings for all public functions and classes

## Testing

- Write tests for all new functionality
- Run tests before pushing code
- Maintain or improve test coverage
- Use descriptive test names that explain what's being tested

## Review Process

1. All PRs require at least one approval
2. Address all review comments
3. Update the PR with any requested changes
4. Once approved, a maintainer will merge your PR

## Reporting Issues

When reporting issues, please include:
- A clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE) file.
