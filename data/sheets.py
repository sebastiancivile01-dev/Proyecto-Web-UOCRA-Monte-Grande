"""Boundary de Google Sheets con dependencias inyectadas."""

from collections.abc import Callable, Sequence
from typing import Any


def load_table(read: Callable[..., Any], worksheet: Any, columns: Sequence[str]) -> Any:
    return read(worksheet, list(columns))


def save_table(write: Callable[..., Any], worksheet: Any, frame: Any, version: Any) -> Any:
    return write(worksheet, frame, version)
