import pandas as pd
from datetime import datetime
import streamlit as st


def render(ctx, opcion):
    guardar_db = ctx.guardar_db
    registrar_log = ctx.registrar_log
    df_propuestas = ctx.df_propuestas
    lista_empresas_historicas = ctx.lista_empresas_historicas
    st.markdown("---") # Línea divisoria
    
    with st.expander("💡 Buzón de Sugerencias y Propuestas (Sistemas)", expanded=False):
        st.markdown("<p style='font-size:0.9rem; color:#666;'>Envíe sugerencias, reporte de errores o ideas de mejora directamente al equipo de desarrollo.</p>", unsafe_allow_html=True)
        
        with st.form("f_prop_global", clear_on_submit=True):
            prop_texto = st.text_area("Describa su propuesta o reporte:")
            
            if st.form_submit_button("📤 Enviar Propuesta al Repositorio"):
                if not prop_texto.strip():
                    st.error("❌ Escriba una propuesta primero.")
                else:
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
                    usuario_actual = st.session_state.usuario_rol
                    
                    nueva_prop = pd.DataFrame([{
                        "Fecha": fecha_hoy, 
                        "Usuario": usuario_actual, 
                        "Propuesta": prop_texto, 
                        "Estado": "Pendiente"
                    }])
                    
                    df_propuestas = pd.concat([df_propuestas, nueva_prop], ignore_index=True)
                    if not guardar_db(df_propuestas, "Propuestas"):
                        st.stop()
                    st.success("✅ ¡Propuesta enviada exitosamente! Gracias por colaborar.")
                    registrar_log("Envió una nueva propuesta al Buzón")
    
      
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
