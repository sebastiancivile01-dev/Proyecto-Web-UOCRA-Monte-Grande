"""Caché real de Streamlit + gspread real; HTTP falso y reloj controlado.

La referencia ANTES conserva las funciones de Fase 1 previas a este parche.
Se ejecutan las 15 cargas actuales, sin importar la app, secretos ni su UI.
"""
import ast
from collections import Counter
from contextlib import ExitStack
import copy
import json
import linecache
import logging
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import unquote

import gspread
from google.auth.credentials import AnonymousCredentials
from gspread.http_client import HTTPClient
import pandas as pd
import requests
import streamlit as st
from streamlit.runtime.caching import cache_utils

import safety


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
APP = ast.parse(SOURCE)
FUNCTION_NAMES = {"_leer_db_cache", "cargar_db", "guardar_db"}

# Copia del árbol de trabajo de refactor/pre-azure-safety antes del parche.
BEFORE = '''
@st.cache_data(ttl=20)
def _leer_db_cache(documento_id, hoja_nombre, columnas):
    return leer_hoja(DOC.worksheet(hoja_nombre), columnas)


def cargar_db(hoja_nombre, columnas):
    versiones = st.session_state.setdefault("_versiones_hojas", {})
    versiones.pop(hoja_nombre, None)
    try:
        df, version = _leer_db_cache(DOC.id, hoja_nombre, columnas)
    except Exception:
        _leer_db_cache.clear()
        st.error(f"No se pudo leer {hoja_nombre}. No se habilitarán escrituras. Recargue para volver a intentar.")
        st.stop()
    versiones[hoja_nombre] = version
    return df


def guardar_db(df, hoja_nombre):
    versiones = st.session_state.setdefault("_versiones_hojas", {})
    version = versiones.pop(hoja_nombre, None)
    try:
        escribir_hoja(DOC.worksheet(hoja_nombre), df, version)
    except ConflictoEscrituraError:
        st.error(f"{hoja_nombre} cambió mientras trabajaba. No se guardó. Actualice los datos y revise los cambios antes de reintentar.")
        return False
    except Exception:
        st.error(f"No se pudo confirmar el guardado en {hoja_nombre}. Actualice y verifique la hoja antes de repetir la operación.")
        return False
    finally:
        _leer_db_cache.clear()
    return True
'''


class StopRun(BaseException):
    pass


class FakeHTTP:
    """Cuenta metadatos, valores y escrituras en la frontera HTTP de gspread."""

    def __init__(self, schemas):
        self.schemas = schemas
        self.values = {name: [cols[:], ["Empresa original" if col == "Empresa" else "1"
                                       for col in cols]]
                       for name, cols in schemas.items()}
        self.events = []
        self.failed_reads = set()
        self.fail_next_metadata = False
        self.timeout_after_write = False

    def request(self, method, endpoint, **kwargs):
        method = method.lower()
        assert endpoint.startswith("https://sheets.googleapis.com/v4/spreadsheets/")
        if "/values/" in endpoint:
            title = unquote(endpoint.split("/values/", 1)[1]).split("!")[0].strip("'")
            assert method in {"get", "put"}, "No se permite clear/append en esta prueba"
            self.events.append((method, "values", title))
            if method == "put":
                assert kwargs["params"]["valueInputOption"] == "RAW"
                self.values[title] = copy.deepcopy(kwargs["json"]["values"])
                if self.timeout_after_write:
                    raise requests.Timeout("Respuesta perdida tras aplicar escritura")
                data = {"updatedRange": title}
            else:
                if title in self.failed_reads:
                    self.quota_error()
                data = {"range": title, "majorDimension": "ROWS",
                        "values": copy.deepcopy(self.values[title])}
        else:
            assert method == "get"
            self.events.append((method, "metadata", None))
            if self.fail_next_metadata:
                self.fail_next_metadata = False
                self.quota_error()
            data = {
                "spreadsheetId": "fake-document",
                "properties": {"title": "Fake document"},
                "sheets": [{"properties": {
                    "sheetId": i, "title": title,
                    "gridProperties": {"rowCount": 100, "columnCount": len(cols)},
                }} for i, (title, cols) in enumerate(self.schemas.items())],
            }
        return self.response(200, data)

    @staticmethod
    def response(status, data):
        response = requests.Response()
        response.status_code = status
        response._content = json.dumps(data).encode()
        return response

    def quota_error(self):
        raise gspread.exceptions.APIError(self.response(429, {"error": {
            "code": 429, "message": "SIMULATED quota exceeded",
            "status": "RESOURCE_EXHAUSTED",
        }}))


class OfflineApp:
    def __init__(self, before=False):
        loads = [node for node in APP.body if isinstance(node, ast.Assign)
                 and isinstance(node.value, ast.Call)
                 and isinstance(node.value.func, ast.Name)
                 and node.value.func.id == "cargar_db"]
        self.schemas = {ast.literal_eval(node.value.args[0]):
                        ast.literal_eval(node.value.args[1]) for node in loads}
        connection = next(node for node in ast.walk(APP)
                          if isinstance(node, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == "DOC"
                                  for t in node.targets))
        definitions = [node for node in APP.body
                       if isinstance(node, ast.FunctionDef)
                       and node.name in FUNCTION_NAMES]

        def segment(node):
            start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
            return dedent("\n".join(SOURCE.splitlines()[start - 1:node.end_lineno]))

        script = "\n\n".join([segment(connection),
                              BEFORE if before else "\n\n".join(map(segment, definitions)),
                              "\n".join(map(segment, loads))])
        self.filename = "<sheets-cache-before>" if before else "<sheets-cache-after>"
        linecache.cache[self.filename] = (len(script), None, script.splitlines(True), self.filename)
        self.code = compile(script, self.filename, "exec")
        self.now = 0.0
        self.http = FakeHTTP(self.schemas)
        self.ui = SimpleNamespace(cache_data=st.cache_data, session_state={},
                                  error=Mock(), stop=Mock(side_effect=StopRun))
        self.env = dict(__name__=self.filename, st=self.ui, pd=pd,
                        client=gspread.Client(auth=AnonymousCredentials()),
                        URL_DEL_EXCEL="https://docs.google.com/spreadsheets/d/fake-document/edit",
                        leer_hoja=safety.leer_hoja, escribir_hoja=safety.escribir_hoja,
                        ConflictoEscrituraError=safety.ConflictoEscrituraError)

    def __enter__(self):
        self.stack = ExitStack()
        previous_logging = logging.root.manager.disable
        logging.disable(logging.CRITICAL)
        self.stack.callback(logging.disable, previous_logging)
        self.stack.enter_context(patch.object(cache_utils, "TTLCACHE_TIMER", lambda: self.now))
        self.stack.enter_context(patch.object(HTTPClient, "request", self.http.request))
        self.network = self.stack.enter_context(patch(
            "requests.sessions.Session.request", side_effect=AssertionError("Red prohibida")))
        self.sockets = self.stack.enter_context(patch(
            "socket.socket.connect", side_effect=AssertionError("Red prohibida")))
        self.snapshots = self.stack.enter_context(patch.object(
            safety, "_snapshot", wraps=safety._snapshot))
        st.cache_data.clear()
        self.stack.callback(st.cache_data.clear)
        return self

    def __exit__(self, *exc):
        try:
            self.network.assert_not_called()
            self.sockets.assert_not_called()
        finally:
            self.stack.close()
            linecache.cache.pop(self.filename, None)

    def run(self, now, screen="Mapa"):
        self.now = now
        self.ui.session_state["menu_seleccionado"] = screen
        stopped = False
        start = len(self.http.events)
        try:
            # Recrea DOC y los decoradores en cada rerun, como app.py.
            exec(self.code, self.env)
        except StopRun:
            stopped = True
        counts = Counter(kind for method, kind, title in self.http.events[start:]
                         if method == "get")
        return sum(counts.values()), stopped

    def load(self, title, columns=None):
        return self.env["cargar_db"](title, self.schemas[title] if columns is None else columns)

    def save(self, title, df):
        return self.env["guardar_db"](df, title)


class SheetsCacheTests(unittest.TestCase):
    def test_cold_load_reruns_navigation_and_ttl_before_after(self):
        for before in (True, False):
            with self.subTest(before=before), OfflineApp(before) as app:
                self.assertEqual(len(app.schemas), 15)
                self.assertEqual(app.run(0), (31, False))
                self.assertEqual(app.snapshots.call_count, 15)
                for now, screen in [(1, "Mapa"), (2, "Mapa"), (3, "Nominas"), (4, "Mapa")]:
                    self.assertEqual(app.run(now, screen), (1, False))
                self.assertEqual(app.snapshots.call_count, 15)
                self.assertEqual(app.run(21), (31 if before else 1, False))
                self.assertEqual(app.run(119), (31 if before else 1, False))
                self.assertEqual(app.run(120), (1 if before else 31, False))

    def test_one_failed_sheet_and_repeated_reruns_before_after(self):
        for before in (True, False):
            with self.subTest(before=before), OfflineApp(before) as app:
                app.http.failed_reads.add("Puntos_Extra")
                self.assertEqual(app.run(0), (31, True))
                self.assertEqual(app.run(1), (31 if before else 1, True))
                # Aunque la red se recupere, el fallo se conserva hasta el TTL.
                app.http.failed_reads.clear()
                self.assertEqual(app.run(2), (31, False) if before else (1, True))
                if not before:
                    start = len(app.http.events)
                    self.assertFalse(app.load("Obras").empty)
                    self.assertEqual(len(app.http.events), start)
                    self.assertNotIn("Puntos_Extra", app.ui.session_state["_versiones_hojas"])
                    self.assertNotIn("Puntos_Extra", app.ui.session_state["_claves_cache_hojas"])
                    self.assertEqual(app.run(120), (31, False))

    def test_empty_sheet_is_valid_but_cached_failure_cannot_authorize_writes(self):
        with OfflineApp() as app:
            app.http.values["Puntos_Extra"] = []
            self.assertEqual(app.run(0), (31, False))
            empty = app.load("Puntos_Extra")
            self.assertTrue(empty.empty)
            self.assertEqual(list(empty.columns), app.schemas["Puntos_Extra"])
            version = app.ui.session_state["_versiones_hojas"]["Puntos_Extra"]
            self.assertIsNotNone(version)
            self.assertTrue(app.save("Puntos_Extra", empty))
            app.http.failed_reads.add("Puntos_Extra")
            # Comprueba que una versión anterior tampoco sobreviva al fallo.
            app.ui.session_state["_versiones_hojas"]["Puntos_Extra"] = version
            with self.assertRaises(StopRun):
                app.load("Puntos_Extra")
            start = len(app.http.events)
            self.assertFalse(app.save("Puntos_Extra", empty))
            with self.assertRaises(StopRun):
                app.load("Puntos_Extra")
            self.assertEqual(len(app.http.events), start)

    def test_worksheet_metadata_failure_is_also_cached(self):
        with OfflineApp() as app:
            app.run(0)
            app.env["_leer_db_cache"].clear("fake-document", "Obras", app.schemas["Obras"])
            app.http.fail_next_metadata = True
            with self.assertRaises(StopRun):
                app.load("Obras")
            start = len(app.http.events)
            with self.assertRaises(StopRun):
                app.load("Obras")
            app.load("Predios")
            self.assertEqual(len(app.http.events), start)

    def test_write_invalidates_original_key_only_before_after(self):
        for before in (True, False):
            with self.subTest(before=before), OfflineApp(before) as app:
                app.run(0)
                df = app.load("Convenios")
                # Los formularios pueden agregar columnas que no están en la clave.
                df["Link_PDF"] = "https://fake/document.pdf"
                start = len(app.http.events)
                self.assertTrue(app.save("Convenios", df))
                self.assertEqual(app.http.events[start:], [
                    ("get", "metadata", None), ("get", "values", "Convenios"),
                    ("put", "values", "Convenios"),
                ])
                self.assertEqual(app.run(1), (31 if before else 3, False))
                self.assertIn("Link_PDF", app.load("Convenios").columns)
                self.assertEqual(app.run(2), (1, False))

    def test_conflict_and_uncertain_write_preserve_other_sheets(self):
        for uncertain in (False, True):
            with self.subTest(uncertain=uncertain), OfflineApp() as app:
                app.run(0)
                df = app.load("Obras")
                df.loc[0, "Empresa"] = "Mi cambio"
                if uncertain:
                    app.http.timeout_after_write = True
                else:
                    app.http.values["Obras"][1][2] = "Cambio externo"
                self.assertFalse(app.save("Obras", df))
                writes = [e for e in app.http.events if e[0] == "put"]
                self.assertEqual(len(writes), 1 if uncertain else 0)
                start = len(app.http.events)
                self.assertFalse(app.save("Obras", df))
                self.assertEqual(len(app.http.events), start)
                self.assertEqual(app.run(1), (3, False))
                self.assertEqual(app.load("Obras").loc[0, "Empresa"],
                                 "Mi cambio" if uncertain else "Cambio externo")

    def test_other_session_with_cached_old_snapshot_cannot_overwrite(self):
        with OfflineApp() as app:
            app.run(0)
            first_state = app.ui.session_state
            first = app.load("Obras")
            app.ui.session_state = {}
            second = app.load("Obras")
            second_state = app.ui.session_state
            first.loc[0, "Empresa"] = "Usuario A"
            second.loc[0, "Empresa"] = "Usuario B"
            app.ui.session_state = first_state
            self.assertTrue(app.save("Obras", first))
            app.ui.session_state = second_state
            self.assertFalse(app.save("Obras", second))
            self.assertEqual(len([e for e in app.http.events if e[0] == "put"]), 1)

    def test_manual_refresh_explicitly_clears_success_and_failure(self):
        branch = next(node for node in ast.walk(APP) if isinstance(node, ast.If)
                      and isinstance(node.test, ast.Call) and node.test.args
                      and isinstance(node.test.args[0], ast.Constant)
                      and "Actualizar Datos" in str(node.test.args[0].value))
        with OfflineApp() as app:
            app.http.failed_reads.add("Puntos_Extra")
            app.run(0)
            app.http.failed_reads.clear()
            app.ui.rerun = Mock(side_effect=StopRun)
            code = compile(ast.Module(body=branch.body, type_ignores=[]), "<refresh>", "exec")
            with self.assertRaises(StopRun):
                exec(code, app.env)
            self.assertEqual(app.run(1), (31, False))


if __name__ == "__main__":
    unittest.main()
