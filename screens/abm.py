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
    if not modulo_permitido(st.session_state.get("usuario_rol"), opcion):
        st.error("Acceso no autorizado para este perfil.")
        st.stop()
    st.title("📥 Ingreso y Modificación de Datos")
    
    tab_predios, tab_obras, tab_delegados, tab_contactos = st.tabs(["🗺️ Predios/Polos", "🏗️ Obras y Empresas", "👥 Delegados y Colab.", "🏢 Contactos"])
    
    with tab_predios:
        st.subheader("Configuración de Polos Industriales")
        acc_predio = st.radio("Acción Predio:", ["➕ Nuevo Polo", "✏️ Modificar", "🗑️ Eliminar"], horizontal=True)
    
        if acc_predio == "➕ Nuevo Polo":
            with st.form("f_n_predio", clear_on_submit=True):
                p_nom = st.text_input("Nombre del Predio/Polo:*")
                c1, c2, c3 = st.columns(3)
                p_lat = c1.text_input("Latitud (Ej: -34.812):")
                p_lon = c2.text_input("Longitud (Ej: -58.531):")
                p_rad = c3.number_input("Radio de influencia (KM):", min_value=0.1, step=0.1, value=1.0)
                p_obs = st.text_area("Observaciones:")
    
                if st.form_submit_button("💾 Guardar Polo"):
                    if not p_nom:
                        st.error("❌ El nombre es obligatorio.")
                    else:
                        nuevo_predio = pd.DataFrame([{"Nombre": p_nom, "Latitud": float(p_lat) if p_lat else 0.0, "Longitud": float(p_lon) if p_lon else 0.0, "Radio_KM": p_rad, "Observaciones": p_obs}])
                        df_predios = pd.concat([df_predios, nuevo_predio], ignore_index=True)
                        if not guardar_db(df_predios, "Predios"):
                            st.stop()
                        st.success("✅ Polo registrado exitosamente.")
                        registrar_log("Agregó Polo")
                        st.rerun()
    
        elif acc_predio == "✏️ Modificar":
            if not df_predios.empty:
                predio_ed = st.selectbox("Seleccione el Polo a modificar:", df_predios['Nombre'].tolist())
                if predio_ed:
                    idx = df_predios[df_predios['Nombre'] == predio_ed].index[0]
                    dat = df_predios.loc[idx]
                    with st.form(f"f_e_predio_{idx}"):
                        nn = st.text_input("Nombre:*", value=str(dat.get('Nombre','')))
                        c1, c2, c3 = st.columns(3)
                        nlat = c1.text_input("Latitud:", value=str(dat.get('Latitud','')))
                        nlon = c2.text_input("Longitud:", value=str(dat.get('Longitud','')))
                        nrad = c3.number_input("Radio (KM):", min_value=0.1, step=0.1, value=float(dat.get('Radio_KM', 1.0)))
                        nobs = st.text_area("Observaciones:", value=str(dat.get('Observaciones','')))
    
                        if st.form_submit_button("🔄 Actualizar"):
                            df_predios.loc[idx, ['Nombre', 'Latitud', 'Longitud', 'Radio_KM', 'Observaciones']] = [nn, float(nlat) if nlat else 0.0, float(nlon) if nlon else 0.0, nrad, nobs]
                            if not guardar_db(df_predios, "Predios"):
                                st.stop()
                            st.success("✅ Polo actualizado.")
                            registrar_log("Actualizó Polo")
                            st.rerun()
    
        elif acc_predio == "🗑️ Eliminar":
            if not df_predios.empty:
                predio_el = st.selectbox("Seleccione el Polo a borrar:", [""] + df_predios['Nombre'].tolist())
                if st.button("🗑️ Eliminar Definitivamente") and predio_el:
                    df_predios = df_predios[df_predios['Nombre'] != predio_el]
                    if not guardar_db(df_predios, "Predios"):
                        st.stop()
                    st.success("✅ Polo eliminado.")
                    registrar_log("Eliminó Polo")
                    st.rerun()
    
    with tab_obras:
        acc_obras = st.radio("Acción Obras:", ["➕ Nueva Obra", "✏️ Modificar Obra", "🗑️ Eliminar Obra"], horizontal=True)
        
        if acc_obras == "➕ Nueva Obra":
            with st.form("f_n_obra", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    p_sel = st.selectbox("Predio/Polo Base:*", [""] + lista_predios_historicos, help="Si no está en la lista, créelo primero en la pestaña 'Predios/Polos'.")
                    e_sel = st.selectbox("Empresa:", ["➕ Nueva..."] + lista_empresas_historicas)
                    e_nueva = st.text_input("Si es Nueva, escríbala:")
                    d_sel = st.multiselect("Delegado/s:", lista_delegados_nombres)
                with col2:
                    jur = st.selectbox("Jurisdicción:", lista_jurisdicciones)
                    obr = st.number_input("Obreros:", min_value=0, step=1)
                    est = st.selectbox("Estado:", lista_estados)
                    lat, lon = st.text_input("Latitud:"), st.text_input("Longitud:")
                    
                    jur_r = False
                    if st.session_state.usuario_rol == "Admin":
                        jur_r = st.checkbox("🔒 Marca Especial: Jurisdicción R")
                
                if st.form_submit_button("💾 Guardar"):
                    p_fin = p_sel 
                    e_fin = e_nueva.strip() if e_sel == "➕ Nueva..." else e_sel
                    
                    if not p_fin: 
                        st.error("❌ Falta seleccionar un Predio/Polo Base.")
                    else:
                        # Auto-generar Obra_ID
                        nuevo_id = 1
                        if not df_obras.empty and 'Obra_ID' in df_obras.columns:
                            nuevo_id = int(pd.to_numeric(df_obras['Obra_ID'], errors='coerce').max() + 1)
    
                        df_obras = pd.concat([df_obras, pd.DataFrame([{
                            "Obra_ID": nuevo_id, "Predio": p_fin, "Empresa": e_fin, "Delegado": ", ".join(d_sel), 
                            "Obreros": obr, "Estado": est, "Jurisdiccion": jur, 
                            "Latitud": float(lat) if lat else None, 
                            "Longitud": float(lon) if lon else None, 
                            "Jurisdiccion_R": "SI" if jur_r else "", # Se guarda como SI
                            "Mujeres": 0  # Inicia en 0 para UOCRA Mujeres
                        }])], ignore_index=True)
                        if not guardar_db(df_obras, "Obras"):
                            st.stop()
                        st.success("Registrada!")
                        registrar_log(f"Alta de Obra #{nuevo_id}: {p_fin} ({e_fin})")
                        st.rerun()
    
        elif acc_obras == "✏️ Modificar Obra":
            if not df_obras.empty:
                opciones_obras = df_obras['Predio'].astype(str) + " (" + df_obras['Empresa'].astype(str) + ")"
                obra_ed = st.selectbox("Obra a modificar:", opciones_obras.tolist())
                
                if obra_ed:
                    idx = opciones_obras[opciones_obras == obra_ed].index[0]
                    dat = df_obras.loc[idx] 
                    del_v = [d for d in str(dat.get('Delegado','')).split(", ") if d in lista_delegados_nombres]
                    
                    with st.form(f"f_e_obra_{idx}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            np = st.text_input("Predio:*", value=str(dat.get('Predio','')))
                            ne = st.text_input("Empresa:", value=str(dat.get('Empresa','')))
                            nd = st.multiselect("Delegado/s:", lista_delegados_nombres, default=del_v)
                            nj = st.selectbox("Jurisdicción:", lista_jurisdicciones, index=lista_jurisdicciones.index(dat['Jurisdiccion']) if dat.get('Jurisdiccion') in lista_jurisdicciones else 0)
                        with col2:
                            no = st.number_input("Obreros:", min_value=0, step=1, value=int(dat.get('Obreros',0) if pd.notna(dat.get('Obreros')) else 0))
                            ne_est = st.selectbox("Estado:", lista_estados, index=lista_estados.index(dat['Estado']) if dat.get('Estado') in lista_estados else 0)
                            nlat = st.text_input("Latitud:", value="" if pd.isna(dat.get('Latitud')) else str(dat['Latitud']))
                            nlon = st.text_input("Longitud:", value="" if pd.isna(dat.get('Longitud')) else str(dat['Longitud']))
                            
                            if st.session_state.usuario_rol == "Admin":
                                es_jur_r = str(dat.get('Jurisdiccion_R', '')).strip().upper() in ['SI', 'SÍ']
                                nj_r = st.checkbox("🔒 Marca Especial: Jurisdicción R", value=es_jur_r)
                            else:
                                nj_r = str(dat.get('Jurisdiccion_R', '')).strip().upper() in ['SI', 'SÍ']
                        
                        if st.form_submit_button("🔄 Actualizar"):
                            obra_id_actual = dat.get('Obra_ID', '')
                            df_obras.loc[idx, ['Obra_ID', 'Predio', 'Empresa', 'Delegado', 'Obreros', 'Estado', 'Latitud', 'Longitud', 'Jurisdiccion', 'Jurisdiccion_R', 'Mujeres']] = [obra_id_actual, np, ne, ", ".join(nd), no, ne_est, float(nlat) if nlat else None, float(nlon) if nlon else None, nj, "SI" if nj_r else "", dat.get('Mujeres', 0)]
                            if not guardar_db(df_obras, "Obras"):
                                st.stop()
                            st.success("Actualizada!")
                            registrar_log("Actualizó Obra")
                            st.rerun()
    
        elif acc_obras == "🗑️ Eliminar Obra":
            if not df_obras.empty:
                opciones_obras_el = [""] + (df_obras['Predio'].astype(str) + " (" + df_obras['Empresa'].astype(str) + ")").tolist()
                obra_el = st.selectbox("Borrar:", opciones_obras_el, key="abm_borrar_obra")
                if st.button("🗑️ Eliminar", key="abm_eliminar_obra") and obra_el != "":
                    idx_el = opciones_obras_el.index(obra_el) - 1
                    df_obras = df_obras.drop(df_obras.index[idx_el])
                    if not guardar_db(df_obras, "Obras"):
                        st.stop()
                    st.success("Eliminada.")
                    registrar_log("Borró Obra")
                    st.rerun()
    
    with tab_delegados:
        acc_del = st.radio("Acción Delegados:", ["➕ Nuevo", "✏️ Modificar", "🗑️ Eliminar"], horizontal=True)
        
        if acc_del == "➕ Nuevo":
            with st.form("f_n_del", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nom = st.text_input("Nombre:*")
                    cuil = st.text_input("CUIL:")
                    cel = st.text_input("Celular:")
                    dom = st.text_input("Domicilio:")
                with col2:
                    nac = st.date_input("Nacimiento:", min_value=datetime(1900, 1, 1), format="DD/MM/YYYY")
                    corr = st.text_input("Correo:")
                    obs = st.text_area("Obs:")
                if st.form_submit_button("💾 Guardar") and nom:
                    df_delegados = pd.concat([df_delegados, pd.DataFrame([{"Nombre": nom, "CUIL": cuil, "Celular": cel, "Domicilio": dom, "Nacimiento": nac.strftime("%d/%m/%Y"), "Correo": corr, "Observacion": obs}])], ignore_index=True)
                    if not guardar_db(df_delegados, "Delegados"):
                        st.stop()
                    st.success("Agregado!")
                    registrar_log("Agregó Delegado")
                    st.rerun()
    
        elif acc_del == "✏️ Modificar":
            if not df_delegados.empty:
                del_ed = st.selectbox("Modificar:", df_delegados['Nombre'].tolist(), key="abm_modificar_delegado")
                if del_ed:
                    idx = df_delegados[df_delegados['Nombre'] == del_ed].index[0]
                    dat = df_delegados.loc[idx]
                    try: 
                        f_obj = datetime.strptime(str(dat.get('Nacimiento', '01/01/2000')), "%d/%m/%Y").date()
                    except: 
                        f_obj = datetime(2000, 1, 1).date()
                    
                    with st.form(f"f_e_del_{idx}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nn = st.text_input("Nombre:*", value=str(dat.get('Nombre','')))
                            ncu = st.text_input("CUIL:", value=str(dat.get('CUIL','')))
                            nce = st.text_input("Celular:", value=str(dat.get('Celular','')))
                            ndo = st.text_input("Domicilio:", value=str(dat.get('Domicilio','')))
                        with col2:
                            nna = st.date_input("Nacimiento:", value=f_obj, min_value=datetime(1900, 1, 1), format="DD/MM/YYYY")
                            nco = st.text_input("Correo:", value=str(dat.get('Correo','')))
                            nob = st.text_area("Obs:", value=str(dat.get('Observacion','')))
                        if st.form_submit_button("🔄 Actualizar"):
                            df_delegados.loc[idx, ['Nombre', 'CUIL', 'Celular', 'Domicilio', 'Nacimiento', 'Correo', 'Observacion']] = [nn, ncu, nce, ndo, nna.strftime("%d/%m/%Y"), nco, nob]
                            if not guardar_db(df_delegados, "Delegados"):
                                st.stop()
                            st.success("Actualizado!")
                            registrar_log("Actualizó Delegado")                            
                            st.rerun()
    
        elif acc_del == "🗑️ Eliminar":
            if not df_delegados.empty:
                del_el = st.selectbox("Borrar:", [""] + df_delegados['Nombre'].tolist(), key="abm_borrar_delegado")
                if st.button("🗑️ Eliminar", key="abm_eliminar_delegado") and del_el:
                    df_delegados = df_delegados[df_delegados['Nombre'] != del_el]
                    if not guardar_db(df_delegados, "Delegados"):
                        st.stop()
                    st.success("Eliminado.")
                    registrar_log("Borró Delegado")                     
                    st.rerun()
    
    with tab_contactos:
        acc_con = st.radio("Acción Contactos:", ["➕ Nuevo", "✏️ Modificar", "🗑️ Eliminar"], horizontal=True)
        
        if acc_con == "➕ Nuevo":
            with st.form("f_n_con", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    cnom = st.text_input("Nombre:*")
                    cemp_sel = st.selectbox("Empresa:", ["➕ Nueva..."] + lista_empresas_historicas)
                    cemp_n = st.text_input("Si es Nueva, escríbala:")
                with col2:
                    ccar = st.text_input("Cargo:")
                    cobs = st.text_area("Obs:")
                if st.form_submit_button("💾 Guardar") and cnom:
                    cemp_f = cemp_n.strip() if cemp_sel == "➕ Nueva..." else cemp_sel
                    if cemp_f:
                        df_contactos = pd.concat([df_contactos, pd.DataFrame([{"Nombre": cnom, "Cargo": ccar, "Empresa": cemp_f, "Observaciones": cobs}])], ignore_index=True)
                        if not guardar_db(df_contactos, "Contactos"):
                            st.stop()
                        st.success("Guardado!")
                        registrar_log("Guardó Contacto") 
                        st.rerun()
    
        elif acc_con == "✏️ Modificar":
            if not df_contactos.empty:
                ops = df_contactos['Nombre'] + " (" + df_contactos['Empresa'] + ")"
                con_ed = st.selectbox("Modificar:", ops.tolist(), key="abm_modificar_contacto")
                if con_ed:
                    idx = ops[ops == con_ed].index[0]
                    dat = df_contactos.loc[idx]
                    with st.form(f"f_e_con_{idx}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nn = st.text_input("Nombre:*", value=str(dat.get('Nombre','')))
                            ne = st.text_input("Empresa:*", value=str(dat.get('Empresa','')))
                        with col2:
                            nc = st.text_input("Cargo:", value=str(dat.get('Cargo','')))
                            no = st.text_area("Obs:", value=str(dat.get('Observaciones','')))
                        if st.form_submit_button("🔄 Actualizar"):
                            df_contactos.loc[idx, ['Nombre', 'Cargo', 'Empresa', 'Observaciones']] = [nn, nc, ne, no]
                            if not guardar_db(df_contactos, "Contactos"):
                                st.stop()
                            st.success("Actualizado!")
                            registrar_log("Actualizó Contacto") 
                            st.rerun()
    
        elif acc_con == "🗑️ Eliminar":
            if not df_contactos.empty:
                ops_el = [""] + (df_contactos['Nombre'] + " (" + df_contactos['Empresa'] + ")").tolist()
                con_el = st.selectbox("Borrar:", ops_el, key="abm_borrar_contacto")
                if st.button("🗑️ Eliminar", key="abm_eliminar_contacto") and con_el:
                    idx = ops_el.index(con_el) - 1
                    df_contactos = df_contactos.drop(df_contactos.index[idx])
                    if not guardar_db(df_contactos, "Contactos"):
                        st.stop()
                    st.success("Eliminado.")
                    registrar_log("Eliminó Contacto") 
                    st.rerun()
    
    # ==========================================
