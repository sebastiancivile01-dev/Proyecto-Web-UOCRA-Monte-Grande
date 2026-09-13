import importlib
import unittest
from datetime import datetime


class Phase2StructureTests(unittest.TestCase):
    def test_authentication_and_logout(self):
        from auth.login import authenticate
        from auth.session import clear_session

        self.assertEqual(authenticate("admin", "admin", "restricted"), "Admin")
        self.assertEqual(authenticate("restricted", "admin", "restricted"), "Restringido")
        self.assertIsNone(authenticate("bad", "admin", "restricted"))
        session = {"usuario_rol": "Admin", "temporary": 1}
        clear_session(session)
        self.assertEqual(session, {"usuario_rol": None})

    def test_authorization_is_role_based(self):
        from auth.authorization import is_allowed

        self.assertTrue(is_allowed("Admin", "any-module"))
        self.assertFalse(is_allowed(None, "any-module"))
        self.assertFalse(is_allowed("Restringido", "admin-only", {"admin-only"}))
        self.assertTrue(is_allowed("Restringido", "mapa", {"admin-only"}))

    def test_sheet_boundary_and_snapshot_state(self):
        from data.sheets import load_table, save_table
        from data.snapshots import forget_sheet, remember_sheet

        calls = []
        read = lambda worksheet, columns: calls.append((worksheet, columns)) or ("frame", "v1")
        write = lambda worksheet, frame, version: calls.append((worksheet, frame, version))
        self.assertEqual(load_table(read, "Obras", ("Obra_ID",)), ("frame", "v1"))
        save_table(write, "Obras", "frame", "v1")
        self.assertEqual(calls, [("Obras", ["Obra_ID"]), ("Obras", "frame", "v1")])

        session = {}
        remember_sheet(session, "Obras", "v1", ("doc", "Obras"))
        forget_sheet(session, "Obras")
        self.assertEqual(session, {"_versiones_hojas": {}, "_claves_cache_hojas": {}})

    def test_services_are_pure_at_import_and_boundary(self):
        from services.bcra import cer_for_date
        from services.calendar import normalize_holidays
        from services.logs import audit

        items = [{"d": "2026-01-01", "v": "100"}, {"d": "2026-02-01", "v": "110"}]
        self.assertEqual(cer_for_date(items, "2026-01-15"), 100.0)
        self.assertIsNone(cer_for_date([], None))
        self.assertEqual(normalize_holidays([{"motivo": "A", "dia": 1, "mes": 1}])[0]["tipo"], "Feriado Nacional")
        rows = []
        audit(rows.append, "Admin", "test", datetime(2026, 1, 2, 3, 4, 5))
        self.assertEqual(rows, [["02/01/2026", "03:04:05", "Admin", "test"]])

    def test_domain_transformations_and_router(self):
        import pandas as pd
        from domain.tables import numeric_columns
        from screens.router import dispatch

        frame = numeric_columns(pd.DataFrame({"Obreros": ["3", None], "Nombre": ["A", "B"]}), ["Obreros"])
        self.assertEqual(frame["Obreros"].tolist(), [3.0, 0.0])
        self.assertEqual(dispatch("mapa", {"mapa": lambda: "ok"}), "ok")

    def test_safe_imports_do_not_start_runtime(self):
        modules = [
            "app", "bootstrap", "auth", "auth.login", "auth.session",
            "auth.authorization", "data", "data.sheets", "data.snapshots",
            "services", "services.bcra", "services.calendar", "services.logs",
            "services.storage", "domain", "domain.tables", "screens", "screens.router",
        ]
        for module in modules:
            with self.subTest(module=module):
                self.assertIsNotNone(importlib.import_module(module))


if __name__ == "__main__":
    unittest.main()
