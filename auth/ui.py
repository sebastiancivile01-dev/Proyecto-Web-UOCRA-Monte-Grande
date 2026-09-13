"""UI de autenticacion; solo se ejecuta cuando el bootstrap la invoca."""

from ui.styles import aplicar_estilos_login


def require_login(st, limpiar_sesion):
    if 'usuario_rol' not in st.session_state:
        st.session_state.usuario_rol = None
    
    if st.session_state.usuario_rol is None:
        aplicar_estilos_login()
        
        st.write("<br><br><br>", unsafe_allow_html=True)
        col_izq, col_centro, col_der = st.columns([1, 1.5, 1])
        
        with col_centro:
            try:
                st.image("https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/main/images.jfif", width=150) 
            except:
                pass
                
            st.markdown("<h2 style='text-align: center; margin-top: 10px; font-weight: 900; color: #0033A0;'>🔒 Acceso Restringido</h2>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: #0033A0; font-size: 1.2rem; font-weight: 900; margin-top: -10px;'>UOCRA Monte Grande</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-weight: bold; font-size: 1.1rem; color: #333;'>Ingrese sus credenciales operativas.</p>", unsafe_allow_html=True)
            
            clave = st.text_input("Contraseña:", type="password")
            
            if st.button("Ingresar al Sistema Operativo", use_container_width=True):
                if clave == st.secrets["passwords"]["admin"]: 
                    limpiar_sesion(st.session_state)
                    st.session_state.usuario_rol = "Admin"
                    st.rerun()
                elif clave == st.secrets["passwords"]["restringido"]:
                    limpiar_sesion(st.session_state)
                    st.session_state.usuario_rol = "Restringido"
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta.")
                    
        st.stop()
