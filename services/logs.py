"""Registro de auditoria mediante una funcion de persistencia inyectada."""

from datetime import datetime


def audit(append_row, role: str | None, action: str, now: datetime | None = None) -> None:
    moment = now or datetime.now()
    append_row([moment.strftime("%d/%m/%Y"), moment.strftime("%H:%M:%S"), role or "Desconocido", action])
