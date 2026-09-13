"""Estado y transformaciones puras de la Carga Simplificada."""

from copy import deepcopy
from urllib.parse import urlencode

import pandas as pd


DEFAULT_LOCATION = {"latitud": -34.821, "longitud": -58.467}
SIMPLE_STATE_KEYS = (
    "simple_kind",
    "simple_step",
    "simple_draft",
    "simple_location",
    "simple_map_candidate",
    "simple_search_results",
    "simple_pending",
    "simple_save_locked",
    "simple_success",
)


def google_maps_url(latitud: float, longitud: float) -> str:
    """Construye un enlace de consulta universal, sin requerir API key."""
    return "https://www.google.com/maps/search/?" + urlencode(
        {"api": "1", "query": f"{float(latitud):.6f},{float(longitud):.6f}"}
    )


def normalize_location(latitud, longitud, source: str, label: str = "") -> dict:
    lat = float(latitud)
    lon = float(longitud)
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("La ubicación está fuera de rango.")
    return {"latitud": lat, "longitud": lon, "source": source, "label": str(label).strip()}


def next_obra_id(df_obras: pd.DataFrame) -> int:
    """Replica la numeración vigente de ABM sin redefinir la identidad de Obra."""
    if df_obras.empty or "Obra_ID" not in df_obras.columns:
        return 1
    ids = pd.to_numeric(df_obras["Obra_ID"], errors="coerce").dropna()
    return int(ids.max() + 1) if not ids.empty else 1


def obra_record(draft: dict, location: dict, obra_id: int) -> dict:
    empresa = draft.get("empresa_nueva", "").strip() if draft.get("empresa") == "➕ Nueva..." else draft.get("empresa", "")
    return {
        "Obra_ID": obra_id,
        "Predio": draft.get("predio", ""),
        "Empresa": empresa,
        "Delegado": ", ".join(draft.get("delegados", [])),
        "Obreros": draft.get("obreros", 0),
        "Estado": draft.get("estado", ""),
        "Latitud": location["latitud"],
        "Longitud": location["longitud"],
        "Jurisdiccion": draft.get("jurisdiccion", ""),
        "Jurisdiccion_R": "SI" if draft.get("jurisdiccion_r") else "",
        "Mujeres": 0,
    }


def predio_record(draft: dict, location: dict) -> dict:
    return {
        "Nombre": draft.get("nombre", ""),
        "Latitud": location["latitud"],
        "Longitud": location["longitud"],
        "Radio_KM": draft.get("radio_km", 1.0),
        "Observaciones": draft.get("observaciones", ""),
    }


def validate_draft(kind: str, draft: dict, location: dict | None) -> list[str]:
    errors = []
    if kind == "predio" and not str(draft.get("nombre", "")).strip():
        errors.append("El nombre del Polo/Predio es obligatorio.")
    if location is None:
        errors.append("Seleccione una ubicación antes de revisar.")
    return errors


def pending_record(kind: str, draft: dict, location: dict, df_obras: pd.DataFrame) -> dict:
    if kind == "obra":
        return obra_record(deepcopy(draft), deepcopy(location), next_obra_id(df_obras))
    if kind == "predio":
        return predio_record(deepcopy(draft), deepcopy(location))
    raise ValueError("Tipo de carga no disponible.")


def clear_simple_state(session: dict, *, keep_mode: bool = True) -> None:
    # Los widgets ocultos se eliminan al siguiente rerun. Borrarlos dentro de
    # un callback puede invalidar el árbol de widgets que Streamlit está usando.
    for key in SIMPLE_STATE_KEYS:
        if key in session:
            del session[key]
    if not keep_mode and "simple_app_mode" in session:
        del session["simple_app_mode"]
