import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import requests

st.markdown("""
    <style>
    /* 1. FONDO GLOBAL DE LA APLICACIÓN */
    .stApp {
        background-image: url("https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/refs/heads/main/UOCRA.jfif"); 
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* 2. CAJA BLANCA SEMITRANSPARENTE (Protege la lectura de los módulos) */
    .block-container {
        background-color: rgba(255, 255, 255, 0.92) !important; /* 92% blanco */
        padding: 2rem 3rem !important;
        border-radius: 15px;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.2);
        margin-top: 40px;
        margin-bottom: 40px;
    }

    /* 3. COLORES INSTITUCIONALES Y BOTONES */
    h1, h2, h3 { color: #0033A0 !important; }
    div.stButton > button:first-child { background-color: #0033A0; color: white; border-radius: 5px; border: 1px solid #0033A0; }
    div.stButton > button:hover { background-color: #002277; color: white; border: 1px solid #002277; }
    [data-testid="stSidebar"] { background-color: #EAEAEA !important; border-right: 2px solid #CCCCCC !important; }
    
    /* 4. SISTEMA DE TARJETAS KPI PROFESIONALES */
    .tarjeta-kpi {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.08);
        border-left: 6px solid #0033A0;
        text-align: center;
        margin-bottom: 20px;
    }
    .tarjeta-kpi.verde { border-left-color: #28a745; }
    .tarjeta-kpi.naranja { border-left-color: #fd7e14; }
    .tarjeta-kpi.violeta { border-left-color: #8A2BE2; }
    .tarjeta-kpi.rojo { border-left-color: #dc3545; }
    .kpi-titulo { color: #6c757d; font-size: 0.9rem; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .kpi-valor { color: #212529; font-size: 2.2rem; font-weight: 900; margin: 0; }
    
    /* 5. RECUADROS PARA CAMPOS DE FORMULARIO */
    div[data-baseweb="input"], 
    div[data-baseweb="select"], 
    div[data-baseweb="textarea"] {
        border: 1px solid #000000 !important; /* Borde negro fino */
        border-radius: 6px !important; /* Curva suave en las esquinas */
        background-color: #ffffff !important; /* Asegura que el fondo del campo sea blanco sólido */
    }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN (CANDADO) ---
if 'usuario_rol' not in st.session_state:
    st.session_state.usuario_rol = None

if st.session_state.usuario_rol is None:
    # 1. CSS para inyectar la imagen de fondo y la caja transparente
    st.markdown("""
        <style>
        .stApp {
            background-image: url("https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/refs/heads/main/UOCRA.jfif");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        [data-testid="stHeader"], [data-testid="stAppViewContainer"] { background: rgba(0,0,0,0) !important; }
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
        </style>
    """, unsafe_allow_html=True)
    
    # 2. Interfaz Visual Centrada
    st.write("<br><br><br>", unsafe_allow_html=True)
    col_izq, col_centro, col_der = st.columns([1, 1.5, 1])
    
    with col_centro:
        try:
            st.image("images.jfif", width=150) 
        except:
            pass
            
        st.markdown("<h2 style='text-align: center; margin-top: 10px; font-weight: 900; color: #0033A0;'>🔒 Acceso Restringido</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #0033A0; font-size: 1.2rem; font-weight: 900; margin-top: -10px;'>UOCRA Monte Grande</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold; font-size: 1.1rem; color: #333;'>Ingrese sus credenciales operativas.</p>", unsafe_allow_html=True)
        
        clave = st.text_input("Contraseña:", type="password")
        
        if st.button("Ingresar al Sistema Operativo", use_container_width=True):
            if clave == "Civile2026": 
                st.session_state.usuario_rol = "Admin"
                st.rerun()
            elif clave == "Morelli2026":
                st.session_state.usuario_rol = "Restringido"
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")
                
    st.stop()

# --- CONEXIÓN A GOOGLE SHEETS ---
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
try:
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 👇 LINK COMPLETO DEL GOOGLE SHEETS 👇
    URL_DEL_EXCEL = "https://docs.google.com/spreadsheets/d/15_0fpPr90DAJsivWACnFNaGXB1Eb1GaOFh4j-OfDnDU/edit?gid=1143014109#gid=1143014109" 
    
    DOC = client.open_by_url(URL_DEL_EXCEL)
except Exception as e:
    st.error(f"⚠️ Error técnico real: {e}")
    st.stop()

# --- FUNCIONES DE BASE DE DATOS EN LA NUBE ---
# --- FUNCIONES DE BASE DE DATOS CON CACHÉ (PARA EVITAR ERROR 429) ---
@st.cache_data(ttl=600) # Guarda los datos en memoria por 10 minutos
def cargar_db(hoja_nombre, columnas):
    try:
        sheet = DOC.worksheet(hoja_nombre)
        datos = sheet.get_all_records()
        if not datos:
            return pd.DataFrame(columns=columnas)
        return pd.DataFrame(datos)
    except Exception as e:
        return pd.DataFrame(columns=columnas)

def guardar_db(df, hoja_nombre):
    try:
        df_limpio = df.fillna("") # Google Sheets no acepta valores nulos
        sheet = DOC.worksheet(hoja_nombre)
        sheet.clear()
        datos_a_subir = [df_limpio.columns.values.tolist()] + df_limpio.values.tolist()
        sheet.update(values=datos_a_subir, range_name="A1")
        
        # 👇 ESTA LÍNEA ES LA MAGIA 👇
        # Borra la memoria RAM para que el cambio se vea al instante
        st.cache_data.clear() 
        
    except Exception as e:
        st.error(f"Error técnico guardando en {hoja_nombre}: {e}")

# --- CARGA GLOBAL Y EXTRACCIÓN DE DATOS ---
# Sincronizado con tus columnas exactas, incluyendo Obra_ID
df_obras = cargar_db("Obras", ["Obra_ID", "Predio", "Empresa", "Delegado", "Obreros", "Estado", "Latitud", "Longitud", "Jurisdiccion", "Jurisdiccion_R", "Mujeres"])
if 'Mujeres' in df_obras.columns: 
    df_obras['Mujeres'] = pd.to_numeric(df_obras['Mujeres'], errors='coerce').fillna(0)
if 'Obreros' in df_obras.columns: 
    df_obras['Obreros'] = pd.to_numeric(df_obras['Obreros'], errors='coerce').fillna(0)

# CARGA DE PREDIOS Y CONVERSIÓN NUMÉRICA
df_predios = cargar_db("Predios", ["Nombre", "Latitud", "Longitud", "Radio_KM", "Observaciones"])
for col in ['Latitud', 'Longitud', 'Radio_KM']:
    if col in df_predios.columns:
        df_predios[col] = pd.to_numeric(df_predios[col], errors='coerce').fillna(0.0)

df_delegados = cargar_db("Delegados", ["Nombre", "CUIL", "Celular", "Domicilio", "Nacimiento", "Correo", "Observacion"])
df_contactos = cargar_db("Contactos", ["Nombre", "Cargo", "Empresa", "Observaciones"])
df_reclamos = cargar_db("Reclamos", ["Nombre", "Empresa", "Motivo", "Ingreso", "Estado", "Finalizacion", "Respuesta", "Observaciones"])
df_eventos = cargar_db("Mujeres_Eventos", ["Titulo", "Fecha", "Observaciones"]) # Sincronizado con tu pestaña
df_convenios = cargar_db("Convenios", ["Empresa", "Detalle_Convenio", "monto $", "Monto %", "Vigencia"])
df_propuestas = cargar_db("Propuestas", ["Fecha", "Usuario", "Propuesta", "Estado"])
df_puntos_extra = cargar_db("Puntos_Extra", ["Nombre", "Latitud", "Longitud", "Color", "Observacion"])
if not df_puntos_extra.empty:
    df_puntos_extra['Latitud'] = pd.to_numeric(df_puntos_extra['Latitud'], errors='coerce').fillna(0.0)
    df_puntos_extra['Longitud'] = pd.to_numeric(df_puntos_extra['Longitud'], errors='coerce').fillna(0.0)

# La lista de predios ahora se alimenta de la base maestra oficial
lista_predios_historicos = sorted(df_predios['Nombre'].dropna().astype(str).tolist()) if not df_predios.empty else []
lista_empresas_historicas = sorted(list(set(pd.concat([df_obras['Empresa'], df_contactos['Empresa'], df_reclamos['Empresa'], df_convenios['Empresa']]).dropna().astype(str).tolist())))
lista_delegados_nombres = df_delegados['Nombre'].tolist() if not df_delegados.empty else []

lista_jurisdicciones = ["Esteban Echeverría", "Ezeiza", "Cañuelas", "Roque Pérez", "Lobos", "Saladillo", "Monte", "General Belgrano", "Las Heras", "Navarro"]
lista_estados = ["Activa", "Intervenida", "Finalizada", "Interrumpida"]

# --- FASE 4: CONEXIÓN API BCRA (CÁLCULO CER) ---
@st.cache_data(ttl=86400) # Cacheamos por 24hs
def obtener_cer(fecha_str=None):
    """Busca el valor del CER en la API Comunitaria del BCRA"""
    try:
        token = st.secrets["BCRA_TOKEN"]
        headers = {'Authorization': f'Bearer {token}'}
        
        # Endpoint de la API Comunitaria para el CER
        url = "https://api.estadisticasbcra.com/cer"
            
        respuesta = requests.get(url, headers=headers, timeout=10)
        
        if respuesta.status_code == 200:
            datos = respuesta.json() # La API comunitaria devuelve una lista de diccionarios: [{'d': '2024-01-01', 'v': 150.5}, ...]
            if not datos: return None
            
            if fecha_str:
                fecha_buscada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                
                # Recorremos la lista de atrás para adelante (desde lo más reciente a lo más viejo)
                for item in reversed(datos):
                    fecha_item = datetime.strptime(item['d'], "%Y-%m-%d").date()
                    # Buscamos la fecha exacta o la más cercana anterior (por si es feriado o fin de semana)
                    if fecha_item <= fecha_buscada:
                        return float(item['v'])
                return None 
            else:
                # Si no se le pasa fecha, devuelve el CER más actual disponible (el último de la lista)
                return float(datos[-1]['v'])
                
        return None
    except Exception as e:
        return None
    
# --- BARRA LATERAL (MENÚ PRINCIPAL) ---
with st.sidebar:
    # ==========================================
    # NUEVO: PANEL DE ACCESOS DIRECTOS (TOP)
    # ==========================================
    st.markdown("""
        <div style="text-align: center; margin-bottom: 15px;">
            <a href="https://www.instagram.com/uocra.juventud.montegrande" target="_blank" style="text-decoration: none;">
                <div style="background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); 
                            color: white; padding: 10px; border-radius: 8px; font-weight: bold; margin-bottom: 12px; 
                            box-shadow: 0px 4px 6px rgba(0,0,0,0.1); transition: 0.3s;">
                    📸 Instagram Seccional
                </div>
            </a>
            
            <div style="font-size: 13px; background-color: white; padding: 8px; border-radius: 6px; border: 1px solid #CCCCCC;">
                <span style="color: gray; font-size: 11px; display: block; margin-bottom: 4px;">🔗 ENLACES ÚTILES</span>
                <a href="https://www.ieric.org.ar/" target="_blank" style="text-decoration: none; color: #0033A0; font-weight: bold;">IERIC</a> &nbsp;|&nbsp; 
                <a href="https://www.uocra.org/" target="_blank" style="text-decoration: none; color: #0033A0; font-weight: bold;">UOCRA</a> &nbsp;|&nbsp; 
                <a href="https://www.srt.gob.ar/" target="_blank" style="text-decoration: none; color: #0033A0; font-weight: bold;">SRT</a>
            </div>
        </div>
                <hr style="margin-top: 10px; margin-bottom: 15px;">
        """, unsafe_allow_html=True)  # <--- ESTA ES LA CLAVE PARA QUE NO SE VEA COMO TEXTO ROTO
        
        st.image("images.jfif", width=150)
        st.title("Menú Principal")
    
    # Botón para forzar la actualización de datos
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()

    # --- NUEVO: ANOTADOR DE PROPUESTAS ---
    with st.expander("💡 Anotador de Propuestas", expanded=False):
        st.markdown("<p style='font-size:0.85rem; color:#666;'>Envíe sugerencias al equipo de Sistemas.</p>", unsafe_allow_html=True)
        with st.form("f_propuestas", clear_on_submit=True):
            prop_texto = st.text_area("Describa su propuesta:")
            
            if st.form_submit_button("📤 Enviar Propuesta"):
                if not prop_texto.strip():
                    st.error("Escriba una propuesta primero.")
                else:
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
                    usuario_actual = st.session_state.usuario_rol
                    
                    nueva_prop = pd.DataFrame([{
                        "Fecha": fecha_hoy, 
                        "Usuario": usuario_actual, 
                        "Propuesta": prop_texto, 
                        "Estado": "Pendiente"
                    }])
                    
                    df_propuestas = pd.concat([df_propuestas, nueva_prop], ignore_index=True)
                    guardar_db(df_propuestas, "Propuestas")
                    st.success("✅ ¡Propuesta enviada exitosamente!")

    st.markdown("---") # Una rayita separadora

    # Botón para cerrar sesión
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.usuario_rol = None
        st.rerun()

    with st.expander("🏛️ Comisión Directiva", expanded=False):
        st.markdown("""
        **1- Sec. Gral:** Roberto Morelli
        
        **2- Sec. Adj:** Alejandro Benitez
        
        **3- Sec. Org:** Rolando Civile
        
        **4- Sec. Actas:** Ruben Fernandez
        
        **5- Sec. Finanzas:** Roberto Oviedo
        """)

    # MAGIA DEL LOGIN: Filtramos los botones según quién entró
    opciones_totales = [
        "1. 🗺️ Mapa Territorial", "2. 📥 Carga de Datos (ABM)", 
        "3. 📋 Nóminas Consolidadas", "4. 🧮 Calculadoras", "5. ⚠️ Repositorio de Reclamos",
        "6. 💜 UOCRA Mujeres", "7. 🤝 Convenios por Empresa", "8. 📊 Tablero de Control",
        "9. 📸 Galería Multimedia"
    ]

    if st.session_state.usuario_rol == "Restringido":
        opciones_permitidas = ["1. 🗺️ Mapa Territorial", "3. 📋 Nóminas Consolidadas", "4. 🧮 Calculadoras", "6. 💜 UOCRA Mujeres", "8. 📊 Tablero de Control", "9. 📸 Galería Multimedia"]
    else:
        opciones_permitidas = opciones_totales
        
    opcion = st.radio("Navegación:", opciones_permitidas)
# ==========================================
# MÓDULO 1: MAPA TERRITORIAL
# ==========================================
if opcion == "1. 🗺️ Mapa Territorial":
    st.title("📍 Control Territorial - Jurisdicción Completa")
    
    if 'puntos_custom' not in st.session_state:
        st.session_state.puntos_custom = []

    st.markdown("### 👁️ Panel de Visualización")
    opciones_mapa = ["🗺️ Vista General", "👤 Foco en Delegados", "🟢 Solo Activas", "🔴 Con Problemas (Interv/Interr)", "⚪ Finalizadas"]
    if st.session_state.usuario_rol == "Admin":
        opciones_mapa.append("🔒 Solo Jurisdicción R")
        
    modo_mapa = st.selectbox("Seleccione el enfoque del mapa:", opciones_mapa)

    # --- 1. DIBUJAMOS EL MAPA A TAMAÑO COMPLETO ---
    m = folium.Map(location=[-35.15, -58.8], zoom_start=8, tiles="CartoDB positron")
    url_geojson = "https://raw.githubusercontent.com/mgaitan/departamentos_argentina/master/departamentos-buenos_aires.json"
    
    def filtrar_partidos(feature):
        n = str(feature['properties'].get('departamento', '')).lower()
        es_jur = any(c in n for c in ["echeverr", "ezeiza", "cañuela", "canuela", "roque p", "lobos", "saladillo", "navarro", "belgrano", "heras"]) or n in ["monte", "san miguel del monte"]
        if "viamonte" in n or "hermoso" in n: es_jur = False
        return {'fillColor': '#3186cc', 'color': '#000000', 'weight': 1.5, 'fillOpacity': 0.15} if es_jur else {'fillColor': 'transparent', 'color': 'transparent', 'weight': 0}

    folium.GeoJson(url_geojson, name="Límites", style_function=filtrar_partidos).add_to(m)

    # DIBUJAR RADIOS DE PREDIOS/POLOS
    if not df_predios.empty:
        for _, p in df_predios.iterrows():
            lat_p, lon_p, rad_p = p.get('Latitud', 0), p.get('Longitud', 0), p.get('Radio_KM', 0)
            if pd.notna(lat_p) and pd.notna(lon_p) and rad_p > 0:
                folium.Circle(
                    location=[lat_p, lon_p],
                    radius=rad_p * 1000,
                    color="#FF8C00", weight=2, fill=True, fill_color="#FFA500", fill_opacity=0.25,
                    tooltip=f"<div style='text-align:center;'><b>📍 Polo/Predio:</b> {p.get('Nombre', 'S/N')}<br><b>Radio de control:</b> {rad_p} KM</div>"
                ).add_to(m)

    # DIBUJAR PUNTOS EXTRA TEMPORALES
    for pt in st.session_state.puntos_custom:
        html_t = f"<div style='text-align:center; max-width:200px;'><h4 style='color:{pt['color']}; margin-bottom:0px;'>📍 {pt['nombre']}</h4><span style='color:gray; font-size:11px;'>[Marcador Temporal]</span><hr style='margin:5px 0;'>{pt['obs']}</div>"
        folium.Marker([pt["lat"], pt["lon"]], tooltip=html_t, icon=folium.Icon(color=pt["color"], icon="info-sign")).add_to(m)

    # DIBUJAR PUNTOS EXTRA PERMANENTES
    if not df_puntos_extra.empty:
        for _, pt in df_puntos_extra.iterrows():
            html_p = f"<div style='text-align:center; max-width:200px;'><h4 style='color:{pt['Color']}; margin-bottom:0px;'>📍 {pt['Nombre']}</h4><span style='color:#0033A0; font-size:11px;'>[Marcador Permanente]</span><hr style='margin:5px 0;'>{pt.get('Observacion', '')}</div>"
            folium.Marker([pt["Latitud"], pt["Longitud"]], tooltip=html_p, icon=folium.Icon(color=pt["Color"], icon="star")).add_to(m)

    # DIBUJAR OBRAS Y EMPRESAS
    df_mapa = df_obras.copy()
    if not df_mapa.empty:
        if "Activas" in modo_mapa: df_mapa = df_mapa[df_mapa['Estado'] == 'Activa']
        elif "Problemas" in modo_mapa: df_mapa = df_mapa[df_mapa['Estado'].isin(['Intervenida', 'Interrumpida'])]
        elif "Finalizadas" in modo_mapa: df_mapa = df_mapa[df_mapa['Estado'] == 'Finalizada']
        elif "Jurisdicción R" in modo_mapa: df_mapa = df_mapa[df_mapa['Jurisdiccion_R'].astype(str).str.strip().str.upper().isin(['SI', 'SÍ'])]

        for _, row in df_mapa.iterrows():
            lat, lon = row.get('Latitud'), row.get('Longitud')
            predio, empresa = str(row.get('Predio', '')).strip(), str(row.get('Empresa', '')).strip()
            if pd.notna(lat) and pd.notna(lon) and (predio not in ["", "nan"] or empresa not in ["", "nan"]):
                est = str(row.get('Estado', ''))
                color = "green" if est == "Activa" else "orange" if est == "Intervenida" else "lightgray" if est == "Finalizada" else "red"
                txt_p, txt_d = predio if predio else "Sin nombre", row.get('Delegado', 'Sin asignar')
                if "Delegados" in modo_mapa:
                    html = f"<div style='text-align: center;'><h3 style='color: #1a5a8a;'>👤 {txt_d}</h3><hr><b>Obra:</b> {txt_p}<br><b>Estado:</b> {est}</div>"
                    icon = folium.Icon(color="darkblue", icon="users", prefix="fa")
                else:
                    es_r = str(row.get('Jurisdiccion_R', '')).strip().upper() in ['SI', 'SÍ']
                    marca_r = " 🔴 [JUR R]" if es_r and st.session_state.usuario_rol == "Admin" else ""
                    
                    html = f"<div><h4 style='color: #3186cc;'>🏗️ {txt_p}{marca_r}</h4><hr><b>Empresa:</b> {empresa}<br><b>Estado:</b> {est}<br><b>Compañeros:</b> {row.get('Obreros', 0)}<hr><b>Delegado/s:</b><br>{txt_d}</div>"
                    icon = folium.Icon(color=color, icon="hard-hat", prefix="fa")
                
                folium.Marker([lat, lon], tooltip=folium.Tooltip(html), icon=icon).add_to(m)
                
    # CSS PARA EL BORDE NEGRO DEL MAPA
    st.markdown("""
        <style>
        iframe {
            border: 3px solid #000000 !important;
            border-radius: 8px;
            box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # RENDERIZAMOS EL MAPA A ANCHO COMPLETO (1000px)
    folium_static(m, width=1000, height=600)

    # --- 2. PANEL DE CONTROL (SOLO ADMIN) DEBAJO DEL MAPA ---
    if st.session_state.usuario_rol == "Admin":
        st.markdown("---")
        st.markdown("<h3 style='color: #0033A0;'>⚙️ Gestor Avanzado de Puntos Extra</h3>", unsafe_allow_html=True)
        st.info("⚠️ **Aviso Importante:** En caso de añadir obras o predios industriales, hágalo desde el módulo '📥 Carga de Datos (ABM)'. Utilice esta herramienta únicamente para agregados extra (Sedes gremiales, puntos de reunión, etc).")
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            with st.expander("➕ Añadir Ubicación Extra"):
                with st.form("form_punto_custom", clear_on_submit=True):
                    p_nom = st.text_input("Nombre del Punto:*")
                    c_lat, c_lon = st.columns(2)
                    p_lat = c_lat.text_input("Latitud (Ej: -34.81):*")
                    p_lon = c_lon.text_input("Longitud (Ej: -58.46):*")
                    
                    c_col, c_tip = st.columns(2)
                    p_col = c_col.selectbox("Color del Globo:", ["Gris", "Azul", "Verde", "Rojo", "Naranja", "Violeta", "Negro", "Rosa"])
                    # Mapeo de colores al inglés para que Folium los entienda
                    mapa_colores = {"Gris":"gray", "Azul":"blue", "Verde":"green", "Rojo":"red", "Naranja":"orange", "Violeta":"purple", "Negro":"black", "Rosa":"pink"}
                    color_final = mapa_colores[p_col]
                    
                    p_tipo = c_tip.radio("Duración:", ["⏳ Temporal (Se borra al salir)", "💾 Permanente (Se guarda en Excel)"])
                    p_obs = st.text_area("Observación / Detalle:")

                    if st.form_submit_button("📍 Colocar en el Mapa"):
                        if not p_nom or not p_lat or not p_lon:
                            st.error("❌ Nombre, Latitud y Longitud son obligatorios.")
                        else:
                            try:
                                lat_f = float(p_lat)
                                lon_f = float(p_lon)
                                
                                if "Temporal" in p_tipo:
                                    st.session_state.puntos_custom.append({"nombre": p_nom, "lat": lat_f, "lon": lon_f, "color": color_final, "obs": p_obs})
                                    st.success("✅ Punto Temporal agregado al mapa.")
                                else:
                                    nuevo_punto = pd.DataFrame([{"Nombre": p_nom, "Latitud": lat_f, "Longitud": lon_f, "Color": color_final, "Observacion": p_obs}])
                                    df_puntos_extra = pd.concat([df_puntos_extra, nuevo_punto], ignore_index=True)
                                    guardar_db(df_puntos_extra, "Puntos_Extra")
                                    st.success("✅ Punto Permanente guardado en Google Sheets.")
                                
                                st.rerun()
                            except ValueError:
                                st.error("❌ Error: Latitud y Longitud deben ser números válidos.")

        with col_p2:
            with st.expander("🗑️ Eliminar Ubicación Extra"):
                # Borrar Temporales
                if st.session_state.puntos_custom:
                    st.write("**Puntos Temporales Activos:**")
                    nombres_temp = [p["nombre"] for p in st.session_state.puntos_custom]
                    temp_a_borrar = st.selectbox("Seleccionar temporal para borrar:", [""] + nombres_temp, key="del_temp")
                    if st.button("🗑️ Borrar Temporal") and temp_a_borrar:
                        st.session_state.puntos_custom = [p for p in st.session_state.puntos_custom if p["nombre"] != temp_a_borrar]
                        st.rerun()
                else:
                    st.info("No hay puntos temporales activos.")
                    
                st.markdown("---")
                
                # Borrar Permanentes
                if not df_puntos_extra.empty:
                    st.write("**Puntos Permanentes (Excel):**")
                    nombres_perm = df_puntos_extra["Nombre"].tolist()
                    perm_a_borrar = st.selectbox("Seleccionar permanente para borrar:", [""] + nombres_perm, key="del_perm")
                    if st.button("🗑️ Borrar Permanente") and perm_a_borrar:
                        df_puntos_extra = df_puntos_extra[df_puntos_extra["Nombre"] != perm_a_borrar]
                        guardar_db(df_puntos_extra, "Puntos_Extra")
                        st.success("✅ Borrado definitivamente del Excel.")
                        st.rerun()
                else:
                    st.info("No hay puntos permanentes guardados.")
# ==========================================
# MÓDULO 2: CARGA DE DATOS (ABM)
# ==========================================
elif opcion == "2. 📥 Carga de Datos (ABM)":
    st.title("📥 Ingreso y Modificación de Datos")
    
    tab_predios, tab_obras, tab_delegados, tab_contactos = st.tabs(["🗺️ Predios/Polos", "🏗️ Obras y Empresas", "👥 Delegados y Colab.", "🏢 Contactos"])

    with tab_predios:
        st.subheader("Configuración de Polos Industriales")
        acc_predio = st.radio("Acción Predio:", ["➕ Nuevo Polo", "✏️ Modificar", "🗑️ Eliminar"], horizontal=True)

        if acc_predio == "➕ Nuevo Polo":
            with st.form("f_n_predio", clear_on_submit=True):
                p_nom = st.text_input("Nombre del Predio/Polo:*")
                c1, c2, c3 = st.columns(3)
                p_lat = c1.text_input("Latitud (Ej: -34.812):")
                p_lon = c2.text_input("Longitud (Ej: -58.531):")
                p_rad = c3.number_input("Radio de influencia (KM):", min_value=0.1, step=0.1, value=1.0)
                p_obs = st.text_area("Observaciones:")

                if st.form_submit_button("💾 Guardar Polo"):
                    if not p_nom:
                        st.error("❌ El nombre es obligatorio.")
                    else:
                        nuevo_predio = pd.DataFrame([{"Nombre": p_nom, "Latitud": float(p_lat) if p_lat else 0.0, "Longitud": float(p_lon) if p_lon else 0.0, "Radio_KM": p_rad, "Observaciones": p_obs}])
                        df_predios = pd.concat([df_predios, nuevo_predio], ignore_index=True)
                        guardar_db(df_predios, "Predios")
                        st.success("✅ Polo registrado exitosamente.")
                        st.rerun()

        elif acc_predio == "✏️ Modificar":
            if not df_predios.empty:
                predio_ed = st.selectbox("Seleccione el Polo a modificar:", df_predios['Nombre'].tolist())
                if predio_ed:
                    idx = df_predios[df_predios['Nombre'] == predio_ed].index[0]
                    dat = df_predios.loc[idx]
                    with st.form("f_e_predio"):
                        nn = st.text_input("Nombre:*", value=str(dat.get('Nombre','')))
                        c1, c2, c3 = st.columns(3)
                        nlat = c1.text_input("Latitud:", value=str(dat.get('Latitud','')))
                        nlon = c2.text_input("Longitud:", value=str(dat.get('Longitud','')))
                        nrad = c3.number_input("Radio (KM):", min_value=0.1, step=0.1, value=float(dat.get('Radio_KM', 1.0)))
                        nobs = st.text_area("Observaciones:", value=str(dat.get('Observaciones','')))

                        if st.form_submit_button("🔄 Actualizar"):
                            df_predios.loc[idx] = [nn, float(nlat) if nlat else 0.0, float(nlon) if nlon else 0.0, nrad, nobs]
                            guardar_db(df_predios, "Predios")
                            st.success("✅ Polo actualizado.")
                            st.rerun()

        elif acc_predio == "🗑️ Eliminar":
            if not df_predios.empty:
                predio_el = st.selectbox("Seleccione el Polo a borrar:", [""] + df_predios['Nombre'].tolist())
                if st.button("🗑️ Eliminar Definitivamente") and predio_el:
                    df_predios = df_predios[df_predios['Nombre'] != predio_el]
                    guardar_db(df_predios, "Predios")
                    st.success("✅ Polo eliminado.")
                    st.rerun()

    with tab_obras:
        acc_obras = st.radio("Acción Obras:", ["➕ Nueva Obra", "✏️ Modificar Obra", "🗑️ Eliminar Obra"], horizontal=True)
        
        if acc_obras == "➕ Nueva Obra":
            with st.form("f_n_obra", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    p_sel = st.selectbox("Predio/Polo Base:*", [""] + lista_predios_historicos, help="Si no está en la lista, créelo primero en la pestaña 'Predios/Polos'.")
                    e_sel = st.selectbox("Empresa:", ["➕ Nueva..."] + lista_empresas_historicas)
                    e_nueva = st.text_input("Si es Nueva, escríbala:")
                    d_sel = st.multiselect("Delegado/s:", lista_delegados_nombres)
                with col2:
                    jur = st.selectbox("Jurisdicción:", lista_jurisdicciones)
                    obr = st.number_input("Obreros:", min_value=0, step=1)
                    est = st.selectbox("Estado:", lista_estados)
                    lat, lon = st.text_input("Latitud:"), st.text_input("Longitud:")
                    
                    jur_r = False
                    if st.session_state.usuario_rol == "Admin":
                        jur_r = st.checkbox("🔒 Marca Especial: Jurisdicción R")
                
                if st.form_submit_button("💾 Guardar"):
                    p_fin = p_sel 
                    e_fin = e_nueva.strip() if e_sel == "➕ Nueva..." else e_sel
                    
                    if not p_fin: 
                        st.error("❌ Falta seleccionar un Predio/Polo Base.")
                    else:
                        # Auto-generar Obra_ID
                        nuevo_id = 1
                        if not df_obras.empty and 'Obra_ID' in df_obras.columns:
                            nuevo_id = int(pd.to_numeric(df_obras['Obra_ID'], errors='coerce').max() + 1)

                        df_obras = pd.concat([df_obras, pd.DataFrame([{
                            "Obra_ID": nuevo_id, "Predio": p_fin, "Empresa": e_fin, "Delegado": ", ".join(d_sel), 
                            "Obreros": obr, "Estado": est, "Jurisdiccion": jur, 
                            "Latitud": float(lat) if lat else None, 
                            "Longitud": float(lon) if lon else None, 
                            "Jurisdiccion_R": "SI" if jur_r else "", # Se guarda como SI
                            "Mujeres": 0  # Inicia en 0 para UOCRA Mujeres
                        }])], ignore_index=True)
                        guardar_db(df_obras, "Obras")
                        st.success("Registrada!")
                        st.rerun()

        elif acc_obras == "✏️ Modificar Obra":
            if not df_obras.empty:
                opciones_obras = df_obras['Predio'].astype(str) + " (" + df_obras['Empresa'].astype(str) + ")"
                obra_ed = st.selectbox("Obra a modificar:", opciones_obras.tolist())
                
                if obra_ed:
                    idx = opciones_obras[opciones_obras == obra_ed].index[0]
                    dat = df_obras.loc[idx] 
                    del_v = [d for d in str(dat.get('Delegado','')).split(", ") if d in lista_delegados_nombres]
                    
                    with st.form("f_e_obra"):
                        col1, col2 = st.columns(2)
                        with col1:
                            np = st.text_input("Predio:*", value=str(dat.get('Predio','')))
                            ne = st.text_input("Empresa:", value=str(dat.get('Empresa','')))
                            nd = st.multiselect("Delegado/s:", lista_delegados_nombres, default=del_v)
                            nj = st.selectbox("Jurisdicción:", lista_jurisdicciones, index=lista_jurisdicciones.index(dat['Jurisdiccion']) if dat.get('Jurisdiccion') in lista_jurisdicciones else 0)
                        with col2:
                            no = st.number_input("Obreros:", min_value=0, step=1, value=int(dat.get('Obreros',0) if pd.notna(dat.get('Obreros')) else 0))
                            ne_est = st.selectbox("Estado:", lista_estados, index=lista_estados.index(dat['Estado']) if dat.get('Estado') in lista_estados else 0)
                            nlat = st.text_input("Latitud:", value="" if pd.isna(dat.get('Latitud')) else str(dat['Latitud']))
                            nlon = st.text_input("Longitud:", value="" if pd.isna(dat.get('Longitud')) else str(dat['Longitud']))
                            
                            if st.session_state.usuario_rol == "Admin":
                                es_jur_r = str(dat.get('Jurisdiccion_R', '')).strip().upper() in ['SI', 'SÍ']
                                nj_r = st.checkbox("🔒 Marca Especial: Jurisdicción R", value=es_jur_r)
                            else:
                                nj_r = str(dat.get('Jurisdiccion_R', '')).strip().upper() in ['SI', 'SÍ']
                        
                        if st.form_submit_button("🔄 Actualizar"):
                            obra_id_actual = dat.get('Obra_ID', '')
                            df_obras.loc[idx] = [obra_id_actual, np, ne, ", ".join(nd), no, ne_est, float(nlat) if nlat else None, float(nlon) if nlon else None, nj, "SI" if nj_r else "", dat.get('Mujeres', 0)]
                            guardar_db(df_obras, "Obras")
                            st.success("Actualizada!")
                            st.rerun()

        elif acc_obras == "🗑️ Eliminar Obra":
            if not df_obras.empty:
                opciones_obras_el = [""] + (df_obras['Predio'].astype(str) + " (" + df_obras['Empresa'].astype(str) + ")").tolist()
                obra_el = st.selectbox("Borrar:", opciones_obras_el)
                if st.button("🗑️ Eliminar") and obra_el != "":
                    idx_el = opciones_obras_el.index(obra_el) - 1
                    df_obras = df_obras.drop(df_obras.index[idx_el])
                    guardar_db(df_obras, "Obras")
                    st.success("Eliminada.")
                    st.rerun()
    
    with tab_delegados:
        acc_del = st.radio("Acción Delegados:", ["➕ Nuevo", "✏️ Modificar", "🗑️ Eliminar"], horizontal=True)
        
        if acc_del == "➕ Nuevo":
            with st.form("f_n_del", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nom = st.text_input("Nombre:*")
                    cuil = st.text_input("CUIL:")
                    cel = st.text_input("Celular:")
                    dom = st.text_input("Domicilio:")
                with col2:
                    nac = st.date_input("Nacimiento:", min_value=datetime(1900, 1, 1), format="DD/MM/YYYY")
                    corr = st.text_input("Correo:")
                    obs = st.text_area("Obs:")
                if st.form_submit_button("💾 Guardar") and nom:
                    df_delegados = pd.concat([df_delegados, pd.DataFrame([{"Nombre": nom, "CUIL": cuil, "Celular": cel, "Domicilio": dom, "Nacimiento": nac.strftime("%d/%m/%Y"), "Correo": corr, "Observacion": obs}])], ignore_index=True)
                    guardar_db(df_delegados, "Delegados")
                    st.success("Agregado!")
                    st.rerun()

        elif acc_del == "✏️ Modificar":
            if not df_delegados.empty:
                del_ed = st.selectbox("Modificar:", df_delegados['Nombre'].tolist())
                if del_ed:
                    idx = df_delegados[df_delegados['Nombre'] == del_ed].index[0]
                    dat = df_delegados.loc[idx]
                    try: 
                        f_obj = datetime.strptime(str(dat.get('Nacimiento', '01/01/2000')), "%d/%m/%Y").date()
                    except: 
                        f_obj = datetime(2000, 1, 1).date()
                    
                    with st.form("f_e_del"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nn = st.text_input("Nombre:*", value=str(dat.get('Nombre','')))
                            ncu = st.text_input("CUIL:", value=str(dat.get('CUIL','')))
                            nce = st.text_input("Celular:", value=str(dat.get('Celular','')))
                            ndo = st.text_input("Domicilio:", value=str(dat.get('Domicilio','')))
                        with col2:
                            nna = st.date_input("Nacimiento:", value=f_obj, min_value=datetime(1900, 1, 1), format="DD/MM/YYYY")
                            nco = st.text_input("Correo:", value=str(dat.get('Correo','')))
                            nob = st.text_area("Obs:", value=str(dat.get('Observacion','')))
                        if st.form_submit_button("🔄 Actualizar"):
                            df_delegados.loc[idx] = [nn, ncu, nce, ndo, nna.strftime("%d/%m/%Y"), nco, nob]
                            guardar_db(df_delegados, "Delegados")
                            st.success("Actualizado!")
                            st.rerun()

        elif acc_del == "🗑️ Eliminar":
            if not df_delegados.empty:
                del_el = st.selectbox("Borrar:", [""] + df_delegados['Nombre'].tolist())
                if st.button("🗑️ Eliminar") and del_el:
                    df_delegados = df_delegados[df_delegados['Nombre'] != del_el]
                    guardar_db(df_delegados, "Delegados")
                    st.success("Eliminado.")
                    st.rerun()

    with tab_contactos:
        acc_con = st.radio("Acción Contactos:", ["➕ Nuevo", "✏️ Modificar", "🗑️ Eliminar"], horizontal=True)
        
        if acc_con == "➕ Nuevo":
            with st.form("f_n_con", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    cnom = st.text_input("Nombre:*")
                    cemp_sel = st.selectbox("Empresa:", ["➕ Nueva..."] + lista_empresas_historicas)
                    cemp_n = st.text_input("Si es Nueva, escríbala:")
                with col2:
                    ccar = st.text_input("Cargo:")
                    cobs = st.text_area("Obs:")
                if st.form_submit_button("💾 Guardar") and cnom:
                    cemp_f = cemp_n.strip() if cemp_sel == "➕ Nueva..." else cemp_sel
                    if cemp_f:
                        df_contactos = pd.concat([df_contactos, pd.DataFrame([{"Nombre": cnom, "Cargo": ccar, "Empresa": cemp_f, "Observaciones": cobs}])], ignore_index=True)
                        guardar_db(df_contactos, "Contactos")
                        st.success("Guardado!")
                        st.rerun()

        elif acc_con == "✏️ Modificar":
            if not df_contactos.empty:
                ops = df_contactos['Nombre'] + " (" + df_contactos['Empresa'] + ")"
                con_ed = st.selectbox("Modificar:", ops.tolist())
                if con_ed:
                    idx = ops[ops == con_ed].index[0]
                    dat = df_contactos.loc[idx]
                    with st.form("f_e_con"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nn = st.text_input("Nombre:*", value=str(dat.get('Nombre','')))
                            ne = st.text_input("Empresa:*", value=str(dat.get('Empresa','')))
                        with col2:
                            nc = st.text_input("Cargo:", value=str(dat.get('Cargo','')))
                            no = st.text_area("Obs:", value=str(dat.get('Observaciones','')))
                        if st.form_submit_button("🔄 Actualizar"):
                            df_contactos.loc[idx] = [nn, nc, ne, no]
                            guardar_db(df_contactos, "Contactos")
                            st.success("Actualizado!")
                            st.rerun()

        elif acc_con == "🗑️ Eliminar":
            if not df_contactos.empty:
                ops_el = [""] + (df_contactos['Nombre'] + " (" + df_contactos['Empresa'] + ")").tolist()
                con_el = st.selectbox("Borrar:", ops_el)
                if st.button("🗑️ Eliminar") and con_el:
                    idx = ops_el.index(con_el) - 1
                    df_contactos = df_contactos.drop(df_contactos.index[idx])
                    guardar_db(df_contactos, "Contactos")
                    st.success("Eliminado.")
                    st.rerun()

# ==========================================
# MÓDULO 3: NÓMINAS
# ==========================================
elif opcion == "3. 📋 Nóminas Consolidadas":
    st.title("📋 Repositorio de Bases de Datos")
    
    # 1. Tarjetas de Resumen
    c1, c2, c3 = st.columns(3)
    emp_totales = len(df_obras['Empresa'].unique()) if not df_obras.empty else 0
    del_totales = len(df_delegados) if not df_delegados.empty else 0
    con_totales = len(df_contactos) if not df_contactos.empty else 0
    
    with c1: st.markdown(f'<div class="tarjeta-kpi"><div class="kpi-titulo">🏢 Empresas Activas</div><div class="kpi-valor">{emp_totales}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="tarjeta-kpi verde"><div class="kpi-titulo">👥 Delegados Registrados</div><div class="kpi-valor">{del_totales}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="tarjeta-kpi naranja"><div class="kpi-titulo">📞 Contactos Agenda</div><div class="kpi-valor">{con_totales}</div></div>', unsafe_allow_html=True)
    
    st.write("Buscador en tiempo real. Escriba para filtrar los resultados automáticamente.")
    t1, t2, t3 = st.tabs(["🏗️ Obras y Empresas", "👥 Padrón de Delegados", "🏢 Agenda de Contactos"])
    
    with t1: 
        busq_obra = st.text_input("🔍 Buscar por Predio o Empresa:", key="b_obras")
        df_mostrar_o = df_obras.copy()
        
        # MAGIA FASE 2: Borramos la columna si existe
        if st.session_state.usuario_rol == "Restringido":
            cols_a_borrar = [col for col in df_mostrar_o.columns if "Jurisdiccion_R" in str(col)]
            if cols_a_borrar:
                df_mostrar_o = df_mostrar_o.drop(columns=cols_a_borrar)
            
        if busq_obra:
            df_mostrar_o = df_mostrar_o[df_mostrar_o['Predio'].str.contains(busq_obra, case=False, na=False) | df_mostrar_o['Empresa'].str.contains(busq_obra, case=False, na=False)]
        st.dataframe(df_mostrar_o, use_container_width=True)
        
    with t2: 
        busq_del = st.text_input("🔍 Buscar Delegado por Nombre o CUIL:", key="b_del")
        df_mostrar_d = df_delegados
        if busq_del:
            df_mostrar_d = df_delegados[df_delegados['Nombre'].str.contains(busq_del, case=False, na=False) | df_delegados['CUIL'].astype(str).str.contains(busq_del, case=False, na=False)]
        st.dataframe(df_mostrar_d, use_container_width=True)
        
    with t3: 
        busq_con = st.text_input("🔍 Buscar Contacto por Nombre o Empresa:", key="b_con")
        df_mostrar_c = df_contactos
        if busq_con:
            df_mostrar_c = df_contactos[df_contactos['Nombre'].str.contains(busq_con, case=False, na=False) | df_contactos['Empresa'].str.contains(busq_con, case=False, na=False)]
        st.dataframe(df_mostrar_c, use_container_width=True)

# ==========================================
# MÓDULO 4: CALCULADORAS GENÉRICAS
# ==========================================
elif opcion == "4. 🧮 Calculadoras":
    st.title("🧮 Módulo de Cálculos Gremiales")

    tab_recibo, tab_ieric, tab_vacaciones, tab_sac = st.tabs([
        "🧾 Calculadora de Recibos", 
        "💰 Fondo Cese (IERIC)", 
        "🏖️ Vacaciones", 
        "🎄 SAC (Aguinaldo)"
    ])
    
    with tab_recibo:
        formato_liq = st.selectbox("📝 Formato Liquidativo (Convenio de Empresa):", ["AESA"])
        st.markdown("---")

        if 'paritarias' not in st.session_state:
            st.session_state.paritarias = {"Ayudante": 5470.0, "MO": 6000.0, "Of": 6800.0, "OfEsp": 7500.0, "Viatico": 15733.30}
        
        with st.expander("⚙️ Actualizar Paritarias Vigentes", expanded=False):
            with st.form("form_p"):
                col1, col2 = st.columns(2)
                with col1:
                    va = st.number_input("Ayudante ($/hr):", value=st.session_state.paritarias["Ayudante"])
                    vm = st.number_input("Medio-Oficial ($/hr):", value=st.session_state.paritarias["MO"])
                    vo = st.number_input("Oficial ($/hr):", value=st.session_state.paritarias["Of"])
                with col2:
                    voe = st.number_input("Of. Esp ($/hr):", value=st.session_state.paritarias["OfEsp"])
                    vv = st.number_input("Viático Diario ($):", value=st.session_state.paritarias["Viatico"])
                if st.form_submit_button("💾 Guardar"):
                    st.session_state.paritarias = {"Ayudante": va, "MO": vm, "Of": vo, "OfEsp": voe, "Viatico": vv}
                    st.success("✅ Actualizado.")

        st.markdown("### 🧮 Carga de Novedades")
        with st.form("form_calc"):
            col1, col2 = st.columns(2)
            with col1:
                n_emp = st.text_input("Nombre del Compañero:")
                e_liq = st.selectbox("Empresa:", ["AESA", "Estándar", "DF Soluciones-Tec"])
                cat = st.selectbox("Categoría:", ["Ayudante", "Medio-Oficial", "Oficial", "Oficial-Especializado"])
                cat_map = {"Ayudante": "Ayudante", "Medio-Oficial": "MO", "Oficial": "Of", "Oficial-Especializado": "OfEsp"}
                vh = st.session_state.paritarias[cat_map[cat]]
                
                st.markdown("**Horas Trabajadas**")
                hn = st.number_input("Hs Norm:", min_value=0.0)
                h50 = st.number_input("Hs 50%:", min_value=0.0)
                h100 = st.number_input("Hs 100%:", min_value=0.0)
                hc = st.number_input("Hs Comp:", min_value=0.0)
                df_f = st.number_input("Días Fer:", min_value=0.0)
                
                ha = st.number_input("Hs Altura:", min_value=0.0)
                hnoc = st.number_input("Hs Nocturnas:", min_value=0.0)
                cpres = st.selectbox("Presentismo (20%):", ["Sí", "No"])
                pesp = st.number_input("% Especialidad:", min_value=0.0)
                pnr = st.number_input("Plus NR (%):", min_value=0.0)

            with col2:
                st.markdown("**Ajustes Extras**")
                dv = st.number_input("Días Vac:", min_value=0.0)
                sb = st.number_input("Sueldo Base (Vac/SAC):", min_value=0.0)
                msac = st.number_input("Meses (SAC):", min_value=0.0, max_value=6.0)
                mr = st.number_input("Mejor Rem:", min_value=0.0)
                
                st.markdown("**Eventuales**")
                rr = st.number_input("Retro Rem:", min_value=0.0)
                rnr = st.number_input("Retro NR:", min_value=0.0)
                er = st.number_input("Ev Rem:", min_value=0.0)
                enr = st.number_input("Ev NR:", min_value=0.0)
                dvi = st.number_input("Días Viático:", min_value=0.0)
                
                st.markdown("**Deducciones**")
                ds = st.number_input("Seguro:", min_value=0.0)
                dg = st.number_input("Ganancias (+/-):", value=0.0)

            if st.form_submit_button("▶ Generar Recibo Teórico", use_container_width=True):
                subtot = (hn*vh) + (h50*vh*1.5) + (h100*vh*2.0) + (hc*vh) + (df_f*9.0*vh)
                mha = ha*vh*0.15
                mhnoc = hnoc*vh*(8/60)
                mpres = ((hn+h50+h100+hc+(df_f*9.0))*vh*0.20) if cpres == "Sí" else 0.0
                mesp = (hn+h50+h100)*vh*(pesp/100)
                mvac = ((sb/25)-(sb/30))*dv if sb>0 and dv>0 else 0.0
                msac_val = (mr/2)*(msac/6) if mr>0 else 0.0
                
                bruto = subtot + mha + mhnoc + mpres + mesp + mvac + msac_val + er + rr
                ret = (bruto*0.11) + (bruto*0.03) + (bruto*0.03) + (bruto*0.025) + ds + dg
                norem = (subtot*(pnr/100)) + (dvi*st.session_state.paritarias["Viatico"]) + enr + rnr
                neto = bruto - ret + norem

                txt = f"EMPLEADO: {n_emp} | EMPRESA: {e_liq}\n{'='*50}\n TOTAL BRUTO: $ {bruto:,.2f}\n TOTAL RETENCIONES: -$ {ret:,.2f}\n TOTAL NO REMUNERATIVOS: $ {norem:,.2f}\n{'='*50}\n NETO A COBRAR: $ {neto:,.2f}"
                st.session_state.recibo_txt = txt
                st.session_state.rec_nombre = n_emp
                st.session_state.rec_empresa = e_liq
                st.success("✅ Generado.")

        if 'recibo_txt' in st.session_state:
            st.code(st.session_state.recibo_txt, language="text")
            st.markdown("---")
            st.markdown("### ⚠️ Iniciar Reclamo por Liquidación")
            motivo_recibo = st.text_input("Motivo de la Diferencia/Reclamo:")
            if st.button("🚨 Enviar al Repositorio de Reclamos", key="btn_recibo"):
                if not motivo_recibo: 
                    st.error("Escriba un motivo.")
                else:
                    df_reclamos = pd.concat([df_reclamos, pd.DataFrame([{"Nombre": st.session_state.rec_nombre, "Empresa": st.session_state.rec_empresa, "Motivo": motivo_recibo, "Ingreso": datetime.now().strftime("%d/%m/%Y"), "Estado": "Activo", "Finalizacion": "En proceso", "Respuesta": "", "Observaciones": "Generado Automáticamente desde Calculadora."}])], ignore_index=True)
                    guardar_db(df_reclamos, "Reclamos")
                    st.success("✅ Reclamo enviado!")

    with tab_ieric:
        st.write("Carga de quincenas históricas para cálculo de aportes y actualización por CER.")
        
        # 1. Intentamos traer el CER de hoy
        cer_actual = obtener_cer()
        if cer_actual:
            st.success(f"🏦 Conexión BCRA Exitosa: Índice CER Actual = {cer_actual}")
        else:
            st.warning("⚠️ No se pudo conectar con el BCRA. Se calcularán montos nominales sin indexar.")
        
        col_i1, col_i2 = st.columns(2)
        ieric_nombre = col_i1.text_input("Nombre del Compañero (Para Registro/Reclamo):")
        ieric_emp = col_i2.selectbox("Empresa:", ["➕ Nueva..."] + lista_empresas_historicas, key="ieric_e")

        if 'quincenas' not in st.session_state: 
            st.session_state.quincenas = []

        with st.form("form_q"):
            c1, c2 = st.columns(2)
            fp = c1.date_input("Fecha de Pago Original")
            bru = c2.number_input("Sueldo Bruto Quincenal ($):", min_value=0.0, step=1000.0)
            if st.form_submit_button("➕ Agregar Quincena") and bru > 0:
                nro = len(st.session_state.quincenas) + 1
                tasa = 0.12 if nro <= 24 else 0.08
                aporte_base = bru * tasa
                
                # 2. Buscamos el CER del día de pago en el BCRA
                fecha_formato_api = fp.strftime("%Y-%m-%d")
                cer_historico = obtener_cer(fecha_formato_api)
                
                # 3. Lógica de Capitalización (Fórmula de Indexación)
                aporte_actualizado = aporte_base
                if cer_historico and cer_actual:
                    aporte_actualizado = aporte_base * (cer_actual / cer_historico)
                
                st.session_state.quincenas.append({
                    "Quincena #": f"Q-{nro:02d}", 
                    "Fecha Pago": fp.strftime("%d/%m/%Y"), 
                    "Bruto": bru, 
                    "Aporte Nominal": aporte_base,
                    "CER Hist.": round(cer_historico, 2) if cer_historico else "N/A",
                    "Aporte Actualizado (CER)": aporte_actualizado
                })
                st.rerun()

        if st.session_state.quincenas:
            df_q = pd.DataFrame(st.session_state.quincenas)
            df_m = df_q.copy()
            df_m["Bruto"] = df_m["Bruto"].apply(lambda x: f"$ {x:,.2f}")
            df_m["Aporte Nominal"] = df_m["Aporte Nominal"].apply(lambda x: f"$ {x:,.2f}")
            df_m["Aporte Actualizado (CER)"] = df_m["Aporte Actualizado (CER)"].apply(lambda x: f"$ {x:,.2f}")
            
            st.dataframe(df_m, use_container_width=True)
            
            col_tot1, col_tot2 = st.columns(2)
            # Mostramos la diferencia entre la plata vieja y la plata indexada
            suma_nominal = sum(q['Aporte Nominal'] for q in st.session_state.quincenas)
            suma_actualizada = sum(q['Aporte Actualizado (CER)'] for q in st.session_state.quincenas)
            
            col_tot1.metric("Deuda Original (Histórica)", f"$ {suma_nominal:,.2f}")
            col_tot2.metric("DEUDA REAL ACTUALIZADA", f"$ {suma_actualizada:,.2f}", delta=f"+$ {(suma_actualizada - suma_nominal):,.2f} por inflación")
            
            st.markdown("---")
            st.markdown("### ⚠️ Iniciar Reclamo de IERIC")
            motivo_ieric = st.text_input("Motivo del Reclamo (Ej: Falta de pago libretas):")
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("🚨 Enviar al Repositorio de Reclamos", key="btn_ieric"):
                if not ieric_nombre or ieric_emp == "➕ Nueva...": 
                    st.error("❌ Complete Nombre y Empresa arriba.")
                elif not motivo_ieric: 
                    st.error("❌ Escriba un motivo.")
                else:
                    # Guardamos el reclamo con el monto actualizado
                    motivo_final = f"{motivo_ieric} | Deuda Actualizada: $ {suma_actualizada:,.2f}"
                    df_reclamos = pd.concat([df_reclamos, pd.DataFrame([{"Nombre": ieric_nombre, "Empresa": ieric_emp, "Motivo": motivo_final, "Ingreso": datetime.now().strftime("%d/%m/%Y"), "Estado": "Activo", "Finalizacion": "En proceso", "Respuesta": "", "Observaciones": "Generado Auto desde IERIC (Con CER)."}])], ignore_index=True)
                    guardar_db(df_reclamos, "Reclamos")
                    st.success("✅ Reclamo enviado!")
            
            if c_btn2.button("🗑️ Borrar Última Quincena"): 
                st.session_state.quincenas.pop()
                st.rerun()

    # 👇 ACÁ AGREGAMOS EL CONTENIDO DE LAS PESTAÑAS NUEVAS 👇
    with tab_vacaciones:
        st.subheader("🏖️ Calculadora de Vacaciones")
        st.info("⏳ Próximamente disponible para su utilización.")
        
    with tab_sac:
        st.subheader("🎄 Cálculo de Sueldo Anual Complementario (SAC)")
        st.info("⏳ Próximamente disponible para su utilización.")

# ==========================================
# MÓDULO 5: REPOSITORIO DE RECLAMOS
# ==========================================
elif opcion == "5. ⚠️ Repositorio de Reclamos":
    st.title("⚠️ Gestión de Reclamos Gremiales")
    tab_r_nuevo, tab_r_bd = st.tabs(["➕ Ingresar Reclamo Manual", "📋 Historial de Reclamos"])
    
    with tab_r_nuevo:
        with st.form("f_reclamos", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                rn = st.text_input("Nombre Empleado:*")
                re_sel = st.selectbox("Empresa:", ["➕ Nueva..."] + lista_empresas_historicas)
                re_n = st.text_input("Si es Nueva, escríbala:")
                rm = st.text_input("Motivo del Reclamo:*")
            with col2:
                fi = st.date_input("Fecha Ingreso:", format="DD/MM/YYYY")
                ract = st.checkbox("🟢 Reclamo Activo (Anula fecha de fin)", value=True)
                ff = st.date_input("Fecha Finalización:", disabled=ract, format="DD/MM/YYYY")
            
            rresp = st.text_area("Respuesta/Resolución:")
            robs = st.text_area("Obs:")
            if st.form_submit_button("💾 Guardar Reclamo"):
                re_fin = re_n.strip() if re_sel == "➕ Nueva..." else re_sel
                if not rn or not rm or not re_fin: 
                    st.error("❌ Nombre, Empresa y Motivo obligatorios.")
                else:
                    df_reclamos = pd.concat([df_reclamos, pd.DataFrame([{"Nombre": rn, "Empresa": re_fin, "Motivo": rm, "Ingreso": fi.strftime("%d/%m/%Y"), "Estado": "Activo" if ract else "Finalizado", "Finalizacion": "En proceso" if ract else ff.strftime("%d/%m/%Y"), "Respuesta": rresp, "Observaciones": robs}])], ignore_index=True)
                    guardar_db(df_reclamos, "Reclamos")
                    st.success("Reclamo asentado!")
                    st.rerun()

    with tab_r_bd:
        st.dataframe(df_reclamos, use_container_width=True)
        if not df_reclamos.empty:
            ops = df_reclamos['Nombre'] + " - " + df_reclamos['Motivo']
            rel = st.selectbox("Eliminar:", [""] + ops.tolist())
            if st.button("🗑️ Eliminar") and rel:
                df_reclamos = df_reclamos.drop(df_reclamos.index[ops.tolist().index(rel)])
                guardar_db(df_reclamos, "Reclamos")
                st.success("Eliminado.")
                st.rerun()

# ==========================================
# MÓDULO 6: UOCRA MUJERES (FASE 3)
# ==========================================
elif opcion == "6. 💜 UOCRA Mujeres":
    # Inyectamos CSS para pintar el módulo de violeta sin romper el resto
    st.markdown("""
        <style>
        div.stTabs [data-baseweb="tab-list"] button {color: #4B0082;}
        div.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {border-bottom-color: #8A2BE2; color: #8A2BE2;}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='color: #8A2BE2;'>💜 Departamento UOCRA Mujeres</h1>", unsafe_allow_html=True)
    
    tab_cupo, tab_eventos = st.tabs(["👷‍♀️ Cupo Femenino en Obras", "📅 Eventos y Participaciones"])
    
    with tab_cupo:
        st.subheader("Asignación de Cupo Femenino")
        if df_obras.empty:
            st.warning("Aún no hay obras registradas en la base de datos.")
        else:
            opciones_obras_m = df_obras['Predio'].astype(str) + " (" + df_obras['Empresa'].astype(str) + ")"
            obra_m_sel = st.selectbox("Seleccione la Obra activa:", opciones_obras_m.tolist())
            
            if obra_m_sel:
                idx_m = opciones_obras_m[opciones_obras_m == obra_m_sel].index[0]
                dat_m = df_obras.loc[idx_m]
                tot_obreros = int(dat_m.get('Obreros', 0))
                mujeres_actual = int(dat_m.get('Mujeres', 0))
                porcentaje = (mujeres_actual / tot_obreros * 100) if tot_obreros > 0 else 0.0
                
                # Tarjetas Visuales de la Obra Seleccionada
                c_m1, c_m2, c_m3 = st.columns(3)
                with c_m1: st.markdown(f'<div class="tarjeta-kpi"><div class="kpi-titulo">Operarios Totales</div><div class="kpi-valor">{tot_obreros}</div></div>', unsafe_allow_html=True)
                with c_m2: st.markdown(f'<div class="tarjeta-kpi violeta"><div class="kpi-titulo">Mujeres Asignadas</div><div class="kpi-valor">{mujeres_actual}</div></div>', unsafe_allow_html=True)
                with c_m3: st.markdown(f'<div class="tarjeta-kpi violeta"><div class="kpi-titulo">% de Participación</div><div class="kpi-valor">{porcentaje:.1f}%</div></div>', unsafe_allow_html=True)
                
                with st.form("f_cupo"):
                    n_mujeres = st.number_input("Modificar Cantidad de Mujeres (Cupo):", min_value=0, step=1, value=mujeres_actual)
                    if st.form_submit_button("💾 Guardar / Actualizar Cupo"):
                        import time # Importamos el reloj para hacer una pausa visual
                        try:
                            # Forzamos que el dato sea entero para que Google Sheets lo tome perfecto
                            df_obras.at[idx_m, 'Mujeres'] = int(n_mujeres)
                            guardar_db(df_obras, "Obras")
                            
                            st.success("✅ ¡Dato guardado en Google Sheets! Actualizando tablero...")
                            time.sleep(1.5) # Frena la web 1.5 segundos para que leas el cartel
                            st.rerun() # Ahora sí, recarga para actualizar el gráfico
                        except Exception as e:
                            st.error(f"❌ Ocurrió un error al intentar guardar: {e}")
                        
        st.markdown("---")
        st.markdown("### 📋 Listado de Cumplimiento por Obra")
        if not df_obras.empty:
            df_cupo_view = df_obras[['Predio', 'Empresa', 'Obreros', 'Mujeres']].copy()
            df_cupo_view['% Participación'] = (df_cupo_view['Mujeres'] / df_cupo_view['Obreros'].replace(0, 1) * 100).round(2).astype(str) + "%"
            st.dataframe(df_cupo_view[df_cupo_view['Mujeres'] > 0], use_container_width=True)
    with tab_eventos:
        st.subheader("Agenda de Participaciones")
        acc_ev = st.radio("Acción Eventos:", ["➕ Nuevo Evento", "🗑️ Eliminar Evento"], horizontal=True)
        
        if acc_ev == "➕ Nuevo Evento":
            with st.form("f_n_evento", clear_on_submit=True):
                e_tit = st.text_input("Título de la Actividad / Evento:*")
                e_fec = st.date_input("Fecha del Evento:", format="DD/MM/YYYY")
                e_obs = st.text_area("Observaciones y Detalle:")
                
                if st.form_submit_button("💾 Guardar en Agenda"):
                    if not e_tit:
                        st.error("❌ El título de la actividad es obligatorio.")
                    else:
                        nuevo_ev = pd.DataFrame([{"Titulo": e_tit, "Fecha": e_fec.strftime("%d/%m/%Y"), "Observaciones": e_obs}])
                        df_eventos = pd.concat([df_eventos, nuevo_ev], ignore_index=True)
                        guardar_db(df_eventos, "Mujeres_Eventos")
                        st.success("✅ Evento agendado correctamente.")
                        st.rerun()
                        
        elif acc_ev == "🗑️ Eliminar Evento":
            if not df_eventos.empty:
                ops_ev = df_eventos['Titulo'] + " (" + df_eventos['Fecha'] + ")"
                ev_el = st.selectbox("Seleccione Evento a borrar:", [""] + ops_ev.tolist())
                if st.button("🗑️ Eliminar") and ev_el != "":
                    idx_el = ops_ev.tolist().index(ev_el)
                    df_eventos = df_eventos.drop(df_eventos.index[idx_el])
                    guardar_db(df_eventos, "Mujeres_Eventos")
                    st.success("Evento borrado.")
                    st.rerun()
        
        st.markdown("---")
        if not df_eventos.empty:
            st.dataframe(df_eventos, use_container_width=True)
# ==========================================
# MÓDULO 7: CONVENIOS POR EMPRESA (FASE 5)
# ==========================================
elif opcion == "7. 🤝 Convenios por Empresa":
    st.title("🤝 Repositorio de Convenios y Paritarias")
    st.markdown("Módulo exclusivo para la Comisión Directiva.")
    
    tab_n_conv, tab_ver_conv = st.tabs(["➕ Gestionar Convenio", "📋 Ver Convenios Cargados"])
    
    with tab_n_conv:
        acc_conv = st.radio("Acción:", ["➕ Nuevo Convenio", "✏️ Modificar", "🗑️ Eliminar"], horizontal=True)
        if acc_conv == "➕ Nuevo Convenio":
            with st.form("f_n_conv", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    c_emp = st.selectbox("Empresa:*", [""] + lista_empresas_historicas)
                    # 👇 ACÁ ESTABA EL ERROR: Decía c_cct, ahora dice c_vig 👇
                    c_vig = st.text_input("Vigencia (Ej: Marzo 2026 - Mayo 2026):")
                with col2:
                    c_monto = st.text_input("Monto Extra $:")
                    c_porc = st.text_input("Monto Extra %:")
                
                c_det = st.text_area("Detalles de Escala / CCT (Descripción):*")
                
                if st.form_submit_button("💾 Guardar Convenio"):
                    if not c_emp or not c_det:
                        st.error("❌ Empresa y Detalles son campos obligatorios.")
                    else:
                        nuevo_conv = pd.DataFrame([{
                            "Empresa": c_emp, "Detalle_Convenio": c_det, 
                            "monto $": c_monto, "Monto %": c_porc, "Vigencia": c_vig
                        }])
                        df_convenios = pd.concat([df_convenios, nuevo_conv], ignore_index=True)
                        guardar_db(df_convenios, "Convenios")
                        st.success("✅ Convenio registrado.")
                        st.rerun()
        elif acc_conv == "✏️ Modificar":
            if not df_convenios.empty:
                opciones_c = df_convenios['Empresa'] + " - " + df_convenios['Vigencia']
                c_ed = st.selectbox("Seleccione el Convenio:", opciones_c.tolist())
                if c_ed:
                    idx = opciones_c.tolist().index(c_ed)
                    dat = df_convenios.loc[idx]
                    with st.form("f_e_conv"):
                        col1, col2 = st.columns(2)
                        with col1:
                            e_emp = st.text_input("Empresa:*", value=str(dat.get('Empresa', '')))
                            e_vig = st.text_input("Vigencia:", value=str(dat.get('Vigencia', '')))
                        with col2:
                            e_monto = st.text_input("Monto Extra $:", value=str(dat.get('monto $', '')))
                            e_porc = st.text_input("Monto Extra %:", value=str(dat.get('Monto %', '')))
                        e_det = st.text_area("Detalles de Escala / CCT:*", value=str(dat.get('Detalle_Convenio', '')))
                        
                        if st.form_submit_button("🔄 Actualizar"):
                            df_convenios.at[idx, 'Empresa'] = e_emp
                            df_convenios.at[idx, 'Detalle_Convenio'] = e_det
                            df_convenios.at[idx, 'monto $'] = e_monto
                            df_convenios.at[idx, 'Monto %'] = e_porc
                            df_convenios.at[idx, 'Vigencia'] = e_vig
                            guardar_db(df_convenios, "Convenios")
                            st.success("✅ Actualizado.")
                            st.rerun()
                            
        elif acc_conv == "🗑️ Eliminar":
            if not df_convenios.empty:
                opciones_el = [""] + (df_convenios['Empresa'] + " - " + df_convenios['Vigencia']).tolist()
                c_el = st.selectbox("Borrar:", opciones_el)
                if st.button("🗑️ Eliminar") and c_el != "":
                    idx_el = opciones_el.index(c_el) - 1
                    df_convenios = df_convenios.drop(df_convenios.index[idx_el])
                    guardar_db(df_convenios, "Convenios")
                    st.success("Eliminado.")
                    st.rerun()

    with tab_ver_conv:
        st.write("Buscador de convenios por empresa.")
        busq_c = st.text_input("🔍 Buscar Empresa:", key="b_conv")
        df_mostrar_conv = df_convenios.copy()
        if busq_c:
            df_mostrar_conv = df_mostrar_conv[df_mostrar_conv['Empresa'].str.contains(busq_c, case=False, na=False)]
        st.dataframe(df_mostrar_conv, use_container_width=True)

# ==========================================
# MÓDULO 8: TABLERO DE CONTROL
# ==========================================
elif opcion == "8. 📊 Tablero de Control":
    st.title("📊 Tablero de Control y Estadísticas")
    st.markdown("Visión analítica general de la Jurisdicción Esteban Echeverría.")
    
    # CSS Súper Agresivo para anular el diseño por defecto y armar tarjetas reales
    st.markdown("""
        <style>
        .tarjeta-kpi {
            background-color: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1);
            border-left: 8px solid #0033A0;
            text-align: center;
            margin-bottom: 20px;
        }
        .tarjeta-kpi.verde { border-left-color: #28a745; }
        .tarjeta-kpi.naranja { border-left-color: #fd7e14; }
        .tarjeta-kpi.violeta { border-left-color: #8A2BE2; }
        .kpi-titulo {
            color: #6c757d;
            font-size: 1.1rem;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .kpi-valor {
            color: #212529;
            font-size: 3.5rem;
            font-weight: 900;
            margin: 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 1. MÉTRICAS PRINCIPALES
    total_obras = len(df_obras) if not df_obras.empty else 0
    obras_activas = len(df_obras[df_obras['Estado'] == 'Activa']) if not df_obras.empty else 0
    total_obreros = int(df_obras['Obreros'].sum()) if not df_obras.empty else 0
    reclamos_activos = len(df_reclamos[df_reclamos['Estado'] == 'Activo']) if not df_reclamos.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="tarjeta-kpi"><div class="kpi-titulo">🏗️ Obras Totales</div><div class="kpi-valor">{total_obras}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="tarjeta-kpi verde"><div class="kpi-titulo">🟢 Obras Activas</div><div class="kpi-valor">{obras_activas}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="tarjeta-kpi"><div class="kpi-titulo">👷‍♂️ Compañeros</div><div class="kpi-valor">{total_obreros}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="tarjeta-kpi naranja"><div class="kpi-titulo">🚨 Reclamos</div><div class="kpi-valor">{reclamos_activos}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 2. GRÁFICOS Y CUPO
    c_graf1, c_graf2 = st.columns(2)
    
    with c_graf1:
        st.subheader("Compañeros por Empresa (Top 5)")
        if not df_obras.empty and total_obreros > 0:
            df_obreros_emp = df_obras.groupby('Empresa')['Obreros'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(df_obreros_emp, color="#0033A0")
        else:
            st.info("No hay datos suficientes para graficar.")

    with c_graf2:
        st.subheader("💜 Impacto Cupo Femenino")
        if not df_obras.empty:
            total_mujeres = int(df_obras['Mujeres'].sum())
            porc_general = (total_mujeres / total_obreros * 100) if total_obreros > 0 else 0.0
            
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                st.markdown(f'<div class="tarjeta-kpi violeta"><div class="kpi-titulo">Compañeras</div><div class="kpi-valor">{total_mujeres}</div></div>', unsafe_allow_html=True)
            with c_m2:
                st.markdown(f'<div class="tarjeta-kpi violeta"><div class="kpi-titulo">Cupo Global</div><div class="kpi-valor">{porc_general:.1f}%</div></div>', unsafe_allow_html=True)
# ==========================================
# MÓDULO 9: GALERÍA MULTIMEDIA
# ==========================================
elif opcion == "9. 📸 Galería Multimedia":
    st.title("📸 Galería de Obras y Eventos")
    st.markdown("Repositorio Audiovisual.")
    st.info("💡 Haga clic en cualquier imagen para verla en alta resolución en una pestaña nueva.")
    
    st.markdown("---")
    
    tab_fotos, tab_videos = st.tabs(["🖼️ Fotografías", "🎥 Videos"])
    
    with tab_fotos:
        st.subheader("Álbum de Marchas, Eventos y Asambleas")
        
        # LISTA DE IDs: Solo tenés que agregar o quitar IDs acá adentro en el futuro.
        fotos_ids = [
            "12FISPzadXqVBHOAoFaq8hh-VshWV7AUY",
            "1OJosCkzy6nf-IN2J1t0hFlz72lC5M9Er",
            "1LBWJrOI-f5PC-lLmplOvgFy8t2-HQUeW",
            "1qpcz7hPiW65yBRcdy6nN_DC5kWdN8LQN",
            "1pLQAd5Jvv-BFtjyT1UV0yP-SfYRKpD9r",
            "1sCFFciZmY1jgrKMxahFtqd5_dkbqmap6",
            "1oQdTetQlS2zB56jzip1ZAAP22gg2QeRT",
            "1yWUA1UgUfubgphPAAGow2orpSRN0pDxE",
            "1-CdsMO60gIWtm0TRRguFhO7b4TwWmN0v",
            "1922DnTBV6ySICImt7Z4FA2rqeHhf7aY0",
            "1CsiQxdHK8RiilirqZ5lKxUuy5l3jsTSs",
            "1oBKTFsxJQTdqg1BA0B_lrj2iQC_RT67-"
        ]
        
        # Motor que genera la grilla de 3 columnas automáticamente
        for i in range(0, len(fotos_ids), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(fotos_ids):
                    img_id = fotos_ids[i+j]
                    url_min = f"https://drive.google.com/thumbnail?id={img_id}&sz=w1000"
                    url_full = f"https://drive.google.com/file/d/{img_id}/view?usp=sharing"
                    
                    # Dibujamos la imagen con borde, sombra y espacio inferior (margin-bottom)
                    cols[j].markdown(f'<a href="{url_full}" target="_blank"><img src="{url_min}" style="width:100%; border-radius:10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.2); margin-bottom: 20px;"></a>', unsafe_allow_html=True)
            
    with tab_videos:
        st.subheader("Videos")
        
        # ID del Video que me pasaste
        video_id = "1hB31u59Blm5TlvM5RKxbls3RXdWpK-MH"
        
        # Usamos un iframe para que el video de Drive se pueda reproducir dentro de la app
        st.markdown(f'''
            <iframe src="https://drive.google.com/file/d/{video_id}/preview" 
            width="100%" height="600" style="border-radius:15px; border:none; box-shadow: 0px 8px 20px rgba(0,0,0,0.3);">
            </iframe>
        ''', unsafe_allow_html=True)
        
        st.caption("▶️ Dele play al video para reproducirlo aquí mismo, o haga clic en el ícono de 'ventana emergente' arriba a la derecha del reproductor para verlo en pantalla completa.")
