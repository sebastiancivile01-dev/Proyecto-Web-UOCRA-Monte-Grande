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
    st.title("🧹 Auditoría y Calidad de Datos")
    st.markdown("Radar automático de celdas vacías ordenado por el responsable con mayor cantidad de faltantes.")
    st.markdown("---")
    
    tablas_a_auditar = {
        "Padrón de Delegados": (df_delegados, "Nombre"),
        "Obras y Empresas": (df_obras, "Predio"),
        "Convenios Vigentes": (df_convenios, "Empresa"),
        "Agenda de Contactos": (df_contactos, "Nombre"),
        "Repositorio de Reclamos": (df_reclamos, "Nombre"),
        "Eventos UOCRA Mujeres": (df_eventos, "Titulo"),
        "Predios/Polos Base": (df_predios, "Nombre")
    }
    alertas_por_responsable = {}
    alertas_totales = 0
    
    # 1. MOTOR DE ESCANEO
    for nombre_tabla, (df_actual, col_id) in tablas_a_auditar.items():
        if df_actual.empty:
            continue
        
        for index, row in df_actual.iterrows():
            columnas_vacias = []
            
            for col in df_actual.columns:
                if "obs" in col.lower():
                    continue
                valor = row[col]
                if pd.isna(valor) or str(valor).strip() == "":
                    columnas_vacias.append(col)
            
            # REGLA EXCEPCIÓN 1: Convenios (Suma Fija vs Porcentaje)
            if "monto $" in columnas_vacias or "Monto %" in columnas_vacias:
                if "monto $" in columnas_vacias and "Monto %" not in columnas_vacias:
                    columnas_vacias.remove("monto $")
                elif "Monto %" in columnas_vacias and "monto $" not in columnas_vacias:
                    columnas_vacias.remove("Monto %")
                elif "monto $" in columnas_vacias and "Monto %" in columnas_vacias:
                    columnas_vacias.remove("monto $")
                    columnas_vacias.remove("Monto %")
                    columnas_vacias.append("Monto ($ o %)")
    
            # REGLA EXCEPCIÓN 2: Obras Aisladas (Sin Predio)
            identificador_personalizado = None
            if nombre_tabla == "Obras y Empresas" and "Predio" in columnas_vacias:
                columnas_vacias.remove("Predio") 
                
                empresa_val = str(row.get("Empresa", "")).strip()
                if empresa_val == "" or empresa_val == "nan":
                    empresa_val = "Empresa sin registrar"
                
                identificador_personalizado = f"Obra Aislada (Sin Predio) - {empresa_val}"
            
            # Procesamos si quedaron errores reales
            if columnas_vacias:
                if identificador_personalizado:
                    identificador = identificador_personalizado
                else:
                    identificador = str(row.get(col_id, f"Fila #{index+1}")).strip()
                    if identificador == "" or identificador == "nan":
                        identificador = f"Registro sin nombre (Fila #{index+1})"
                
                faltantes_str = ", ".join(columnas_vacias)
                responsables = []
                mensaje_alerta = ""
    
                # Lógica de Redacción Limpia
                if nombre_tabla == "Padrón de Delegados":
                    resp = str(row.get("Nombre", "")).strip()
                    responsables = [resp] if resp and resp != "nan" else ["Desconocido"]
                    mensaje_alerta = f"Tu Perfil Personal | Falta: {faltantes_str}"
                    
                elif nombre_tabla == "Obras y Empresas":
                    resp_str = str(row.get("Delegado", "")).strip()
                    if resp_str in ["", "nan", "Sin asignar"]:
                        responsables = ["Obras Sin Delegado Asignado"]
                    else:
                        responsables = [r.strip() for r in resp_str.split(",")]
                    
                    if "Obra Aislada" in identificador:
                        mensaje_alerta = f"{identificador} | Falta: {faltantes_str}"
                    else:
                        mensaje_alerta = f"Obra: {identificador} | Falta: {faltantes_str}"
                    
                else:
                    responsables = ["Gestión General (Comisión Directiva)"]
                    mensaje_alerta = f"{nombre_tabla} ({identificador}) | Falta: {faltantes_str}"
    
                # Guardamos la alerta
                for r in responsables:
                    if r not in alertas_por_responsable:
                        alertas_por_responsable[r] = []
                    alertas_por_responsable[r].append(mensaje_alerta)
                
                alertas_totales += 1
    
    # ==========================================
    # 2. MOTOR DE ORDENAMIENTO (MAYOR A MENOR)
    # ==========================================
    # Ordena primero por cantidad de alertas (negativo para que sea descendente) y luego por nombre
    responsables_ordenados = sorted(
        alertas_por_responsable.keys(),
        key=lambda r: (-len(alertas_por_responsable[r]), r)
    )
    
    # ==========================================
    # 3. GENERADOR DEL DOCUMENTO DESCARGABLE
    # ==========================================
    if alertas_totales > 0:
        texto_reporte = "=================================================\n"
        texto_reporte += "📋 REPORTE DE AUDITORÍA - UOCRA MONTE GRANDE\n"
        texto_reporte += f"📅 Fecha y Hora de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        texto_reporte += f"🚨 Total de datos faltantes detectados: {alertas_totales}\n"
        texto_reporte += "=================================================\n\n"
    
        for responsable in responsables_ordenados:
            cantidad = len(alertas_por_responsable[responsable])
            texto_reporte += f"👤 RESPONSABLE: {responsable.upper()} ({cantidad} pendientes)\n"
            texto_reporte += "-" * 50 + "\n"
            for alerta in alertas_por_responsable[responsable]:
                texto_reporte += f"  • {alerta}\n"
            texto_reporte += "\n"
    
        st.download_button(
            label="📄 Descargar Reporte de Faltantes (.txt)",
            data=texto_reporte,
            file_name=f"Auditoria_UOCRA_{datetime.now().strftime('%d_%m_%Y')}.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
    
    # ==========================================
    # 4. INTERFAZ VISUAL (Acordeones)
    # ==========================================
    if alertas_totales == 0:
        st.balloons()
        st.success("🏆 ¡Felicitaciones! Todas las bases de datos están 100% completas.")
    else:
        st.error(f"Se detectaron **{alertas_totales}** registros incompletos. Puede descargar el reporte arriba o revisarlos aquí:")
        
        for responsable in responsables_ordenados:
            alertas = alertas_por_responsable[responsable]
            icono = "🏢" if "Gestión General" in responsable or "Sin Delegado" in responsable else "👤"
    
            with st.expander(f"{icono} {responsable} ({len(alertas)} pendientes)", expanded=False):
                for alerta in alertas:
                    partes = alerta.split("| Falta: ")
                    if len(partes) == 2:
                        st.markdown(f"- 📍 **{partes[0].strip()}** | Falta: **{partes[1]}**")
                    else:
                        st.markdown(f"- 📍 {alerta}")
    
    
    # ==========================================
