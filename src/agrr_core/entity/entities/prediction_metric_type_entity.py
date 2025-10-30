"""Metric type enumeration."""

from enum import Enum

class MetricType(Enum):
    """Supported weather metrics."""
    TEMPERATURE = "temperature"
    PRECIPITATION = "precipitation"
    SUNSHINE = "sunshine"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    WIND_SPEED = "wind_speed"
