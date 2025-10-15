"""Adapter interfaces package."""

# Clients
from .clients.http_client_interface import HttpClientInterface
from .clients.llm_client_interface import LLMClientInterface

# I/O Services
from .io.file_service_interface import FileServiceInterface
from .io.csv_service_interface import CsvServiceInterface
from .io.html_table_service_interface import HtmlTableServiceInterface

# ML Services
from .ml.prediction_service_interface import PredictionServiceInterface
from .ml.time_series_service_interface import TimeSeriesServiceInterface

# Structures
from .structures.html_table_structures import HtmlTable, TableRow

__all__ = [
    # Clients
    'HttpClientInterface',
    'LLMClientInterface',
    # I/O Services
    'FileServiceInterface',
    'CsvServiceInterface',
    'HtmlTableServiceInterface',
    # ML Services
    'PredictionServiceInterface',
    'TimeSeriesServiceInterface',
    # Structures
    'HtmlTable',
    'TableRow',
]
