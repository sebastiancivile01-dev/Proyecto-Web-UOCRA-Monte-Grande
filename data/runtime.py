"""Inicializacion de Sheets y carga de tablas, sin efectos al importar."""

import json
from datetime import datetime

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

from safety import ConflictoEscrituraError, cargar_geojson_local, escribir_hoja, leer_hoja


def initialize():
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
    @st.cache_data(ttl=120)
    def _leer_db_cache(documento_id, hoja_nombre, columnas):
        try:
            return leer_hoja(DOC.worksheet(hoja_nombre), columnas)
        except Exception:
            # None es un fallo cacheado; una hoja vacía devuelve (DataFrame, snapshot).
            return None
    
    
    def cargar_db(hoja_nombre, columnas):
        versiones = st.session_state.setdefault("_versiones_hojas", {})
        claves = st.session_state.setdefault("_claves_cache_hojas", {})
        versiones.pop(hoja_nombre, None)
        claves.pop(hoja_nombre, None)
        try:
            clave_cache = (DOC.id, hoja_nombre, list(columnas))
            resultado = _leer_db_cache(*clave_cache)
        except Exception:
            resultado = None
        if resultado is None:
            st.error(f"No se pudo leer {hoja_nombre}. No se habilitarán escrituras. Recargue para volver a intentar.")
            st.stop()
        df, version = resultado
        versiones[hoja_nombre] = version
        claves[hoja_nombre] = clave_cache
        return df
    
    
    def guardar_db(df, hoja_nombre):
        versiones = st.session_state.setdefault("_versiones_hojas", {})
        claves = st.session_state.setdefault("_claves_cache_hojas", {})
        version = versiones.pop(hoja_nombre, None)
        clave_cache = claves.pop(hoja_nombre, None)
        try:
            if version is None or clave_cache is None:
                raise ValueError("Falta una lectura válida de esta hoja.")
            escribir_hoja(DOC.worksheet(hoja_nombre), df, version)
        except ConflictoEscrituraError:
            st.error(f"{hoja_nombre} cambió mientras trabajaba. No se guardó. Actualice los datos y revise los cambios antes de reintentar.")
            return False
        except Exception:
            st.error(f"No se pudo confirmar el guardado en {hoja_nombre}. Actualice y verifique la hoja antes de repetir la operación.")
            return False
        finally:
            if clave_cache is not None:
                _leer_db_cache.clear(*clave_cache)
        return True
    
    
    @st.cache_data
    def cargar_limites_mapa():
        return cargar_geojson_local()
    
    
    def registrar_log(accion_realizada):
        """Guarda un registro silencioso de quién hizo qué y a qué hora."""
        try:
            # 1. Obtenemos el usuario de la sesión actual
            usuario_actual = st.session_state.get("usuario_rol", "Desconocido")
            
            # 2. Obtenemos fecha y hora
            ahora = datetime.now()
            fecha = ahora.strftime("%d/%m/%Y")
            hora = ahora.strftime("%H:%M:%S")
            
            # 3. Nos conectamos solo a la pestaña de Logs y agregamos la fila al final
            # IMPORTANTE: Reemplazá "NOMBRE_DE_TU_EXCEL" por el nombre real de tu archivo en Google Drive
            hoja_logs = client.open("Base_Datos_UOCRA").worksheet("Logs_Auditoria")
            
            # append_row inserta los datos en la primera fila vacía que encuentre hacia abajo
            hoja_logs.append_row([fecha, hora, usuario_actual, accion_realizada])
            
        except Exception as e:
            # Si falla el registro por un corte de internet, lo ignoramos para no frenar la app
            pass
    
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
        # Carga del historial de escalas salariales (Paritarias)
    df_paritarias = cargar_db("Paritarias_Historia", ["Fecha_Carga", "Periodo_Vigencia", "Oficial_Especializado", "Oficial", "Medio_Oficial", "Ayudante", "Sereno", "Viatico"])
    df_delegados = cargar_db("Delegados", ["Nombre", "CUIL", "Celular", "Domicilio", "Nacimiento", "Correo", "Observacion"])
    df_contactos = cargar_db("Contactos", ["Nombre", "Cargo", "Empresa", "Observaciones"])
    df_reclamos = cargar_db("Reclamos", ["Nombre", "Empresa", "Motivo", "Ingreso", "Estado", "Finalizacion", "Respuesta", "Observaciones"])
    df_eventos = cargar_db("Mujeres_Eventos", ["Titulo", "Fecha", "Observaciones"])
    df_convenios = cargar_db("Convenios", ["Empresa", "Detalle_Convenio", "monto $", "Monto %", "Vigencia"])
    df_propuestas = cargar_db("Propuestas", ["Fecha", "Usuario", "Propuesta", "Estado"])
    df_cerebro = cargar_db("Cerebro_IA", ["Fecha", "Regla", "Contexto"])
    df_observaciones = cargar_db("Observaciones_Empresas", ["Fecha", "Empresa", "Observacion", "Usuario"])
    df_puntos_extra = cargar_db("Puntos_Extra", ["Nombre", "Latitud", "Longitud", "Color", "Observacion"])
    if not df_puntos_extra.empty:
        df_puntos_extra['Latitud'] = pd.to_numeric(df_puntos_extra['Latitud'], errors='coerce').fillna(0.0)
        df_puntos_extra['Longitud'] = pd.to_numeric(df_puntos_extra['Longitud'], errors='coerce').fillna(0.0)
    
    lista_predios_historicos = sorted(df_predios['Nombre'].dropna().astype(str).tolist()) if not df_predios.empty else []
    lista_empresas_historicas = sorted(list(set(pd.concat([df_obras['Empresa'], df_contactos['Empresa'], df_reclamos['Empresa'], df_convenios['Empresa']]).dropna().astype(str).tolist())))
    lista_delegados_nombres = df_delegados['Nombre'].tolist() if not df_delegados.empty else []
    
    lista_jurisdicciones = ["Esteban Echeverría", "Ezeiza", "Cañuelas", "Roque Pérez", "Lobos", "Saladillo", "Monte", "General Belgrano", "Las Heras", "Navarro"]
    lista_estados = ["Activa", "Intervenida", "Finalizada", "Interrumpida"]
    
    return {
        "DOC": DOC, "client": client, "_leer_db_cache": _leer_db_cache,
        "cargar_db": cargar_db, "guardar_db": guardar_db,
        "cargar_limites_mapa": cargar_limites_mapa, "registrar_log": registrar_log,
        "df_obras": df_obras, "df_cierres": df_cierres, "df_galeria": df_galeria,
        "df_predios": df_predios, "df_documentos": df_documentos, "df_paritarias": df_paritarias,
        "df_delegados": df_delegados, "df_contactos": df_contactos, "df_reclamos": df_reclamos,
        "df_eventos": df_eventos, "df_convenios": df_convenios, "df_propuestas": df_propuestas,
        "df_cerebro": df_cerebro, "df_observaciones": df_observaciones, "df_puntos_extra": df_puntos_extra,
        "lista_predios_historicos": lista_predios_historicos,
        "lista_empresas_historicas": lista_empresas_historicas,
        "lista_delegados_nombres": lista_delegados_nombres,
        "lista_jurisdicciones": lista_jurisdicciones, "lista_estados": lista_estados,
    }