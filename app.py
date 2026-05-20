import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64

# ==========================================
# ⚙️ CONFIGURACIÓN GLOBAL Y ENLACES
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5

# FUNCIÓN COMODÍN PARA LIMPIAR Y FORMATEAR NÚMEROS EN LA VISTA
def f_num(val):
    try: return f"{int(float(str(val).replace('$', '').replace('USD', '').replace('.', '').replace(',', '').strip())):,}".replace(",", ".")
    except: return str(val)

# ==========================================
# ⚙️ DETECCIÓN DEL LINK EXTERNO (CLIENTE)
# ==========================================
query_params = st.query_params

# Si en la URL viene el parámetro "?q=", significa que entró un CLIENTE desde el link externo
if "q" in query_params:
    try:
        # Decodificamos de forma segura los datos que viajan en el link
        datos_b64 = query_params["q"]
        datos_json = base64.b64decode(datos_b64).decode()
        propuesta_cliente = json.loads(datos_json)
        
        st.set_page_config(page_title="EDF SEGUROS - Propuesta", layout="wide", page_icon="🛡️")
        
        # Estilos visuales para la propuesta del cliente externos
        st.markdown("""
            <style>
            .tabla-edf { width:100%; border-collapse: collapse; margin-top: 15px; font-family: sans-serif; background-color: white; }
            .tabla-edf th { background-color: #f0f7ff !important; color: #1E3A8A !important; padding: 12px; border: 1px solid #ddd; text-align: right; font-size: 14px; }
            .tabla-edf th:first-child, .tabla-edf td:first-child { text-align: left !important; }
            .tabla-edf td { padding: 10px; border: 1px solid #ddd; text-align: right; font-size: 14px; color: #333; }
            .izq-negrita { text-align: left !important; font-weight: bold; }
            .der { text-align: right !important; font-weight: bold; }
            .ben-fila { background-color: #f8f9fa; padding: 10px 18px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #1E3A8A !important; font-size: 14px; color: #333; }
            .caja-azul { background-color: #ffffff; padding: 18px; border-radius: 12px; height: 100%; border: 1px solid #e0e0e0; border-top: 5px solid #1E3A8A !important; }
            </style>
        """, unsafe_allow_html=True)

        # Encabezado alineado a la izquierda sin la camarita rota
        st.markdown(f"""
        <div style="font-family: sans-serif; text-align: left !important; padding-left: 5px; margin-bottom: 15px; margin-top: 20px;">
            <h2 style="margin: 0 0 6px 0; font-size: 22px; color: #111; text-align: left !important;">Asegurado: {propuesta_cliente.get('n', 'Cliente')}</h2>
            <p style="margin: 0; font-size: 16px; color: #555; text-align: left !important;"><b>Vehículo:</b> {propuesta_cliente.get('v', 'Vehículo')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Dibujamos la tabla usando el componente nativo seguro
        df_cli = pd.DataFrame(propuesta_cliente.get("tab", []))
        if not df_cli.empty:
            for col in ["Contado", "10 Cuotas", "Deducible"]:
                if col in df_cli.columns:
                    df_cli[col] = pd.to_numeric(df_cli[col], errors='coerce').fillna(0).astype(int)
            
            st.dataframe(
                df_cli, use_container_width=True, hide_index=True,
                column_config={
                    "Aseguradora": st.column_config.TextColumn("ASEGURADORA"),
                    "Contado": st.column_config.NumberColumn("CONTADO", format="%d"),
                    "10 Cuotas": st.column_config.NumberColumn("10 CUOTAS", format="%d"),
                    "Deducible": st.column_config.NumberColumn("DEDUCIBLE", format="%d")
                }
            )
            
        if propuesta_cliente.get("ben"):
            st.write("")
            st.markdown("### ✅ Beneficios Incluidos")
            for b in propuesta_cliente.get("ben", "").split('\n'):
                if b.strip(): st.markdown(f'<div class="ben-fila">{b.strip()}</div>', unsafe_allow_html=True)
                
        st.write("")
        st.markdown("### ⚠️ Coberturas Complementarias")
        cx1, cx2, cx3 = st.columns(3)
        def b_html_cli(tit, ico, txt):
            if not txt: return ""
            out = f'<div class="caja-azul"><span style="font-weight:bold; color:#1E3A8A;">{ico} {tit}</span><br>'
            for l in txt.split('\n'): out += f'<span style="display:block; margin-top:3px;">{l.strip()}</span>'
            return out + '</div>'
            
        cx1.markdown(b_html_cli("Hogar", "🏠", propuesta_cliente.get("ch", "")), unsafe_allow_html=True)
        cx2.markdown(b_html_cli("Alquiler / Auto Sust.", "🚗", propuesta_cliente.get("ca", "")), unsafe_allow_html=True)
        cx3.markdown(b_html_cli("Bici", "🚲", propuesta_cliente.get("cb", "")), unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown(f"<div style='display:flex; justify-content:space-between; color:gray;'><div><b>Asesor:</b> {propuesta_cliente.get('e','EDF')} | <b>Contacto:</b> {propuesta_cliente.get('cont', '')}</div><div><b>Fecha:</b> {propuesta_cliente.get('fecha','')}</div></div>", unsafe_allow_html=True)
        
        # Freno absoluto: el cliente se planta acá y jamás ve tu CRM interno
        st.stop()
    except Exception as e:
        st.error("Error al cargar la propuesta externa. Contacte a su asesor.")
        st.stop()


# ==========================================
# 🏢 LÓGICA DEL INTERFAZ DEL ASESOR (CRM CONTRASEÑA)
# ==========================================
if "historico" not in st.session_state: st.session_state.historico = []
if "edit_data" not in st.session_state: st.session_state.edit_data = {}

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS generales para las grillas del CRM
st.markdown("""
    <style>
    .ben-fila { background-color: #f8f9fa; padding: 10px 18px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #1E3A8A !important; font-size: 14px; color: #333; }
    .caja-azul { background-color: #ffffff; padding: 18px; border-radius: 12px; height: 100%; border: 1px solid #e0e0e0; border-top: 5px solid #1E3A8A !important; }
    </style>
""", unsafe_allow_html=True)

USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "GS": "GSanchez2025", "MDF": "Matiti2025", "EH": "EHugo2025", "AP": "APerdomo2025", "RS": "RSierra2025", "LT": "LTomasi2025", "EC": "ECabral2025", "PG": "PGagliardi2025"}
if 'usuario_actual' not in st.session_state: st.session_state['usuario_actual'] = "RDF"

if 'logueado' not in st.session_state or not st.session_state['logueado']:
    st.title("🛡️ EDF SEGUROS")
    u_sel = st.selectbox("Seleccione su Usuario:", list(USUARIOS.keys()))
    p_in = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar", type="primary"):
        if USUARIOS.get(u_sel) == p_in:
            st.session_state['logueado'] = True
            st.session_state['usuario_actual'] = u_sel
            st.rerun()
        else: st.error("Contraseña incorrecta.")
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(spreadsheet=URL_HOJA, ttl=0)
df_raw.columns = df_raw.columns.str.strip()
df_raw['Premio_Total_USD'] = (pd.to_numeric(df_raw.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0) + (pd.to_numeric(df_raw.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0) / TC_USD)).round(0)
df_raw['Fin de Vigencia'] = pd.to_datetime(df_raw['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date

with st.sidebar:
    st.title(f"👤 {USUARIOS.get(st.session_state.usuario_actual, 'Asesor')}")
    def get_list(col): return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
    f_ej = st.selectbox("Ejecutivo", get_list('Ejecutivo'))
    f_as = st.selectbox("Aseguradora", get_list('Aseguradora'))
    f_ra = st.selectbox("Ramo", get_list('Ramo'))
    f_co = st.selectbox("Corredor", get_list('Corredor'))
    f_ag = st.selectbox("Agente", get_list('Agente'))
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]

tab_car, tab_ven, tab_cot, tab_flota, tab_historial, tab_an = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR INDIVIDUAL", "🚛 FLOTAS", "📜 HISTORIAL", "📊 ANÁLISIS"])

# --- PESTAÑA CARTERA ---
with tab_car:
    busq = st.text_input("🔍 Buscar cliente o matrícula en cartera...")
    df_c = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f
    df_disp_c = df_c.copy()
    if 'Fin de Vigencia' in df_disp_c.columns: df_disp_c['Fin de Vigencia'] = pd.to_datetime(df_disp_c['Fin de Vigencia']).dt.strftime('%d/%m/%Y')
    
    cols_actuales_c = list(df_disp_c.columns)
    col_primera, col_final_1, col_final_2, col_final_3 = "Adjunto (póliza)", "Mail", "Celular", "Marca temporal"
    if col_primera in cols_actuales_c: cols_actuales_c.remove(col_primera)
    if col_final_1 in cols_actuales_c: cols_actuales_c.remove(col_final_1)
    if col_final_2 in cols_actuales_c: cols_actuales_c.remove(col_final_2)
    if col_final_3 in cols_actuales_c: cols_actuales_c.remove(col_final_3)
    
    st.data_editor(df_disp_c, use_container_width=True, hide_index=True, column_order=[col_primera] + cols_actuales_c + [col_final_1, col_final_2, col_final_3], column_config={"Adjunto (póliza)": st.column_config.LinkColumn("📄 Póliza", display_text="📎 Ver PDF")})

# --- PESTAÑA VENCIMIENTOS ---
with tab_ven:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        c1, c2 = st.columns(2)
        f_ini, f_fin = c1.date_input("Desde:", date.today().replace(day=1)), c2.date_input("Hasta:", date.today() + timedelta(days=90))
        df_venc_f = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')
        df_venc_disp = df_venc_f.copy()
        if 'Fin de Vigencia' in df_venc_disp.columns: df_venc_disp['Fin de Vigencia'] = pd.to_datetime(df_venc_disp['Fin de Vigencia']).dt.strftime('%d/%m/%Y')
        
        cols_actuales_v = list(df_venc_disp.columns)
        if col_primera in cols_actuales_v: cols_actuales_v.remove(col_primera)
        if col_final_1 in cols_actuales_v: cols_actuales_v.remove(col_final_1)
        if col_final_2 in cols_actuales_v: cols_actuales_v.remove(col_final_2)
        if col_final_3 in cols_actuales_v: cols_actuales_v.remove(col_final_3)
        
        st.data_editor(df_venc_disp, use_container_width=True, hide_index=True, column_order=[col_primera] + cols_actuales_v + [col_final_1, col_final_2, col_final_3], column_config={"Adjunto (póliza)": st.column_config.LinkColumn("📄 Póliza", display_text="📎 Ver PDF")})
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_venc_f.to_excel(writer, index=False, sheet_name='Vencimientos')
        st.download_button(label="📥 Exportar a Excel", data=output.getvalue(), file_name=f"Vencimientos.xlsx")

# --- PESTAÑA COTIZADOR INDIVIDUAL ---
with tab_cot:
    st.subheader("📝 Cotizador Seguros Individuales")
    edit_ind = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Individual" else {}
    
    with st.container(border=True):
        c_doc, c_nom, c_veh, c_ase, c_con = st.columns([1.5, 2, 2, 1, 2])
        doc_in = c_doc.text_input("CI/RUT", value=edit_ind.get("doc", ""), key="ci_v_final")
        n_cot = c_nom.text_input("Nombre", value=edit_ind.get('n', ''), key="nom_v_final")
        v_cot = c_veh.text_input("Vehículo", value=edit_ind.get("v", ""), key="veh_v_final")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="ase_v_final")
        cont_cot = c_con.text_input("Contacto Asesor", value=edit_ind.get("cont", "099 635 244"), key="cont_v_final")

    cols_individual = ["Aseguradora", "Contado", "10 Cuotas", "Deducible"]
    if edit_ind and "tab" in edit_ind: df_p_init = pd.DataFrame(edit_ind["tab"])
    else: df_p_init = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "SURA", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "MAPFRE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "SANCOR", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}])
    t_edit = st.data_editor(df_p_init, num_rows="dynamic", use_container_width=True, column_order=cols_individual, key="editor_individual_completo")
    
    txt_beneficios_def = "• Auxilio mecánico e ilimitado\n• Cobertura Mercosur\n• Cristales, cerraduras y espejos sin límite de eventos ni deducible\n• Gestión de siniestros"
    txt_hogar_def = "• Incendio Edificio e Incendio Contenido 40.000\n• Hurto Contenido 10.000\n• Costo ANUAL: 95 IVA INC"
    txt_alquiler_def = "• Auto sustituto por 10 días o 250 en efectivo si no se utiliza."
    txt_bici_def = "• Cobertura por Hurto e Incendio de la bicicleta dentro y fuera del hogar: 1.500"

    col_a, col_b = st.columns(2)
    with col_a: b_cot = st.text_area("Beneficios:", value=edit_ind.get("ben", txt_beneficios_def), height=150, key="ben_v_final")
    with col_b:
        st.markdown("**Coberturas Complementarias**")
        c_h = st.text_area("Hogar:", value=edit_ind.get("ch", txt_hogar_def), height=80, key="hog_v_final")
        c_a = st.text_area("Auto Sustituto / Alquiler:", value=edit_ind.get("ca", txt_alquiler_def), height=50, key="alq_v_final")
        c_b = st.text_area("Bici Eléctrica:", value=edit_ind.get("cb", txt_bici_def), height=50, key="bic_v_final")

    if st.button("💾 Guardar propuesta y Generar Link", type="primary", use_container_width=True, key="save_ind_btn"):
        datos_i = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": n_cot, "v": v_cot, "e": e_cot, "cont": cont_cot, "doc": doc_in, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b, "tipo": "Individual"}
        st.session_state.historico.append(datos_i)
        st.session_state.edit_data = datos_i
        
        # Generamos el enlace encriptado seguro en Base64
        datos_b64 = base64.b64encode(json.dumps(datos_i).encode()).decode()
        link_cliente = f"https://edfseguros.streamlit.app/?q={datos_b64}"
        
        st.success("✅ ¡Propuesta guardada con éxito en el Historial!")
        st.text_input("🔗 Copiá este Link y enviáselo al cliente por WhatsApp:", value=link_cliente)

# --- PESTAÑA FLOTAS ---
with tab_flota:
    st.subheader("🚛 Cotizador Seguro de Flotas")
    edit_f = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Flota" else {}
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_asegurado = st.text_input("Asegurado", value=edit_f.get('n', ''), key="f_nom_fl")
        f_cia_elegida = st.text_input("Compañía Aseguradora", value=edit_f.get('e', 'SBI'), key="f_cia_fl")
    with col_f2:
        f_asesor_nombre = st.text_input("Asesor", value=edit_f.get('e_nombre', 'EDF SEGUROS'), key="f_as_fl")
        f_contacto = st.text_input("Contacto", value=edit_f.get('cont', '099 635 244'), key="f_co_fl")

    cols_f = ["Marca", "Modelo", "Año", "Matrícula", "Cobertura", "Contado", "Deducible"]
    if edit_f and "tab" in edit_f: df_f_init = pd.DataFrame(edit_f["tab"])
    else: df_f_init = pd.DataFrame([{"Marca": "", "Modelo": "", "Año": "", "Matrícula": "", "Cobertura": "Todo Riesgo", "Contado": 0, "Deducible": 0}])
    t_flota = st.data_editor(df_f_init, num_rows="dynamic", use_container_width=True, column_order=cols_f, key="editor_flotas")
    f_obs = st.text_area("Observaciones / Comentarios:", value=edit_f.get('ben', ''), height=100, key="f_obs_fl")

    if st.button("💾 Guardar propuesta de Flota y Generar Link", key="btn_save_fl", use_container_width=True):
        nueva_f = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": f_asegurado, "e": f_cia_elegida, "e_nombre": f_asesor_nombre, "cont": f_contacto, "tab": t_flota.to_dict(orient='records'), "ben": f_obs, "tipo": "Flota"}
        st.session_state.historico.append(nueva_f)
        st.session_state.edit_data = nueva_f
        
        datos_b64 = base64.b64encode(json.dumps(nueva_f).encode()).decode()
        link_flota = f"https://edfseguros.streamlit.app/?q={datos_b64}"
        
        st.success("✅ ¡Propuesta de Flota guardada con éxito!")
        st.text_input("🔗 Enlace para mandar al cliente de Flotas:", value=link_flota)

# --- PESTAÑA HISTORIAL ---
with tab_historial:
    st.subheader("📜 Historial de Propuestas Guardadas")
    if st.session_state.historico:
        for i, reg in enumerate(reversed(st.session_state.historico)):
            idx_real = len(st.session_state.historico) - 1 - i
            col_info, col_edit, col_del = st.columns([0.7, 0.15, 0.15])
            with col_info:
                icon = "🚚" if reg.get("tipo") == "Flota" else "🚗"
                st.write(f"📅 **{reg.get('fecha', '')[:10]}** | {icon} {reg.get('tipo')} | **{reg.get('n', 'Cliente')}**")
            with col_edit:
                if st.button("✏️ Cargar/Editar", key=f"edit_{idx_real}"):
                    st.session_state.edit_data = reg
                    st.success("Cargada.")
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_{idx_real}"):
                    st.session_state.historico.pop(idx_real)
                    st.rerun()
    else: st.info("No hay propuestas en el historial temporal todavía.")

# --- PESTAÑA ANÁLISIS ---
with tab_an:
    st.subheader("📊 Análisis de Cartera")
    if not df_f.empty:
        t_usd = df_f['Premio_Total_USD'].sum()
        k1, k2 = st.columns(2)
        k1.metric("Cartera Total (USD)", f"USD {t_usd:,.0f}")
        k2.metric("Total de Pólizas", f"{len(df_f)}")
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Compañía", hole=0.4), use_container_width=True)
        with c2: st.plotly_chart(px.pie(df_f, names='Ramo', values='Premio_Total_USD', title="Ramo", hole=0.4), use_container_width=True)
