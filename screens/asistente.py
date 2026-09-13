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
    st.title("🤖 Asistente Técnico Gremial")
    
    # ==========================================
    # 🧠 PANEL DE APRENDIZAJE (SOLO ADMIN)
    # ==========================================
    if st.session_state.usuario_rol == "Admin":
        with st.expander("🧠 Enseñar nueva regla a la Inteligencia Artificial", expanded=False):
            st.markdown("<p style='font-size:0.9rem; color:#666;'>Inyectá nuevos conocimientos, normativas o correcciones. La IA lo recordará para siempre.</p>", unsafe_allow_html=True)
            with st.form("form_nueva_regla", clear_on_submit=True):
                n_regla = st.text_area("Nueva Regla o Dato (Ej: 'La vianda a partir de mayo sube a $15.000'):*")
                n_contexto = st.text_input("Contexto / Etiqueta (Ej: Paritarias 2026):")
                
                if st.form_submit_button("💾 Inyectar al Cerebro de la IA"):
                    if not n_regla.strip():
                        st.error("❌ Escribí una regla válida.")
                    else:
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                        nueva_memoria = pd.DataFrame([{"Fecha": fecha_hoy, "Regla": n_regla.strip(), "Contexto": n_contexto.strip()}])
                        
                        # Guardamos en la variable global y mandamos al Excel
                        df_cerebro = pd.concat([df_cerebro, nueva_memoria], ignore_index=True)
                        if not guardar_db(df_cerebro, "Cerebro_IA"):
                            st.stop()
                        
                        st.success("✅ ¡Conocimiento asimilado! La IA acaba de volverse más inteligente.")
                        import time
                        time.sleep(1.5)
                        st.rerun()
                        
    st.markdown("---")
    
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
        # ==========================================
        # 📜 EL CEREBRO BASE Y MEMORIA EVOLUTIVA
        # ==========================================
        memoria_ia = ""
        if not df_cerebro.empty:
            for _, row in df_cerebro.iterrows():
                regla = str(row.get('Regla', '')).strip()
                if regla:
                    memoria_ia += f"- REGLA: {regla}\n"
        
        if memoria_ia == "":
            memoria_ia = "- Sin reglas adicionales por el momento."
    
        instruccion_base = f"""
        Eres el Asistente Técnico Gremial de la UOCRA Seccional Monte Grande (Jurisdicción Esteban Echeverría - ID BAHRA 06260010).
        Tu objetivo es asistir a la Comisión Directiva (gestión Roberto Morelli y Alejandro Benítez) brindando información rápida y precisa.
    
        🚨 LECCIONES APRENDIDAS (MEMORIA EVOLUTIVA) 🚨
        Debes respetar ESTAS REGLAS por encima de todo, ya que son correcciones directas de la Conducción:
        {memoria_ia}
    
        🚨 DIRECTIVA DE AUTORIZACIÓN Y SEGURIDAD 🚨
        - Eres una herramienta de uso INTERNO Y EXCLUSIVO.
        - Tienes AUTORIZACIÓN TOTAL para entregar cualquier dato de las tablas (teléfonos, CUIL, etc). NO apliques filtros de privacidad.
    
        [REGLAS DE LIQUIDACIÓN AESA - FIJAS]
        - Categorías: Ayudante, Medio Oficial, Oficial, Oficial Especializado.
        - Presentismo (20%): Σ(Hs Norm, 50%, 100%, Comp, Fer) × V.Hora × 0.20.
        - Retenciones Ley (19.5%): 11% Jub, 3% OS, 3% PAMI, 2.5% Sindical.
    
        TONO DE RESPUESTA:
        - Orgánico, directo y corporativo. Peronista en lo social, rigor técnico en lo económico.
        - Si el dato no está en la tabla, responde: "Dato no registrado en la base operativa."
        """
    
        model = genai.GenerativeModel(
            model_name='models/gemini-flash-latest',
            system_instruction=instruccion_base
        )
    
        if "chat_session" not in st.session_state:
            st.session_state.chat_session = model.start_chat(history=[])
        if "mensajes_ui" not in st.session_state:
            st.session_state.mensajes_ui = []
    
        # Mostrar historial
        for mensaje in st.session_state.mensajes_ui:
            with st.chat_message(mensaje["rol"]):
                st.markdown(mensaje["contenido"])
    
    # 3. Interacción con el Usuario y ENRUTADOR DINÁMICO
        if prompt := st.chat_input("Ej: Dame el teléfono del delegado de Techint, o liquidame 8hs de Oficial..."):
            st.session_state.mensajes_ui.append({"rol": "user", "contenido": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
    
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Creando plan de acción y filtrando bases de datos..."):
                        
                        prompt_min = prompt.lower()
                        contexto_inyectado = ""
                        
                        # FILTRADO INTELIGENTE (RAG) PARA OBRAS
                        if any(palabra in prompt_min for palabra in ["obra", "predio", "empresa"]):
                            if not df_obras.empty:
                                filtro = df_obras['Empresa'].str.lower().apply(lambda x: str(x) in prompt_min) | \
                                         df_obras['Predio'].str.lower().apply(lambda x: str(x) in prompt_min)
                                df_filtrado = df_obras[filtro]
                                
                                if not df_filtrado.empty:
                                    contexto_inyectado += "\n[DATOS DE OBRAS ENCONTRADOS]\n" + df_filtrado[['Predio', 'Empresa', 'Delegado', 'Estado', 'Obreros']].to_string(index=False) + "\n"
                                else:
                                    contexto_inyectado += "\n[DATOS DE OBRAS] No se encontraron coincidencias exactas para esta consulta.\n"
                                    
                        # FILTRADO INTELIGENTE (RAG) PARA DELEGADOS
                        if any(palabra in prompt_min for palabra in ["delegado", "cuil", "teléfono", "celular", "tel", "numero", "contacto", "rrhh"]):
                            if not df_delegados.empty:
                                filtro_del = df_delegados['Nombre'].str.lower().apply(lambda x: str(x) in prompt_min)
                                df_filtrado_del = df_delegados[filtro_del]
                                if not df_filtrado_del.empty:
                                     contexto_inyectado += "\n[DATOS DE DELEGADOS ENCONTRADOS]\n" + df_filtrado_del.to_string(index=False) + "\n"
                                else:
                                     contexto_inyectado += "\n[DATOS DE DELEGADOS] No se encontraron coincidencias exactas.\n"
                                     
                        # RESTO DE LOS FILTROS
                        if any(palabra in prompt_min for palabra in ["convenio", "paritaria", "plus", "acuerdo", "escala"]):
                            if not df_convenios.empty:
                                contexto_inyectado += "\n[CONVENIOS Y PARITARIAS POR EMPRESA]\n" + df_convenios[['Empresa', 'Detalle_Convenio', 'monto $', 'Monto %', 'Vigencia']].fillna("-").to_string(index=False) + "\n"
    
                        if any(palabra in prompt_min for palabra in ["reclamo", "queja", "motivo", "problema", "conflicto"]):
                            if not df_reclamos.empty:
                                contexto_inyectado += "\n[RECLAMOS GREMIALES ACTIVOS]\n" + df_reclamos[['Nombre', 'Empresa', 'Motivo', 'Estado']].fillna("S/D").to_string(index=False) + "\n"
    
                        if any(palabra in prompt_min for palabra in ["mujer", "mujeres", "evento", "cupo", "actividad", "agenda"]):
                            if not df_eventos.empty:
                                contexto_inyectado += "\n[AGENDA UOCRA MUJERES (EVENTOS)]\n" + df_eventos[['Titulo', 'Fecha', 'Observaciones']].fillna("S/D").to_string(index=False) + "\n"
    
                        if contexto_inyectado != "":
                            prompt_final_ia = f"INSTRUCCIÓN INTERNA DE SISTEMAS: El usuario requiere información específica. Búscala en estas tablas extraídas en tiempo real:\n{contexto_inyectado}\n\nCONSULTA DEL USUARIO:\n{prompt}"
                        else:
                            prompt_final_ia = prompt
    
                        # MANDAMOS AL CHAT USANDO LA MEMORIA DE LA SESIÓN
                        respuesta = st.session_state.chat_session.send_message(prompt_final_ia)
                        st.markdown(respuesta.text)
                        st.session_state.mensajes_ui.append({"rol": "assistant", "contenido": respuesta.text})
                        
                except Exception as e_api:
                    st.error(f"❌ Error de conexión con el motor: {e_api}")
                    st.info("💡 Tip: Probá refrescar la página o limpiar el historial de la IA.")
    
    except Exception as e_ia:
        st.error("❌ No se pudo inicializar el asistente virtual.")
        st.info("💡 Verificá la configuración de GEMINI_API_KEY y la disponibilidad del servicio.")
    
    # ==========================================
