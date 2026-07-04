# Contributing

Thank you for your interest in contributing to mdconvert!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/vvChu/mdconverter.git
cd mdconverter

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mdconverter --cov-report=html
```

## Code Quality

```bash
# Lint with Ruff
ruff check src/ tests/

# Format with Ruff
ruff format src/ tests/

# Type check with MyPy
mypy src/
```

## Documentation

```bash
# Install docs dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve docs locally
mkdocs serve

# Build docs
mkdocs build
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests and linting
5. Commit with descriptive message
6. Push and create a PR

## Code Style

- Use type hints for all functions
- Add docstrings to public functions
- Follow PEP 8 guidelines
- Keep functions focused and small
