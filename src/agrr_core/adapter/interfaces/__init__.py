"""Adapter layer interfaces."""

from .file_repository_interface import FileRepositoryInterface
from .http_service_interface import HttpServiceInterface

__all__ = [
    "FileRepositoryInterface",
    "HttpServiceInterface"
]
