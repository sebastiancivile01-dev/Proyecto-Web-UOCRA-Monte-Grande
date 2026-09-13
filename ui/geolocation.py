"""Componente mínimo de consentimiento de ubicación del navegador (CCv2)."""

from collections.abc import Callable

import streamlit as st


def _component():
    return st.components.v2.component(
    "uocra_current_location",
    html="<button id='location' type='button'></button><p id='message' aria-live='polite'></p>",
    css="""
        button { width: 100%; min-height: 48px; border: 0; border-radius: 8px;
                 background: var(--st-primary-color); color: white; font: inherit; font-weight: 600; }
        button:disabled { opacity: .7; }
        p { color: var(--st-text-color); font: inherit; margin: .5rem 0 0; }
    """,
    js="""
export default function(component) {
  const { parentElement, setTriggerValue } = component;
  const button = parentElement.querySelector('#location');
  const message = parentElement.querySelector('#message');
  if (!button || !message) return;
  button.textContent = 'Usar ubicación actual';
  const onClick = () => {
    if (!navigator.geolocation) {
      message.textContent = 'Este navegador no permite geolocalización.';
      setTriggerValue('error', 'unsupported');
      return;
    }
    button.disabled = true;
    message.textContent = 'Solicitando permiso de ubicación…';
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords = position.coords;
        setTriggerValue('location', {latitud: coords.latitude, longitud: coords.longitude, exactitud: coords.accuracy});
        button.disabled = false;
        message.textContent = 'Ubicación recibida.';
      },
      () => {
        setTriggerValue('error', 'unavailable');
        button.disabled = false;
        message.textContent = 'No se pudo usar la ubicación. Puede buscar o marcar el mapa.';
      },
      {enableHighAccuracy: true, timeout: 10000, maximumAge: 60000}
    );
  };
  button.addEventListener('click', onClick);
  return () => button.removeEventListener('click', onClick);
}
""",
    )


_CURRENT_LOCATION = _component()


def current_location(*, key: str, on_location_change: Callable[[], None] | None = None):
    global _CURRENT_LOCATION
    callbacks = {"on_location_change": on_location_change or (lambda: None), "on_error_change": lambda: None}
    try:
        return _CURRENT_LOCATION(key=key, **callbacks)
    except ValueError as error:
        # AppTest recrea el runtime; volver a registrar conserva el uso normal.
        if "is not registered" not in str(error):
            raise
        _CURRENT_LOCATION = _component()
        return _CURRENT_LOCATION(key=key, **callbacks)
