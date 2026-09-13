"""Bootstrap, carga de dependencias y router de la aplicacion."""

import folium
import google.generativeai as genai
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from streamlit_folium import folium_static

from auth.ui import require_login
from data.runtime import initialize
from safety import limpiar_sesion, modulo_permitido
from services.runtime import build as build_services
from ui.components import tarjeta_kpi
from ui.styles import (
    aplicar_estilos_estadisticas,
    aplicar_estilos_globales,
    aplicar_estilos_mapa,
    aplicar_estilos_mujeres,
)
from screens.context import ScreenContext
from screens import (
    abm,
    asistente,
    auditoria,
    calculadoras,
    documentacion,
    estadisticas,
    galeria,
    map as map_screen,
    mujeres,
    nominas,
    observaciones,
    propuestas,
    reclamos,
    simplified,
)
from screens import mode, navigation


def main() -> None:
    aplicar_estilos_globales()
    require_login(st, limpiar_sesion)

    app_mode = mode.render(st, limpiar_sesion)
    if app_mode is None:
        st.stop()

    data = initialize()
    services = build_services(st, data["df_cierres"])
    opcion = ""
    if app_mode == "complete":
        opcion = navigation.render(st, services["abrir_calendario_flotante"], limpiar_sesion)
    context = ScreenContext(
        st=st,
        pd=pd,
        folium=folium,
        folium_static=folium_static,
        genai=genai,
        build=build,
        MediaIoBaseUpload=MediaIoBaseUpload,
        service_account=service_account,
        tarjeta_kpi=tarjeta_kpi,
        aplicar_estilos_estadisticas=aplicar_estilos_estadisticas,
        aplicar_estilos_mapa=aplicar_estilos_mapa,
        aplicar_estilos_mujeres=aplicar_estilos_mujeres,
        modulo_permitido=modulo_permitido,
        opcion=opcion,
        **data,
        **services,
    )

    if app_mode == "simple":
        simplified.render(context)
        return

    handlers = {
        "1. 🗺️ Mapa Territorial": map_screen.render,
        "2. 📥 Carga de Datos (ABM)": abm.render,
        "3. 📋 Nóminas": nominas.render,
        "4. 🧮 Calculadoras": calculadoras.render,
        "5. ⚠️ Reclamos": reclamos.render,
        "6. 💜 UOCRA Mujeres": mujeres.render,
        "7. 🤝 Convenios y Documentación": documentacion.render,
        "8. 📊 Estadísticas": estadisticas.render,
        "9. 📸 Galería Multimedia": galeria.render,
        "10. 🤖 Chat GPT UOCRA": asistente.render,
        "11. 🧹 Auditoría": auditoria.render,
        "12. 📝 Observaciones por Empresa": observaciones.render,
    }
    handlers[opcion](context)
    propuestas.render(context, opcion)
