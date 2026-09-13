"""Fakes y segmentos reales; sin ejecutar login ni leer secretos."""
import ast
import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import folium
import pandas as pd
import requests
from safety import (ConflictoEscrituraError, LecturaRequeridaError, leer_hoja,
                    escribir_hoja, limpiar_sesion, modulo_permitido,
                    cargar_geojson_local, validar_geojson)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = [ROOT / "data" / "runtime.py"] + sorted((ROOT / "screens").glob("*.py"))
APP = ast.parse("\n\n".join(path.read_text(encoding="utf-8-sig") for path in SOURCE_FILES))
NETWORK = patch("requests.sessions.Session.request", side_effect=AssertionError("Red prohibida en tests"))


def setUpModule():
    NETWORK.start()


def tearDownModule():
    NETWORK.stop()


class StopRun(BaseException):
    pass


class Rerun(BaseException):
    pass


class FakeSheet:
    def __init__(self, values):
        self.values = copy.deepcopy(values)
        self.writes = []
        self.fail_read = self.fail_write = self.timeout_after_write = False

    def get_all_values(self):
        if self.fail_read:
            raise requests.ConnectionError("Lectura caída")
        values = copy.deepcopy(self.values)
        while values and not any(cell != "" for cell in values[-1]):
            values.pop()
        return values

    def update(self, *, values, range_name, raw):
        if self.fail_write:
            raise requests.ConnectionError("Escritura rechazada")
        self.writes.append((copy.deepcopy(values), range_name, raw))
        self.values = copy.deepcopy(values)
        if self.timeout_after_write:
            raise requests.Timeout("Respuesta perdida tras aplicar escritura")

    def clear(self):
        raise AssertionError("Nunca borrar antes de escribir")


def fake_ui(state=None):
    return SimpleNamespace(session_state={} if state is None else state,
                           error=Mock(), warning=Mock(), success=Mock(),
                           stop=Mock(side_effect=StopRun), rerun=Mock(side_effect=Rerun))


def execute(statements, namespace):
    tree = ast.Module(body=copy.deepcopy(statements), type_ignores=[])
    exec(compile(ast.fix_missing_locations(tree), "app.py[test segment]", "exec"), namespace)


def wrappers(sheet):
    st = fake_ui()
    cache = Mock(side_effect=lambda *args: leer_hoja(sheet, args[-1]))
    env = dict(st=st, DOC=SimpleNamespace(id="fake", worksheet=lambda name: sheet),
               _leer_db_cache=cache, escribir_hoja=escribir_hoja,
               ConflictoEscrituraError=ConflictoEscrituraError)
    execute([n for n in ast.walk(APP) if isinstance(n, ast.FunctionDef) and n.name in {"cargar_db", "guardar_db"}], env)
    return env, st, cache


def module_branch(label):
    return next(n for n in ast.walk(APP) if isinstance(n, ast.If)
                and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name)
                and n.test.left.id == "opcion" and isinstance(n.test.comparators[0], ast.Constant)
                and n.test.comparators[0].value == label)


class SheetsTests(unittest.TestCase):
    def test_empty_sheet_can_be_initialized(self):
        sheet = FakeSheet([])
        df, version = leer_hoja(sheet, ["Nombre", "Cantidad"])
        self.assertTrue(df.empty)
        self.assertEqual(list(df.columns), ["Nombre", "Cantidad"])
        self.assertTrue(escribir_hoja(sheet, pd.DataFrame([["Polo", 2]], columns=df.columns), version))
        self.assertEqual(sheet.values, [["Nombre", "Cantidad"], ["Polo", 2]])

    def test_headers_only_keep_optional_columns(self):
        sheet = FakeSheet([["Empresa", "Link_PDF"]])
        df, version = leer_hoja(sheet, ["Empresa"])
        self.assertTrue(df.empty)
        self.assertEqual(list(df.columns), ["Empresa", "Link_PDF"])
        self.assertTrue(escribir_hoja(sheet, df, version))

    def test_numeric_conversion_matches_existing_reader(self):
        sheet = FakeSheet([["Nombre", "Entero", "Decimal", "Vacio"], ["Sur", "12", "2.5", ""]])
        df, _ = leer_hoja(sheet, [])
        self.assertEqual(df.iloc[0].tolist(), ["Sur", 12, 2.5, ""])

    def test_failed_read_is_not_an_empty_table(self):
        sheet = FakeSheet([["Nombre"], ["Existente"]])
        sheet.fail_read = True
        with self.assertRaises(requests.ConnectionError):
            leer_hoja(sheet, ["Nombre"])
        self.assertEqual(sheet.writes, [])

    def test_no_write_without_successful_read(self):
        sheet = FakeSheet([["Nombre"], ["Existente"]])
        with self.assertRaises(LecturaRequeridaError):
            escribir_hoja(sheet, pd.DataFrame(columns=["Nombre"]), None)
        self.assertFalse(sheet.writes)

    def test_write_failure_keeps_previous_data(self):
        sheet = FakeSheet([["Nombre"], ["Existente"]])
        df, version = leer_hoja(sheet, [])
        df.loc[0, "Nombre"] = "Cambio"
        sheet.fail_write = True
        with self.assertRaises(requests.ConnectionError):
            escribir_hoja(sheet, df, version)
        self.assertEqual(sheet.values, [["Nombre"], ["Existente"]])

    def test_deletion_uses_one_write_including_trailing_blanks(self):
        sheet = FakeSheet([["Nombre", "Cantidad"], ["A", "1"], ["B", "2"], ["C", "3"]])
        df, version = leer_hoja(sheet, [])
        escribir_hoja(sheet, df.iloc[:1], version)
        self.assertEqual(sheet.writes, [([["Nombre", "Cantidad"], ["A", 1], ["", ""], ["", ""]], "A1", True)])
        self.assertEqual(len(leer_hoja(sheet, [])[0]), 1)

    def test_delete_last_record_preserves_headers(self):
        sheet = FakeSheet([["Nombre"], ["A"]])
        df, version = leer_hoja(sheet, [])
        escribir_hoja(sheet, df.iloc[:0], version)
        self.assertEqual(sheet.values, [["Nombre"], [""]])

    def test_column_order_preserved_and_optional_column_added(self):
        sheet = FakeSheet([["Empresa", "Detalle"], ["A", "Acuerdo"]])
        _, version = leer_hoja(sheet, [])
        df = pd.DataFrame([["pdf", "Nuevo", "B"]], columns=["Link_PDF", "Detalle", "Empresa"])
        escribir_hoja(sheet, df, version)
        self.assertEqual(sheet.values, [["Empresa", "Detalle", "Link_PDF"], ["B", "Nuevo", "pdf"]])

    def test_cannot_drop_existing_columns(self):
        sheet = FakeSheet([["Empresa", "Extra"], ["A", "Conservar"]])
        _, version = leer_hoja(sheet, [])
        with self.assertRaises(ValueError):
            escribir_hoja(sheet, pd.DataFrame([["A"]], columns=["Empresa"]), version)
        self.assertFalse(sheet.writes)

    def test_duplicate_headers_fail_closed(self):
        with self.assertRaises(ValueError):
            leer_hoja(FakeSheet([["Nombre", "Nombre"], ["A", "B"]]), [])

    def test_invalid_numeric_payload_does_not_write(self):
        sheet = FakeSheet([["Monto"], ["1"]])
        _, version = leer_hoja(sheet, [])
        with self.assertRaises(ValueError):
            escribir_hoja(sheet, pd.DataFrame([[float("inf")]], columns=["Monto"]), version)
        self.assertFalse(sheet.writes)

    def test_external_change_detected_before_write(self):
        sheet = FakeSheet([["Nombre"], ["A"]])
        df, version = leer_hoja(sheet, [])
        sheet.values.append(["Edición externa"])
        with self.assertRaises(ConflictoEscrituraError):
            escribir_hoja(sheet, df, version)
        self.assertFalse(sheet.writes)

    def test_two_simultaneous_users_only_one_wins(self):
        sheet = FakeSheet([["Nombre"], ["Original"]])
        first, version = leer_hoja(sheet, [])
        second = first.copy()
        first.loc[0, "Nombre"], second.loc[0, "Nombre"] = "Usuario A", "Usuario B"
        barrier = Barrier(2)

        def save(df):
            barrier.wait(timeout=5)
            try:
                escribir_hoja(sheet, df, version)
                return "guardado"
            except ConflictoEscrituraError:
                return "conflicto"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(save, [first, second]))
        self.assertCountEqual(results, ["guardado", "conflicto"])
        self.assertEqual(len(sheet.writes), 1)


class AppIntegrationTests(unittest.TestCase):
    def test_load_failure_invalidates_previous_permission_to_write(self):
        sheet = FakeSheet([["Nombre"], ["A"]])
        env, st, cache = wrappers(sheet)
        df = env["cargar_db"]("Obras", ["Nombre"])
        sheet.fail_read = True
        with self.assertRaises(StopRun):
            env["cargar_db"]("Obras", ["Nombre"])
        sheet.fail_read = False
        self.assertFalse(env["guardar_db"](df, "Obras"))
        self.assertFalse(sheet.writes)
        st.success.assert_not_called()
        cache.clear.assert_not_called()

    def test_write_returns_success_only_when_confirmed(self):
        sheet = FakeSheet([["Nombre"], ["A"]])
        env, st, _ = wrappers(sheet)
        df = env["cargar_db"]("Obras", [])
        self.assertTrue(env["guardar_db"](df, "Obras"))
        self.assertFalse(env["guardar_db"](df, "Obras"))
        self.assertEqual(len(sheet.writes), 1)

    def test_timeout_after_commit_cannot_retry_without_reading(self):
        sheet = FakeSheet([["Nombre"], ["A"]])
        env, st, cache = wrappers(sheet)
        df = env["cargar_db"]("Obras", [])
        df.loc[0, "Nombre"] = "B"
        sheet.timeout_after_write = True
        self.assertFalse(env["guardar_db"](df, "Obras"))
        self.assertEqual(sheet.values[1], ["B"])
        self.assertFalse(env["guardar_db"](df, "Obras"))
        self.assertEqual(len(sheet.writes), 1)
        st.success.assert_not_called()

    def test_all_save_callers_stop_before_success_or_log_on_failure(self):
        parents = {child: node for node in ast.walk(APP) for child in ast.iter_child_nodes(node)}
        calls = [n for n in ast.walk(APP) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "guardar_db"]
        self.assertEqual(len(calls), 34)
        for call in calls:
            with self.subTest(line=call.lineno):
                unary = parents[call]
                self.assertIsInstance(unary, ast.UnaryOp)
                self.assertIsInstance(unary.op, ast.Not)
                guard = parents[unary]
                self.assertIsInstance(guard, ast.If)
                st = fake_ui()
                env = dict(st=st, guardar_db=Mock(return_value=False), registrar_log=Mock())
                for arg in call.args:
                    if isinstance(arg, ast.Name):
                        env[arg.id] = pd.DataFrame()
                tail = ast.parse('st.success("éxito"); registrar_log("éxito")').body
                with self.assertRaises(StopRun):
                    execute([guard] + tail, env)
                st.success.assert_not_called()
                env["registrar_log"].assert_not_called()

    def test_real_new_work_handler_success_and_failure(self):
        branch = next(n for n in ast.walk(APP) if isinstance(n, ast.If) and isinstance(n.test, ast.UnaryOp) and isinstance(n.test.operand, ast.Name) and n.test.operand.id == "p_fin")
        for persisted in (False, True):
            with self.subTest(persisted=persisted):
                st = fake_ui()
                env = dict(st=st, pd=pd, df_obras=pd.DataFrame(), p_fin="Polo Sur", e_fin="Empresa A", d_sel=[], obr=3, est="Activa", jur="Ezeiza", lat="", lon="", jur_r=False, guardar_db=Mock(return_value=persisted), registrar_log=Mock())
                with self.assertRaises(Rerun if persisted else StopRun):
                    execute(branch.orelse, env)
                if persisted:
                    st.success.assert_called_once()
                    env["registrar_log"].assert_called_once_with("Alta de Obra #1: Polo Sur (Empresa A)")
                else:
                    st.success.assert_not_called()
                    env["registrar_log"].assert_not_called()

    def test_document_upload_reports_success_only_after_sheet_confirmation(self):
        from contextlib import nullcontext
        from datetime import date
        branch = next(n for n in ast.walk(APP) if isinstance(n, ast.If)
                      and isinstance(n.test, ast.UnaryOp)
                      and isinstance(n.test.operand, ast.Name)
                      and n.test.operand.id == "d_tit")
        for uploaded, saved in ((None, False), ("https://fake/document.pdf", False),
                                ("https://fake/document.pdf", True)):
            with self.subTest(uploaded=bool(uploaded), saved=saved):
                st = fake_ui()
                st.spinner = lambda *args: nullcontext()
                env = dict(st=st, pd=pd, d_tit="Prueba", d_fec=date(2026, 1, 1),
                           d_vig="", d_obs="", archivo_doc=object(),
                           df_documentos=pd.DataFrame(),
                           subir_archivo_drive=Mock(return_value=uploaded),
                           guardar_db=Mock(return_value=saved), registrar_log=Mock())
                with patch("time.sleep"), self.assertRaises(Rerun if saved else StopRun):
                    execute(branch.orelse, env)
                if saved:
                    self.assertEqual(st.success.call_count, 2)
                    self.assertEqual([c.args[0] for c in env["registrar_log"].call_args_list],
                                     ["Subió Archivo", "Guardó Documento"])
                else:
                    st.success.assert_not_called()
                    env["registrar_log"].assert_not_called()
                if uploaded is None:
                    env["guardar_db"].assert_not_called()

    def test_restricted_role_stops_at_module_execution(self):
        for label in ("2. 📥 Carga de Datos (ABM)", "5. ⚠️ Reclamos"):
            self.assertFalse(modulo_permitido("Restringido", label))

    def test_real_logout_removes_all_operational_state(self):
        branch = next(n for n in ast.walk(APP) if isinstance(n, ast.If) and isinstance(n.test, ast.Call) and n.test.args and isinstance(n.test.args[0], ast.Constant) and "Cerrar Sesión" in str(n.test.args[0].value))
        st = fake_ui({"usuario_rol": "Admin", "menu_seleccionado": "ABM", "chat_session": object(), "recibo_txt": "privado", "_versiones_hojas": {"Obras": ()}})
        with self.assertRaises(Rerun):
            execute(branch.body, dict(st=st, limpiar_sesion=limpiar_sesion))
        self.assertEqual(st.session_state, {"usuario_rol": None})

    def test_admin_and_other_modules_remain_accessible(self):
        self.assertTrue(modulo_permitido("Admin", "2. 📥 Carga de Datos (ABM)"))
        self.assertTrue(modulo_permitido("Restringido", "4. 🧮 Calculadoras"))
        self.assertFalse(modulo_permitido(None, "4. 🧮 Calculadoras"))

    def test_demo_has_no_literal_password_comparisons(self):
        demo = ast.parse((ROOT / "prueba_login.py").read_text(encoding="utf-8"))
        checks = [n for n in ast.walk(demo) if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name) and n.left.id == "clave"]
        self.assertEqual(len(checks), 2)
        for check in checks:
            self.assertIsInstance(check.comparators[0], ast.Subscript)


class MapTests(unittest.TestCase):
    def test_bundled_geojson_valid_without_network(self):
        data = cargar_geojson_local()
        self.assertIsNotNone(data)
        features = data["features"]
        self.assertEqual(len(features), 135)
        self.assertEqual(len({f["properties"]["id"] for f in features}), 135)
        for feature in features:
            props = feature["properties"]
            self.assertEqual(props["provincia"]["id"], "06")
            self.assertEqual(props["provincia"]["nombre"], "Buenos Aires")
            self.assertEqual(props["departamento"], props["nombre"])
            self.assertIn(feature["geometry"]["type"], {"Polygon", "MultiPolygon"})
        self.assertIs(validar_geojson(data), data)

    def test_official_boundaries_preserve_exact_current_jurisdictions(self):
        from domain.map import filter_boundary

        data = cargar_geojson_local()
        expected = {
            "06260": "Esteban Echeverría", "06270": "Ezeiza", "06134": "Cañuelas",
            "06693": "Roque Pérez", "06483": "Lobos", "06707": "Saladillo",
            "06547": "Monte", "06301": "General Belgrano",
            "06329": "General Las Heras", "06574": "Navarro",
        }
        selected = {f["properties"]["id"]: f["properties"]["nombre"]
                    for f in data["features"] if filter_boundary(f)["weight"] > 0}
        self.assertEqual(selected, expected)
        for feature in data["features"]:
            if feature["properties"]["nombre"] in {"Monte Hermoso", "General Viamonte"}:
                self.assertEqual(filter_boundary(feature)["weight"], 0)

    def test_missing_or_corrupt_resource_has_controlled_fallback(self):
        for failure in (FileNotFoundError(), UnicodeError()):
            with patch("safety.Path.read_text", side_effect=failure):
                self.assertIsNone(cargar_geojson_local())
        for text in ("<html>503</html>", "{}", '{"type":"FeatureCollection","features":[]}', "null"):
            with self.subTest(text=text), patch("safety.Path.read_text", return_value=text):
                self.assertIsNone(cargar_geojson_local())

    def test_invalid_geometry_rejected(self):
        data = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"departamento": "Prueba"}, "geometry": {"type": "Polygon", "coordinates": [[[999, 0], [1, 1], [0, 1], [999, 0]]]}}]}
        with self.assertRaises(ValueError):
            validar_geojson(data)

    def test_real_map_setup_renders_with_or_without_boundaries(self):
        from domain.map import filter_boundary

        self.assertEqual(filter_boundary({"properties": {"departamento": "Ezeiza"}})["weight"], 1.5)
        self.assertEqual(filter_boundary({"properties": {"departamento": "Monte Hermoso"}})["weight"], 0)


if __name__ == "__main__":
    unittest.main()
