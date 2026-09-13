"""Reglas puras para el filtrado de limites territoriales."""


def filter_boundary(feature):
    name = str(feature["properties"].get("departamento", "")).lower()
    is_jurisdiction = any(
        candidate in name
        for candidate in [
            "echeverr", "ezeiza", "cañuela", "canuela", "roque p",
            "lobos", "saladillo", "navarro", "belgrano", "heras",
        ]
    ) or name in ["monte", "san miguel del monte"]
    if "viamonte" in name or "hermoso" in name:
        is_jurisdiction = False
    return (
        {"fillColor": "#3186cc", "color": "#000000", "weight": 1.5, "fillOpacity": 0.15}
        if is_jurisdiction
        else {"fillColor": "transparent", "color": "transparent", "weight": 0}
    )