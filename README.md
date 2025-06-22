# Smart Pandoc Debugger

A command-line tool to help debug and fix issues in Pandoc markdown documents.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (recommended for fast installation)

### Installation & Setup

```bash
# Clone and set up the project
git clone https://github.com/yourusername/smart-pandoc-debugger.git
cd smart-pandoc-debugger

# Install with uv (recommended)
uv pip install -e '.[dev]'

# Or with pip
# pip install -e '.[dev]'
```

## 🛠️ Basic Usage

### Analyze a Markdown File

```bash
spd your_document.md
```

### Or pipe content directly

```bash
echo "# Test Document\n\nThis is a test" | spd
```

### Example Output

```
📄 Analyzing: test.md

🔍 DIAGNOSTIC REPORT
==================================================
📊 Document Stats:
   • Lines: 42
   • Words: 150
   • Characters: 1024

🚨 Issues Found:
   • Unmatched dollar signs (potential math mode issue)
   • Unmatched LaTeX environments (3 begins, 2 ends)
```

## 🧪 Development

### Run Tests

```bash
# Run core tests (Tier 1 only for now)
spd test

# Run all tests (including incomplete tiers)
pytest
```

### Check Code Quality

```bash
# Format code
black src tests

# Check style
flake8
```

## 📖 Documentation

### Project Documentation
- [Roadmap](./docs/roadmap/README.md) - Current and planned development roadmap
- [Architecture](./docs/ARCHITECTURE.md) - System architecture overview
- [Development Guide](./docs/DEVELOPMENT.md) - Contributing and development guidelines

### Current Status (v0.0.0)
- [Current Version](./docs/roadmap/V0.0.md) - Features and changes in the current version
- [Next Steps](./docs/roadmap/V1.0.md) - Upcoming features in development

## 📝 License

MIT - See [LICENSE](LICENSE) for details.
</div>
