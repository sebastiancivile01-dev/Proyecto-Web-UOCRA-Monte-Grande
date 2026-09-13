import io
import json
import time
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

from domain.map import filter_boundary


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
    limites_geojson = cargar_limites_mapa()
    
    if limites_geojson is not None:
        folium.GeoJson(limites_geojson, name="Límites", style_function=filter_boundary).add_to(m)
    else:
        st.warning("Límites territoriales no disponibles. Se muestran las obras, polos y marcadores sin esa capa.")
    
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
    aplicar_estilos_mapa()
    
    # RENDERIZAMOS EL MAPA (El tamaño se ajusta por CSS)
    folium_static(m, width=725, height=600)
    
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
                                    registrar_log("Agregó Punto Temporal al Mapa")
                                else:
                                    nuevo_punto = pd.DataFrame([{"Nombre": p_nom, "Latitud": lat_f, "Longitud": lon_f, "Color": color_final, "Observacion": p_obs}])
                                    df_puntos_extra = pd.concat([df_puntos_extra, nuevo_punto], ignore_index=True)
                                    if not guardar_db(df_puntos_extra, "Puntos_Extra"):
                                        st.stop()
                                    st.success("✅ Punto Permanente guardado en Google Sheets.")
                                    registrar_log("Agregó Punto Permanente al Mapa")
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
                        if not guardar_db(df_puntos_extra, "Puntos_Extra"):
                            st.stop()
                        st.success("✅ Borrado definitivamente del Excel.")
                        registrar_log("Borró Punto del Mapa")
                        st.rerun()
                else:
                    st.info("No hay puntos permanentes guardados.")
    # ==========================================
