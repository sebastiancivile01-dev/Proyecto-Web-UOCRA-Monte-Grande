"""Boundary de almacenamiento externo; el cliente se inyecta al invocar."""


def upload(upload_fn, content, filename: str):
    return upload_fn(content, filename)
