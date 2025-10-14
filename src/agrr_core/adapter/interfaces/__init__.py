"""Adapter layer interfaces."""

from .file_repository_interface import FileRepositoryInterface
from .http_service_interface import HttpServiceInterface
from .prediction_service_interface import PredictionServiceInterface

__all__ = [
    "FileRepositoryInterface",
    "HttpServiceInterface",
    "PredictionServiceInterface"
]
