import io
import json
import time
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st


def render(ctx):
    opcion = ctx.opcion
    folium = ctx.folium
    folium_static = ctx.folium_static
    genai = ctx.genai
    build = ctx.build
    MediaIoBaseUpload = ctx.MediaIoBaseUpload
    service_account = ctx.service_account
    tarjeta_kpi = ctx.tarjeta_kpi
    aplicar_estilos_estadisticas = ctx.aplicar_estilos_estadisticas
    aplicar_estilos_mapa = ctx.aplicar_estilos_mapa
    aplicar_estilos_mujeres = ctx.aplicar_estilos_mujeres
    modulo_permitido = ctx.modulo_permitido
    cargar_limites_mapa = ctx.cargar_limites_mapa
    guardar_db = ctx.guardar_db
    cargar_db = ctx.cargar_db
    registrar_log = ctx.registrar_log
    obtener_cer = ctx.obtener_cer
    subir_archivo_drive = ctx.subir_archivo_drive
    df_obras = ctx.df_obras
    df_cierres = ctx.df_cierres
    df_galeria = ctx.df_galeria
    df_predios = ctx.df_predios
    df_documentos = ctx.df_documentos
    df_paritarias = ctx.df_paritarias
    df_delegados = ctx.df_delegados
    df_contactos = ctx.df_contactos
    df_reclamos = ctx.df_reclamos
    df_eventos = ctx.df_eventos
    df_convenios = ctx.df_convenios
    df_propuestas = ctx.df_propuestas
    df_cerebro = ctx.df_cerebro
    df_observaciones = ctx.df_observaciones
    df_puntos_extra = ctx.df_puntos_extra
    lista_predios_historicos = ctx.lista_predios_historicos
    lista_empresas_historicas = ctx.lista_empresas_historicas
    lista_delegados_nombres = ctx.lista_delegados_nombres
    lista_jurisdicciones = ctx.lista_jurisdicciones
    lista_estados = ctx.lista_estados
    if not modulo_permitido(st.session_state.get("usuario_rol"), opcion):
        st.error("Acceso no autorizado para este perfil.")
        st.stop()
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
                    if not guardar_db(df_reclamos, "Reclamos"):
                        st.stop()
                    st.success("Reclamo asentado!")
                    st.rerun()
    
    with tab_r_bd:
        st.dataframe(df_reclamos, use_container_width=True)
        if not df_reclamos.empty:
            ops = df_reclamos['Nombre'] + " - " + df_reclamos['Motivo']
            rel = st.selectbox("Eliminar:", [""] + ops.tolist())
            if st.button("🗑️ Eliminar") and rel:
                df_reclamos = df_reclamos.drop(df_reclamos.index[ops.tolist().index(rel)])
                if not guardar_db(df_reclamos, "Reclamos"):
                    st.stop()
                st.success("Eliminado.")
                st.rerun()
    
    # ==========================================
