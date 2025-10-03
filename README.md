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

## Quick Start

### Basic Usage

```python
from agrr_core import WeatherController, OpenMeteoWeatherRepository, InMemoryPredictionRepository, FetchWeatherDataInteractor, PredictWeatherInteractor

# Initialize the system
weather_repo = OpenMeteoWeatherRepository()
prediction_repo = InMemoryPredictionRepository()

fetch_interactor = FetchWeatherDataInteractor(weather_repo)
predict_interactor = PredictWeatherInteractor(weather_repo, prediction_repo)

controller = WeatherController(fetch_interactor, predict_interactor)

# Fetch historical weather data
weather_result = controller.get_weather_data_sync(
    latitude=35.7,  # Tokyo latitude
    longitude=139.7,  # Tokyo longitude
    start_date="2019-01-01",
    end_date="2023-12-31"
)

# Generate weather prediction
prediction_result = controller.predict_weather_sync(
    latitude=35.7,
    longitude=139.7,
    start_date="2019-01-01",
    end_date="2023-12-31",
    prediction_days=365
)

print(f"Historical data points: {len(prediction_result['historical_data'])}")
print(f"Forecast points: {len(prediction_result['forecast'])}")
```

### Run Examples

```bash
# Simple example (equivalent to original script)
python simple_weather_example.py

# Detailed example with error handling
python example_usage.py
```

## Features

- 🌤️ **Weather Data Fetching**: Get historical weather data from Open-Meteo API
- 🔮 **Weather Prediction**: Predict future weather using Prophet time series model
- 🏗️ **Clean Architecture**: Implemented following clean architecture principles
- 📊 **Data Processing**: Convert and process weather data using pandas
- 🎯 **Easy to Use**: Simple API for both synchronous and asynchronous usage

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

## Dependencies

- `requests>=2.25.0` - HTTP client for API calls
- `pandas>=1.3.0` - Data manipulation and analysis
- `prophet>=1.1.0` - Time series forecasting
- `matplotlib>=3.5.0` - Plotting (optional)
- `numpy>=1.20.0` - Numerical computations

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
