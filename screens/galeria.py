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
                                    if not guardar_db(df_galeria, "Galeria"):
                                        st.stop()
                                    st.success("Foto eliminada.")
                                    registrar_log("Eliminó Foto") 
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
                        if not guardar_db(df_galeria, "Galeria"):
                            st.stop()
                        st.success("Video eliminado.")
                        registrar_log("Eliminó Video") 
                        import time
                        time.sleep(1)
                        st.rerun()
                st.divider()
    
    # --- PESTAÑA 3: CARGA DE MATERIAL ---
    # --- CÓDIGO CORRECTO DEL MÓDULO 9 ---
    with tab_subir:
        st.subheader("Subir Nuevo Material a la Nube")
        with st.form("form_galeria", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                m_tit = st.text_input("Título / Descripción común para el grupo:*")
            with col_m2:
                m_tipo = st.selectbox("Tipo de Archivo:", ["Foto", "Video"])
                
            # ACÁ ESTÁ LA SUBIDA MÚLTIPLE DE FOTOS/VIDEOS
            archivos_multimedia = st.file_uploader(
                "📄 Arrastrá todas las Fotos o Videos aquí", 
                type=["jpg", "jpeg", "png", "mp4", "mov", "jfif"],
                accept_multiple_files=True 
            )
            
            if st.form_submit_button("💾 Guardar todo en Galería"):
                if not m_tit:
                    st.error("❌ El Título es obligatorio.")
                elif not archivos_multimedia:
                    st.error("❌ No seleccionaste ningún archivo.")
                else:
                    nuevos_registros = []
                    progreso = st.progress(0)
                    
                    for i, archivo in enumerate(archivos_multimedia):
                        with st.spinner(f"Subiendo archivo {i+1} de {len(archivos_multimedia)} a la nube..."):
                            extension = archivo.name.split('.')[-1]
                            nombre_limpio = f"Media_{m_tit}_{i+1}.{extension}".replace(" ", "_")
                            
                            m_link = subir_archivo_drive(archivo, nombre_limpio)
                            
                            if m_link:
                                from datetime import datetime
                                nuevos_registros.append({
                                    "Fecha": datetime.now().strftime("%d/%m/%Y"), 
                                    "Titulo": f"{m_tit} ({i+1})", 
                                    "Tipo": m_tipo, 
                                    "Link": m_link
                                })
                        progreso.progress((i + 1) / len(archivos_multimedia))
                    
                    if nuevos_registros:
                        df_nuevos = pd.DataFrame(nuevos_registros)
                        df_galeria = pd.concat([df_galeria, df_nuevos], ignore_index=True)
                        if not guardar_db(df_galeria, "Galeria"):
                            st.stop()
                        
                        st.success(f"✅ ¡Se subieron {len(nuevos_registros)} archivos correctamente!")
                        import time
                        time.sleep(2)
                        st.rerun()
                    
    # ==========================================
