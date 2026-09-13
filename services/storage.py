"""Boundary de almacenamiento externo; el cliente se inyecta al invocar."""

from pathlib import PurePosixPath
import uuid


def unique_object_name(filename: str) -> str:
    """Conserva el nombre legible bajo un prefijo único para cada carga."""
    basename = PurePosixPath(filename.replace("\\", "/")).name
    if basename in {"", ".", ".."}:
        raise ValueError("El archivo debe tener un nombre.")
    return f"{uuid.uuid4().hex}/{basename}"


def upload(upload_fn, content, filename: str):
    return upload_fn(content, filename)
