import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión UOCRA - Seccional Monte Grande", layout="wide", page_icon="🏗️")

# --- SISTEMA DE LOGIN (CANDADO) ---
if 'usuario_rol' not in st.session_state:
    st.session_state.usuario_rol = None

if st.session_state.usuario_rol is None:
    st.title("🔒 Acceso Restringido - UOCRA Monte Grande")
    st.markdown("Por favor, ingrese su clave para acceder al sistema operativo.")
    
    clave = st.text_input("Contraseña:", type="password")
    
    if st.button("Ingresar"):
        if clave == "Civile2026":  # Clave para ustedes 4 (acceso total)
            st.session_state.usuario_rol = "Admin"
            st.rerun()
        elif clave == "Morelli2026": # Clave para el usuario número 5
            st.session_state.usuario_rol = "Restringido"
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta.")
    
    st.stop() # Esto es clave: frena la página acá y no carga nada de lo que sigue

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

# La lista de predios ahora se alimenta de la base maestra oficial
lista_predios_historicos = sorted(df_predios['Nombre'].dropna().astype(str).tolist()) if not df_predios.empty else []
lista_empresas_historicas = sorted(list(set(pd.concat([df_obras['Empresa'], df_contactos['Empresa'], df_reclamos['Empresa']]).dropna().astype(str).tolist())))
lista_delegados_nombres = df_delegados['Nombre'].tolist() if not df_delegados.empty else []

lista_jurisdicciones = ["Esteban Echeverría", "Ezeiza", "Cañuelas", "Roque Pérez", "Lobos", "Saladillo", "Monte", "General Belgrano", "Las Heras", "Navarro"]
lista_estados = ["Activa", "Intervenida", "Finalizada", "Interrumpida"]

# --- BARRA LATERAL (MENÚ PRINCIPAL) ---
st.sidebar.image("images.jfif", width=150)
st.sidebar.title("Menú Principal")

# Botón para cerrar sesión
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.usuario_rol = None
    st.rerun()

with st.sidebar.expander("🏛️ Comisión Directiva", expanded=False):
    st.markdown("""
    **1- Sec. Gral:** Roberto Morelli
    
    **2- Sec. Adj:** Alejandro Benitez
    
    **3- Sec. Org:** Rolando Civile
    
    **4- Sec. Actas:** Ruben Fernandez
    
    **5- Sec. Finanzas:** R. Oviedo
    """)

# MAGIA DEL LOGIN: Filtramos los botones según quién entró
opciones_totales = [
    "1. 🗺️ Mapa Territorial", "2. 📥 Carga de Datos (ABM)", 
    "3. 📋 Nóminas Consolidadas", "4. 🧮 Calculadoras", "5. ⚠️ Repositorio de Reclamos",
    "6. 💜 UOCRA Mujeres"
]

if st.session_state.usuario_rol == "Restringido":
    # Morelli también puede ver UOCRA Mujeres y las nóminas (sin la jur_R)
    opciones_permitidas = ["1. 🗺️ Mapa Territorial", "3. 📋 Nóminas Consolidadas", "6. 💜 UOCRA Mujeres"]
else:
    # Si es Admin, ve todo
    opciones_permitidas = opciones_totales

opcion = st.sidebar.radio("Navegación:", opciones_permitidas)

# ==========================================
# MÓDULO 1: MAPA TERRITORIAL
# ==========================================
if opcion == "1. 🗺️ Mapa Territorial":
    st.title("📍 Control Territorial - Jurisdicción Completa")
    st.markdown("### 👁️ Panel de Visualización")
    modo_mapa = st.selectbox("Seleccione el enfoque del mapa:", ["🗺️ Vista General", "👤 Foco en Delegados", "🟢 Solo Activas", "🔴 Con Problemas (Interv/Interr)", "⚪ Finalizadas"])
    st.markdown("---")

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
                    color="#FF8C00",
                    weight=2,
                    fill=True,
                    fill_color="#FFA500",
                    fill_opacity=0.25,
                    tooltip=f"<div style='text-align:center;'><b>📍 Polo/Predio:</b> {p.get('Nombre', 'S/N')}<br><b>Radio de control:</b> {rad_p} KM</div>"
                ).add_to(m)

    df_mapa = df_obras.copy()
    if not df_mapa.empty:
        if "Activas" in modo_mapa: df_mapa = df_mapa[df_mapa['Estado'] == 'Activa']
        elif "Problemas" in modo_mapa: df_mapa = df_mapa[df_mapa['Estado'].isin(['Intervenida', 'Interrumpida'])]
        elif "Finalizadas" in modo_mapa: df_mapa = df_mapa[df_mapa['Estado'] == 'Finalizada']

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
                    # Si es Admin y es Jurisdicción R (Soporta "SI" y "Sí"), le agregamos una marca roja
                    es_r = str(row.get('Jurisdiccion_R', '')).strip().upper() in ['SI', 'SÍ']
                    marca_r = " 🔴 [JUR R]" if es_r and st.session_state.usuario_rol == "Admin" else ""
                    
                    html = f"<div><h4 style='color: #3186cc;'>🏗️ {txt_p}{marca_r}</h4><hr><b>Empresa:</b> {empresa}<br><b>Estado:</b> {est}<br><b>Compañeros:</b> {row.get('Obreros', 0)}<hr><b>Delegado/s:</b><br>{txt_d}</div>"
                    icon = folium.Icon(color=color, icon="hard-hat", prefix="fa")
                
                folium.Marker([lat, lon], tooltip=folium.Tooltip(html), icon=icon).add_to(m)
                
    folium_static(m, width=1000, height=600)

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

    tab_recibo, tab_ieric = st.tabs(["🧾 Calculadora de Recibos", "💰 Fondo Cese (IERIC)"])
    
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
        st.write("Carga de quincenas históricas para cálculo de aportes.")
        
        col_i1, col_i2 = st.columns(2)
        ieric_nombre = col_i1.text_input("Nombre del Compañero (Para Registro/Reclamo):")
        ieric_emp = col_i2.selectbox("Empresa:", ["➕ Nueva..."] + lista_empresas_historicas, key="ieric_e")

        if 'quincenas' not in st.session_state: 
            st.session_state.quincenas = []

        with st.form("form_q"):
            c1, c2 = st.columns(2)
            fp = c1.date_input("Fecha de Pago")
            bru = c2.number_input("Sueldo Bruto Quincenal ($):", min_value=0.0, step=1000.0)
            if st.form_submit_button("➕ Agregar Quincena") and bru > 0:
                nro = len(st.session_state.quincenas) + 1
                tasa = 0.12 if nro <= 24 else 0.08
                st.session_state.quincenas.append({"Quincena #": f"Q-{nro:02d}", "Fecha": fp.strftime("%d/%m/%Y"), "Bruto": bru, "Tasa Ley": f"{int(tasa*100)}%", "Aporte Cese": bru * tasa})
                st.rerun()

        if st.session_state.quincenas:
            df_q = pd.DataFrame(st.session_state.quincenas)
            df_m = df_q.copy()
            df_m["Bruto"] = df_m["Bruto"].apply(lambda x: f"$ {x:,.2f}")
            df_m["Aporte Cese"] = df_m["Aporte Cese"].apply(lambda x: f"$ {x:,.2f}")
            st.dataframe(df_m, use_container_width=True)
            col_tot1, col_tot2 = st.columns(2)
            col_tot1.metric("Suma Bruta", f"$ {sum(q['Bruto'] for q in st.session_state.quincenas):,.2f}")
            col_tot2.metric("TOTAL FONDO", f"$ {sum(q['Aporte Cese'] for q in st.session_state.quincenas):,.2f}")
            
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
                    df_reclamos = pd.concat([df_reclamos, pd.DataFrame([{"Nombre": ieric_nombre, "Empresa": ieric_emp, "Motivo": motivo_ieric, "Ingreso": datetime.now().strftime("%d/%m/%Y"), "Estado": "Activo", "Finalizacion": "En proceso", "Respuesta": "", "Observaciones": "Generado Auto desde IERIC."}])], ignore_index=True)
                    guardar_db(df_reclamos, "Reclamos")
                    st.success("✅ Reclamo enviado!")
            
            if c_btn2.button("🗑️ Borrar Última Quincena"): 
                st.session_state.quincenas.pop()
                st.rerun()

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
            # Lista de obras disponibles para asignar cupo
            opciones_obras_m = df_obras['Predio'].astype(str) + " (" + df_obras['Empresa'].astype(str) + ")"
            obra_m_sel = st.selectbox("Seleccione la Obra activa:", opciones_obras_m.tolist())
            
            if obra_m_sel:
                idx_m = opciones_obras_m[opciones_obras_m == obra_m_sel].index[0]
                dat_m = df_obras.loc[idx_m]
                tot_obreros = int(dat_m.get('Obreros', 0))
                mujeres_actual = int(dat_m.get('Mujeres', 0))
                
                st.info(f"👥 **Total de operarios registrados en esta obra:** {tot_obreros}")
                
                with st.form("f_cupo"):
                    n_mujeres = st.number_input("Cantidad de Mujeres asignadas (Cupo):", min_value=0, step=1, value=mujeres_actual)
                    
                    # Cálculo automático de participación
                    if tot_obreros > 0:
                        porcentaje = (n_mujeres / tot_obreros) * 100
                    else:
                        porcentaje = 0.0
                        
                    st.markdown(f"### 📊 Porcentaje de Participación Femenina: **{porcentaje:.2f}%**")
                    
                    if st.form_submit_button("💾 Guardar / Actualizar Cupo"):
                        df_obras.at[idx_m, 'Mujeres'] = n_mujeres
                        guardar_db(df_obras, "Obras")
                        st.success("✅ Cupo femenino actualizado exitosamente.")
                        st.rerun()
                        
        st.markdown("---")
        st.markdown("### 📋 Listado de Cumplimiento por Obra")
        if not df_obras.empty:
            df_cupo_view = df_obras[['Predio', 'Empresa', 'Obreros', 'Mujeres']].copy()
            # Evitamos dividir por cero en la tabla visual
            df_cupo_view['% Participación'] = (df_cupo_view['Mujeres'] / df_cupo_view['Obreros'].replace(0, 1) * 100).round(2).astype(str) + "%"
            # Mostramos solo las que tienen compañeras cargadas
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
