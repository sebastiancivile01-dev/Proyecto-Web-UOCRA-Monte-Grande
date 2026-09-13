"""Politicas de autorizacion reutilizables."""


def is_allowed(role: str | None, module: str, restricted_modules: set[str] | None = None) -> bool:
    if role == "Admin":
        return True
    if role != "Restringido":
        return False
    return module not in (restricted_modules or set())
