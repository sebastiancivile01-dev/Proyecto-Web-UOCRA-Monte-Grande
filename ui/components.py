"""Componentes visuales reutilizables de la aplicación."""

from html import escape

import streamlit as st


_VARIANTES_KPI = {"", "verde", "naranja", "violeta", "rojo"}


def tarjeta_kpi(titulo, valor, variante=""):
    """Muestra una tarjeta KPI con el diseño institucional."""

    variante_normalizada = str(variante).strip().lower()

    if variante_normalizada not in _VARIANTES_KPI:
        raise ValueError(f"Variante de KPI no válida: {variante}")

    clases = "tarjeta-kpi"

    if variante_normalizada:
        clases += f" {variante_normalizada}"

    st.markdown(
        (
            f'<div class="{clases}">'
            f'<div class="kpi-titulo">{escape(str(titulo))}</div>'
            f'<div class="kpi-valor">{escape(str(valor))}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )
