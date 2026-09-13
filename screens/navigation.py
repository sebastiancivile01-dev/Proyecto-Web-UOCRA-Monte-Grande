"""Menu y navegacion de la aplicacion."""


def render(st, abrir_calendario_flotante, limpiar_sesion):
    # --- BARRA LATERAL (MENÚ PRINCIPAL) ---
    with st.sidebar:
        try:
            URL_FOTO_CHICA = "https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/main/images.jfif"
            col_izq, col_centro, col_der = st.columns([1, 2, 1])
            with col_centro:
                st.image(URL_FOTO_CHICA, use_container_width=True)
        except:
            st.markdown("<h3 style='text-align: center; color: #0033A0;'>UOCRA</h3>", unsafe_allow_html=True)
            
        st.markdown("---") 
    
     
            
        # =========================================================
        # 2. COMISIÓN DIRECTIVA Y NAVEGACIÓN (CORREGIDO)
        # =========================================================
        st.markdown("<h2 style='text-align: center; color: #0033A0; margin-bottom: 0;'>UOCRA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.85rem; font-weight: bold; color: #555; margin-top: 0;'>Seccional Monte Grande<br>Conducción: Roberto Morelli</p>", unsafe_allow_html=True)
        
        # --- TU EXPANDER ORIGINAL DE LA COMISIÓN DIRECTIVA CON NOMBRES REALES ---
        with st.sidebar.expander("👥 Comisión Directiva", expanded=False):
            st.markdown("""
            1- Sec. Gral:👤 Roberto Morelli
            
            2- Sec. Adj:👤 Alejandro Benitez
            
            3- Sec. Org:👤 Rolando Civile
            
            4- Sec. Act:👤 Ruben Fernandez
            
            5- Sec. Fin:👤 Roberto Oviedo
            """)
            
        st.markdown("---")
    
           # 1. BOTONES OPERATIVOS JUNTOS
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            limpiar_sesion(st.session_state)
            st.rerun()
            
        st.markdown("---")
    
        # Memoria para recordar qué botón se apretó (Limpio de números)
        if 'menu_seleccionado' not in st.session_state:
            st.session_state.menu_seleccionado = "🗺️ Mapa Territorial"
    
        rol_actual = st.session_state.get("usuario_rol", "Restringido")
    
        # --- MÓDULO: MAPA TERRITORIAL (Fijo arriba) ---
        if st.sidebar.button("🗺️ Mapa Territorial", use_container_width=True):
            st.session_state.menu_seleccionado = "🗺️ Mapa Territorial"
    
        # --- DESPLEGABLE 1: CARGA DE DATOS ---
        with st.sidebar.expander("📁 Carga de Datos", expanded=False):
            # Opciones exclusivas del Admin
            if rol_actual == "Admin":
                if st.button("📥 Carga de Datos (ABM)", use_container_width=True): 
                    st.session_state.menu_seleccionado = "📥 Carga de Datos (ABM)"
                if st.button("⚠️ Reclamos", use_container_width=True): 
                    st.session_state.menu_seleccionado = "⚠️ Reclamos"
            
            # Opciones visibles por todos
            if st.button("🤝 Convenios y Documentación", use_container_width=True): 
                st.session_state.menu_seleccionado = "🤝 Convenios y Documentación"
            if st.button("📝 Observaciones por Empresa", use_container_width=True): 
                st.session_state.menu_seleccionado = "📝 Observaciones por Empresa"
    
        # --- MÓDULO: CALCULADORAS (Fijo al medio) ---
        if st.sidebar.button("🧮 Calculadoras", use_container_width=True):
            st.session_state.menu_seleccionado = "🧮 Calculadoras"
    
        # --- DESPLEGABLE 2: VISUALIZACIÓN DE DATOS ---
        with st.sidebar.expander("📊 Visualización de Datos", expanded=False):
            if st.button("📋 Nóminas", use_container_width=True): 
                st.session_state.menu_seleccionado = "📋 Nóminas"
            if st.button("📊 Estadísticas", use_container_width=True): 
                st.session_state.menu_seleccionado = "📊 Estadísticas"
            if st.button("💜 UOCRA Mujeres", use_container_width=True): 
                st.session_state.menu_seleccionado = "💜 UOCRA Mujeres"
            if st.button("🧹 Auditoría", use_container_width=True): 
                st.session_state.menu_seleccionado = "🧹 Auditoría"
            if st.button("📸 Galería Multimedia", use_container_width=True): 
                st.session_state.menu_seleccionado = "📸 Galería Multimedia"
    
        # --- MÓDULO: CHAT GPT (Fijo abajo) ---
        if st.sidebar.button("🤖 Chat GPT UOCRA", use_container_width=True):
            st.session_state.menu_seleccionado = "🤖 Chat GPT UOCRA"
    
        # =========================================================
        # TRADUCTOR INTELIGENTE (Evita errores de pantalla en blanco)
        # =========================================================
        opcion_map = {
            "🗺️ Mapa Territorial": "1. 🗺️ Mapa Territorial",
            "📥 Carga de Datos (ABM)": "2. 📥 Carga de Datos (ABM)",
            "📋 Nóminas": "3. 📋 Nóminas",
            "🧮 Calculadoras": "4. 🧮 Calculadoras",
            "⚠️ Reclamos": "5. ⚠️ Reclamos",
            "💜 UOCRA Mujeres": "6. 💜 UOCRA Mujeres",
            "🤝 Convenios y Documentación": "7. 🤝 Convenios y Documentación",
            "📊 Estadísticas": "8. 📊 Estadísticas",
            "📸 Galería Multimedia": "9. 📸 Galería Multimedia",
            "🧹 Auditoría": "11. 🧹 Auditoría",
            "📝 Observaciones por Empresa": "12. 📝 Observaciones por Empresa"
        }
        
        # BLINDAJE PARA EL CHAT GPT:
        # Si en tu código el módulo abajo de todo se llama "10. 🤖 Chat GPT UOCRA", dejalos así.
        # Si se llega a llamar "10. 🤖 Asistente Virtual", cambiá el texto de la derecha.
        if st.session_state.menu_seleccionado == "🤖 Chat GPT UOCRA":
            opcion = "10. 🤖 Chat GPT UOCRA"
        else:
            opcion = opcion_map.get(st.session_state.menu_seleccionado, "1. 🗺️ Mapa Territorial")
        
        st.markdown("---")
        
        # Reemplazamos st.caption por un texto blindado en HTML
        st.markdown("<p style='color: #666666; font-weight: bold; font-size: 0.85rem; margin-bottom: 5px;'>🔗 ENLACES ÚTILES</p>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; font-weight: bold; font-size: 0.9rem;'>
            <a href='https://www.ieric.org.ar/' target='_blank' style='color: #1f77b4; text-decoration: none;'>IERIC</a> | 
            <a href='https://www.uocra.org/' target='_blank' style='color: #1f77b4; text-decoration: none;'>UOCRA</a> | 
            <a href='https://www.argentina.gob.ar/trabajo' target='_blank' style='color: #1f77b4; text-decoration: none;'>CGT</a>  | 
            <a href='https://www.construirsalud.com.ar/' target='_blank' style='color: #1f77b4; text-decoration: none;'>MUTUAL</a> |
            <a href='https://servicios.infoleg.gob.ar/infolegInternet/anexos/20000-24999/20993/texact.htm' target='_blank' style='color: #1f77b4; text-decoration: none;'>LEY SIND</a> |
            <a href='https://www.uocra.org/?s=convenio-colectivo-de-trabajo&lang=1' target='_blank' style='color: #1f77b4; text-decoration: none;'>CCT</a> |
            <a href='https://servicios.infoleg.gob.ar/infolegInternet/anexos/35000-39999/38568/texact.htm' target='_blank' style='color: #1f77b4; text-decoration: none;'>SEG.HIG.</a> |
            <a href='https://servicios.infoleg.gob.ar/infolegInternet/anexos/25000-29999/27238/norma.htm' target='_blank' style='color: #1f77b4; text-decoration: none;'>22.250</a>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("#")
        
        # =========================================================
        # ACCESOS DIRECTOS Y REDES (CORREGIDO Y CENTRADO)
        # =========================================================
        st.sidebar.markdown("---")
        st.sidebar.markdown("<p style='text-align: center; font-weight: bold; color: #0033A0; margin-bottom: 5px;'>🌐 Redes Oficiales</p>", unsafe_allow_html=True)
        
        # Creamos 3 columnas: Izquierda (vacía), Centro (la foto), Derecha (vacía)
        col_izq, col_centro, col_der = st.sidebar.columns([1, 2, 1])
        
        with col_centro:
            # ENLACE E IMAGEN DE INSTAGRAM (Centrado)
            st.markdown(
                '<div style="text-align: center;">'
                '<a href="https://www.instagram.com/uocra_seccional_montegrande/" target="_blank">'
                '<img src="https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/main/instagram.png" width="100%" style="border-radius:10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">'
                '</a>'
                '</div>', 
                unsafe_allow_html=True
            )
            st.markdown("<p style='text-align: center; font-size: 0.8rem; margin-top: 5px;'>Instagram</p>", unsafe_allow_html=True)
        # 4. BOTÓN DEL CALENDARIO ABAJO DE TODO
        st.markdown("---")
        if st.button("📅 Calendario y Feriados", type="primary", use_container_width=True):
            abrir_calendario_flotante()
            
    # ==========================================
    return opcion