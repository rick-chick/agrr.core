"""Framework layer repositories."""

from .file_repository import FileRepository
from .http_client import HttpClient
from .html_table_fetcher import HtmlTableFetcher
from .csv_downloader import CsvDownloader

__all__ = [
    'FileRepository',
    'HttpClient',
    'HtmlTableFetcher',
    'CsvDownloader',
]
