"""Helpers de sesion sin acceso directo a Streamlit."""


def current_role(session: dict) -> str | None:
    return session.get("usuario_rol")


def set_role(session: dict, role: str | None) -> None:
    session["usuario_rol"] = role


def clear_session(session: dict) -> None:
    """Limpia estado de usuario conservando la referencia del mapping."""
    session.clear()
    session["usuario_rol"] = None


def logout(session: dict) -> None:
    clear_session(session)
