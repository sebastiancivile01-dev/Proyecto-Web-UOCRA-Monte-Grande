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
    st.title("📝 Historial y Novedades por Empresa")
    st.markdown("Registre y consulte anotaciones, alertas o historial gremial de cada empresa contratista.")
    
    tab_nueva, tab_historial = st.tabs(["➕ Nueva Observación", "📚 Ver Historial y Filtros"])
    
    # --- Pestaña 1: Carga de Datos ---
    with tab_nueva:
        with st.form("form_obs_empresa", clear_on_submit=True):
            empresa_sel = st.selectbox("Seleccione la Empresa:*", [""] + lista_empresas_historicas)
            obs_texto = st.text_area("Escriba la observación:*", placeholder="Ej: La empresa presenta atrasos en el pago de quincenas...")
            
            if st.form_submit_button("💾 Guardar Observación"):
                if not empresa_sel or not obs_texto.strip():
                    st.error("❌ Debe seleccionar una empresa y escribir una observación.")
                else:
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
                    usuario_act = st.session_state.get("usuario_rol", "Desconocido")
                    
                    nueva_obs = pd.DataFrame([{
                        "Fecha": fecha_hoy,
                        "Empresa": empresa_sel,
                        "Observacion": obs_texto.strip(),
                        "Usuario": usuario_act
                    }])
                    
                    df_observaciones = pd.concat([df_observaciones, nueva_obs], ignore_index=True)
                    if not guardar_db(df_observaciones, "Observaciones_Empresas"):
                        st.stop()
                    st.success("✅ Observación registrada con éxito.")
                    import time
                    time.sleep(1.5)
                    st.rerun()
    
    # --- Pestaña 2: Visualización con FILTROS INTELIGENTES ---
    with tab_historial:
        if df_observaciones.empty:
            st.info("No hay observaciones registradas en la base de datos.")
        else:
            # FILTROS SUPERIORES
            st.markdown("### 🔍 Panel de Búsqueda")
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                filtro_empresa = st.selectbox("🏢 Filtrar por Empresa:", ["Todas"] + lista_empresas_historicas)
            with col_f2:
                busqueda_texto = st.text_input("🔤 Buscar por palabra clave:", placeholder="Ej: Sueldos, Inspección...")
    
            # Aplicamos los filtros al DataFrame
            df_vista = df_observaciones.copy()
            
            # Filtro 1: Empresa
            if filtro_empresa != "Todas":
                df_vista = df_vista[df_vista['Empresa'] == filtro_empresa]
            
            # Filtro 2: Texto (si escribió algo)
            if busqueda_texto:
                df_vista = df_vista[df_vista['Observacion'].str.contains(busqueda_texto, case=False, na=False)]
                
            st.markdown("---")
    
            if df_vista.empty:
                st.warning("No se encontraron observaciones que coincidan con los filtros aplicados.")
            else:
                st.write(f"Se encontraron **{len(df_vista)}** observaciones:")
                
                # Invertimos para ver lo más reciente primero
                df_vista = df_vista.iloc[::-1].reset_index(drop=True)
                
                for idx, row in df_vista.iterrows():
                    # Tarjeta visual mejorada
                    st.markdown(f"""
                    <div style="border-left: 6px solid #ffc107; padding: 15px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; color: #666; font-size: 0.85rem; font-weight: bold;">
                            <span>📅 {row.get('Fecha', '')}</span>
                            <span>👤 Cargo: {row.get('Usuario', '')}</span>
                        </div>
                        <div style="color: #0033A0; font-size: 1.3rem; font-weight: 900; margin-top: 10px; text-transform: uppercase;">
                            🏢 {row.get('Empresa', '')}
                        </div>
                        <div style="color: #333; margin-top: 10px; padding: 10px; background: white; border-radius: 5px; border: 1px solid #eee; line-height: 1.5;">
                            {row.get('Observacion', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botón de eliminar (Solo para Admin)
                    if st.session_state.get("usuario_rol", "") == "Admin":
                        # Buscamos el ID original por si hay varios con la misma fecha
                        try:
                            idx_original = df_observaciones[(df_observaciones['Fecha'] == row['Fecha']) & 
                                                          (df_observaciones['Observacion'] == row['Observacion'])].index[0]
                            if st.button(f"🗑️ Eliminar Nota #{idx_original}", key=f"del_obs_{idx_original}"):
                                df_observaciones = df_observaciones.drop(idx_original)
                                if not guardar_db(df_observaciones, "Observaciones_Empresas"):
                                    st.stop()
                                st.success("✅ Eliminado.")
                                time.sleep(1)
                                st.rerun()
                        except Exception:
                            pass
    # ==========================================
    # PIE DE PÁGINA: BUZÓN GLOBAL DE PROPUESTAS
    # ==========================================
