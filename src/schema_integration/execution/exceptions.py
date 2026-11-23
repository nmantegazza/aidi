"""Exceptions for schema integration execution step."""

from __future__ import annotations


class DataPortingError(Exception):
    """Base exception for data porting errors."""

    pass


class UnresolvableColumnError(DataPortingError):
    """Raised when a mapped column cannot be found in the source table."""

    pass


class TableNotFoundError(DataPortingError):
    """Raised when a mapped source table is missing from source data."""

    pass


class UnresolvableJoinError(DataPortingError):
    """Raised when multiple source tables mapped without valid foreign keys."""

    pass

