"""Selección del modo de uso posterior al login."""


def render(st, limpiar_sesion):
    mode = st.session_state.get("simple_app_mode")
    if mode in {"complete", "simple"}:
        return mode
    # Mantiene el comportamiento de sesiones anteriores al selector de modo.
    if "menu_seleccionado" in st.session_state:
        st.session_state.simple_app_mode = "complete"
        return "complete"

    st.title("UOCRA Monte Grande")
    st.write("Elija cómo desea usar la aplicación.")
    with st.container(border=True):
        st.subheader("APP COMPLETA")
        st.caption("Gestión, consultas y herramientas de la aplicación.")
        if st.button("Abrir App Completa", key="mode_complete", type="primary", width="stretch"):
            st.session_state.simple_app_mode = "complete"
            st.rerun()
    with st.container(border=True):
        st.subheader("CARGA SIMPLIFICADA")
        st.caption("Alta rápida de obra o polo desde celular o PC.")
        if st.button("Abrir Carga Simplificada", key="mode_simple", width="stretch"):
            st.session_state.simple_app_mode = "simple"
            st.rerun()
    st.button("🚪 Cerrar Sesión", key="mode_logout", on_click=limpiar_sesion, args=(st.session_state,))
    return None
