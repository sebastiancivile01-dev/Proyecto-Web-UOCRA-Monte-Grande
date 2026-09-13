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
    st.title("🤝 Convenios y Documentación")
    st.markdown("Repositorio oficial de actas, paritarias y documentos de la Seccional.")
    
    seccion_elegida = st.radio("Seleccione el apartado a gestionar:", ["1️⃣ Convenios", "2️⃣ Documentación"], horizontal=True)
    st.markdown("---")
    
    if seccion_elegida == "1️⃣ Convenios":
        tab_n_conv, tab_ver_conv = st.tabs(["➕ Gestionar Convenio", "📋 Ver Convenios Cargados"])
        
        with tab_n_conv:
            acc_conv = st.radio("Acción:", ["➕ Nuevo Convenio", "✏️ Modificar", "🗑️ Eliminar"], horizontal=True)
            
            if acc_conv == "➕ Nuevo Convenio":
                with st.form("f_n_conv", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        c_emp = st.selectbox("Empresa:*", [""] + lista_empresas_historicas)
                        c_vig = st.text_input("Vigencia (Ej: Marzo 2026 - Mayo 2026):")
                    with col2:
                        c_monto = st.text_input("Monto Extra $:")
                        c_porc = st.text_input("Monto Extra %:")
                    
                    c_det = st.text_area("Detalles de Escala / CCT (Descripción):*")
                    archivo_pdf = st.file_uploader("📄 Arrastrá el PDF del Convenio aquí", type=["pdf"])
                    
                    if st.form_submit_button("💾 Guardar Convenio"):
                        if not c_emp or not c_det:
                            st.error("❌ Empresa y Detalles son obligatorios.")
                        else:
                            c_link = "" 
                            
                            if archivo_pdf is not None:
                                with st.spinner("Subiendo archivo a Google Cloud..."):
                                    codigo_unico = str(uuid.uuid4())[:8]
                                    nombre_limpio = f"{codigo_unico}_Convenio_{c_emp}.pdf".replace(" ", "_")
                                    c_link = subir_archivo_drive(archivo_pdf, nombre_limpio)
                            
                                    if not c_link:
                                        st.error("⚠️ Error al subir el PDF.")
                                        st.stop()
                            
                            nuevo_conv = pd.DataFrame([{
                                "Empresa": c_emp, "Detalle_Convenio": c_det, 
                                "monto $": c_monto, "Monto %": c_porc, "Vigencia": c_vig, "Link_PDF": c_link
                            }])
                            df_convenios = pd.concat([df_convenios, nuevo_conv], ignore_index=True)
                            if not guardar_db(df_convenios, "Convenios"):
                                st.stop()
                            if c_link:
                                st.success("✅ Archivo subido con éxito.")
                                registrar_log("Subió PDF de Convenio")
                            st.success("✅ Convenio registrado exitosamente.")
                            import time
                            time.sleep(2)
                            st.rerun()
    
            elif acc_conv == "✏️ Modificar":
                if not df_convenios.empty:
                    opciones_c = df_convenios['Empresa'] + " - " + df_convenios['Vigencia']
                    c_ed = st.selectbox("Seleccione el Convenio:", opciones_c.tolist())
                    if c_ed:
                        idx = opciones_c.tolist().index(c_ed)
                        dat = df_convenios.loc[idx]
                        with st.form(f"f_e_conv_{idx}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                e_emp = st.text_input("Empresa:*", value=str(dat.get('Empresa', '')))
                                e_vig = st.text_input("Vigencia:", value=str(dat.get('Vigencia', '')))
                            with col2:
                                e_monto = st.text_input("Monto Extra $:", value=str(dat.get('monto $', '')))
                                e_porc = st.text_input("Monto Extra %:", value=str(dat.get('Monto %', '')))
                            e_det = st.text_area("Detalles de Escala / CCT:*", value=str(dat.get('Detalle_Convenio', '')))
                            e_link = st.text_input("🔗 Archivo de Respaldo (Link PDF):", value=str(dat.get('Link_PDF', '')))
                            
                            if st.form_submit_button("🔄 Actualizar"):
                                df_convenios.at[idx, 'Empresa'] = e_emp
                                df_convenios.at[idx, 'Detalle_Convenio'] = e_det
                                df_convenios.at[idx, 'monto $'] = e_monto
                                df_convenios.at[idx, 'Monto %'] = e_porc
                                df_convenios.at[idx, 'Vigencia'] = e_vig
                                df_convenios.at[idx, 'Link_PDF'] = e_link
                                if not guardar_db(df_convenios, "Convenios"):
                                    st.stop()
                                st.success("✅ Actualizado.")
                                st.rerun()
                                
            elif acc_conv == "🗑️ Eliminar":
                if not df_convenios.empty:
                    opciones_el = [""] + (df_convenios['Empresa'] + " - " + df_convenios['Vigencia']).tolist()
                    c_el = st.selectbox("Borrar:", opciones_el)
                    if st.button("🗑️ Eliminar") and c_el != "":
                        idx_el = opciones_el.index(c_el) - 1
                        df_convenios = df_convenios.drop(df_convenios.index[idx_el])
                        if not guardar_db(df_convenios, "Convenios"):
                            st.stop()
                        st.success("Eliminado.")
                        st.rerun()
    
        with tab_ver_conv:
            busq_c = st.text_input("🔍 Buscar Empresa:", key="b_conv")
            df_mostrar_conv = df_convenios.copy()
            if busq_c:
                df_mostrar_conv = df_mostrar_conv[df_mostrar_conv['Empresa'].astype(str).str.contains(busq_c, case=False, na=False, regex=False)]
            
            for _, row in df_mostrar_conv.iterrows():
                with st.expander(f"🏢 {row.get('Empresa', '')} | Vigencia: {row.get('Vigencia', '')}"):
                    st.write(f"**Detalle:** {row.get('Detalle_Convenio', '')}")
                    st.write(f"**Monto $:** {row.get('monto $', '-')} | **Monto %:** {row.get('Monto %', '-')}")
                    link_pdf = str(row.get('Link_PDF', '')).strip()
                    if link_pdf and link_pdf.startswith("http"):
                        st.markdown(f'<a href="{link_pdf}" target="_blank" style="display: inline-block; padding: 8px 16px; background-color: #0033A0; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">📄 Abrir Documento PDF</a>', unsafe_allow_html=True)
    
    # ESTO TIENE QUE ESTAR SANGRAMIENTO NIVEL 1 (Adentro del Módulo 7)
    elif seccion_elegida == "2️⃣ Documentación":
        tab_subir, tab_ver = st.tabs(["📤 Cargar Documento", "📚 Ver Documentación"])
        
        with tab_subir:
            with st.form("form_doc", clear_on_submit=True):
                d_tit = st.text_input("Título del Documento:*")
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    d_fec = st.date_input("Fecha:", format="DD/MM/YYYY")
                with col_d2:
                    d_vig = st.text_input("Vigencia (Opcional):")
                    
                d_obs = st.text_area("Observaciones (Opcional):")
                # Acá pedimos UN SOLO ARCHIVO, y solo PDF
                archivo_doc = st.file_uploader("📄 Arrastrá el PDF del Documento aquí", type=["pdf"])
                
                if st.form_submit_button("💾 Guardar Documento"):
                    if not d_tit:
                        st.error("❌ El Título es obligatorio.")
                    else:
                        d_link = ""
                        if archivo_doc is not None:
                            with st.spinner("Subiendo archivo a Google Cloud..."):
                                nombre_limpio = f"Doc_{d_tit}.pdf".replace(" ", "_")
                                d_link = subir_archivo_drive(archivo_doc, nombre_limpio)
                                if not d_link:
                                    st.error("⚠️ Error al subir el PDF.")
                                    st.stop()
                                    
                        nuevo_doc = pd.DataFrame([{
                            "Titulo": d_tit, "Fecha": d_fec.strftime("%d/%m/%Y"), 
                            "Vigencia": d_vig, "Observaciones": d_obs, "Link_PDF": d_link
                        }])
                        df_documentos = pd.concat([df_documentos, nuevo_doc], ignore_index=True)
                        if not guardar_db(df_documentos, "Documentos"):
                            st.stop()
                        if d_link:
                            st.success("✅ Archivo subido con éxito")
                            registrar_log("Subió Archivo")
                        st.success("✅ ¡Documento guardado!")
                        registrar_log("Guardó Documento") 
                        import time
                        time.sleep(2)
                        st.rerun()
    
        with tab_ver:
            if df_documentos.empty:
                st.info("No hay documentos subidos todavía.")
            else:
                # LLAVE DE SEGURIDAD 1: Buscador único
                b_doc = st.text_input("🔍 Buscar por Título:", key="buscador_docs_unico")
                df_doc_view = df_documentos.copy()
                if b_doc:
                    df_doc_view = df_doc_view[df_doc_view['Titulo'].astype(str).str.contains(b_doc, case=False, na=False, regex=False)]
                
                # Usamos enumerate para generar un ID 100% único por cada tarjeta
                for num_fila, (idx, doc) in enumerate(df_doc_view.iterrows()):
                    
                    # 1. Dibujamos la tarjeta visual del documento
                    st.markdown(f"""
                    <div style="border-left: 5px solid #0033A0; padding: 15px; background-color: #f8f9fa; border-radius: 8px; margin-top: 15px; margin-bottom: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="color: #666; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">📅 {doc.get('Fecha', '')} | Vigencia: {doc.get('Vigencia', 'N/A')}</div>
                        <div style="color: #0033A0; font-size: 1.2rem; font-weight: 900; margin-top: 5px;">{doc.get('Titulo', '')}</div>
                        <div style="color: #333; margin-top: 5px;"><i>"{doc.get('Observaciones', '')}"</i></div>
                        <br>
                        <a href="{doc.get('Link_PDF', '#')}" target="_blank" style="background-color: #28a745; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 0.9rem;">📥 Abrir Archivo</a>
                    </div>
                    """, unsafe_allow_html=True)
    
                    # 2. CAPA DE SEGURIDAD: Chequeamos el rol del usuario
                    usuario_actual = st.session_state.get("usuario_rol", "")
                    
                    if usuario_actual == "Admin":
                        # LLAVE DE SEGURIDAD 2: Botón de eliminar blindado
                        if st.button("🗑️ Eliminar", key=f"del_doc_{idx}_unico_{num_fila}"):
                            try:
                                # Borramos la fila exacta del dataframe original
                                df_documentos = df_documentos.drop(idx)
                                # Guardamos en la base de datos
                                if not guardar_db(df_documentos, "Documentos"):
                                    st.stop()
                                st.success("✅ Documento eliminado del sistema.")
                                registrar_log("Eliminó Documento") 
                                import time
                                time.sleep(1)
                                st.rerun()
                            except KeyError:
                                st.error("⚠️ El documento ya no existe en la base.")
                            
                    st.write("") # Un espacio en blanco para separar el siguiente documento
    
    # ==========================================
