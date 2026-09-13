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
    st.title("📋 Repositorio de Bases de Datos")
    
    # 1. Tarjetas de Resumen
    c1, c2, c3 = st.columns(3)
    emp_totales = len(df_obras['Empresa'].unique()) if not df_obras.empty else 0
    del_totales = len(df_delegados) if not df_delegados.empty else 0
    con_totales = len(df_contactos) if not df_contactos.empty else 0
    
    with c1:
        tarjeta_kpi("🏢 Empresas Activas", emp_totales)
    
    with c2:
        tarjeta_kpi(
            "👥 Delegados Registrados",
            del_totales,
            variante="verde",
        )
    
    with c3:
        tarjeta_kpi(
            "📞 Contactos Agenda",
            con_totales,
            variante="naranja",
        )
    
    st.write("Buscador en tiempo real. Escriba para filtrar los resultados automáticamente.")
    t1, t2, t3 = st.tabs([
        "🏗️ Obras y Empresas",
        "👥 Padrón de Delegados",
        "🏢 Agenda de Contactos",
    ])
    
    with t1:
        busq_obra = st.text_input(
            "🔍 Buscar por Predio o Empresa:",
            key="b_obras",
        )
        df_mostrar_o = df_obras.copy()
        
        # Oculta la jurisdicción restringida para ese perfil.
        if st.session_state.usuario_rol == "Restringido":
            cols_a_borrar = [
                col
                for col in df_mostrar_o.columns
                if "Jurisdiccion_R" in str(col)
            ]
            if cols_a_borrar:
                df_mostrar_o = df_mostrar_o.drop(columns=cols_a_borrar)
            
        if busq_obra:
            df_mostrar_o = df_mostrar_o[
                df_mostrar_o["Predio"].str.contains(
                    busq_obra,
                    case=False,
                    na=False,
                )
                | df_mostrar_o["Empresa"].str.contains(
                    busq_obra,
                    case=False,
                    na=False,
                )
            ]
    
        st.dataframe(df_mostrar_o, use_container_width=True)
        
    with t2:
        busq_del = st.text_input(
            "🔍 Buscar Delegado por Nombre o CUIL:",
            key="b_del",
        )
        df_mostrar_d = df_delegados
    
        if busq_del:
            df_mostrar_d = df_delegados[
                df_delegados["Nombre"].str.contains(
                    busq_del,
                    case=False,
                    na=False,
                )
                | df_delegados["CUIL"].astype(str).str.contains(
                    busq_del,
                    case=False,
                    na=False,
                )
            ]
    
        st.dataframe(df_mostrar_d, use_container_width=True)
        
    with t3:
        busq_con = st.text_input(
            "🔍 Buscar Contacto por Nombre o Empresa:",
            key="b_con",
        )
        df_mostrar_c = df_contactos
    
        if busq_con:
            df_mostrar_c = df_contactos[
                df_contactos["Nombre"].str.contains(
                    busq_con,
                    case=False,
                    na=False,
                )
                | df_contactos["Empresa"].str.contains(
                    busq_con,
                    case=False,
                    na=False,
                )
            ]
    
        st.dataframe(df_mostrar_c, use_container_width=True)
        
    # ==========================================
