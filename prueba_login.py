import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Prueba de Login UOCRA", layout="wide", page_icon="🏗️")

# --- SISTEMA DE LOGIN (CANDADO) ---
if 'usuario_rol' not in st.session_state:
    st.session_state.usuario_rol = None

if st.session_state.usuario_rol is None:
    # 1. CSS Global para Fondo en la Raíz, Caja Centrada y Botón UOCRA
    st.markdown("""
        <style>
        /* Inyección de Fondo en la Raíz Absoluta de Streamlit */
        .stApp {
            background-image: url("https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/refs/heads/main/UOCRA.jfif");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        
        /* Hacemos transparente la franja superior y el contenedor para que pase el fondo */
        [data-testid="stHeader"], [data-testid="stAppViewContainer"] { 
            background: rgba(0,0,0,0) !important; 
        }

        /* Caja semi-transparente para que el login se lea perfecto sobre la foto */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 3rem;
            border-radius: 15px;
            box-shadow: 0px 8px 25px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center !important;
        }
        
        /* Estilo idéntico a tu app original para el botón de Ingresar */
        div.stButton > button:first-child { 
            background-color: #0033A0; 
            color: white; 
            border-radius: 5px; 
            border: 1px solid #0033A0; 
            font-weight: bold; 
        }
        div.stButton > button:hover { 
            background-color: #002277; 
            color: white; 
            border: 1px solid #002277; 
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 2. Interfaz Visual Centrada 
    st.write("<br><br><br>", unsafe_allow_html=True) # Espacio desde el techo
    col_izq, col_centro, col_der = st.columns([1, 1.5, 1])
    
    with col_centro:
        # Logo
        try:
            st.image("images.jfif", width=150) 
        except:
            st.warning("⚠️ Logo no encontrado")
            
        # Títulos Visuales en NEGRITA y COLOR UOCRA
        st.markdown("<h2 style='text-align: center; margin-top: 10px; font-weight: 900; color: #0033A0;'>🔒 Acceso Restringido</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #0033A0; font-size: 1.2rem; font-weight: 900; margin-top: -10px;'>UOCRA Monte Grande</h3>", unsafe_allow_html=True)
        
        # Texto descriptivo
        st.markdown("<p style='text-align: center; font-weight: bold; font-size: 1.1rem; color: #333;'>Ingrese sus credenciales operativas.</p>", unsafe_allow_html=True)
        
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
                
    st.stop() # Frena la página acá y no carga el resto

# --- LO QUE SE VE DESPUÉS DE PASAR EL CANDADO ---
# Le sacamos la foto de fondo para que la app "simulada" se vea limpia
st.markdown("<style>.stApp { background-image: none; background-color: #F8F9FA; }</style>", unsafe_allow_html=True)

st.success(f"✅ ¡El candado funcionó perfecto! Entraste con el rol: **{st.session_state.usuario_rol}**")
st.info("🏗️ Acá es donde cargarían todos los módulos pesados (Mapa, Excel, BCRA) en la app principal.")

if st.button("Cerrar Sesión para probar el candado de nuevo"):
    st.session_state.usuario_rol = None
    st.rerun()
