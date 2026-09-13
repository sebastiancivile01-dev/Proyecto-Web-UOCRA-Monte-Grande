"""Calculos BCRA puros sobre una respuesta ya obtenida."""

from datetime import date, datetime


def cer_for_date(items: list[dict], target: str | None = None) -> float | None:
    if not items:
        return None
    if target is None:
        return float(items[-1]["v"])
    wanted = datetime.strptime(target, "%Y-%m-%d").date()
    for item in reversed(items):
        if datetime.strptime(item["d"], "%Y-%m-%d").date() <= wanted:
            return float(item["v"])
    return None
