"""Protecciones acotadas para la fase 1; sin UI ni conexiones al importar.

El bloqueo serializa sesiones de UN proceso. Sheets no ofrece compare-and-swap
para esta actualización: otras instancias y editores externos no comparten
el bloqueo. No habilitar múltiples escritores externos a este proceso.
"""
import json
import math
from pathlib import Path
from threading import RLock

import pandas as pd
from gspread.utils import numericise_all

_SHEETS_LOCK = RLock()
GEOJSON_PATH = Path(__file__).resolve().parent / "assets" / "departamentos-buenos_aires.json"
MODULOS_ADMIN = {"2. 📥 Carga de Datos (ABM)", "5. ⚠️ Reclamos"}


class LecturaRequeridaError(RuntimeError):
    pass


class ConflictoEscrituraError(RuntimeError):
    pass


def _snapshot(values):
    return tuple(tuple(row) for row in values)


def leer_hoja(sheet, columnas):
    """Una sola lectura produce tanto los datos como su versión de comparación.

    Se conserva la conversión numérica predeterminada de get_all_records().
    Los errores se propagan: nunca equivalen a una hoja vacía.
    """
    with _SHEETS_LOCK:
        values = sheet.get_all_values()
        version = _snapshot(values)
        if not values or not any(any(cell != "" for cell in row) for row in values):
            return pd.DataFrame(columns=columnas), version
        headers = list(values[0])
        if not all(headers) or len(set(headers)) != len(headers):
            raise ValueError("La hoja tiene encabezados vacíos o duplicados.")
        rows = [numericise_all(list(row)) for row in values[1:]]
        return pd.DataFrame(rows, columns=headers), version


def escribir_hoja(sheet, df, version):
    """Comprueba versión y reemplaza valores en UNA petición, sin clear previo.

    Las filas sobrantes se vacían dentro de esa misma petición. No se cambian
    formatos ni el orden de columnas existentes; se permiten columnas nuevas
    que ya agregan los formularios (por ejemplo Link_PDF en Convenios).
    Una excepción de red puede tener resultado incierto: no reintentar a ciegas.
    """
    if version is None:
        raise LecturaRequeridaError("Falta una lectura válida de esta hoja.")
    with _SHEETS_LOCK:
        actual = sheet.get_all_values()
        if _snapshot(actual) != version:
            raise ConflictoEscrituraError("La hoja cambió desde su lectura.")
        columns = list(df.columns)
        if not all(columns) or len(set(columns)) != len(columns):
            raise ValueError("Las columnas a guardar no son válidas.")
        anteriores = list(actual[0]) if actual and any(actual[0]) else []
        if not set(anteriores).issubset(columns):
            raise ValueError("La escritura eliminaría columnas existentes.")
        columns = anteriores + [col for col in columns if col not in anteriores]
        limpio = df.reindex(columns=columns).fillna("")
        values = [columns] + limpio.values.tolist()
        alto = max(len(actual), len(values))
        ancho = max([len(row) for row in actual + values], default=0)
        values = [row + [""] * (ancho - len(row)) for row in values]
        values.extend([[""] * ancho for _ in range(alto - len(values))])
        # Validar serialización antes de emitir cualquier escritura.
        json.dumps(values, allow_nan=False)
        sheet.update(values=values, range_name="A1", raw=True)
    return True


def limpiar_sesion(estado):
    for key in list(estado):
        del estado[key]
    estado["usuario_rol"] = None


def modulo_permitido(rol, opcion):
    return rol == "Admin" or (rol == "Restringido" and opcion not in MODULOS_ADMIN)


def validar_geojson(data):
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise ValueError("Se esperaba un GeoJSON FeatureCollection.")
    features = data.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("El GeoJSON no contiene límites.")
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("Feature inválido.")
        props = feature.get("properties")
        if not isinstance(props, dict) or not isinstance(props.get("departamento"), str):
            raise ValueError("Falta el nombre del departamento.")
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError("Geometría de límites inválida.")
        coords = geometry.get("coordinates")
        polygons = [coords] if geometry["type"] == "Polygon" else coords
        if not isinstance(polygons, list) or not polygons:
            raise ValueError("Geometría vacía.")
        for polygon in polygons:
            if not isinstance(polygon, list) or not polygon:
                raise ValueError("Polígono vacío.")
            for ring in polygon:
                if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
                    raise ValueError("Anillo inválido.")
                for point in ring:
                    if not isinstance(point, list) or len(point) < 2:
                        raise ValueError("Coordenada inválida.")
                    x, y = point[:2]
                    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y)):
                        raise ValueError("Coordenada no finita.")
                    if not (-180 <= x <= 180 and -90 <= y <= 90):
                        raise ValueError("Coordenada fuera de rango.")
    return data


def cargar_geojson_local(path=GEOJSON_PATH):
    """Sin red; si el recurso falta o está dañado, el mapa conserva sus marcadores."""
    try:
        return validar_geojson(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError, TypeError):
        return None
