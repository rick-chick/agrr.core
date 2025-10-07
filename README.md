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
agrr progress --crop rice --variety Koshihikari --start-date 2024-05-01 --weather-file weather_data.json
```

### Distribution

**配布方法 (Distribution Methods):**

1. **ネイティブバイナリ配布** ⭐️ Python環境不要
   ```bash
   # ビルド
   ./build_standalone.sh
   
   # 配布
   # dist/agrr (113MB) をユーザーに配布
   
   # 実行（Python不要）
   chmod +x agrr
   ./agrr --help
   ```

2. **Wheelパッケージ配布** - Python環境が必要
   ```bash
   # ビルド
   python3 -m build
   
   # 配布
   # dist/agrr_core-0.1.0-py3-none-any.whl をユーザーに配布
   
   # インストール
   pip install agrr_core-0.1.0-py3-none-any.whl
   agrr --help
   ```

3. **PyPI公開** (最も簡単)
   ```bash
   # PyPIにアップロード後
   pip install agrr-core
   agrr --help
   ```

4. **Docker** (コンテナ配布)
   ```bash
   # Build Docker image
   docker build -t agrr .
   
   # Run
   docker run --rm agrr weather --location 35.6762,139.6503 --days 7
   docker run --rm agrr crop --query "トマト"
   ```

5. **GitHubから直接インストール**
   ```bash
   pip install git+https://github.com/yourusername/agrr.core.git
   agrr --help
   ```

詳細は[DISTRIBUTION.md](DISTRIBUTION.md)を参照してください。

## Quick Start

### CLI Usage

#### Weather Data Fetching

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

#### Growth Progress Calculation

Calculate daily growth progress based on GDD (Growing Degree Days) from weather data file:

```bash
# Calculate growth progress for rice (Koshihikari variety)
agrr progress --crop rice --variety Koshihikari --start-date 2024-05-01 --weather-file weather_data.json

# With short options
agrr progress -c tomato -v Aiko -s 2024-06-01 -w weather_data.csv

# JSON output
agrr progress -c rice -s 2024-05-01 -w weather_data.json --format json

# Table output (default)
agrr progress -c rice -s 2024-05-01 -w weather_data.json --format table
```

**Weather data file format (JSON):**
```json
{
  "data": [
    {
      "time": "2024-05-01T00:00:00",
      "temperature_2m_mean": 20.5,
      "temperature_2m_max": 25.0,
      "temperature_2m_min": 15.0
    },
    ...
  ]
}
```

**Weather data file format (CSV):**
```csv
time,temperature_2m_mean,temperature_2m_max,temperature_2m_min
2024-05-01T00:00:00,20.5,25.0,15.0
2024-05-02T00:00:00,21.0,26.0,16.0
...
```

**Table output example:**
```
=== Growth Progress for Rice ===
Variety: Koshihikari
Start Date: 2024-05-01
Total Records: 100

Date         Stage                GDD       Progress  Complete
-----------------------------------------------------------------
2024-05-01   Vegetative           15.0       1.5%     No
2024-05-02   Vegetative           30.0       3.0%     No
2024-05-03   Vegetative           45.5       4.6%     No
...
2024-08-08   Maturity            1000.0     100.0%    Yes

Final Progress: 100.0%
Total GDD Accumulated: 1000.0 / 1000.0
```

**JSON output example:**
```json
{
  "crop_name": "Rice",
  "variety": "Koshihikari",
  "start_date": "2024-05-01T00:00:00",
  "progress_records": [
    {
      "date": "2024-05-01T00:00:00",
      "cumulative_gdd": 15.0,
      "total_required_gdd": 1000.0,
      "growth_percentage": 1.5,
      "stage_name": "Vegetative",
      "is_complete": false
    },
    ...
  ]
}
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
- 🌱 **Growth Progress Calculation**: Calculate daily growth progress based on GDD (Growing Degree Days)
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
