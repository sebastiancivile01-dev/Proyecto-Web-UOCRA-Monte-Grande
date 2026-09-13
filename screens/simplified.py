"""Wizard mobile-first para altas rápidas, sobre los contratos existentes."""

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from domain.simple_load import (
    DEFAULT_LOCATION,
    clear_simple_state,
    google_maps_url,
    normalize_location,
    pending_record,
    validate_draft,
)
from services.geocoding import search_places
from ui.geolocation import current_location


KIND_LABELS = {"obra": "Nueva Obra", "predio": "Nuevo Polo / Predio"}


def _set_step(step: str) -> None:
    st.session_state.simple_step = step


def _start(kind: str) -> None:
    clear_simple_state(st.session_state)
    st.session_state.simple_kind = kind
    st.session_state.simple_step = "form"


def _back_to_types() -> None:
    clear_simple_state(st.session_state)


def _back_to_mode() -> None:
    clear_simple_state(st.session_state, keep_mode=False)


def _to_complete() -> None:
    clear_simple_state(st.session_state)
    st.session_state.simple_app_mode = "complete"


def _use_location(latitud, longitud, source: str, label: str = "") -> None:
    st.session_state.simple_location = normalize_location(latitud, longitud, source, label)
    if "simple_map_candidate" in st.session_state:
        del st.session_state["simple_map_candidate"]


def _render_header() -> None:
    st.button("Cambiar carga", key="simple_back_types", width="stretch", on_click=_back_to_types)
    st.button("Cambiar modo", key="simple_back_mode", width="stretch", on_click=_back_to_mode)
    st.button("Ir a App Completa", key="simple_to_complete", width="stretch", on_click=_to_complete)


def _render_type_selection() -> None:
    st.title("Carga Simplificada")
    st.write("¿Qué desea cargar?")
    with st.container(border=True):
        st.subheader("Nueva Obra")
        st.caption("Alta rápida usando los campos vigentes de Obras.")
        st.button("Cargar nueva obra", key="simple_choose_obra", type="primary", width="stretch", on_click=_start, args=("obra",))
    with st.container(border=True):
        st.subheader("Nuevo Polo / Predio")
        st.caption("Alta rápida usando los campos vigentes de Predios.")
        st.button("Cargar nuevo polo", key="simple_choose_predio", width="stretch", on_click=_start, args=("predio",))
    with st.expander("Próximamente"):
        st.write("Delegado, Reclamo, Observación y Documento se incorporarán en otra etapa.")
    st.button("Volver a selección de modo", key="simple_select_mode", on_click=_back_to_mode)


def _render_form(ctx, kind: str) -> None:
    draft = st.session_state.setdefault("simple_draft", {})
    st.title(KIND_LABELS[kind])
    st.caption("Paso 1 de 3 · Complete los datos principales.")

    if kind == "obra":
        with st.form("simple_form_obra"):
            predio = st.selectbox("Polo / Predio (opcional)", [""] + ctx.lista_predios_historicos, key="simple_form_obra_predio")
            empresa = st.selectbox("Empresa", ["➕ Nueva..."] + ctx.lista_empresas_historicas, key="simple_form_obra_empresa")
            empresa_nueva = st.text_input("Nueva empresa", key="simple_form_obra_empresa_nueva") if empresa == "➕ Nueva..." else ""
            delegados = st.multiselect("Delegado/s", ctx.lista_delegados_nombres, key="simple_form_obra_delegados")
            jurisdiccion = st.selectbox("Jurisdicción", ctx.lista_jurisdicciones, key="simple_form_obra_jurisdiccion")
            obreros = st.number_input("Obreros", min_value=0, step=1, key="simple_form_obra_obreros")
            estado = st.selectbox("Estado", ctx.lista_estados, key="simple_form_obra_estado")
            jurisdiccion_r = st.checkbox("Marca especial: Jurisdicción R", key="simple_form_obra_jurisdiccion_r")
            submitted = st.form_submit_button("Continuar a ubicación", type="primary", width="stretch")
        if submitted:
            next_draft = {
                "predio": predio,
                "empresa": empresa,
                "empresa_nueva": empresa_nueva,
                "delegados": delegados,
                "jurisdiccion": jurisdiccion,
                "obreros": int(obreros),
                "estado": estado,
                "jurisdiccion_r": jurisdiccion_r,
            }
            errors = validate_draft(kind, next_draft, {"latitud": 0, "longitud": 0})
            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.session_state.simple_draft = next_draft
                _set_step("location")
                st.rerun()
    else:
        with st.form("simple_form_predio"):
            nombre = st.text_input("Nombre del Polo / Predio", key="simple_form_predio_nombre")
            radio_km = st.number_input("Radio de influencia (KM)", min_value=0.1, step=0.1, value=1.0, key="simple_form_predio_radio")
            observaciones = st.text_area("Observaciones", key="simple_form_predio_observaciones")
            submitted = st.form_submit_button("Continuar a ubicación", type="primary", width="stretch")
        if submitted:
            next_draft = {"nombre": nombre, "radio_km": radio_km, "observaciones": observaciones}
            errors = validate_draft(kind, next_draft, {"latitud": 0, "longitud": 0})
            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.session_state.simple_draft = next_draft
                _set_step("location")
                st.rerun()

    if draft:
        st.button("Cancelar esta carga", key="simple_cancel_form", on_click=_back_to_types)


def _map_for_location(location: dict | None):
    import folium

    center = (location or DEFAULT_LOCATION)
    map_ = folium.Map(location=[center["latitud"], center["longitud"]], zoom_start=14, tiles="OpenStreetMap")
    if location:
        folium.Marker(
            [location["latitud"], location["longitud"]],
            tooltip="Ubicación seleccionada",
        ).add_to(map_)
    return map_


def _render_location(ctx, kind: str) -> None:
    st.title("Elegir ubicación")
    st.caption("Paso 2 de 3 · Use una opción. La última ubicación confirmada reemplaza la anterior.")
    location = st.session_state.get("simple_location")

    with st.container(border=True):
        st.subheader("Buscar dirección o lugar")
        with st.form("simple_search_location", border=False):
            query = st.text_input("Dirección, empresa o lugar", key="simple_search_query")
            searched = st.form_submit_button("Buscar ubicación", width="stretch")
        if searched:
            try:
                st.session_state.simple_search_results = search_places(query)
            except Exception:
                st.session_state.simple_search_results = []
                st.warning("No se pudo buscar ahora. Puede marcar el mapa o usar la ubicación actual.")
        results = st.session_state.get("simple_search_results", [])
        if results:
            labels = [result["label"] for result in results]
            selected_label = st.selectbox("Resultados", labels, key="simple_search_selected")
            selected = results[labels.index(selected_label)]
            if st.button("Usar resultado seleccionado", key="simple_use_search", width="stretch"):
                _use_location(selected["latitud"], selected["longitud"], "Búsqueda", selected["label"])
                st.rerun()

    with st.container(border=True):
        st.subheader("Marcar en el mapa")
        st.caption("Toque o haga clic en el punto deseado. Puede elegir otro punto antes de confirmarlo.")
        map_data = st_folium(
            _map_for_location(location),
            key=f"simple_map_{kind}",
            height=360,
            use_container_width=True,
            returned_objects=["last_clicked"],
        )
        clicked = map_data.get("last_clicked") if isinstance(map_data, dict) else None
        if clicked:
            st.session_state.simple_map_candidate = {"latitud": clicked["lat"], "longitud": clicked["lng"]}
        candidate = st.session_state.get("simple_map_candidate")
        if candidate:
            st.caption(f"Punto marcado: {candidate['latitud']:.6f}, {candidate['longitud']:.6f}")
            if st.button("Usar punto marcado", key="simple_use_map", width="stretch"):
                _use_location(candidate["latitud"], candidate["longitud"], "Mapa")
                st.rerun()

    with st.container(border=True):
        st.subheader("Usar ubicación actual")
        st.caption("El navegador pedirá permiso. Si no está disponible, puede usar las otras opciones.")
        gps = current_location(key=f"simple_gps_{kind}")
        current = getattr(gps, "location", None)
        gps_error = getattr(gps, "error", None)
        if current:
            _use_location(current["latitud"], current["longitud"], "Ubicación actual")
            st.rerun()
        if gps_error:
            st.info("No se recibió ubicación del dispositivo. Busque una dirección o marque el mapa.")

    location = st.session_state.get("simple_location")
    if location:
        st.success(f"Ubicación seleccionada: {location['latitud']:.6f}, {location['longitud']:.6f} ({location['source']})")
        st.link_button("Abrir / verificar en Google Maps", google_maps_url(location["latitud"], location["longitud"]), width="stretch")
        if st.button("Continuar a revisión", key="simple_to_review", type="primary", width="stretch"):
            errors = validate_draft(kind, st.session_state.get("simple_draft", {}), location)
            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.session_state.simple_pending = pending_record(kind, st.session_state["simple_draft"], location, ctx.df_obras)
                st.session_state.simple_save_locked = False
                _set_step("review")
                st.rerun()
    else:
        st.info("Seleccione una ubicación para continuar.")
    st.button("Volver a datos", key="simple_back_form", on_click=_set_step, args=("form",))


def _render_review(ctx, kind: str) -> None:
    pending = st.session_state.get("simple_pending")
    if not pending:
        _set_step("form")
        st.rerun()
    st.title(f"Revisar {KIND_LABELS[kind]}")
    st.caption("Paso 3 de 3 · Verifique la información antes de guardar.")
    labels = {
        "Obra_ID": "Obra ID", "Predio": "Polo / Predio", "Empresa": "Empresa", "Delegado": "Delegado/s",
        "Obreros": "Obreros", "Estado": "Estado", "Jurisdiccion": "Jurisdicción", "Jurisdiccion_R": "Jurisdicción R",
        "Nombre": "Nombre", "Radio_KM": "Radio de influencia (KM)", "Observaciones": "Observaciones",
    }
    with st.container(border=True):
        for key, value in pending.items():
            if key in {"Latitud", "Longitud", "Mujeres"}:
                continue
            st.write(f"**{labels.get(key, key)}:** {value if value != '' else '—'}")
        st.write(f"**Ubicación:** {pending['Latitud']:.6f}, {pending['Longitud']:.6f}")
    st.link_button("Abrir / verificar en Google Maps", google_maps_url(pending["Latitud"], pending["Longitud"]), width="stretch")
    if st.button("Editar", key="simple_edit_review", width="stretch"):
        _set_step("form")
        st.rerun()
    if st.button("Confirmar y guardar", key="simple_confirm_save", type="primary", width="stretch", disabled=st.session_state.get("simple_save_locked", False)):
        st.session_state.simple_save_locked = True
        table = "Obras" if kind == "obra" else "Predios"
        existing = ctx.df_obras if kind == "obra" else ctx.df_predios
        frame = pd.concat([existing, pd.DataFrame([pending])], ignore_index=True)
        if ctx.guardar_db(frame, table):
            ctx.registrar_log("Alta de Obra desde Carga Simplificada" if kind == "obra" else "Agregó Polo desde Carga Simplificada")
            clear_simple_state(st.session_state)
            st.session_state.simple_success = KIND_LABELS[kind]
            _set_step("success")
            st.rerun()
        else:
            st.session_state.simple_save_locked = False
            st.warning("El borrador se conserva. Actualice los datos e intente nuevamente.")


def _render_success() -> None:
    saved = st.session_state.get("simple_success", "Registro")
    st.success(f"{saved} guardado correctamente.")
    st.button("Cargar otro registro", key="simple_another", type="primary", width="stretch", on_click=_back_to_types)
    st.button("Ir a App Completa", key="simple_success_complete", width="stretch", on_click=_to_complete)
    st.button("Cambiar modo", key="simple_success_mode", width="stretch", on_click=_back_to_mode)


def render(ctx) -> None:
    """Renderiza sólo la carga rápida; ABM y navegación completa quedan intactos."""
    if ctx.st.session_state.get("usuario_rol") != "Admin":
        st.title("Carga Simplificada")
        st.error("Esta carga utiliza los permisos actuales de ABM y requiere perfil Admin.")
        st.button("Volver a selección de modo", key="simple_restricted_mode", on_click=_back_to_mode)
        return

    kind = st.session_state.get("simple_kind")
    step = st.session_state.get("simple_step", "choose")
    if step == "success":
        _render_success()
        return
    if not kind:
        _render_type_selection()
        return
    _render_header()
    if step == "form":
        _render_form(ctx, kind)
    elif step == "location":
        _render_location(ctx, kind)
    elif step == "review":
        _render_review(ctx, kind)
    else:
        _back_to_types()
        st.rerun()
