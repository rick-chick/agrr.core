# agrr-core

A Python package for agrr core functionality.

## Description

This package provides core functionality for the agrr project.

## Installation

### From source

```bash
git clone https://github.com/yourusername/agrr.core.git
cd agrr.core
pip install -e .
```

### Development installation

```bash
git clone https://github.com/yourusername/agrr.core.git
cd agrr.core
pip install -e ".[dev]"
```

## Usage

```python
import agrr.core

# Your code here
print(f"agrr.core version: {agrr.core.__version__}")
```

## Development

### Running tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=agrr.core

# Run only fast tests (skip slow ones)
pytest -m "not slow"

# Run specific test file
pytest tests/test_basic.py
```

### Code formatting

```bash
black src tests
```

### Linting

```bash
flake8 src tests
```

### Type checking

```bash
mypy src
```

## Requirements

- Python >= 3.8

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
