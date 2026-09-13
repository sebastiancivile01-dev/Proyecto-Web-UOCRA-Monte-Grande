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
    st.title("📊 Tablero de Control y Estadísticas")
    st.markdown("Visión analítica general de la Jurisdicción Esteban Echeverría.")
    
    # CSS Súper Agresivo para anular el diseño por defecto...
    # Amplía las tarjetas KPI para el tablero.
    aplicar_estilos_estadisticas()
    
    st.markdown("---")
    
    # 1. MÉTRICAS PRINCIPALES
    total_obras = len(df_obras) if not df_obras.empty else 0
    obras_activas = len(df_obras[df_obras['Estado'] == 'Activa']) if not df_obras.empty else 0
    total_obreros = int(df_obras['Obreros'].sum()) if not df_obras.empty else 0
    reclamos_activos = len(df_reclamos[df_reclamos['Estado'] == 'Activo']) if not df_reclamos.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        tarjeta_kpi("🏗️ Obras Totales", total_obras)
    
    with col2:
        tarjeta_kpi("🟢 Obras Activas", obras_activas, variante="verde")
    
    with col3:
        tarjeta_kpi("👷‍♂️ Compañeros", total_obreros)
    
    with col4:
        tarjeta_kpi("🚨 Reclamos", reclamos_activos, variante="naranja")
        
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
                tarjeta_kpi(
                    "Compañeras",
                    total_mujeres,
                    variante="violeta",
                )
    
            with c_m2:
                tarjeta_kpi(
                    "Cupo Global",
                    f"{porc_general:.1f}%",
                    variante="violeta",
                )
    # ==========================================
