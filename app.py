import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import requests
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io

st.markdown("""
    <style>
    /* 1. FONDO GLOBAL DE LA APLICACIÓN */
    .stApp {
        background-image: url("https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/main/banner_uocra.jpg"); 
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* 2. CAJA BLANCA SEMITRANSPARENTE (Protege la lectura de los módulos) */
    .block-container {
        background-color: rgba(255, 255, 255, 0.92) !important;
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
        border: 1px solid #000000 !important;
        border-radius: 6px !important;
        background-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN Y MEMORIA ---
if 'usuario_rol' not in st.session_state:
    st.session_state.usuario_rol = None

if st.session_state.usuario_rol is None:
    st.markdown("""
        <style>
        .stApp {
            background-image: url("https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/main/banner_uocra.jpg");
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
    
    URL_DEL_EXCEL = "https://docs.google.com/spreadsheets/d/15_0fpPr90DAJsivWACnFNaGXB1Eb1GaOFh4j-OfDnDU/edit?gid=1143014109#gid=1143014109" 
    
    DOC = client.open_by_url(URL_DEL_EXCEL)
except Exception as e:
    st.error(f"⚠️ Error técnico real: {e}")
    st.stop()

# --- FUNCIONES DE BASE DE DATOS EN LA NUBE ---
@st.cache_data(ttl=600)
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
        df_limpio = df.fillna("")
        sheet = DOC.worksheet(hoja_nombre)
        sheet.clear()
        datos_a_subir = [df_limpio.columns.values.tolist()] + df_limpio.values.tolist()
        sheet.update(values=datos_a_subir, range_name="A1")
        st.cache_data.clear() 
    except Exception as e:
        st.error(f"Error técnico guardando en {hoja_nombre}: {e}")

# --- CARGA GLOBAL Y EXTRACCIÓN DE DATOS ---
df_obras = cargar_db("Obras", ["Obra_ID", "Predio", "Empresa", "Delegado", "Obreros", "Estado", "Latitud", "Longitud", "Jurisdiccion", "Jurisdiccion_R", "Mujeres"])
if 'Mujeres' in df_obras.columns: 
    df_obras['Mujeres'] = pd.to_numeric(df_obras['Mujeres'], errors='coerce').fillna(0)
if 'Obreros' in df_obras.columns: 
    df_obras['Obreros'] = pd.to_numeric(df_obras['Obreros'], errors='coerce').fillna(0)
df_cierres = cargar_db("Cierres_Quincenales", ["Empresa", "Quincena", "Fechas"])
df_galeria = cargar_db("Galeria", ["Fecha", "Titulo", "Tipo", "Link"])
df_predios = cargar_db("Predios", ["Nombre", "Latitud", "Longitud", "Radio_KM", "Observaciones"])
for col in ['Latitud', 'Longitud', 'Radio_KM']:
    if col in df_predios.columns:
        df_predios[col] = pd.to_numeric(df_predios[col], errors='coerce').fillna(0.0)
df_documentos = cargar_db("Documentos", ["Titulo", "Fecha", "Vigencia", "Observaciones", "Link_PDF"])  
df_delegados = cargar_db("Delegados", ["Nombre", "CUIL", "Celular", "Domicilio", "Nacimiento", "Correo", "Observacion"])
df_contactos = cargar_db("Contactos", ["Nombre", "Cargo", "Empresa", "Observaciones"])
df_reclamos = cargar_db("Reclamos", ["Nombre", "Empresa", "Motivo", "Ingreso", "Estado", "Finalizacion", "Respuesta", "Observaciones"])
df_eventos = cargar_db("Mujeres_Eventos", ["Titulo", "Fecha", "Observaciones"])
df_convenios = cargar_db("Convenios", ["Empresa", "Detalle_Convenio", "monto $", "Monto %", "Vigencia"])
df_propuestas = cargar_db("Propuestas", ["Fecha", "Usuario", "Propuesta", "Estado"])
df_cerebro = cargar_db("Cerebro_IA", ["Fecha", "Regla", "Contexto"])
df_puntos_extra = cargar_db("Puntos_Extra", ["Nombre", "Latitud", "Longitud", "Color", "Observacion"])
if not df_puntos_extra.empty:
    df_puntos_extra['Latitud'] = pd.to_numeric(df_puntos_extra['Latitud'], errors='coerce').fillna(0.0)
    df_puntos_extra['Longitud'] = pd.to_numeric(df_puntos_extra['Longitud'], errors='coerce').fillna(0.0)

lista_predios_historicos = sorted(df_predios['Nombre'].dropna().astype(str).tolist()) if not df_predios.empty else []
lista_empresas_historicas = sorted(list(set(pd.concat([df_obras['Empresa'], df_contactos['Empresa'], df_reclamos['Empresa'], df_convenios['Empresa']]).dropna().astype(str).tolist())))
lista_delegados_nombres = df_delegados['Nombre'].tolist() if not df_delegados.empty else []

lista_jurisdicciones = ["Esteban Echeverría", "Ezeiza", "Cañuelas", "Roque Pérez", "Lobos", "Saladillo", "Monte", "General Belgrano", "Las Heras", "Navarro"]
lista_estados = ["Activa", "Intervenida", "Finalizada", "Interrumpida"]

# --- FASE 4: CONEXIÓN API BCRA (CÁLCULO CER) ---
@st.cache_data(ttl=86400)
def obtener_cer(fecha_str=None):
    try:
        token = st.secrets["BCRA_TOKEN"]
        headers = {'Authorization': f'Bearer {token}'}
        url = "https://api.estadisticasbcra.com/cer"
        respuesta = requests.get(url, headers=headers, timeout=10)
        
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if not datos: return None
            if fecha_str:
                fecha_buscada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                for item in reversed(datos):
                    fecha_item = datetime.strptime(item['d'], "%Y-%m-%d").date()
                    if fecha_item <= fecha_buscada:
                        return float(item['v'])
                return None 
            else:
                return float(datos[-1]['v'])
        return None
    except Exception as e:
        return None

# --- FASE 5: CONEXIÓN API FERIADOS Y CALENDARIO MODAL ---
@st.cache_data(ttl=86400)
def obtener_feriados_argentina():
    anio_actual = datetime.now().year
    url = f"https://nolaborables.com.ar/api/v2/feriados/{anio_actual}"
    lista_fechas = []
    
    # 1. Intentamos traer los feriados de la API
    try:
        respuesta = requests.get(url, timeout=5)
        if respuesta.status_code == 200:
            datos_api = respuesta.json()
            if len(datos_api) > 0:
                for f in datos_api:
                    lista_fechas.append({
                        "motivo": f["motivo"], 
                        "dia": f["dia"], 
                        "mes": f["mes"], 
                        "tipo": "Feriado Nacional",
                        "color": "#28a745"
                    })
    except:
        pass
        
# 1. BASE DE DATOS NACIONAL 2026 (Feriados Inamovibles, Trasladables y Turísticos)
    feriados_fijos = [
        {"motivo": "Año Nuevo", "dia": 1, "mes": 1, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Carnaval", "dia": 16, "mes": 2, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Carnaval", "dia": 17, "mes": 2, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Fines turísticos (Puente)", "dia": 23, "mes": 3, "tipo": "Día no laborable", "color": "#fd7e14"},
        {"motivo": "Día Nacional de la Memoria por la Verdad y la Justicia", "dia": 24, "mes": 3, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Veterano y Caídos en Malvinas / Jueves Santo", "dia": 2, "mes": 4, "tipo": "Inamovible / No laborable", "color": "#28a745"},
        {"motivo": "Viernes Santo", "dia": 3, "mes": 4, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Día del Trabajador", "dia": 1, "mes": 5, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Día de la Revolución de Mayo", "dia": 25, "mes": 5, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Paso a la Inmortalidad del Gral. Güemes", "dia": 15, "mes": 6, "tipo": "Feriado trasladable", "color": "#28a745"},
        {"motivo": "Paso a la Inmortalidad del Gral. Manuel Belgrano", "dia": 20, "mes": 6, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Día de la Independencia", "dia": 9, "mes": 7, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Fines turísticos (Puente)", "dia": 10, "mes": 7, "tipo": "Día no laborable", "color": "#fd7e14"},
        {"motivo": "Paso a la Inmortalidad del Gral. San Martín", "dia": 17, "mes": 8, "tipo": "Feriado trasladable", "color": "#28a745"},
        {"motivo": "Día del Respeto a la Diversidad Cultural", "dia": 12, "mes": 10, "tipo": "Feriado trasladable", "color": "#28a745"},
        {"motivo": "Día de la Soberanía Nacional", "dia": 23, "mes": 11, "tipo": "Feriado trasladable", "color": "#28a745"},
        {"motivo": "Fines turísticos (Puente)", "dia": 7, "mes": 12, "tipo": "Día no laborable", "color": "#fd7e14"},
        {"motivo": "Inmaculada Concepción de María", "dia": 8, "mes": 12, "tipo": "Feriado inamovible", "color": "#28a745"},
        {"motivo": "Navidad", "dia": 25, "mes": 12, "tipo": "Feriado inamovible", "color": "#28a745"}
    ]
    lista_fechas.extend(feriados_fijos)

    # 3. Sumamos SIEMPRE las fechas gremiales de la UOCRA
    fechas_uocra = [
        {"motivo": "Día del Obrero de la Construcción (CCT 76/22)", "dia": 22, "mes": 4, "tipo": "Día Gremial", "color": "#0033A0"},
        {"motivo": "Día de la Lealtad Peronista", "dia": 17, "mes": 10, "tipo": "Fecha Histórica", "color": "#0033A0"},
        {"motivo": "Día Internacional de la Mujer Trabajadora", "dia": 8, "mes": 3, "tipo": "Fecha Histórica", "color": "#8A2BE2"}
    ]
    lista_fechas.extend(fechas_uocra)
    
    # Ordenamos cronológicamente
    lista_fechas.sort(key=lambda x: (x["mes"], x["dia"]))
    return lista_fechas
    
    fechas_uocra = [
        {"motivo": "Día del Obrero de la Construcción (CCT 76/22)", "dia": 22, "mes": 4, "tipo": "Día Gremial", "color": "#0033A0"},
        {"motivo": "Día de la Lealtad Peronista", "dia": 17, "mes": 10, "tipo": "Fecha Histórica", "color": "#0033A0"},
        {"motivo": "Día Internacional de la Mujer Trabajadora", "dia": 8, "mes": 3, "tipo": "Fecha Histórica", "color": "#8A2BE2"}
    ]
    lista_fechas.extend(fechas_uocra)
    lista_fechas.sort(key=lambda x: (x["mes"], x["dia"]))
    return lista_fechas

# ESTA ES LA MAGIA: @st.dialog crea una ventana flotante (Modal)
@st.dialog("📅 Calendario Gremial y Feriados Nacionales", width="large")
def abrir_calendario_flotante():
    hoy = datetime.now()
    anio_actual = hoy.year
    feriados = obtener_feriados_argentina()
    nombres_meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    # ==========================================
    # 1. RADAR: PRÓXIMOS 3 EVENTOS
    # ==========================================
    st.markdown("<h4 style='color: #0033A0;'>⏳ Próximos Feriados y Fechas Clave</h4>", unsafe_allow_html=True)
    
    proximos_eventos = []
    if feriados:
        for f in feriados:
            try:
                # Armamos la fecha real del feriado para compararla con la de hoy
                fecha_f = datetime(anio_actual, f["mes"], f["dia"])
                if fecha_f.date() >= hoy.date():
                    proximos_eventos.append(f)
            except ValueError:
                pass # Por si hay errores de fecha bisiesta
        
        # Cortamos la lista para mostrar solo los siguientes 3
        proximos_eventos = proximos_eventos[:3]

    if not proximos_eventos:
        st.info("No hay feriados o eventos registrados próximamente.")
    else:
        # Creamos la cantidad de columnas exacta según los eventos que queden
        cols_prox = st.columns(len(proximos_eventos))
        for i, f in enumerate(proximos_eventos):
            mes_texto = nombres_meses[f["mes"]]
            with cols_prox[i]:
                st.markdown(f'''
                <div style="border-left: 5px solid {f['color']}; background-color: white; padding: 15px; border-radius: 12px; margin-bottom: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.08);">
                    <div style="color: {f['color']}; font-weight: 900; font-size: 1.1rem; margin-bottom: 5px;">{f['dia']} de {mes_texto}</div>
                    <div style="font-weight: bold; color: #333; font-size: 0.9rem;">{f['motivo']}</div>
                    <div style="font-size: 0.75rem; color: #666; text-transform: uppercase; margin-top: 5px;">{f['tipo']}</div>
                </div>
                ''', unsafe_allow_html=True)

    st.markdown("---")
    
    # ==========================================
    # 2. CIERRES QUINCENALES POR EMPRESA
    # ==========================================
    st.markdown("<h4 style='color: #0033A0;'>🏭 Cierres Quincenales por Empresa</h4>", unsafe_allow_html=True)
    
    if not df_cierres.empty:
        empresas_con_cierre = sorted(df_cierres['Empresa'].astype(str).str.strip().dropna().unique().tolist())
        empresas_con_cierre = [emp for emp in empresas_con_cierre if emp != ""]

        if empresas_con_cierre:
            empresa_seleccionada = st.selectbox("Seleccione la empresa registrada para ver su cronograma:", [""] + empresas_con_cierre)

            if empresa_seleccionada:
                df_filtrado = df_cierres[df_cierres['Empresa'] == empresa_seleccionada]
                
                st.markdown(f"<p style='text-align:center; color:#666; font-size:0.95rem; margin-top: 10px;'>Cronograma oficial de <b>{empresa_seleccionada}</b></p>", unsafe_allow_html=True)
                
                # Grilla de 4 columnas
                cols_q = st.columns(4)
                
                for i, (_, row) in enumerate(df_filtrado.iterrows()):
                    q_nom = str(row.get('Quincena', ''))
                    q_fec = str(row.get('Fechas', ''))
                    
                    tarjeta_q = f"""
                    <div style="border-top: 4px solid #0033A0; background-color: #f4f6f9; padding: 12px; border-radius: 6px; margin-bottom: 12px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="color: #0033A0; font-weight: 900; font-size: 0.85rem; text-transform: uppercase;">{q_nom}</div>
                        <div style="color: #333; font-weight: 600; font-size: 0.8rem; margin-top: 5px;">{q_fec}</div>
                    </div>
                    """
                    cols_q[i % 4].markdown(tarjeta_q, unsafe_allow_html=True)
        else:
            st.info("No hay cronogramas cargados. Ingrese los datos en la pestaña 'Cierres_Quincenales' del Excel.")
    else:
        st.info("La base de cierres quincenales está vacía o no se detectó la pestaña 'Cierres_Quincenales'.")

    st.markdown("---")
    
    # ==========================================
    # 3. AGENDA ANUAL COMPLETA (ACORDEÓN)
    # ==========================================
    with st.expander("🗓️ Ver Calendario Anual Completo (Todos los feriados)", expanded=False):
        if not feriados:
            st.warning("⚠️ No se pudo conectar a la base de feriados en este momento.")
        else:
            col_izq, col_der = st.columns(2)
            for i, f in enumerate(feriados):
                mes_texto = nombres_meses[f["mes"]]
                tarjeta_html = f"""
                <div style="border-left: 5px solid {f['color']}; background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <div style="color: {f['color']}; font-weight: 900; font-size: 1.1rem; margin-bottom: 5px;">{f['dia']} de {mes_texto}</div>
                    <div style="font-weight: bold; color: #333;">{f['motivo']}</div>
                    <div style="font-size: 0.8rem; color: #666; text-transform: uppercase;">{f['tipo']}</div>
                </div>
                """
                if i % 2 == 0:
                    col_izq.markdown(tarjeta_html, unsafe_allow_html=True)
                else:
                    col_der.markdown(tarjeta_html, unsafe_allow_html=True)

# --- FUNCIÓN PARA SUBIR ARCHIVOS A GOOGLE CLOUD STORAGE ---
def subir_archivo_drive(archivo_subido, nombre_archivo):
    try:
        import json
        from google.oauth2 import service_account
        from google.cloud import storage
        import streamlit as st
        
        # Leemos tus credenciales de Streamlit
        creds_json = st.secrets["gcp_service_account"]
        creds_dict = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        
        # Conectamos con el motor de Storage
        storage_client = storage.Client(credentials=creds, project=creds_dict["project_id"])
        
        # Tu balde oficial
        nombre_balde = "uocra-mg-archivos-2026" 
        bucket = storage_client.bucket(nombre_balde)
        
        # Preparamos el archivo
        blob = bucket.blob(nombre_archivo)
        
        # Lo subimos
        blob.upload_from_string(
            archivo_subido.getvalue(), 
            content_type=archivo_subido.type
        )
        
        # Devolvemos el link público directo
        return blob.public_url
        
    except Exception as e:
        import streamlit as st
        st.error(f"Error al subir a Cloud Storage: {e}")
        return None
        
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

    # 1. BOTONES OPERATIVOS JUNTOS
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.usuario_rol = None
        st.rerun()
        
    st.markdown("---")
        
    # 2. COMISIÓN DIRECTIVA Y NAVEGACIÓN
    with st.expander("🏛️ Comisión Directiva", expanded=False):
        st.markdown("""
        **1- Sec. Gral:** Roberto Morelli
        
        **2- Sec. Adj:** Alejandro Benitez
        
        **3- Sec. Org:** Rolando Civile
        
        **4- Sec. Actas:** Ruben Fernandez
        
        **5- Sec. Finanzas:** Roberto Oviedo
        """)
        opciones_totales = [
        "1. 🗺️ Mapa Territorial", "2. 📥 Carga de Datos (ABM)", 
        "3. 📋 Nóminas", "4. 🧮 Calculadoras", "5. ⚠️ Reclamos",
        "6. 💜 UOCRA Mujeres", "7. 🤝 Convenios y Documentación", "8. 📊 Estadísticas",
        "9. 📸 Galería Multimedia", "10. 🤖 Chat GPT UOCRA", "11. 🧹 Auditoría"
    ]
   
    if st.session_state.usuario_rol == "Restringido":
        opciones_permitidas = ["1. 🗺️ Mapa Territorial", "3. 📋 Nóminas", "4. 🧮 Calculadoras", "6. 💜 UOCRA Mujeres", "7. 🤝 Convenios y Documentación", "8. 📊 Estadísticas", "9. 📸 Galería Multimedia", "10. 🤖 Chat GPT UOCRA", "11. 🧹 Auditoría"]
    else:
        opciones_permitidas = opciones_totales
        
    opcion = st.radio("Navegación:", opciones_permitidas)
    
    # 3. ENLACES Y REDES
    st.markdown("---") 
    st.caption("🔗 ENLACES ÚTILES")
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
    st.caption("📱 REDES SOCIALES")
    st.markdown("""
    <div style='text-align: center; margin-bottom: 15px;'>
        <a href='https://www.instagram.com/uocra.juventud.montegrande?igsh=MW5rbGU3c3M4M3F5' target='_blank' style='text-decoration: none;'>
            <img src='https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Instagram_icon.png/600px-Instagram_icon.png' width='45px' style='vertical-align: middle; margin-right: 10px;'>
            <span style='font-size: 1.1rem; font-weight: bold; color: #e1306c; vertical-align: middle;'>Instagram</span>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # 4. BOTÓN DEL CALENDARIO ABAJO DE TODO
    st.markdown("---")
    if st.button("📅 Calendario y Feriados", type="primary", use_container_width=True):
        abrir_calendario_flotante()
        
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
            # 👇 ESCUDO ANTIBALAS: Intentamos convertir las coordenadas a números reales 👇
            try:
                lat = float(row.get('Latitud'))
                lon = float(row.get('Longitud'))
            except (ValueError, TypeError):
                # Si la celda está vacía, tiene un espacio, o texto, ignoramos esta fila y seguimos
                continue 
            
            predio, empresa = str(row.get('Predio', '')).strip(), str(row.get('Empresa', '')).strip()
            
            # Verificamos que las coordenadas no sean cero (0.0) y que haya datos de empresa
            if pd.notna(lat) and pd.notna(lon) and (lat != 0.0 and lon != 0.0) and (predio not in ["", "nan"] or empresa not in ["", "nan"]):
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
elif opcion == "3. 📋 Nóminas":
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
elif opcion == "5. ⚠️ Reclamos":
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
# MÓDULO 7: CONVENIOS Y DOCUMENTACIÓN
# ==========================================
elif opcion == "7. 🤝 Convenios y Documentación":
    st.title("🤝 Convenios y Documentación")
    st.markdown("Repositorio oficial de actas, paritarias y documentos de la Seccional.")
    
    seccion_elegida = st.radio("Seleccione el apartado a gestionar:", ["1️⃣ Convenios", "2️⃣ Documentación"], horizontal=True)
    st.markdown("---")
    
    if seccion_elegida == "1️⃣ Convenios":
        tab_n_conv, tab_ver_conv = st.tabs(["➕ Gestionar Convenio", "📋 Ver Convenios Cargados"])
        
        with tab_n_conv:
            acc_conv = st.radio("Acción:", ["➕ Nuevo Convenio", "✏️ Modificar", "🗑️ Eliminar"], horizontal=True)
            
            if acc_conv == "➕ Nuevo Convenio":
                with st.form("f_n_conv", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        c_emp = st.selectbox("Empresa:*", [""] + lista_empresas_historicas)
                        c_vig = st.text_input("Vigencia (Ej: Marzo 2026 - Mayo 2026):")
                    with col2:
                        c_monto = st.text_input("Monto Extra $:")
                        c_porc = st.text_input("Monto Extra %:")
                    
                    c_det = st.text_area("Detalles de Escala / CCT (Descripción):*")
                    archivo_pdf = st.file_uploader("📄 Arrastrá el PDF del Convenio aquí", type=["pdf"],
                    accept_multiple_files=True)
                    
                    if st.form_submit_button("💾 Guardar Convenio"):
                        if not c_emp or not c_det:
                            st.error("❌ Empresa y Detalles son obligatorios.")
                        else:
                            c_link = "" 
                            if archivo_pdf is not None:
                                with st.spinner("Subiendo archivo a Google Drive..."):
                                    nombre_limpio = f"Convenio_{c_emp}_{c_vig}.pdf".replace(" ", "_")
                                    c_link = subir_archivo_drive(archivo_pdf, nombre_limpio)
                                    if c_link:
                                        st.success("✅ Archivo subido con éxito.")
                                    else:
                                        st.error("⚠️ Error al subir el PDF.")
                            
                            nuevo_conv = pd.DataFrame([{
                                "Empresa": c_emp, "Detalle_Convenio": c_det, 
                                "monto $": c_monto, "Monto %": c_porc, "Vigencia": c_vig, "Link_PDF": c_link
                            }])
                            df_convenios = pd.concat([df_convenios, nuevo_conv], ignore_index=True)
                            guardar_db(df_convenios, "Convenios")
                            st.success("✅ Convenio registrado exitosamente.")
                            import time
                            time.sleep(2)
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
                            e_link = st.text_input("🔗 Archivo de Respaldo (Link PDF):", value=str(dat.get('Link_PDF', '')))
                            
                            if st.form_submit_button("🔄 Actualizar"):
                                df_convenios.at[idx, 'Empresa'] = e_emp
                                df_convenios.at[idx, 'Detalle_Convenio'] = e_det
                                df_convenios.at[idx, 'monto $'] = e_monto
                                df_convenios.at[idx, 'Monto %'] = e_porc
                                df_convenios.at[idx, 'Vigencia'] = e_vig
                                df_convenios.at[idx, 'Link_PDF'] = e_link
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
            busq_c = st.text_input("🔍 Buscar Empresa:", key="b_conv")
            df_mostrar_conv = df_convenios.copy()
            if busq_c:
                df_mostrar_conv = df_mostrar_conv[df_mostrar_conv['Empresa'].str.contains(busq_c, case=False, na=False)]
            
            for _, row in df_mostrar_conv.iterrows():
                with st.expander(f"🏢 {row.get('Empresa', '')} | Vigencia: {row.get('Vigencia', '')}"):
                    st.write(f"**Detalle:** {row.get('Detalle_Convenio', '')}")
                    st.write(f"**Monto $:** {row.get('monto $', '-')} | **Monto %:** {row.get('Monto %', '-')}")
                    link_pdf = str(row.get('Link_PDF', '')).strip()
                    if link_pdf and link_pdf.startswith("http"):
                        st.markdown(f'<a href="{link_pdf}" target="_blank" style="display: inline-block; padding: 8px 16px; background-color: #0033A0; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">📄 Abrir Documento PDF</a>', unsafe_allow_html=True)

    elif seccion_elegida == "2️⃣ Documentación":
        tab_subir, tab_ver = st.tabs(["📤 Cargar Documento", "📚 Ver Documentación"])
        
        with tab_subir:
            with st.form("form_doc", clear_on_submit=True):
                d_tit = st.text_input("Título del Documento:*")
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    d_fec = st.date_input("Fecha:", format="DD/MM/YYYY")
                with col_d2:
                    d_vig = st.text_input("Vigencia (Opcional):")
                    
                d_obs = st.text_area("Observaciones (Opcional):")
                archivo_doc = st.file_uploader("📄 Arrastrá el PDF del Documento aquí", type=["pdf"])
                
                if st.form_submit_button("💾 Guardar Documento"):
                    if not d_tit:
                        st.error("❌ El Título es obligatorio.")
                    else:
                        d_link = ""
                        if archivo_doc is not None:
                            with st.spinner("Subiendo archivo a Google Drive..."):
                                nombre_limpio = f"Doc_{d_tit}.pdf".replace(" ", "_")
                                d_link = subir_archivo_drive(archivo_doc, nombre_limpio)
                                if d_link:
                                    st.success("✅ Archivo subido con éxito.")
                                else:
                                    st.error("⚠️ Error al subir el PDF.")
                                    
                        nuevo_doc = pd.DataFrame([{
                            "Titulo": d_tit, "Fecha": d_fec.strftime("%d/%m/%Y"), 
                            "Vigencia": d_vig, "Observaciones": d_obs, "Link_PDF": d_link
                        }])
                        df_documentos = pd.concat([df_documentos, nuevo_doc], ignore_index=True)
                        guardar_db(df_documentos, "Documentos")
                        st.success("✅ ¡Documento guardado!")
                        import time
                        time.sleep(2)
                        st.rerun()

        with tab_ver:
            if df_documentos.empty:
                st.info("No hay documentos subidos todavía.")
            else:
                b_doc = st.text_input("🔍 Buscar por Título:")
                df_doc_view = df_documentos.copy()
                if b_doc:
                    df_doc_view = df_doc_view[df_doc_view['Titulo'].str.contains(b_doc, case=False, na=False)]
                
                # Usamos iterrows y sacamos el 'idx' (Índice real del Excel) para saber exactamente qué fila borrar
                for idx, doc in df_doc_view.iterrows():
                    
                    # 1. Dibujamos la tarjeta visual del documento
                    st.markdown(f"""
                    <div style="border-left: 5px solid #0033A0; padding: 15px; background-color: #f8f9fa; border-radius: 8px; margin-top: 15px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="color: #666; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">📅 {doc.get('Fecha', '')} | Vigencia: {doc.get('Vigencia', 'N/A')}</div>
                        <div style="color: #0033A0; font-size: 1.2rem; font-weight: 900; margin-top: 5px;">{doc.get('Titulo', '')}</div>
                        <div style="color: #333; margin-top: 5px;"><i>"{doc.get('Observaciones', '')}"</i></div>
                        <br>
                        <a href="{doc.get('Link_PDF', '#')}" target="_blank" style="background-color: #28a745; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 0.9rem;">📥 Abrir Archivo</a>
                    </div>
                    """, unsafe_allow_html=True)

                    # 2. CAPA DE SEGURIDAD: Chequeamos el rol del usuario
                    usuario_actual = st.session_state.get("usuario_rol", "")
                    
                    if usuario_actual == "Admin":
                        # Le ponemos una llave única (key) al botón usando el número de fila (idx)
                        if st.button("🗑️ Eliminar", key=f"del_doc_{idx}"):
                            # Borramos la fila exacta del dataframe original
                            df_documentos = df_documentos.drop(idx)
                            # Guardamos en la base de datos
                            guardar_db(df_documentos, "Documentos")
                            st.success("✅ Documento eliminado del sistema.")
                            import time
                            time.sleep(1)
                            st.rerun()
                            
                    st.write("") # Un espacio en blanco para separar el siguiente documento

# ==========================================
# MÓDULO 8: TABLERO DE CONTROL
# ==========================================
elif opcion == "8. 📊 Estadísticas":
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
    st.markdown("Repositorio Audiovisual institucional y operativo.")
    
    # 3 Pestañas para organizar la visualización y la carga
    tab_fotos, tab_videos, tab_subir = st.tabs(["🖼️ Fotografías", "🎥 Videos", "📤 Subir Material"])
    
    # --- PESTAÑA 1: FOTOS ---
    with tab_fotos:
        st.subheader("Álbum de Marchas, Eventos y Asambleas")
        df_fotos = df_galeria[df_galeria['Tipo'] == 'Foto'].copy()
        
        if df_fotos.empty:
            st.info("No hay fotografías subidas en la base de datos.")
        else:
            # Invertimos para ver las más nuevas arriba
            df_fotos = df_fotos.iloc[::-1].reset_index()
            
            # Motor que genera la grilla de 3 columnas automáticamente
            for i in range(0, len(df_fotos), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(df_fotos):
                        row = df_fotos.iloc[i+j]
                        idx_real = row['index'] # Índice para poder borrar
                        link_img = str(row.get('Link', '')).strip()
                        
                        with cols[j]:
                            # Dibujamos la foto con su título y fecha
                            if link_img.startswith("http"):
                                st.image(link_img, caption=f"📍 {row.get('Titulo', '')} ({row.get('Fecha', '')})", use_container_width=True)
                            
                            # CAPA DE SEGURIDAD VIP: Solo Civile2026 (Admin) ve el tachito
                            usuario_actual = st.session_state.get("usuario_rol", "")
                            if usuario_actual == "Admin":
                                if st.button("🗑️ Eliminar", key=f"del_f_{idx_real}"):
                                    df_galeria = df_galeria.drop(idx_real)
                                    guardar_db(df_galeria, "Galeria")
                                    st.success("Foto eliminada.")
                                    import time
                                    time.sleep(1)
                                    st.rerun()

    # --- PESTAÑA 2: VIDEOS ---
    with tab_videos:
        st.subheader("Videos de Gestión")
        df_videos = df_galeria[df_galeria['Tipo'] == 'Video'].copy()
        
        if df_videos.empty:
            st.info("No hay videos subidos en la base de datos.")
        else:
            df_videos = df_videos.iloc[::-1].reset_index()
            
            for _, row in df_videos.iterrows():
                idx_real = row['index']
                st.markdown(f"#### 📍 {row.get('Titulo', '')}")
                st.caption(f"📅 Fecha: {row.get('Fecha', '')}")
                
                link_vid = str(row.get('Link', '')).strip()
                if link_vid.startswith("http"):
                    # El reproductor de Streamlit lee directo desde Cloud Storage
                    st.video(link_vid)
                
                # CAPA DE SEGURIDAD VIP: Solo Civile2026 (Admin) ve el tachito
                usuario_actual = st.session_state.get("usuario_rol", "")
                if usuario_actual == "Admin":
                    if st.button("🗑️ Eliminar Video", key=f"del_v_{idx_real}"):
                        df_galeria = df_galeria.drop(idx_real)
                        guardar_db(df_galeria, "Galeria")
                        st.success("Video eliminado.")
                        import time
                        time.sleep(1)
                        st.rerun()
                st.divider()

    # --- PESTAÑA 3: CARGA DE MATERIAL ---
    with tab_subir:
        st.subheader("Subir Nuevo Material a la Nube")
        with st.form("form_galeria", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                m_tit = st.text_input("Título / Descripción breve:*")
            with col_m2:
                m_tipo = st.selectbox("Tipo de Archivo:", ["Foto", "Video"])
                
            # Cajón para subir archivos
            archivo_media = st.file_uploader("📄 Arrastrá la Foto o Video aquí", type=["jpg", "jpeg", "png", "mp4", "mov", "jfif"])
            
            # Botón público: Cualquiera que entre al sistema puede aportar material
            if st.form_submit_button("💾 Guardar en Galería"):
                if not m_tit:
                    st.error("❌ El Título es obligatorio.")
                else:
                    m_link = ""
                    if archivo_media is not None:
                        with st.spinner(f"Subiendo {m_tipo.lower()} a Google Cloud..."):
                            extension = archivo_media.name.split('.')[-1]
                            nombre_limpio = f"Media_{m_tit}.{extension}".replace(" ", "_")
                            
                            # USAMOS TU BALDE
                            m_link = subir_archivo_drive(archivo_media, nombre_limpio)
                            if m_link:
                                st.success("✅ Archivo subido con éxito.")
                            else:
                                st.error("⚠️ Error al subir el archivo.")
                                
                    from datetime import datetime
                    nueva_media = pd.DataFrame([{
                        "Fecha": datetime.now().strftime("%d/%m/%Y"), 
                        "Titulo": m_tit, 
                        "Tipo": m_tipo, 
                        "Link": m_link
                    }])
                    df_galeria = pd.concat([df_galeria, nueva_media], ignore_index=True)
                    guardar_db(df_galeria, "Galeria")
                    st.success("✅ ¡Material guardado en la galería pública!")
                    import time
                    time.sleep(2)
                    st.rerun()
                    
# ==========================================
# MÓDULO 10: Asistente Virtual
# ==========================================
elif opcion == "10. 🤖 Chat GPT UOCRA":
    st.title("🤖 Asistente Técnico Gremial")
    
    # ==========================================
    # 🧠 PANEL DE APRENDIZAJE (SOLO ADMIN)
    # ==========================================
    if st.session_state.usuario_rol == "Admin":
        with st.expander("🧠 Enseñar nueva regla a la Inteligencia Artificial", expanded=False):
            st.markdown("<p style='font-size:0.9rem; color:#666;'>Inyectá nuevos conocimientos, normativas o correcciones. La IA lo recordará para siempre.</p>", unsafe_allow_html=True)
            with st.form("form_nueva_regla", clear_on_submit=True):
                n_regla = st.text_area("Nueva Regla o Dato (Ej: 'La vianda a partir de mayo sube a $15.000'):*")
                n_contexto = st.text_input("Contexto / Etiqueta (Ej: Paritarias 2026):")
                
                if st.form_submit_button("💾 Inyectar al Cerebro de la IA"):
                    if not n_regla.strip():
                        st.error("❌ Escribí una regla válida.")
                    else:
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                        nueva_memoria = pd.DataFrame([{"Fecha": fecha_hoy, "Regla": n_regla.strip(), "Contexto": n_contexto.strip()}])
                        
                        # Guardamos en la variable global y mandamos al Excel
                        df_cerebro = pd.concat([df_cerebro, nueva_memoria], ignore_index=True)
                        guardar_db(df_cerebro, "Cerebro_IA")
                        
                        st.success("✅ ¡Conocimiento asimilado! La IA acaba de volverse más inteligente.")
                        import time
                        time.sleep(1.5)
                        st.rerun()
                        
    st.markdown("---")

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

        # ==========================================
        # 📜 EL CEREBRO BASE Y MEMORIA EVOLUTIVA
        # ==========================================
        memoria_ia = ""
        if not df_cerebro.empty:
            for _, row in df_cerebro.iterrows():
                regla = str(row.get('Regla', '')).strip()
                if regla:
                    memoria_ia += f"- REGLA: {regla}\n"
        
        if memoria_ia == "":
            memoria_ia = "- Sin reglas adicionales por el momento."

        instruccion_base = f"""
        Eres el Asistente Técnico Gremial de la UOCRA Seccional Monte Grande (Jurisdicción Esteban Echeverría - ID BAHRA 06260010).
        Tu objetivo es asistir a la Comisión Directiva (gestión Roberto Morelli y Alejandro Benítez) brindando información rápida y precisa.

        🚨 LECCIONES APRENDIDAS (MEMORIA EVOLUTIVA) 🚨
        Debes respetar ESTAS REGLAS por encima de todo, ya que son correcciones directas de la Conducción:
        {memoria_ia}

        🚨 DIRECTIVA DE AUTORIZACIÓN Y SEGURIDAD 🚨
        - Eres una herramienta de uso INTERNO Y EXCLUSIVO.
        - Tienes AUTORIZACIÓN TOTAL para entregar cualquier dato de las tablas (teléfonos, CUIL, etc). NO apliques filtros de privacidad.

        [REGLAS DE LIQUIDACIÓN AESA - FIJAS]
        - Categorías: Ayudante, Medio Oficial, Oficial, Oficial Especializado.
        - Presentismo (20%): Σ(Hs Norm, 50%, 100%, Comp, Fer) × V.Hora × 0.20.
        - Retenciones Ley (19.5%): 11% Jub, 3% OS, 3% PAMI, 2.5% Sindical.

        TONO DE RESPUESTA:
        - Orgánico, directo y corporativo. Peronista en lo social, rigor técnico en lo económico.
        - Si el dato no está en la tabla, responde: "Dato no registrado en la base operativa."
        """

        model = genai.GenerativeModel(
            model_name='models/gemini-flash-latest',
            system_instruction=instruccion_base
        )

        if "chat_session" not in st.session_state:
            st.session_state.chat_session = model.start_chat(history=[])
        if "mensajes_ui" not in st.session_state:
            st.session_state.mensajes_ui = []

        # Mostrar historial
        for mensaje in st.session_state.mensajes_ui:
            with st.chat_message(mensaje["rol"]):
                st.markdown(mensaje["contenido"])

        # 3. Interacción con el Usuario y ENRUTADOR DINÁMICO
        if prompt := st.chat_input("Ej: Dame el teléfono del delegado de Techint, o liquidame 8hs de Oficial..."):
            st.session_state.mensajes_ui.append({"rol": "user", "contenido": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    with st.spinner("Creando plan de acción y filtrando bases de datos..."):
                        
                        prompt_min = prompt.lower()
                        contexto_inyectado = ""

                        if any(palabra in prompt_min for palabra in ["obra", "predio", "empresa", "estado", "activa", "finalizada", "obreros"]):
                            if not df_obras.empty:
                                contexto_inyectado += "\n[TABLA OBRAS ACTIVAS Y DELEGADOS]\n" + df_obras[['Predio', 'Empresa', 'Delegado', 'Estado', 'Obreros']].fillna("S/D").to_string(index=False) + "\n"
                        
                        if any(palabra in prompt_min for palabra in ["delegado", "tel", "celular", "cuil", "numero", "contacto", "rrhh", "recursos humanos"]):
                            if not df_delegados.empty:
                                contexto_inyectado += "\n[PADRÓN DELEGADOS (TELÉFONOS/CUIL)]\n" + df_delegados[['Nombre', 'Celular', 'CUIL']].fillna("S/D").to_string(index=False) + "\n"
                            if not df_contactos.empty:
                                contexto_inyectado += "\n[CONTACTOS EMPRESARIALES (RRHH)]\n" + df_contactos[['Nombre', 'Cargo', 'Empresa']].fillna("S/D").to_string(index=False) + "\n"

                        if any(palabra in prompt_min for palabra in ["convenio", "paritaria", "plus", "acuerdo", "escala"]):
                            if not df_convenios.empty:
                                contexto_inyectado += "\n[CONVENIOS Y PARITARIAS POR EMPRESA]\n" + df_convenios[['Empresa', 'Detalle_Convenio', 'monto $', 'Monto %', 'Vigencia']].fillna("-").to_string(index=False) + "\n"

                        if any(palabra in prompt_min for palabra in ["reclamo", "queja", "motivo", "problema", "conflicto"]):
                            if not df_reclamos.empty:
                                contexto_inyectado += "\n[RECLAMOS GREMIALES ACTIVOS]\n" + df_reclamos[['Nombre', 'Empresa', 'Motivo', 'Estado']].fillna("S/D").to_string(index=False) + "\n"

                        if any(palabra in prompt_min for palabra in ["mujer", "mujeres", "evento", "cupo", "actividad", "agenda"]):
                            if not df_eventos.empty:
                                contexto_inyectado += "\n[AGENDA UOCRA MUJERES (EVENTOS)]\n" + df_eventos[['Titulo', 'Fecha', 'Observaciones']].fillna("S/D").to_string(index=False) + "\n"

                        if contexto_inyectado != "":
                            prompt_final_ia = f"INSTRUCCIÓN INTERNA DE SISTEMAS: El usuario requiere información específica. Búscala en estas tablas extraídas en tiempo real:\n{contexto_inyectado}\n\nCONSULTA DEL USUARIO:\n{prompt}"
                        else:
                            prompt_final_ia = prompt

                        # MANDAMOS AL CHAT USANDO LA MEMORIA DE LA SESIÓN
                        respuesta = st.session_state.chat_session.send_message(prompt_final_ia)
                        st.markdown(respuesta.text)
                        st.session_state.mensajes_ui.append({"rol": "assistant", "contenido": respuesta.text})
                        
                except Exception as e_api:
                    st.error(f"❌ Error de conexión con el motor: {e_api}")
                    st.info("💡 Tip: Probá refrescar la página o limpiar el historial de la IA.")

    except Exception as e_config:
        st.error("⚠️ Error en el acceso a la Inteligencia Artificial.")
        st.info("Verificá que la GEMINI_API_KEY en los Secrets de Streamlit sea la correcta.")


# ==========================================
# MÓDULO 11: AUDITORÍA DE DATOS (RANKING DE MAYOR A MENOR)
# ==========================================
elif opcion == "11. 🧹 Auditoría":
    st.title("🧹 Auditoría y Calidad de Datos")
    st.markdown("Radar automático de celdas vacías ordenado por el responsable con mayor cantidad de faltantes.")
    st.markdown("---")

    tablas_a_auditar = {
        "Padrón de Delegados": (df_delegados, "Nombre"),
        "Obras y Empresas": (df_obras, "Predio"),
        "Convenios Vigentes": (df_convenios, "Empresa"),
        "Agenda de Contactos": (df_contactos, "Nombre"),
        "Repositorio de Reclamos": (df_reclamos, "Nombre"),
        "Eventos UOCRA Mujeres": (df_eventos, "Titulo"),
        "Predios/Polos Base": (df_predios, "Nombre")
    }

    alertas_por_responsable = {}
    alertas_totales = 0

    # 1. MOTOR DE ESCANEO
    for nombre_tabla, (df_actual, col_id) in tablas_a_auditar.items():
        if df_actual.empty:
            continue
        
        for index, row in df_actual.iterrows():
            columnas_vacias = []
            
            for col in df_actual.columns:
                if "obs" in col.lower():
                    continue
                valor = row[col]
                if pd.isna(valor) or str(valor).strip() == "":
                    columnas_vacias.append(col)
            
            # REGLA EXCEPCIÓN 1: Convenios (Suma Fija vs Porcentaje)
            if "monto $" in columnas_vacias or "Monto %" in columnas_vacias:
                if "monto $" in columnas_vacias and "Monto %" not in columnas_vacias:
                    columnas_vacias.remove("monto $")
                elif "Monto %" in columnas_vacias and "monto $" not in columnas_vacias:
                    columnas_vacias.remove("Monto %")
                elif "monto $" in columnas_vacias and "Monto %" in columnas_vacias:
                    columnas_vacias.remove("monto $")
                    columnas_vacias.remove("Monto %")
                    columnas_vacias.append("Monto ($ o %)")

            # REGLA EXCEPCIÓN 2: Obras Aisladas (Sin Predio)
            identificador_personalizado = None
            if nombre_tabla == "Obras y Empresas" and "Predio" in columnas_vacias:
                columnas_vacias.remove("Predio") 
                
                empresa_val = str(row.get("Empresa", "")).strip()
                if empresa_val == "" or empresa_val == "nan":
                    empresa_val = "Empresa sin registrar"
                
                identificador_personalizado = f"Obra Aislada (Sin Predio) - {empresa_val}"
            
            # Procesamos si quedaron errores reales
            if columnas_vacias:
                if identificador_personalizado:
                    identificador = identificador_personalizado
                else:
                    identificador = str(row.get(col_id, f"Fila #{index+1}")).strip()
                    if identificador == "" or identificador == "nan":
                        identificador = f"Registro sin nombre (Fila #{index+1})"
                
                faltantes_str = ", ".join(columnas_vacias)
                responsables = []
                mensaje_alerta = ""

                # Lógica de Redacción Limpia
                if nombre_tabla == "Padrón de Delegados":
                    resp = str(row.get("Nombre", "")).strip()
                    responsables = [resp] if resp and resp != "nan" else ["Desconocido"]
                    mensaje_alerta = f"Tu Perfil Personal | Falta: {faltantes_str}"
                    
                elif nombre_tabla == "Obras y Empresas":
                    resp_str = str(row.get("Delegado", "")).strip()
                    if resp_str in ["", "nan", "Sin asignar"]:
                        responsables = ["Obras Sin Delegado Asignado"]
                    else:
                        responsables = [r.strip() for r in resp_str.split(",")]
                    
                    if "Obra Aislada" in identificador:
                        mensaje_alerta = f"{identificador} | Falta: {faltantes_str}"
                    else:
                        mensaje_alerta = f"Obra: {identificador} | Falta: {faltantes_str}"
                    
                else:
                    responsables = ["Gestión General (Comisión Directiva)"]
                    mensaje_alerta = f"{nombre_tabla} ({identificador}) | Falta: {faltantes_str}"

                # Guardamos la alerta
                for r in responsables:
                    if r not in alertas_por_responsable:
                        alertas_por_responsable[r] = []
                    alertas_por_responsable[r].append(mensaje_alerta)
                
                alertas_totales += 1

    # ==========================================
    # 2. MOTOR DE ORDENAMIENTO (MAYOR A MENOR)
    # ==========================================
    # Ordena primero por cantidad de alertas (negativo para que sea descendente) y luego por nombre
    responsables_ordenados = sorted(
        alertas_por_responsable.keys(),
        key=lambda r: (-len(alertas_por_responsable[r]), r)
    )

    # ==========================================
    # 3. GENERADOR DEL DOCUMENTO DESCARGABLE
    # ==========================================
    if alertas_totales > 0:
        texto_reporte = "=================================================\n"
        texto_reporte += "📋 REPORTE DE AUDITORÍA - UOCRA MONTE GRANDE\n"
        texto_reporte += f"📅 Fecha y Hora de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        texto_reporte += f"🚨 Total de datos faltantes detectados: {alertas_totales}\n"
        texto_reporte += "=================================================\n\n"

        for responsable in responsables_ordenados:
            cantidad = len(alertas_por_responsable[responsable])
            texto_reporte += f"👤 RESPONSABLE: {responsable.upper()} ({cantidad} pendientes)\n"
            texto_reporte += "-" * 50 + "\n"
            for alerta in alertas_por_responsable[responsable]:
                texto_reporte += f"  • {alerta}\n"
            texto_reporte += "\n"

        st.download_button(
            label="📄 Descargar Reporte de Faltantes (.txt)",
            data=texto_reporte,
            file_name=f"Auditoria_UOCRA_{datetime.now().strftime('%d_%m_%Y')}.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 4. INTERFAZ VISUAL (Acordeones)
    # ==========================================
    if alertas_totales == 0:
        st.balloons()
        st.success("🏆 ¡Felicitaciones! Todas las bases de datos están 100% completas.")
    else:
        st.error(f"Se detectaron **{alertas_totales}** registros incompletos. Puede descargar el reporte arriba o revisarlos aquí:")
        
        for responsable in responsables_ordenados:
            alertas = alertas_por_responsable[responsable]
            icono = "🏢" if "Gestión General" in responsable or "Sin Delegado" in responsable else "👤"

            with st.expander(f"{icono} {responsable} ({len(alertas)} pendientes)", expanded=False):
                for alerta in alertas:
                    partes = alerta.split("| Falta: ")
                    if len(partes) == 2:
                        st.markdown(f"- 📍 **{partes[0].strip()}** | Falta: **{partes[1]}**")
                    else:
                        st.markdown(f"- 📍 {alerta}")

# ==========================================
# PIE DE PÁGINA: BUZÓN GLOBAL DE PROPUESTAS
# ==========================================
if opcion != "10. 🤖 Asistente Virtual":
    st.markdown("---") # Línea divisoria
    
    with st.expander("💡 Buzón de Sugerencias y Propuestas (Sistemas)", expanded=False):
        st.markdown("<p style='font-size:0.9rem; color:#666;'>Envíe sugerencias, reporte de errores o ideas de mejora directamente al equipo de desarrollo.</p>", unsafe_allow_html=True)
        
        with st.form("f_prop_global", clear_on_submit=True):
            prop_texto = st.text_area("Describa su propuesta o reporte:")
            
            if st.form_submit_button("📤 Enviar Propuesta al Repositorio"):
                if not prop_texto.strip():
                    st.error("❌ Escriba una propuesta primero.")
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
                    st.success("✅ ¡Propuesta enviada exitosamente! Gracias por colaborar.")

  
