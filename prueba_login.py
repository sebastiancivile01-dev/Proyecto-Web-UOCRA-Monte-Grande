# --- SISTEMA DE LOGIN (CANDADO) --- (Corrección Maestra de Desfase Visual)
if 'usuario_rol' not in st.session_state:
    st.session_state.usuario_rol = None

if st.session_state.usuario_rol is None:
    # 1. CSS Global para Fondo, Caja Centrada y Alineación Absoluta
    st.markdown("""
        <style>
        /* Fondo Global */
        [data-testid="stAppViewContainer"] {
            background-image: url("https://acercandonaciones.com/img/1594911762_2601.jpg");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        /* Esconder Cabecera de Streamlit */
        [data-testid="stHeader"] { background: rgba(0,0,0,0); }

        /* Hack CSS para forzar la alineación central absoluta de los elementos nativos */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center !important;
        }

        /* Caja semi-transparente para que el login se lea perfecto */
        .caja-login-pro {
            background-color: rgba(255, 255, 255, 0.92);
            padding: 3rem;
            border-radius: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
            text-align: center;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 2. Interfaz Visual Centrada (Usamos Columnas sin divs HTML para no romper renderizado)
    # Centramos usando columnas nativas [izq, centro, der]
    col_izq, col_centro, col_der = st.columns([1, 1.8, 1])
    
    with col_centro:
        # Usamos Puro HTML para el Logo y los Títulos para control absoluto
        try:
            # Ponemos el logo nativo (images.jfif)
            st.image("images.jfif", width=160) 
        except:
            st.warning("⚠️ No se encontró la imagen 'images.jfif' en GitHub")
            
        # Títulos Visuales
        st.markdown("<h2 style='text-align: center; margin-top: 10px;'>🔒 Acceso Restringido</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #6c757d; font-size: 1.1rem; margin-top: -10px;'>UOCRA Monte Grande</h3>", unsafe_allow_html=True)
        st.write("Ingrese sus credenciales operativas.")
        
        # El formulario nativo de Streamlit
        clave = st.text_input("Contraseña:", type="password")
        
        if st.button("Ingresar al Sistema Operativo", use_container_width=True):
            if clave == "Civile2026":  # Clave Admin
                st.session_state.usuario_rol = "Admin"
                st.rerun()
            elif clave == "Morelli2026": # Clave Restringida
                st.session_state.usuario_rol = "Restringido"
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")
                
    st.stop() # Frena la página acá
