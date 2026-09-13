"""Servicios externos diferidos: BCRA, feriados y Cloud Storage."""

from datetime import datetime

import requests


def build(st):
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
            
    return {
        "obtener_cer": obtener_cer,
        "obtener_feriados_argentina": obtener_feriados_argentina,
        "abrir_calendario_flotante": abrir_calendario_flotante,
        "subir_archivo_drive": subir_archivo_drive,
    }