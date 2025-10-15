"""Adapter interfaces package."""

from .file_repository_interface import FileRepositoryInterface
from .llm_client import LLMClient
from .prediction_service_interface import PredictionServiceInterface
from .forecast_repository_interface import ForecastRepositoryInterface
from .http_service_interface import HttpServiceInterface
from .html_table_fetch_interface import HtmlTableFetchInterface
from .html_table_structures import HtmlTable, TableRow
from .time_series_interface import TimeSeriesInterface
from .csv_service_interface import CsvServiceInterface

__all__ = [
    'FileRepositoryInterface',
    'LLMClient',
    'PredictionServiceInterface',
    'ForecastRepositoryInterface',
    'HttpServiceInterface',
    'HtmlTableFetchInterface',
    'HtmlTable',
    'TableRow',
    'TimeSeriesInterface',
    'CsvServiceInterface',
]
