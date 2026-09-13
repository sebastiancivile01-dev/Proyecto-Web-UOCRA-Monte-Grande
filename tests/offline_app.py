"""Real bootstrap/screens with synthetic tables and no external clients."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
import streamlit as st


def tables(populated=False):
    tree = ast.parse((Path(__file__).resolve().parents[1] / "data/runtime.py").read_text(encoding="utf-8"))
    frames = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "cargar_db":
            name, columns = map(ast.literal_eval, node.args)
            frames[name] = pd.DataFrame(columns=columns)
    if populated:
        defaults = {"Empresa": "Empresa A", "Predio": "Polo A", "Nombre": "Persona A",
                    "Estado": "Activa", "Latitud": -34.8, "Longitud": -58.5,
                    "Radio_KM": 1.0, "Obra_ID": 1, "Obreros": 10, "Mujeres": 2,
                    "Jurisdiccion": "Ezeiza", "Jurisdiccion_R": "SI", "CUIL": 20123456789,
                    "Fecha": "01/09/2026", "Nacimiento": "01/01/1980", "Titulo": "Acta [A]",
                    "Observacion": "Nota [A]", "Tipo": "Foto", "Quincena": "Q1", "Fechas": "1 al 15"}
        for name, frame in frames.items():
            frames[name] = pd.DataFrame([{col: defaults.get(col, "") for col in frame.columns}])
        frames["Predios"].at[0, "Nombre"] = "Polo A"
        for col, value in zip(["Ayudante", "Medio_Oficial", "Oficial", "Oficial_Especializado", "Viatico"], [5470, 6000, 6800, 7500, 15733.3]):
            frames["Paritarias_Historia"][col] = value
    return frames


def initialize():
    frames = st.session_state.setdefault("_test_tables", tables())
    source = ast.parse((Path(__file__).resolve().parents[1] / "data/runtime.py").read_text(encoding="utf-8"))
    result = {}
    for node in ast.walk(source):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "cargar_db":
            result[node.targets[0].id] = frames[ast.literal_eval(node.value.args[0])].copy(deep=True)

    def save(frame, name):
        st.session_state.setdefault("_test_writes", []).append((name, frame.copy(deep=True)))
        if st.session_state.get("_test_fail_save", False):
            return False
        frames[name] = frame.copy(deep=True)
        return True

    result.update(guardar_db=save, cargar_db=lambda name, cols: frames[name].copy(deep=True),
                  registrar_log=lambda action: st.session_state.setdefault("_test_logs", []).append(action),
                  cargar_limites_mapa=lambda: None,
                  lista_empresas_historicas=["Empresa A", "Empresa B"],
                  lista_predios_historicos=frames["Predios"]["Nombre"].tolist(),
                  lista_delegados_nombres=frames["Delegados"]["Nombre"].tolist(),
                  lista_jurisdicciones=["Ezeiza", "Esteban Echeverría"],
                  lista_estados=["Activa", "Intervenida", "Finalizada", "Interrumpida"])
    return result


def run():
    import bootstrap
    from contextlib import ExitStack
    model = MagicMock()
    model.start_chat.return_value.send_message.return_value.text = "Respuesta local simulada"

    def response(url, **kwargs):
        if url == "https://api.estadisticasbcra.com/cer":
            return SimpleNamespace(status_code=200, json=lambda: [{"d": "1900-01-01", "v": 100.0}])
        if url.startswith("https://nolaborables.com.ar/api/v2/feriados/"):
            return SimpleNamespace(status_code=200, json=lambda: [])
        raise AssertionError("Unexpected external request")

    with ExitStack() as stack:
        stack.enter_context(patch.object(bootstrap, "initialize", initialize))
        stack.enter_context(patch.object(st, "secrets", {"passwords": {"admin": "test-admin", "restringido": "test-restricted"}, "GEMINI_API_KEY": "test", "BCRA_TOKEN": "test"}))
        stack.enter_context(patch("requests.get", side_effect=response))
        stack.enter_context(patch("requests.sessions.Session.request", side_effect=AssertionError("Network forbidden")))
        stack.enter_context(patch("socket.socket.connect", side_effect=AssertionError("Network forbidden")))
        stack.enter_context(patch("gspread.authorize", side_effect=AssertionError("Sheets forbidden")))
        stack.enter_context(patch("google.cloud.storage.Client", side_effect=AssertionError("Storage forbidden")))
        stack.enter_context(patch.object(bootstrap.genai, "configure"))
        stack.enter_context(patch.object(bootstrap.genai, "GenerativeModel", return_value=model))
        stack.enter_context(patch("time.sleep"))
        bootstrap.main()
