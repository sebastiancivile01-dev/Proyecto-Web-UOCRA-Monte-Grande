"""Normalizacion de feriados sin realizar requests al importar."""


def normalize_holidays(items: list[dict]) -> list[dict]:
    return [{"motivo": item["motivo"], "dia": item["dia"], "mes": item["mes"], "tipo": item.get("tipo", "Feriado Nacional"), "color": item.get("color", "#28a745")} for item in items]
