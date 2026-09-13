"""Validacion de credenciales inyectadas, sin leer secrets al importar."""


def authenticate(password: str, admin_password: str, restricted_password: str) -> str | None:
    if password == admin_password:
        return "Admin"
    if password == restricted_password:
        return "Restringido"
    return None
