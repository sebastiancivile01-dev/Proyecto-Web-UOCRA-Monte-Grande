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
    # Inyectamos CSS para pintar el módulo de violeta sin romper el resto
    # Aplica el diseño violeta propio del módulo.
    aplicar_estilos_mujeres()
    
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
                with c_m1:
                    tarjeta_kpi("Operarios Totales", tot_obreros)
    
                with c_m2:
                    tarjeta_kpi(
                        "Mujeres Asignadas",
                        mujeres_actual,
                        variante="violeta",
                    )
    
                with c_m3:
                    tarjeta_kpi(
                        "% de Participación",
                        f"{porcentaje:.1f}%",
                        variante="violeta",
                    )                
                with st.form(f"f_cupo_{idx_m}"):
                    n_mujeres = st.number_input("Modificar Cantidad de Mujeres (Cupo):", min_value=0, step=1, value=mujeres_actual)
                    if st.form_submit_button("💾 Guardar / Actualizar Cupo"):
                        import time # Importamos el reloj para hacer una pausa visual
                        try:
                            # Forzamos que el dato sea entero para que Google Sheets lo tome perfecto
                            df_obras.at[idx_m, 'Mujeres'] = int(n_mujeres)
                            if not guardar_db(df_obras, "Obras"):
                                st.stop()
                            
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
                        if not guardar_db(df_eventos, "Mujeres_Eventos"):
                            st.stop()
                        st.success("✅ Evento agendado correctamente.")
                        st.rerun()
                        
        elif acc_ev == "🗑️ Eliminar Evento":
            if not df_eventos.empty:
                ops_ev = df_eventos['Titulo'] + " (" + df_eventos['Fecha'] + ")"
                ev_el = st.selectbox("Seleccione Evento a borrar:", [""] + ops_ev.tolist())
                if st.button("🗑️ Eliminar") and ev_el != "":
                    idx_el = ops_ev.tolist().index(ev_el)
                    df_eventos = df_eventos.drop(df_eventos.index[idx_el])
                    if not guardar_db(df_eventos, "Mujeres_Eventos"):
                        st.stop()
                    st.success("Evento borrado.")
                    st.rerun()
        
        st.markdown("---")
        if not df_eventos.empty:
            st.dataframe(df_eventos, use_container_width=True)
    # ==========================================
