"""Behavioral regressions, using real Streamlit reruns against offline fixtures."""
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

from offline_app import tables


def widget(elements, label):
    return next(element for element in elements if element.label == label)


class ScreenTests(unittest.TestCase):
    def app(self, menu="🧮 Calculadoras", populated=False, role="Admin", frames=None):
        app = AppTest.from_string("from offline_app import run\nrun()", default_timeout=20)
        app.session_state["usuario_rol"] = role
        app.session_state["menu_seleccionado"] = menu
        app.session_state["_test_tables"] = frames if frames is not None else tables(populated)
        return app.run()

    def clean(self, app):
        self.assertEqual([e.message for e in app.exception], [])

    def ieric(self):
        app = self.app()
        widget(app.button, "💰 Cese Laboral\n(IERIC)").click().run()
        widget(app.text_input, "Nombre del Compañero (Para Registro/Reclamo):").set_value("Persona A")
        app.selectbox(key="ieric_e").set_value("Empresa A").run()
        widget(app.number_input, "Sueldo Bruto Quincenal ($):").set_value(10000)
        widget(app.button, "➕ Agregar Quincena").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["quincenas"][0]["Aporte Nominal"], 1200)
        return app

    def test_ieric_identity_change_discards_amounts_and_form(self):
        for label, new_value in [("Nombre del Compañero (Para Registro/Reclamo):", "Persona B"), ("Empresa:", "Empresa B")]:
            with self.subTest(identity=label):
                app = self.ieric()
                elements = app.text_input if label.startswith("Nombre") else app.selectbox
                widget(elements, label).set_value(new_value).run()
                self.clean(app)
                self.assertEqual(app.session_state["quincenas"], [])
                self.assertEqual(widget(app.number_input, "Sueldo Bruto Quincenal ($):").value, 0)
                self.assertFalse(any(b.key == "btn_ieric" for b in app.button))
                widget(app.number_input, "Sueldo Bruto Quincenal ($):").set_value(20000)
                widget(app.button, "➕ Agregar Quincena").click().run()
                widget(app.text_input, "Motivo del Reclamo (Ej: Falta de pago libretas):").set_value("Falta de pago")
                app.button(key="btn_ieric").click().run()
                self.clean(app)
                name, saved = app.session_state["_test_writes"][-1]
                self.assertEqual(name, "Reclamos")
                self.assertEqual(saved.iloc[-1]["Nombre"], "Persona B" if label.startswith("Nombre") else "Persona A")
                self.assertEqual(saved.iloc[-1]["Empresa"], "Empresa A" if label.startswith("Nombre") else "Empresa B")
                self.assertIn("2,400.00", saved.iloc[-1]["Motivo"])

    def test_ieric_back_and_rerun_never_reassign_old_amounts(self):
        app = self.ieric().run()
        self.assertEqual(len(app.session_state["quincenas"]), 1)
        widget(app.button, "⬅️ Volver al Panel").click().run()
        widget(app.button, "💰 Cese Laboral\n(IERIC)").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["quincenas"], [])
        self.assertFalse(any(b.key == "btn_ieric" for b in app.button))

    def test_calendar_receives_closings_through_bootstrap(self):
        for populated in (False, True):
            with self.subTest(populated=populated):
                app = self.app(populated=populated)
                button = next(b for b in app.button if "Calendario" in b.label)
                button.click().run()
                self.clean(app)
                if populated:
                    # AppTest reruns the full script for dialog widgets; reopen it.
                    widget(app.selectbox, "Seleccione la empresa registrada para ver su cronograma:").set_value("Empresa A")
                    next(b for b in app.button if "Calendario" in b.label).click().run()
                    self.clean(app)
                    self.assertTrue(any("1 al 15" in m.value for m in app.markdown))

    def test_literal_searches_do_not_raise_regex_errors(self):
        for menu, key in [("📋 Nóminas", "b_obras"), ("📋 Nóminas", "b_del"), ("📋 Nóminas", "b_con"), ("🤝 Convenios y Documentación", "b_conv")]:
            with self.subTest(key=key):
                app = self.app(menu, populated=True)
                app.text_input(key=key).set_value("[").run()
                self.clean(app)

    def test_observation_delete_targets_displayed_company(self):
        frames = tables(True)
        frames["Observaciones_Empresas"] = pd.DataFrame([
            {"Fecha": "01/09/2026 12:00", "Empresa": company, "Observacion": "Mismo texto", "Usuario": "Admin"}
            for company in ("Empresa A", "Empresa B")])
        app = self.app("📝 Observaciones por Empresa", frames=frames)
        widget(app.selectbox, "🏢 Filtrar por Empresa:").set_value("Empresa B").run()
        next(b for b in app.button if b.label.startswith("🗑️ Eliminar Nota")).click().run()
        self.clean(app)
        name, saved = app.session_state["_test_writes"][-1]
        self.assertEqual(name, "Observaciones_Empresas")
        self.assertEqual(saved["Empresa"].tolist(), ["Empresa A"])

    def test_abm_simultaneous_delete_tabs_have_unique_buttons(self):
        app = self.app("📥 Carga de Datos (ABM)", populated=True)
        widget(app.radio, "Acción Obras:").set_value("🗑️ Eliminar Obra")
        widget(app.radio, "Acción Delegados:").set_value("🗑️ Eliminar")
        widget(app.radio, "Acción Contactos:").set_value("🗑️ Eliminar").run()
        self.clean(app)

    def test_abm_edits_preserve_column_mapping_and_optional_data(self):
        cases = [("Predios", "Acción Predio:", "✏️ Modificar", "f_e_predio"),
                 ("Obras", "Acción Obras:", "✏️ Modificar Obra", "f_e_obra"),
                 ("Delegados", "Acción Delegados:", "✏️ Modificar", "f_e_del"),
                 ("Contactos", "Acción Contactos:", "✏️ Modificar", "f_e_con")]
        for sheet, label, action, form in cases:
            for extra in (False, True):
                with self.subTest(sheet=sheet, optional_column=extra):
                    frames = tables(True)
                    original = frames[sheet].copy()
                    if extra:
                        original["Extra"] = "Conservar"
                    if sheet == "Delegados":
                        original["CUIL"] = original["CUIL"].astype(str)
                    frames[sheet] = original[original.columns[::-1]].copy()
                    expected = frames[sheet].copy(deep=True)
                    app = self.app("📥 Carga de Datos (ABM)", frames=frames)
                    widget(app.radio, label).set_value(action).run()
                    widget(app.button, "🔄 Actualizar").click().run()
                    self.clean(app)
                    name, saved = app.session_state["_test_writes"][-1]
                    self.assertEqual(name, sheet)
                    pd.testing.assert_frame_equal(saved, expected, check_dtype=False)

    def test_contact_edit_draft_does_not_follow_another_person(self):
        frames = tables(True)
        frames["Contactos"] = pd.DataFrame([
            {"Nombre": name, "Empresa": "Empresa A", "Cargo": "Original", "Observaciones": ""}
            for name in ("Persona A", "Persona B")])
        app = self.app("📥 Carga de Datos (ABM)", frames=frames)
        widget(app.radio, "Acción Contactos:").set_value("✏️ Modificar").run()
        widget(app.text_input, "Cargo:").set_value("Borrador de A").run()
        widget(app.selectbox, "Modificar:").set_value("Persona B (Empresa A)").run()
        self.clean(app)
        self.assertEqual(widget(app.text_input, "Cargo:").value, "Original")

    def test_all_screens_empty_and_populated_for_both_roles(self):
        menus = ["🗺️ Mapa Territorial", "📥 Carga de Datos (ABM)", "📋 Nóminas", "🧮 Calculadoras",
                 "⚠️ Reclamos", "💜 UOCRA Mujeres", "🤝 Convenios y Documentación", "📊 Estadísticas",
                 "📸 Galería Multimedia", "🤖 Chat GPT UOCRA", "🧹 Auditoría", "📝 Observaciones por Empresa"]
        for populated in (False, True):
            for role in ("Admin", "Restringido"):
                app = self.app(populated=populated, role=role)
                for menu in menus:
                    with self.subTest(populated=populated, role=role, screen=menu):
                        app.session_state["menu_seleccionado"] = menu
                        app.run()
                        self.clean(app)
                        denied = role == "Restringido" and menu in {"📥 Carga de Datos (ABM)", "⚠️ Reclamos"}
                        if denied:
                            self.assertTrue(any("Acceso no autorizado" in e.value for e in app.error))
                        else:
                            self.assertTrue(any(b.label == "📤 Enviar Propuesta al Repositorio" for b in app.button))
                self.assertNotIn("_test_writes", app.session_state)

    def test_login_logout_clears_operational_state_and_role(self):
        for password, role in [("test-admin", "Admin"), ("test-restricted", "Restringido")]:
            with self.subTest(role=role):
                app = self.app(role=None)
                widget(app.text_input, "Contraseña:").set_value("incorrecta")
                widget(app.button, "Ingresar al Sistema Operativo").click().run()
                self.assertIsNone(app.session_state["usuario_rol"])
                widget(app.text_input, "Contraseña:").set_value(password)
                widget(app.button, "Ingresar al Sistema Operativo").click().run()
                self.clean(app)
                self.assertEqual(app.session_state["usuario_rol"], role)
                for key in ("quincenas", "recibo_txt", "chat_session", "_versiones_hojas", "ieric_identidad"):
                    app.session_state[key] = "stale"
                widget(app.button, "🚪 Cerrar Sesión").click().run()
                self.clean(app)
                self.assertIsNone(app.session_state["usuario_rol"])
                for key in ("quincenas", "recibo_txt", "chat_session", "_versiones_hojas", "ieric_identidad", "menu_seleccionado"):
                    self.assertNotIn(key, app.session_state)

    def test_quincena_manual_and_automatic_preserve_calculated_identity(self):
        import datetime
        for automatic in (False, True):
            with self.subTest(automatic=automatic):
                app = self.app()
                widget(app.button, "🧾 Liquidación\nQuincena").click().run()
                if not automatic:
                    widget(app.radio, "⚙️ Seleccione el método de carga:").set_value("✍️ Carga Manual (Clásica)").run()
                    widget(app.number_input, "Hs Normales:").set_value(8)
                else:
                    widget(app.date_input, "Día de Inicio de Quincena").set_value(datetime.date(2026, 9, 7))
                    widget(app.date_input, "Día de Fin de Quincena").set_value(datetime.date(2026, 9, 7))
                    widget(app.time_input, "Salida L-V").set_value(datetime.time(16)).run()
                widget(app.text_input, "Nombre del Compañero:").set_value("Persona A")
                widget(app.number_input, "Valor Hora ($):").set_value(100)
                widget(app.button, "▶ Generar Recibo Teórico").click().run()
                self.clean(app)
                self.assertIn("NETO A COBRAR: $ 772.80", app.session_state["recibo_txt"])
                widget(app.text_input, "Nombre del Compañero:").set_value("Persona B").run()
                widget(app.text_input, "Motivo de la Diferencia/Reclamo:").set_value("Diferencia")
                app.button(key="btn_recibo").click().run()
                self.clean(app)
                self.assertEqual(app.session_state["_test_writes"][-1][1].iloc[-1]["Nombre"], "Persona A")

    def test_other_calculators_and_paritaria_save(self):
        app = self.app()
        for label in ("🏖️ Cálculo\nVacaciones", "🎄 Aguinaldo\n(SAC)"):
            widget(app.button, label).click().run()
            self.clean(app)
            self.assertTrue(any("Próximamente" in i.value for i in app.info))
            widget(app.button, "⬅️ Volver al Panel").click().run()
        widget(app.button, "📈 Gestión Histórica de Paritarias (Exclusivo Admin)").click().run()
        widget(app.text_input, "Período de Vigencia (Ej: '1° Quincena Abril 2026'):*").set_value("Prueba local")
        widget(app.number_input, "Ayudante $").set_value(6000)
        widget(app.button, "💾 Guardar Nueva Escala").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["_test_writes"][-1][0], "Paritarias_Historia")
        self.assertEqual(app.session_state["_test_writes"][-1][1].iloc[-1]["Ayudante"], 6000)
        self.assertEqual(app.dataframe[0].value.iloc[0]["Ayudante"], "$ 6,000.00")
        restricted = self.app(role="Restringido")
        restricted.session_state["calc_activa"] = "Paritarias"
        restricted.run()
        self.clean(restricted)
        self.assertFalse(any("Guardar Nueva Escala" in b.label for b in restricted.button))

    def test_proposals_and_assistant_use_local_boundaries(self):
        app = self.app("🤖 Chat GPT UOCRA", populated=True)
        app.chat_input[0].set_value("Obra empresa A y delegado persona A").run()
        self.clean(app)
        self.assertEqual(app.session_state["mensajes_ui"][-1]["contenido"], "Respuesta local simulada")
        widget(app.text_area, "Describa su propuesta o reporte:").set_value("Propuesta ficticia")
        widget(app.button, "📤 Enviar Propuesta al Repositorio").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["_test_writes"][-1][0], "Propuestas")

    def test_ieric_failed_save_never_reports_success(self):
        app = self.ieric()
        app.session_state["_test_fail_save"] = True
        widget(app.text_input, "Motivo del Reclamo (Ej: Falta de pago libretas):").set_value("Diferencia")
        app.button(key="btn_ieric").click().run()
        self.clean(app)
        self.assertFalse(any("Reclamo enviado" in s.value for s in app.success))

    def test_document_and_observation_search_are_literal(self):
        app = self.app("🤝 Convenios y Documentación", populated=True)
        widget(app.radio, "Seleccione el apartado a gestionar:").set_value("2️⃣ Documentación").run()
        app.text_input(key="buscador_docs_unico").set_value("[A]").run()
        self.clean(app)
        self.assertTrue(any("Acta [A]" in m.value for m in app.markdown))
        app = self.app("📝 Observaciones por Empresa", populated=True)
        widget(app.text_input, "🔤 Buscar por palabra clave:").set_value("[A]").run()
        self.clean(app)
        self.assertTrue(any("Nota [A]" in m.value for m in app.markdown))

    def test_pending_ieric_claim_cannot_submit_after_identity_changes(self):
        app = self.ieric()
        widget(app.text_input, "Motivo del Reclamo (Ej: Falta de pago libretas):").set_value("Diferencia").run()
        widget(app.text_input, "Nombre del Compañero (Para Registro/Reclamo):").set_value("Persona B")
        app.button(key="btn_ieric").click().run()
        self.clean(app)
        self.assertNotIn("_test_writes", app.session_state)
        self.assertEqual(app.session_state["quincenas"], [])

    def test_ieric_removing_last_quincena_removes_claim_action(self):
        app = self.ieric()
        widget(app.button, "🗑️ Borrar Última Quincena").click().run()
        self.clean(app)
        self.assertEqual(app.session_state["quincenas"], [])
        self.assertFalse(any(b.key == "btn_ieric" for b in app.button))

    def test_cupo_and_convenio_drafts_reset_when_entity_changes(self):
        frames = tables(True)
        second = frames["Obras"].iloc[0].to_dict()
        second.update(Obra_ID=2, Empresa="Empresa B")
        frames["Obras"] = pd.concat([frames["Obras"], pd.DataFrame([second])], ignore_index=True)
        app = self.app("💜 UOCRA Mujeres", frames=frames)
        widget(app.number_input, "Modificar Cantidad de Mujeres (Cupo):").set_value(7).run()
        widget(app.selectbox, "Seleccione la Obra activa:").set_value("Polo A (Empresa B)").run()
        self.clean(app)
        self.assertEqual(widget(app.number_input, "Modificar Cantidad de Mujeres (Cupo):").value, 2)
        second = frames["Convenios"].iloc[0].to_dict()
        second["Empresa"] = "Empresa B"
        frames["Convenios"] = pd.concat([frames["Convenios"], pd.DataFrame([second])], ignore_index=True)
        app = self.app("🤝 Convenios y Documentación", frames=frames)
        widget(app.radio, "Acción:").set_value("✏️ Modificar").run()
        widget(app.text_input, "Monto Extra $:").set_value("1234").run()
        widget(app.selectbox, "Seleccione el Convenio:").set_value("Empresa B - ").run()
        self.clean(app)
        self.assertEqual(widget(app.text_input, "Monto Extra $:").value, "")


class StorageTests(unittest.TestCase):
    def test_runtime_upload_does_not_replace_an_existing_document(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock, patch
        import streamlit as st
        from services.runtime import build

        fake_st = SimpleNamespace(cache_data=lambda **kw: lambda fn: fn,
                                  dialog=lambda *a, **kw: lambda fn: fn)
        uploaded = {}
        preconditions = []

        def blob(name):
            def upload(data, **kwargs):
                preconditions.append(kwargs.get("if_generation_match"))
                if name in uploaded and kwargs.get("if_generation_match") == 0:
                    raise RuntimeError("Precondition failed")
                uploaded[name] = data
            return SimpleNamespace(upload_from_string=upload, public_url="https://storage.test/" + name)

        bucket = SimpleNamespace(blob=blob)
        client = MagicMock()
        client.bucket.return_value = bucket
        with patch.object(st, "secrets", {"gcp_service_account": '{"project_id":"offline-test"}'}), \
             patch("google.oauth2.service_account.Credentials.from_service_account_info"), \
             patch("google.cloud.storage.Client", return_value=client), \
             patch.object(st, "error"):
            upload = build(fake_st, pd.DataFrame())["subir_archivo_drive"]
            first = upload(SimpleNamespace(getvalue=lambda: b"first", type="application/pdf"), "Doc_Acta.pdf")
            second = upload(SimpleNamespace(getvalue=lambda: b"second", type="application/pdf"), "Doc_Acta.pdf")
            with patch("services.storage.uuid.uuid4", return_value=SimpleNamespace(hex="fixed")):
                protected = upload(SimpleNamespace(getvalue=lambda: b"protected", type="application/pdf"), "Doc_Acta.pdf")
                collision = upload(SimpleNamespace(getvalue=lambda: b"replacement", type="application/pdf"), "Doc_Acta.pdf")
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertNotEqual(first, second)
        self.assertIsNotNone(protected)
        self.assertIsNone(collision)
        self.assertEqual(sorted(uploaded.values()), [b"first", b"protected", b"second"])
        self.assertEqual(preconditions, [0, 0, 0, 0])

    def test_physical_names_preserve_basename_and_extension(self):
        from services.storage import unique_object_name
        from pathlib import PurePosixPath
        for name, basename in [("Doc_Acta.pdf", "Doc_Acta.pdf"), ("../Acta.pdf", "Acta.pdf"),
                               ("carpeta\\foto.png", "foto.png"), ("Media_Asamblea_1.mp4", "Media_Asamblea_1.mp4")]:
            with self.subTest(name=name):
                first, second = unique_object_name(name), unique_object_name(name)
                self.assertNotEqual(first, second)
                self.assertEqual(PurePosixPath(first).name, basename)
                self.assertEqual(len(PurePosixPath(first).parts), 2)
        for invalid in ("", ".", "..", "/"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                unique_object_name(invalid)


if __name__ == "__main__":
    unittest.main()
