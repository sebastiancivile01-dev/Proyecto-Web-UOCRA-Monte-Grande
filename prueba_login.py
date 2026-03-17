import streamlit as st

# Configuración básica
st.set_page_config(page_title="Prueba de Login UOCRA", layout="wide")

# 1. CSS para el Fondo y la Caja de Cristal
st.markdown("""
    <style>
    /* Imagen de fondo para toda la pantalla */
    [data-testid="stAppViewContainer"] {
        /* ACÁ VA EL LINK DE TU IMAGEN DE FONDO. Te dejé una de prueba */
        background-image: url("https://acercandonaciones.com/img/1594911762_2601.jpg"); 
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    /* Hacemos transparente la franja de arriba de Streamlit */
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }
    /* Caja semi-transparente para que el login se lea perfecto */
    .caja-login {
        background-color: rgba(255, 255, 255, 0.90);
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        text-align: center;
        margin-top: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Lógica del candado
if 'usuario_rol' not in st.session_state:
    st.session_state.usuario_rol = None

if st.session_state.usuario_rol is None:
    # Usamos columnas para centrar la caja en el medio de la pantalla
    col_izq, col_centro, col_der = st.columns([1, 1.5, 1])
    
    with col_centro:
        st.markdown('<div class="caja-login">', unsafe_allow_html=True)
        
        # LOGO DE UOCRA: Usamos la imagen que ya tenías en el menú (images.jfif)
        try:
            st.image("images.jfif", width=150) 
        except:
            st.warning("⚠️ No se encontró la imagen 'images.jfif' en GitHub")
            
        st.title("🔒 Acceso Restringido")
        st.markdown("### UOCRA Monte Grande")
        st.markdown("Ingrese sus credenciales operativas.")
        
        st.write("") # Espacio
        clave = st.text_input("Contraseña:", type="password")
        
        if st.button("Ingresar al Sistema", use_container_width=True):
            if clave == "Civile2026" or clave == "Morelli2026":
                st.session_state.usuario_rol = "Logueado"
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")
                
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop() # Frena la página acá

# 3. Pantalla de Éxito (solo se ve si pasás el login)
st.success("✅ ¡Login Exitoso! El diseño funciona perfecto.")
if st.button("Cerrar Sesión para probar de nuevo"):
    st.session_state.usuario_rol = None
    st.rerun()
