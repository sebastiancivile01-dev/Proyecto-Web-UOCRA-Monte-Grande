"""Búsqueda geográfica acotada para el flujo simplificado."""

import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "UOCRA-Monte-Grande-Carga-Simplificada/1.0"}


def search_places(query: str, request_get=requests.get) -> list[dict]:
    """Busca manualmente hasta cinco lugares argentinos, sin autocomplete masivo."""
    query = query.strip()
    if not query:
        return []
    response = request_get(
        NOMINATIM_URL,
        params={"q": query, "format": "jsonv2", "limit": 5, "countrycodes": "ar", "addressdetails": 1},
        headers=NOMINATIM_HEADERS,
        timeout=8,
    )
    response.raise_for_status()
    results = []
    for item in response.json():
        try:
            results.append(
                {
                    "label": item.get("display_name", "Ubicación sin nombre"),
                    "latitud": float(item["lat"]),
                    "longitud": float(item["lon"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return results
