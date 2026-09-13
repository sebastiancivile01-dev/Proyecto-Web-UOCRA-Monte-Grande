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
    st.title("🧮 Módulo de Cálculos Gremiales")
    
    # --- CONEXIÓN A LA BASE DE PARITARIAS ---
    def limpiar_numero(val, default):
        try:
            if str(val).strip() == "": return default
            limpio = str(val).replace("$", "").replace(" ", "")
            if "," in limpio and "." in limpio: limpio = limpio.replace(".", "").replace(",", ".")
            elif "," in limpio: limpio = limpio.replace(",", ".")
            return float(limpio)
        except:
            return default
    
    if not df_paritarias.empty:
        ultima_paritaria = df_paritarias.iloc[-1]
        val_ay = limpiar_numero(ultima_paritaria.get("Ayudante"), 5470.0)
        val_mo = limpiar_numero(ultima_paritaria.get("Medio_Oficial"), 6000.0)
        val_of = limpiar_numero(ultima_paritaria.get("Oficial"), 6800.0)
        val_of_esp = limpiar_numero(ultima_paritaria.get("Oficial_Especializado"), 7500.0)
        val_viatico = limpiar_numero(ultima_paritaria.get("Viatico"), 15733.30)
        periodo_vigente = str(ultima_paritaria.get("Periodo_Vigencia", "Desconocido"))
    else:
        val_ay, val_mo, val_of, val_of_esp, val_viatico = 5470.0, 6000.0, 6800.0, 7500.0, 15733.30
        periodo_vigente = "Valores de Emergencia (Falta cargar en BD)"
    
    # ==========================================
    # MEMORIA DE NAVEGACIÓN (DASHBOARD)
    # ==========================================
    if 'calc_activa' not in st.session_state:
        st.session_state.calc_activa = "Menu"
    
    if st.session_state.calc_activa == "Menu":
        st.markdown("### Seleccione la herramienta de auditoría:")
        st.write("") # Espacio
        
        # Dibujamos las 4 Tarjetas Gigantes
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        if col_t1.button("🧾 Liquidación\nQuincena", use_container_width=True): 
            st.session_state.calc_activa = "Quincena"
            st.rerun()
        if col_t2.button("💰 Cese Laboral\n(IERIC)", use_container_width=True): 
            st.session_state.calc_activa = "IERIC"
            st.rerun()
        if col_t3.button("🏖️ Cálculo\nVacaciones", use_container_width=True): 
            st.session_state.calc_activa = "Vacaciones"
            st.rerun()
        if col_t4.button("🎄 Aguinaldo\n(SAC)", use_container_width=True): 
            st.session_state.calc_activa = "SAC"
            st.rerun()
        
        # Tarjeta exclusiva para el Admin
        if st.session_state.get("usuario_rol", "") == "Admin":
            st.markdown("---")
            if st.button("📈 Gestión Histórica de Paritarias (Exclusivo Admin)", use_container_width=True): 
                st.session_state.calc_activa = "Paritarias"
                st.rerun()
    
    # ==========================================
    # PANTALLAS DE LAS CALCULADORAS
    # ==========================================
    else:
        # EL BOTÓN PARA VOLVER ARRIBA DE TODO A LA IZQUIERDA
        col_btn, _ = st.columns([1, 3])
        if col_btn.button("⬅️ Volver al Panel"):
            st.session_state.calc_activa = "Menu"
            st.rerun()
        
        st.markdown("---")
    
    # ---------------------------------------------------------
        # 1. PANTALLA: CALCULADORA DE QUINCENA
        # ---------------------------------------------------------
        if st.session_state.calc_activa == "Quincena":
            import datetime
            st.markdown("### 🧾 Auditoría de Recibo Quincenal")
            
            modo_carga = st.radio("⚙️ Seleccione el método de carga:", ["🤖 Carga Automática (Inteligente)", "✍️ Carga Manual (Clásica)"], horizontal=True)
            formato_liq = st.selectbox("📝 Formato Liquidativo (Convenio de Empresa):", ["AESA"])
            st.markdown("---")
    
            # =================================================================
            # 1. DATOS DEL COMPAÑERO Y ESCALA (MODIFICABLE)
            # =================================================================
            st.markdown("### 👤 1. Datos y Escala Salarial")
            c_dat1, c_dat2, c_dat3 = st.columns(3)
            n_emp = c_dat1.text_input("Nombre del Compañero:")
            e_liq = c_dat2.selectbox("Empresa:", ["AESA", "Estándar", "DF Soluciones-Tec"])
            cat = c_dat3.selectbox("Categoría:", ["Ayudante", "Medio-Oficial", "Oficial", "Oficial-Especializado"])
            
            # Traemos los valores sugeridos de la base de datos
            cat_valores = {"Ayudante": val_ay, "Medio-Oficial": val_mo, "Oficial": val_of, "Oficial-Especializado": val_of_esp}
            vh_sugerido = float(cat_valores[cat])
            viatico_sugerido = float(val_viatico)
            
            # FILA DE VALORES MODIFICABLES
            c_vh1, c_vh2, c_vh3 = st.columns([1.5, 1.5, 2.5])
            vh = c_vh1.number_input("Valor Hora ($):", value=vh_sugerido, min_value=0.0, step=100.0, help="Modifique para recibos antiguos.")
            v_viatico_final = c_vh2.number_input("Viático Diario ($):", value=viatico_sugerido, min_value=0.0, step=500.0, help="Modifique para recibos antiguos.")
            c_vh3.info(f"💡 Sugerencia actual: **{periodo_vigente}**")
            st.markdown("---")
    
            # =================================================================
            # 2. CONFIGURACIÓN GENERAL Y HORAS
            # =================================================================
            if modo_carga == "🤖 Carga Automática (Inteligente)":
                st.markdown("### 📅 2. Parámetros de la Quincena y Horario")
                c_f1, c_f2 = st.columns(2)
                hoy = datetime.date.today()
                f_inicio = c_f1.date_input("Día de Inicio de Quincena", hoy.replace(day=1))
                f_fin = c_f2.date_input("Día de Fin de Quincena", hoy.replace(day=15))
    
                st.markdown("**⏱️ Horario Habitual (Lunes a Viernes)**")
                c_h1, c_h2, c_h3 = st.columns(3)
                h_ent_lv = c_h1.time_input("Entrada L-V", datetime.time(7, 0))
                h_sal_lv = c_h2.time_input("Salida L-V", datetime.time(17, 0))
                paga_almuerzo = c_h3.selectbox("Hora de Almuerzo:", ["Se descuenta (1 hora diaria)", "Jornada continua (No se descuenta)"])
                
                st.markdown("**❌ Ausencias y Descuentos (Lunes a Viernes)**")
                c_aus1, c_aus2 = st.columns([2, 1])
                
                dias_totales = (f_fin - f_inicio).days + 1
                dias_lv_dict = {}
                for i in range(dias_totales):
                    d = f_inicio + datetime.timedelta(days=i)
                    if d.weekday() < 5:
                        nombres_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
                        dias_lv_dict[f"{nombres_dias[d.weekday()]} {d.strftime('%d/%m')}"] = d
                        
                faltas_str = c_aus1.multiselect("Días completos que faltó:", list(dias_lv_dict.keys()), help="No sumarán horas en absoluto.")
                hs_descuento_parcial = c_aus2.number_input("Descontar Horas (Llegadas tarde/retiro):", min_value=0.0, value=0.0)
    
                st.markdown("**📅 Fines de Semana de esta Quincena**")
                finde_data = {}
                hay_findes = False
                for i in range(dias_totales):
                    dia = f_inicio + datetime.timedelta(days=i)
                    if dia.weekday() in [5, 6]:
                        hay_findes = True
                        nombre_dia = "Sábado" if dia.weekday() == 5 else "Domingo"
                        
                        cc1, cc2, cc3 = st.columns([1.5, 1, 1])
                        trabajo_check = cc1.checkbox(f"¿Trabajó {nombre_dia} {dia.strftime('%d/%m')}?", key=f"chk_{dia}")
                        ent_f = cc2.time_input(f"Ent.", datetime.time(7, 0), key=f"ent_{dia}", label_visibility="collapsed")
                        sal_f = cc3.time_input(f"Sal.", datetime.time(13, 0) if dia.weekday() == 5 else datetime.time(17,0), key=f"sal_{dia}", label_visibility="collapsed")
                        
                        finde_data[dia] = {
                            "trabajo": trabajo_check, "entrada": ent_f, "salida": sal_f, "es_sabado": dia.weekday() == 5
                        }
                
                if not hay_findes:
                    st.info("No hay sábados ni domingos en este rango de fechas.")
                st.markdown("---")
    
            # =================================================================
            # 3. FORMULARIO FINAL: CARGA ORDENADA Y DEDUCCIONES
            # =================================================================
            if modo_carga == "🤖 Carga Automática (Inteligente)":
                st.markdown("### 🧮 3. Ajustes de Recibo y Cálculo Final")
            else:
                st.markdown("### 🕒 2. Carga de Horas y Descuentos")
    
            with st.form("form_calc"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # ORDEN EXACTO (Columna Izquierda)
                    if modo_carga == "✍️ Carga Manual (Clásica)":
                        hn = st.number_input("Hs Normales:", min_value=0.0, value=0.0)
                    
                    cpres = st.selectbox("Presentismo (20%):", ["Sí", "No"])
                    
                    if modo_carga == "✍️ Carga Manual (Clásica)":
                        h50 = st.number_input("Hs al 50%:", min_value=0.0, value=0.0)
                        h100 = st.number_input("Hs al 100%:", min_value=0.0, value=0.0)
                    
                    hc = st.number_input("Hs Compensatorias:", min_value=0.0, value=0.0)
                    df_f = st.number_input("Días Feriados (Pagos):", min_value=0.0, value=0.0)
                    pesp = st.number_input("% Especialidad:", min_value=0.0, value=0.0)
                    ha = st.number_input("Hs Altura:", min_value=0.0, value=0.0)
                    hnoc = st.number_input("Hs Nocturnas:", min_value=0.0, value=0.0)
                    pnr = st.number_input("Plus NR (%):", min_value=0.0, value=0.0)
                    enr = st.number_input("Ev NR:", min_value=0.0, value=0.0)
    
                with col2:
                    # EL RESTO (Columna Derecha)
                    if modo_carga == "✍️ Carga Manual (Clásica)":
                        hs_descuento_parcial = st.number_input("Descontar Horas (Llegada tarde):", min_value=0.0, value=0.0)
                        
                    dv = st.number_input("Días Vac:", min_value=0.0, value=0.0)
                    sb = st.number_input("Sueldo Base (Vac/SAC):", min_value=0.0, value=0.0)
                    msac = st.number_input("Meses (SAC):", min_value=0.0, max_value=6.0, value=0.0)
                    mr = st.number_input("Mejor Rem:", min_value=0.0, value=0.0)
                    rr = st.number_input("Retro Rem:", min_value=0.0, value=0.0)
                    rnr = st.number_input("Retro NR:", min_value=0.0, value=0.0)
                    er = st.number_input("Ev Rem:", min_value=0.0, value=0.0)
                    dvi = st.number_input("Días Viático:", min_value=0.0, value=0.0)
                    ds = st.number_input("Seguro:", min_value=0.0, value=0.0)
                    dg = st.number_input("Ganancias (+/-):", value=0.0)
    
                if st.form_submit_button("▶ Generar Recibo Teórico", use_container_width=True):
                    
                    # ==========================================
                    # LÓGICA DEL MOTOR INTELIGENTE
                    # ==========================================
                    if modo_carga == "🤖 Carga Automática (Inteligente)":
                        hn, h50, h100 = 0.0, 0.0, 0.0
                        dias_totales = (f_fin - f_inicio).days + 1
                        desc_almuerzo = 1.0 if "Se descuenta" in paga_almuerzo else 0.0
                        dias_ausente = [dias_lv_dict[k] for k in faltas_str]
                        
                        for i in range(dias_totales):
                            dia_actual = f_inicio + datetime.timedelta(days=i)
                            wd = dia_actual.weekday() 
                            
                            if wd < 5: # L-V
                                if dia_actual in dias_ausente: continue
                                t_inicio = datetime.datetime.combine(dia_actual, h_ent_lv)
                                t_fin = datetime.datetime.combine(dia_actual, h_sal_lv)
                                if t_fin < t_inicio: t_fin += datetime.timedelta(days=1) 
                                
                                horas_reales = (t_fin - t_inicio).total_seconds() / 3600.0
                                horas_reales = max(0.0, horas_reales - desc_almuerzo)
                                
                                if horas_reales > 9.0:
                                    hn += 9.0
                                    h50 += (horas_reales - 9.0)
                                else:
                                    hn += horas_reales
                                        
                            elif wd in [5, 6]: # FINDE
                                datos_dia = finde_data.get(dia_actual)
                                if datos_dia and datos_dia["trabajo"]: 
                                    t_inicio = datetime.datetime.combine(dia_actual, datos_dia["entrada"])
                                    t_fin = datetime.datetime.combine(dia_actual, datos_dia["salida"])
                                    if t_fin < t_inicio: t_fin += datetime.timedelta(days=1)
                                    
                                    duracion_total = (t_fin - t_inicio).total_seconds() / 3600.0
                                    if duracion_total > 4.0:
                                        duracion_total = max(0.0, duracion_total - desc_almuerzo)
    
                                    if duracion_total > 0:
                                        if datos_dia["es_sabado"]: 
                                            limite_13 = datetime.datetime.combine(dia_actual, datetime.time(13, 0))
                                            if t_inicio < limite_13:
                                                duracion_antes_13 = (min(t_fin, limite_13) - t_inicio).total_seconds() / 3600.0
                                                if duracion_antes_13 > 4.0:
                                                    duracion_antes_13 = max(0.0, duracion_antes_13 - desc_almuerzo)
                                                
                                                hn += duracion_antes_13
                                                h100 += (duracion_total - duracion_antes_13)
                                            else:
                                                h100 += duracion_total 
                                        else: 
                                            h100 += duracion_total 
                        
                        if hs_descuento_parcial > 0:
                            hn = max(0.0, hn - hs_descuento_parcial)
    
                    if modo_carga == "✍️ Carga Manual (Clásica)" and 'hs_descuento_parcial' in locals():
                         hn = max(0.0, hn - hs_descuento_parcial)
    
                    # ==========================================
                    # CÁLCULO MONETARIO
                    # ==========================================
                    subtot = (hn*vh) + (h50*vh*1.5) + (h100*vh*2.0) + (hc*vh) + (df_f*9.0*vh)
                    mha = ha*vh*0.15
                    mhnoc = hnoc*vh*(8/60)
                    mpres = ((hn+h50+h100+hc+(df_f*9.0))*vh*0.20) if cpres == "Sí" else 0.0
                    mesp = (hn+h50+h100)*vh*(pesp/100)
                    mvac = ((sb/25)-(sb/30))*dv if sb>0 and dv>0 else 0.0
                    msac_val = (mr/2)*(msac/6) if mr>0 else 0.0
                    
                    bruto = subtot + mha + mhnoc + mpres + mesp + mvac + msac_val + er + rr
                    ret = (bruto*0.11) + (bruto*0.03) + (bruto*0.03) + (bruto*0.025) + ds + dg
                    norem = (subtot*(pnr/100)) + (dvi*v_viatico_final) + enr + rnr 
                    neto = bruto - ret + norem
    
                    txt = f"EMPLEADO: {n_emp} | EMPRESA: {e_liq}\n"
                    if modo_carga == "🤖 Carga Automática (Inteligente)":
                        txt += f"⏱️ MOTOR INTELIGENTE: {hn} Hs Normales | {h50} Hs al 50% | {h100} Hs al 100%\n"
                    txt += f"{'='*50}\n TOTAL BRUTO: $ {bruto:,.2f}\n TOTAL RETENCIONES: -$ {ret:,.2f}\n TOTAL NO REMUNERATIVOS: $ {norem:,.2f}\n{'='*50}\n NETO A COBRAR: $ {neto:,.2f}"
                    
                    st.session_state.recibo_txt = txt
                    st.session_state.rec_nombre = n_emp
                    st.session_state.rec_empresa = e_liq
                    st.success("✅ Generado.")
                    registrar_log("Generó Liquidación") 
    
            if 'recibo_txt' in st.session_state:
                st.code(st.session_state.recibo_txt, language="text")
                st.markdown("---")
                st.markdown("### ⚠️ Iniciar Reclamo por Liquidación")
                motivo_recibo = st.text_input("Motivo de la Diferencia/Reclamo:")
                if st.button("🚨 Enviar al Repositorio de Reclamos", key="btn_recibo"):
                    if not motivo_recibo: st.error("Escriba un motivo.")
                    else:
                        from datetime import datetime
                        df_reclamos = pd.concat([df_reclamos, pd.DataFrame([{"Nombre": st.session_state.rec_nombre, "Empresa": st.session_state.rec_empresa, "Motivo": motivo_recibo, "Ingreso": datetime.now().strftime("%d/%m/%Y"), "Estado": "Activo", "Finalizacion": "En proceso", "Respuesta": "", "Observaciones": f"Generado desde Calculadora ({'Modo Inteligente' if modo_carga != '✍️ Carga Manual (Clásica)' else 'Manual'})."}])], ignore_index=True)
                        if not guardar_db(df_reclamos, "Reclamos"):
                            st.stop()
                        st.success("✅ Reclamo enviado!")
                        registrar_log("Envió un Reclamo del sistema")
    
        # ---------------------------------------------------------
        # 2. PANTALLA: IERIC
        # ---------------------------------------------------------
        elif st.session_state.calc_activa == "IERIC":
            st.markdown("### 💰 Fondo de Cese Laboral (IERIC)")
            st.write("Carga de quincenas históricas para cálculo de aportes y actualización por CER.")
            
            cer_actual = obtener_cer()
            if cer_actual:
                st.success(f"🏦 Conexión BCRA Exitosa: Índice CER Actual = {cer_actual}")
            else:
                st.warning("⚠️ No se pudo conectar con el BCRA. Se calcularán montos nominales sin indexar.")
            
            col_i1, col_i2 = st.columns(2)
            ieric_nombre = col_i1.text_input("Nombre del Compañero (Para Registro/Reclamo):", key="ieric_nombre")
            ieric_emp = col_i2.selectbox("Empresa:", ["➕ Nueva..."] + lista_empresas_historicas, key="ieric_e")
    
            # La identidad pertenece a los importes, incluso tras volver al panel.
            identidad_ieric = (ieric_nombre, ieric_emp)
            if st.session_state.get("ieric_identidad") != identidad_ieric:
                if st.session_state.get("quincenas"):
                    st.info("Cambió el Nombre o la Empresa. Cargue nuevamente las quincenas para esta identidad.")
                st.session_state.quincenas = []
                for key in ("ieric_bruto", "ieric_fecha", "ieric_motivo"):
                    st.session_state.pop(key, None)
                st.session_state.ieric_identidad = identidad_ieric

            if 'quincenas' not in st.session_state: st.session_state.quincenas = []
    
            with st.form("form_q"):
                c1, c2 = st.columns(2)
                fp = c1.date_input("Fecha de Pago Original", key="ieric_fecha")
                bru = c2.number_input("Sueldo Bruto Quincenal ($):", min_value=0.0, step=1000.0, key="ieric_bruto")
                if st.form_submit_button("➕ Agregar Quincena") and bru > 0:
                    nro = len(st.session_state.quincenas) + 1
                    tasa = 0.12 if nro <= 24 else 0.08
                    aporte_base = bru * tasa
                    
                    fecha_formato_api = fp.strftime("%Y-%m-%d")
                    cer_historico = obtener_cer(fecha_formato_api)
                    
                    aporte_actualizado = aporte_base
                    if cer_historico and cer_actual:
                        aporte_actualizado = aporte_base * (cer_actual / cer_historico)
                    
                    st.session_state.quincenas.append({
                        "Quincena #": f"Q-{nro:02d}", "Fecha Pago": fp.strftime("%d/%m/%Y"), 
                        "Bruto": bru, "Aporte Nominal": aporte_base,
                        "CER Hist.": round(cer_historico, 2) if cer_historico else "N/A",
                        "Aporte Actualizado (CER)": aporte_actualizado
                    })
                    st.rerun()
    
            if st.session_state.quincenas:
                df_q = pd.DataFrame(st.session_state.quincenas)
                df_m = df_q.copy()
                df_m["Bruto"] = df_m["Bruto"].apply(lambda x: f"$ {x:,.2f}")
                df_m["Aporte Nominal"] = df_m["Aporte Nominal"].apply(lambda x: f"$ {x:,.2f}")
                df_m["Aporte Actualizado (CER)"] = df_m["Aporte Actualizado (CER)"].apply(lambda x: f"$ {x:,.2f}")
                
                st.dataframe(df_m, use_container_width=True)
                
                col_tot1, col_tot2 = st.columns(2)
                suma_nominal = sum(q['Aporte Nominal'] for q in st.session_state.quincenas)
                suma_actualizada = sum(q['Aporte Actualizado (CER)'] for q in st.session_state.quincenas)
                
                col_tot1.metric("Deuda Original (Histórica)", f"$ {suma_nominal:,.2f}")
                col_tot2.metric("DEUDA REAL ACTUALIZADA", f"$ {suma_actualizada:,.2f}", delta=f"+$ {(suma_actualizada - suma_nominal):,.2f} por inflación")
                
                st.markdown("---")
                st.markdown("### ⚠️ Iniciar Reclamo de IERIC")
                motivo_ieric = st.text_input("Motivo del Reclamo (Ej: Falta de pago libretas):", key="ieric_motivo")
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("🚨 Enviar al Repositorio de Reclamos", key="btn_ieric"):
                    if not ieric_nombre or ieric_emp == "➕ Nueva...": st.error("❌ Complete Nombre y Empresa arriba.")
                    elif not motivo_ieric: st.error("❌ Escriba un motivo.")
                    else:
                        from datetime import datetime
                        motivo_final = f"{motivo_ieric} | Deuda Actualizada: $ {suma_actualizada:,.2f}"
                        df_reclamos = pd.concat([df_reclamos, pd.DataFrame([{"Nombre": ieric_nombre, "Empresa": ieric_emp, "Motivo": motivo_final, "Ingreso": datetime.now().strftime("%d/%m/%Y"), "Estado": "Activo", "Finalizacion": "En proceso", "Respuesta": "", "Observaciones": "Generado Auto desde IERIC (Con CER)."}])], ignore_index=True)
                        if not guardar_db(df_reclamos, "Reclamos"):
                            st.stop()
                        st.success("✅ Reclamo enviado!")
                
                def borrar_ultima_quincena():
                    if st.session_state.get("quincenas"):
                        st.session_state.quincenas.pop()

                c_btn2.button("🗑️ Borrar Última Quincena", on_click=borrar_ultima_quincena)
    
        # ---------------------------------------------------------
        # 3. PANTALLA: VACACIONES
        # ---------------------------------------------------------
        elif st.session_state.calc_activa == "Vacaciones":
            st.markdown("### 🏖️ Calculadora de Vacaciones")
            st.info("⏳ Próximamente disponible para su utilización.")
    
        # ---------------------------------------------------------
        # 4. PANTALLA: SAC
        # ---------------------------------------------------------
        elif st.session_state.calc_activa == "SAC":
            st.markdown("### 🎄 Cálculo de Sueldo Anual Complementario (SAC)")
            st.info("⏳ Próximamente disponible para su utilización.")
    
        # ---------------------------------------------------------
        # 5. PANTALLA: PARITARIAS (SOLO ADMIN)
        # ---------------------------------------------------------
        elif st.session_state.calc_activa == "Paritarias" and st.session_state.get("usuario_rol", "") == "Admin":
            st.markdown("### 📈 Registro Histórico de Escalas Salariales")
            
            with st.expander("➕ Cargar Nueva Escala / Paritaria", expanded=False):
                with st.form("form_paritaria", clear_on_submit=True):
                    p_periodo = st.text_input("Período de Vigencia (Ej: '1° Quincena Abril 2026'):*")
                    
                    st.markdown("**Valores por Hora ($):**")
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        p_of_esp = st.number_input("Oficial Especializado $", min_value=0.0, format="%.2f")
                        p_of = st.number_input("Oficial $", min_value=0.0, format="%.2f")
                    with col_p2:
                        p_mo = st.number_input("Medio Oficial $", min_value=0.0, format="%.2f")
                        p_ay = st.number_input("Ayudante $", min_value=0.0, format="%.2f")
                        
                    col_ext1, col_ext2 = st.columns(2)
                    with col_ext1:
                        p_sereno = st.number_input("Valor MENSUAL Sereno $ (Opcional)", min_value=0.0, format="%.2f")
                    with col_ext2:
                        p_viatico = st.number_input("Viático Diario $", min_value=0.0, format="%.2f")
                    
                    if st.form_submit_button("💾 Guardar Nueva Escala"):
                        if not p_periodo:
                            st.error("❌ El Período de Vigencia es obligatorio.")
                        else:
                            from datetime import datetime
                            nueva_paritaria = pd.DataFrame([{
                                "Fecha_Carga": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "Periodo_Vigencia": p_periodo,
                                "Oficial_Especializado": p_of_esp, "Oficial": p_of,
                                "Medio_Oficial": p_mo, "Ayudante": p_ay,
                                "Sereno": p_sereno, "Viatico": p_viatico
                            }])
                            df_paritarias = pd.concat([df_paritarias, nueva_paritaria], ignore_index=True)
                            if not guardar_db(df_paritarias, "Paritarias_Historia"):
                                st.stop()
                            st.success("✅ ¡Escala salarial guardada en la historia!")
                            import time
                            time.sleep(2)
                            st.rerun()
                            
            st.markdown("---")
            st.markdown("### 📚 Historial Registrado")
            if df_paritarias.empty:
                st.info("No hay paritarias registradas en la base de datos.")
            else:
                df_mostrar = df_paritarias.iloc[::-1].copy()
                for col in ["Oficial_Especializado", "Oficial", "Medio_Oficial", "Ayudante", "Sereno", "Viatico"]:
                    df_mostrar[col] = df_mostrar[col].apply(lambda x: f"$ {x:,.2f}" if isinstance(x, (int, float)) and pd.notna(x) else f"$ {float(str(x).replace('$','').replace(' ','').replace('.','').replace(',','.')):,.2f}" if str(x).replace('$','').replace(' ','').replace('.','').replace(',','.').replace('-','',1).replace('.','',1).isdigit() else x)
                st.dataframe(df_mostrar, hide_index=True, use_container_width=True)            
    # ==========================================
