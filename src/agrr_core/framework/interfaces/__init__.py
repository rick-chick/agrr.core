"""Framework layer interfaces package.

These interfaces define contracts for internal Framework layer components.
They are used for abstraction and testing within the Framework layer.
"""

from .csv_service_interface import CsvServiceInterface
from .html_table_fetch_interface import HtmlTableFetchInterface
from .html_table_structures import HtmlTable, TableRow
from .http_service_interface import HttpServiceInterface
from .time_series_interface import TimeSeriesInterface, TimeSeriesModel, FittedTimeSeriesModel

__all__ = [
    "CsvServiceInterface",
    "HtmlTableFetchInterface",
    "HtmlTable",
    "TableRow",
    "HttpServiceInterface",
    "TimeSeriesInterface",
    "TimeSeriesModel",
    "FittedTimeSeriesModel",
]
