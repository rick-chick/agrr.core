# agrr-core

A Python package for weather data fetching and prediction using Prophet machine learning model.

## Description

This package provides weather data fetching from Open-Meteo API and weather prediction using Prophet time series model, implemented following clean architecture principles.

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

### Using as a command-line tool

After installation, `agrr` command is available system-wide:

```bash
# Install the package
pip install -e .

# Now you can use 'agrr' command anywhere
agrr --help
agrr weather --location 35.6762,139.6503 --days 7
agrr crop --query "トマト"
```

### Distribution

**配布方法 (Distribution Methods):**

1. **Wheelパッケージ配布** (推奨)
   ```bash
   # ビルド
   python3 -m build
   
   # 配布
   # dist/agrr_core-0.1.0-py3-none-any.whl をユーザーに配布
   
   # インストール
   pip install agrr_core-0.1.0-py3-none-any.whl
   agrr --help
   ```

2. **PyPI公開** (最も簡単)
   ```bash
   # PyPIにアップロード後
   pip install agrr-core
   agrr --help
   ```

3. **Docker** (真のスタンドアロン)
   ```bash
   # Build Docker image
   docker build -t agrr .
   
   # Run
   docker run --rm agrr weather --location 35.6762,139.6503 --days 7
   docker run --rm agrr crop --query "トマト"
   ```

4. **GitHubから直接インストール**
   ```bash
   pip install git+https://github.com/yourusername/agrr.core.git
   agrr --help
   ```

## Quick Start

### CLI Usage

Get weather data from the command line:

```bash
# Using the agrr command (after pip install -e .)
agrr weather --location 35.6762,139.6503 --days 7
agrr crop --query "トマト"
agrr predict-file --input weather.json --output predictions.json

# Or using the standalone binary
./dist/agrr weather --location 35.6762,139.6503 --days 7

# Or using Python module
python -m agrr_core.cli weather --location 35.6762,139.6503 --days 7

# Get weather for specific date range
agrr weather --location 35.6762,139.6503 --start-date 2024-01-01 --end-date 2024-01-07

# Get weather for New York with JSON output
agrr weather --location 40.7128,-74.0060 --days 5 --json

# Short options
agrr weather -l 35.6762,139.6503 -d 7 --json
```

#### Output Formats

**Table format (default):**
```
================================================================================
WEATHER FORECAST
================================================================================

Location: 35.6762°N, 139.6911°E | Elevation: 37m | Timezone: Asia/Tokyo

Date         Max Temp   Min Temp   Avg Temp   Precip   Sunshine  
----------------------------------------------------------------------
2024-01-15   15.5°C     8.2°C      11.8°C     5.0mm    8.0h      
...
```

**JSON format (with `--json` flag):**
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "time": "2024-01-15",
        "temperature_2m_max": 15.5,
        "temperature_2m_min": 8.2,
        "temperature_2m_mean": 11.8,
        "precipitation_sum": 5.0,
        "sunshine_duration": 28800.0,
        "sunshine_hours": 8.0
      }
    ],
    "total_count": 1,
    "location": {
      "latitude": 35.6762,
      "longitude": 139.6911,
      "elevation": 37.0,
      "timezone": "Asia/Tokyo"
    }
  }
}
```


## Features

- 🌤️ **Weather Data Fetching**: Get historical weather data from Open-Meteo API
- 🔮 **Weather Prediction**: Predict future weather using Prophet time series model
- 🏗️ **Clean Architecture**: Implemented following clean architecture principles
- 📊 **Data Processing**: Convert and process weather data using pandas
- 💻 **CLI Support**: Command-line interface with table and JSON output formats

## Development

### Running tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=agrr_core

# Run only fast tests (skip slow ones)
pytest -m "not slow"
```

### Code formatting

```bash
black src tests
```

### Type checking

```bash
mypy src
```

## Requirements

- Python >= 3.8

## Dependencies

- `requests>=2.25.0` - HTTP client for API calls
- `pandas>=1.3.0` - Data manipulation and analysis
- `prophet>=1.1.0` - Time series forecasting
- `numpy>=1.20.0` - Numerical computations

## Documentation

詳細なドキュメントは[docs/README.md](docs/README.md)を参照してください。

- [アーキテクチャ設計](ARCHITECTURE.md)
- [CLI API Reference](docs/api/README.md)

## License

This project is licensed under the MIT License.
