"""Pruebas del wizard de Carga Simplificada sin servicios externos."""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
from streamlit.testing.v1 import AppTest

from offline_app import tables


def button(app, label):
    return next(item for item in app.button if item.label == label)


class SimpleLoadDomainTests(unittest.TestCase):
    def test_location_replacement_and_google_maps_url(self):
        from domain.simple_load import google_maps_url, normalize_location

        searched = normalize_location(-34.81, -58.48, "Búsqueda", "Monte Grande")
        marked = normalize_location(-34.82, -58.47, "Mapa")
        self.assertNotEqual(searched, marked)
        self.assertEqual(marked["source"], "Mapa")
        self.assertEqual(
            google_maps_url(marked["latitud"], marked["longitud"]),
            "https://www.google.com/maps/search/?api=1&query=-34.820000%2C-58.470000",
        )
        with self.assertRaises(ValueError):
            normalize_location(91, 0, "Mapa")

    def test_records_reuse_current_columns_and_id_rule(self):
        from domain.simple_load import obra_record, pending_record, predio_record

        obras = pd.DataFrame({"Obra_ID": [2, "8"], "Predio": ["A", "B"]})
        location = {"latitud": -34.8, "longitud": -58.5}
        obra = obra_record(
            {"predio": "Polo A", "empresa": "➕ Nueva...", "empresa_nueva": "Empresa nueva", "delegados": ["D1"],
             "obreros": 4, "estado": "Activa", "jurisdiccion": "Ezeiza", "jurisdiccion_r": True},
            location,
            9,
        )
        self.assertEqual(obra["Obra_ID"], 9)
        self.assertEqual(obra["Empresa"], "Empresa nueva")
        self.assertEqual(obra["Jurisdiccion_R"], "SI")
        self.assertEqual(obra["Mujeres"], 0)
        predio = predio_record({"nombre": "Polo A", "radio_km": 1.5, "observaciones": ""}, location)
        self.assertEqual(predio["Radio_KM"], 1.5)
        self.assertEqual(pending_record("obra", {"predio": "Polo A"}, location, obras)["Obra_ID"], 9)

    def test_validation_and_clear_do_not_touch_other_state(self):
        from domain.simple_load import clear_simple_state, validate_draft

        self.assertEqual(validate_draft("obra", {}, None), ["Seleccione una ubicación antes de revisar."])
        session = {"usuario_rol": "Admin", "menu_seleccionado": "mapa", "simple_draft": {"nombre": "A"},
                   "simple_form_predio_nombre": "A", "simple_app_mode": "simple"}
        clear_simple_state(session)
        self.assertEqual(session, {"usuario_rol": "Admin", "menu_seleccionado": "mapa", "simple_form_predio_nombre": "A", "simple_app_mode": "simple"})
        clear_simple_state(session, keep_mode=False)
        self.assertEqual(session, {"usuario_rol": "Admin", "menu_seleccionado": "mapa", "simple_form_predio_nombre": "A"})

    def test_geocoder_is_manual_bounded_and_credential_free(self):
        from services.geocoding import NOMINATIM_HEADERS, NOMINATIM_URL, search_places

        request_get = Mock(return_value=SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: [{"display_name": "Monte Grande, Argentina", "lat": "-34.82", "lon": "-58.47"}],
        ))
        self.assertEqual(search_places("   ", request_get), [])
        request_get.assert_not_called()
        results = search_places("Monte Grande", request_get)
        self.assertEqual(results[0]["latitud"], -34.82)
        request_get.assert_called_once_with(
            NOMINATIM_URL,
            params={"q": "Monte Grande", "format": "jsonv2", "limit": 5, "countrycodes": "ar", "addressdetails": 1},
            headers=NOMINATIM_HEADERS,
            timeout=8,
        )


class SimplifiedAppTests(unittest.TestCase):
    def app(self, *, mode="simple", role="Admin", populated=True, frames=None):
        app = AppTest.from_string("from offline_app import run\nrun()", default_timeout=20)
        app.session_state["usuario_rol"] = role
        if mode is not None:
            app.session_state["simple_app_mode"] = mode
        app.session_state["_test_tables"] = frames if frames is not None else tables(populated)
        return app.run()

    def clean(self, app):
        self.assertEqual([error.message for error in app.exception], [])

    def set_review(self, app, kind, pending, draft=None):
        app.session_state["simple_kind"] = kind
        app.session_state["simple_step"] = "review"
        app.session_state["simple_pending"] = pending
        app.session_state["simple_draft"] = draft or {"kept": True}
        app.session_state["simple_location"] = {"latitud": pending["Latitud"], "longitud": pending["Longitud"], "source": "Mapa"}
        return app.run()

    def test_mode_selection_complete_and_simplified(self):
        app = self.app(mode=None, populated=False)
        self.clean(app)
        button(app, "Abrir App Completa").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["simple_app_mode"], "complete")
        self.assertTrue(any(item.label == "🧮 Calculadoras" for item in app.button))

        app = self.app(mode=None, populated=False)
        button(app, "Abrir Carga Simplificada").click().run()
        self.clean(app)
        self.assertTrue(any(item.label == "Cargar nueva obra" for item in app.button))

    def test_restricted_keeps_existing_abm_permission(self):
        app = self.app(role="Restringido")
        self.clean(app)
        self.assertTrue(any("requiere perfil Admin" in item.value for item in app.error))
        self.assertFalse(any(item.label == "Cargar nueva obra" for item in app.button))

    def test_wizard_navigation_empty_tables_and_draft_isolation(self):
        app = self.app(populated=False)
        button(app, "Cargar nuevo polo").click().run()
        self.clean(app)
        self.assertTrue(any(item.label == "Continuar a ubicación" for item in app.button))
        button(app, "Continuar a ubicación").click().run()
        self.assertTrue(any("obligatorio" in item.value for item in app.error))
        app.text_input(key="simple_form_predio_nombre").set_value("Polo móvil")
        button(app, "Continuar a ubicación").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["simple_step"], "location")
        self.assertEqual(app.session_state["simple_draft"]["nombre"], "Polo móvil")
        # La salida limpia el borrador explícito; los widgets ocultos se
        # descartan en el rerun siguiente según la semántica de Streamlit.
        from domain.simple_load import clear_simple_state
        clear_simple_state(app.session_state)
        self.assertNotIn("simple_draft", app.session_state)
        self.assertNotIn("simple_location", app.session_state)

    def test_new_obra_without_predio_continues_to_location(self):
        app = self.app(populated=True)
        button(app, "Cargar nueva obra").click().run()
        button(app, "Continuar a ubicación").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["simple_step"], "location")
        self.assertEqual(app.session_state["simple_draft"]["predio"], "")

    def test_complete_abm_saves_obra_without_predio(self):
        app = self.app(mode="complete", populated=True)
        app.session_state["menu_seleccionado"] = "📥 Carga de Datos (ABM)"
        app.run()
        next(item for item in app.radio if item.label == "Acción Obras:").set_value("➕ Nueva Obra").run()
        next(item for item in app.selectbox if item.label == "Empresa:").set_value("Empresa A")
        button(app, "💾 Guardar").click().run()
        self.clean(app)
        table, saved = app.session_state["_test_writes"][-1]
        self.assertEqual(table, "Obras")
        self.assertEqual(saved.iloc[-1]["Predio"], "")
        self.assertEqual(saved.iloc[-1]["Empresa"], "Empresa A")

    def test_change_load_discards_review_draft(self):
        app = self.app(populated=True)
        pending = {"Nombre": "Polo a descartar", "Latitud": -34.82, "Longitud": -58.47,
                   "Radio_KM": 1.0, "Observaciones": ""}
        app = self.set_review(app, "predio", pending, {"nombre": "Polo a descartar"})
        button(app, "Cambiar carga").click().run()
        self.clean(app)
        self.assertNotIn("simple_draft", app.session_state)
        self.assertNotIn("simple_pending", app.session_state)
        self.assertTrue(any(item.label == "Cargar nueva obra" for item in app.button))

    def test_save_success_clears_only_simplified_draft_and_cannot_double_write(self):
        app = self.app(populated=True)
        pending = {"Nombre": "Polo guardado", "Latitud": -34.82, "Longitud": -58.47, "Radio_KM": 1.0, "Observaciones": ""}
        app = self.set_review(app, "predio", pending)
        button(app, "Confirmar y guardar").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["simple_step"], "success")
        self.assertNotIn("simple_draft", app.session_state)
        self.assertEqual(len(app.session_state["_test_writes"]), 1)
        self.assertEqual(app.session_state["_test_writes"][0][0], "Predios")
        self.assertEqual(app.session_state["_test_writes"][0][1].iloc[-1]["Nombre"], "Polo guardado")
        self.assertNotIn("simple_save_locked", app.session_state)

    def test_failed_save_keeps_exact_pending_draft(self):
        app = self.app(populated=True)
        pending = {"Nombre": "Polo pendiente", "Latitud": -34.82, "Longitud": -58.47, "Radio_KM": 1.0, "Observaciones": ""}
        app = self.set_review(app, "predio", pending, {"nombre": "Polo pendiente"})
        app.session_state["_test_fail_save"] = True
        button(app, "Confirmar y guardar").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["simple_pending"], pending)
        self.assertEqual(app.session_state["simple_draft"], {"nombre": "Polo pendiente"})
        self.assertFalse(app.session_state["simple_save_locked"])
        self.assertTrue(any("borrador se conserva" in item.value for item in app.warning))

    def test_new_obra_uses_guarded_save_boundary(self):
        app = self.app(populated=True)
        pending = {"Obra_ID": 2, "Predio": "Polo A", "Empresa": "Empresa B", "Delegado": "", "Obreros": 2,
                   "Estado": "Activa", "Latitud": -34.82, "Longitud": -58.47, "Jurisdiccion": "Ezeiza",
                   "Jurisdiccion_R": "", "Mujeres": 0}
        app = self.set_review(app, "obra", pending)
        button(app, "Confirmar y guardar").click().run()
        self.clean(app)
        sheet, saved = app.session_state["_test_writes"][0]
        self.assertEqual(sheet, "Obras")
        self.assertEqual(saved.iloc[-1].to_dict(), pending)

    def test_simplified_screen_is_single_column_and_has_no_direct_sheet_write(self):
        source = Path("screens/simplified.py").read_text(encoding="utf-8")
        self.assertNotIn("append_row", source)
        self.assertNotIn(".worksheet(", source)
        self.assertNotIn("st.dataframe", source)
        self.assertNotIn("st.columns", source)
        self.assertIn("ctx.guardar_db", source)

    def test_gps_component_uses_explicit_browser_consent(self):
        source = Path("ui/geolocation.py").read_text(encoding="utf-8")
        self.assertIn("navigator.geolocation.getCurrentPosition", source)
        self.assertIn("Usar ubicación actual", source)
        self.assertIn("setTriggerValue('location'", source)


if __name__ == "__main__":
    unittest.main()
