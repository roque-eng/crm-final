import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io

# --- INICIALIZACIÓN DE MEMORIA (HISTORIAL) ---
if "historico" not in st.session_state:
    st.session_state.historico = []

if "edit_data" not in st.session_state:
    st.session_state.edit_data = {}
# ---------------------------------------------

# Definición Global de Usuarios
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "GS": "GSanchez2025", "MDF": "Matiti2025", "EH": "EHugo2025", "AP": "APerdomo2025", "RS": "RSierra2025", "LT": "LTomasi2025", "EC": "ECabral2025", "PG": "PGagliardi2025"}

if 'usuario_actual' not in st.session_state:
    st.session_state['usuario_actual'] = "RDF"

# ==========================================
# ⚙️ CONFIGURACIÓN Y CONEXIONES
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

# TÍTULO DE ACCESO SOLICITADO: "EDF SEGUROS"
st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS Limpios y Profesionales en Azul para la propuesta impresa
st.markdown("""
    <style>
    @media print { 
        .stButton, [data-testid="stSidebar"], .stDownloadButton, footer, header, .no-print, [data-testid="stWidgetLabel"] { display: none !important; } 
        [data-testid="stAppViewContainer"] { background-color: white !important; }
    }
    
    .tabla-edf { width:100%; border-collapse: collapse; margin-top: 20px; font-family: sans-serif; background-color: white; }
    .tabla-edf th { background-color: #f0f7ff !important; color: #1E3A8A !important; padding: 12px; border: 1px solid #ddd; text-align: center; font-size: 15px; }
    .tabla-edf td { padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 14px; color: #333; }
    .der { text-align: right !important; font-weight: bold; }

    .ben-fila { 
        background-color: #f8f9fa; padding: 12px 20px; border-radius: 8px; margin-bottom: 10px; 
        border-left: 6px solid #1E3A8A !important; width: 100%; font-size: 15px; color: #333;
    }
    
    .caja-azul { 
        background-color: #ffffff; padding: 20px; border-radius: 12px; height: 100%; border: 1px solid #e0e0e0; 
        border-top: 5px solid #1E3A8A !important; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    .costo-res { 
        color: #1E3A8A !important; font-weight: bold; display: block; margin-top: 10px; font-size: 18px; 
        background: #f0f7ff !important; padding: 5px 10px; border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Autenticación Básica del Asesor
if 'logueado' not in st.session_state or not st.session_state['logueado']:
    st.title("🛡️ EDF SEGUROS")
    u_sel = st.selectbox("Seleccione su Usuario:", list(USUARIOS.keys()))
    p_in = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar", type="primary"):
        if USUARIOS.get(u_sel) == p_in:
            st.session_state['logueado'] = True
            st.session_state['usuario_actual'] = u_sel
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    st.stop()

# Lectura de Planilla Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(spreadsheet=URL_HOJA, ttl=0)
df_raw.columns = df_raw.columns.str.strip()
df_raw['Premio_Total_USD'] = (pd.to_numeric(df_raw.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0) + (pd.to_numeric(df_raw.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0) / TC_USD)).round(0)
df_raw['Fin de Vigencia'] = pd.to_datetime(df_raw['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date

with st.sidebar:
    nombre_asesor = USUARIOS.get(st.session_state.get('usuario_actual', 'RDF'), "Asesor")
    st.title(f"👤 {nombre_asesor}")

    def get_list(col): 
        return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
    
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

tab_car, tab_ven, tab_cot, tab_flota, tab_historial, tab_an = st.tabs([
    "👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR INDIVIDUAL", "🚛 FLOTAS", "📜 HISTORIAL", "📊 ANÁLISIS"
])

# --- PESTAÑA CARTERA ---
with tab_car:
    busq = st.text_input("🔍 Buscar cliente o matrícula en cartera...")
    df_c = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f
    df_disp_c = df_c.copy()
    if 'Fin de Vigencia' in df_disp_c.columns:
        df_disp_c['Fin de Vigencia'] = pd.to_datetime(df_disp_c['Fin de Vigencia']).dt.strftime('%d/%m/%Y')
        
    # Agregamos la columna interactiva con el ícono de PDF apuntando al link de Drive
    st.data_editor(
        df_disp_c,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Link Póliza Digital": st.column_config.LinkColumn(
                "📄 Póliza",
                help="Abrir documento en Google Drive",
                display_text="📎 Ver PDF"
            )
        }
    )

# --- PESTAÑA VENCIMIENTOS ---
with tab_ven:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        c1, c2 = st.columns(2)
        f_ini = c1.date_input("Desde:", date.today().replace(day=1))
        f_fin = c2.date_input("Hasta:", date.today() + timedelta(days=90))
        df_venc_f = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')
        df_venc_disp = df_venc_f.copy()
        df_venc_disp['Fin de Vigencia'] = pd.to_datetime(df_venc_disp['Fin de Vigencia']).dt.strftime('%d/%m/%Y')
        st.dataframe(df_venc_disp, use_container_width=True, hide_index=True)
        
        # Botón para Exportar a Excel reincorporado
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_venc_f.to_excel(writer, index=False, sheet_name='Vencimientos')
        st.download_button(
            label="📥 Exportar a Excel",
            data=output.getvalue(),
            file_name=f"Vencimientos_{f_ini}_al_{f_fin}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- FUNCIÓN COMODÍN PARA LIMPIAR NÚMEROS ---
def f_num(val):
    try: return f"{int(float(str(val).replace('$', '').replace('USD', '').replace('.', '').replace(',', '').strip())):,}".replace(",", ".")
    except: return str(val)

# --- PESTAÑA COTIZADOR INDIVIDUAL ---
with tab_cot:
    st.subheader("📝 Cotizador Seguros Individuales")
    edit_ind = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Individual" else {}
    
    # Se unificó el término y se asocia correctamente al estado interno
    modo_impresion_ind = st.toggle("🖨️ ACTIVAR MODO IMPRESIÓN / VISTA PREVIA", value=False, key="toggle_print_ind")
    
    if not modo_impresion_ind:
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
        
        # Textos pre-escritos originales reincorporados
        txt_beneficios_def = "• Auxilio mecánico e ilimitado\n• Cobertura Mercosur\n• Cristales, cerraduras y espejos sin límite de eventos ni deducible\n• Gestión de siniestros"
        txt_hogar_def = "• Incendio Edificio e Incendio Contenido USD 40.000\n• Hurto Contenido USD 10.000\n• Costo ANUAL: USD 95 IVA INC"
        txt_alquiler_def = "• Auto sustituto por 10 días o USD 250 en efectivo si no se utiliza."
        txt_bici_def = "• Cobertura por Hurto e Incendio de la bicicleta dentro y fuera del hogar: USD 1.500"

        col_a, col_b = st.columns(2)
        with col_a: b_cot = st.text_area("Beneficios:", value=edit_ind.get("ben", txt_beneficios_def), height=150, key="ben_v_final")
        with col_b:
            st.markdown("**Coberturas Complementarias**")
            c_h = st.text_area("Hogar:", value=edit_ind.get("ch", txt_hogar_def), height=80, key="hog_v_final")
            c_a = st.text_area("Auto Sustituto / Alquiler:", value=edit_ind.get("ca", txt_alquiler_def), height=50, key="alq_v_final")
            c_b = st.text_area("Bici Eléctrica:", value=edit_ind.get("cb", txt_bici_def), height=50, key="bic_v_final")

        if st.button("💾 Guardar propuesta en Historial", type="primary", use_container_width=True, key="save_ind_btn"):
            datos_i = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": n_cot, "v": v_cot, "e": e_cot, "cont": cont_cot, "doc": doc_in, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b, "tipo": "Individual"}
            st.session_state.historico.append(datos_i)
            st.session_state.edit_data = datos_i
            st.success("✅ ¡Guardado con éxito! Activá el interruptor 'Modo Impresión / Vista Previa' de arriba para visualizar.")
            st.rerun()
            
    else:
        # VISTA DE PROPUESTA LIMPIA INTERNA (INDIVIDUAL)
        col_l, col_i = st.columns([1, 2])
        with col_l: st.image("https://rpyiditlookfcrgeterf.supabase.co/storage/v1/object/public/logos/EDF%20Logotipo%20PNG.png", width=180)
        with col_i:
            st.markdown(f"## Asegurado: {edit_ind.get('n', 'Cliente')}")
            st.markdown(f"### 📋 Propuesta para: **{edit_ind.get('v', 'Vehículo')}**")
        
        t_html = """<table class="tabla-edf"><thead><tr><th>ASEGURADORA</th><th style="text-align: right;">CONTADO</th><th style="text-align: right;">10 CUOTAS</th><th style="text-align: right;">DEDUCIBLE</th></tr></thead><tbody>"""
        for row in edit_ind.get("tab", []):
            t_html += f"""<tr><td><b>{row.get('Aseguradora','')}</b></td><td class="der" style="color: #1E3A8A;">USD {f_num(row.get('Contado',0))}</td><td class="der">USD {f_num(row.get('10 Cuotas',0))}</td><td class="der">USD {f_num(row.get('Deducible',0))}</td></tr>"""
        t_html += "</tbody></table>"
        st.markdown(t_html, unsafe_allow_html=True)
        
        if edit_ind.get("ben"):
            st.write("")
            st.markdown("### ✅ Beneficios Incluidos")
            for b in edit_ind.get("ben", "").split('\n'):
                if b.strip(): st.markdown(f'<div class="ben-fila">{b.strip()}</div>', unsafe_allow_html=True)
                
        st.write("")
        st.markdown("### ⚠️ Coberturas Complementarias")
        cx1, cx2, cx3 = st.columns(3)
        def b_html(tit, ico, txt):
            if not txt: return ""
            out = f'<div class="caja-azul"><span style="font-weight:bold; color:#1E3A8A;">{ico} {tit}</span><br>'
            for l in txt.split('\n'):
                if "$" in l or "Costo" in l or "COSTO" in l: out += f'<span class="costo-res">💰 {l.replace("•","").strip()}</span>'
                else: out += f'<span style="display:block; margin-top:3px;">{l.strip()}</span>'
            return out + '</div>'
        cx1.markdown(b_html("Hogar", "🏠", edit_ind.get("ch", "")), unsafe_allow_html=True)
        cx2.markdown(b_html("Alquiler / Auto Sust.", "🚗", edit_ind.get("ca", "")), unsafe_allow_html=True)
        cx3.markdown(b_html("Bici", "🚲", edit_ind.get("cb", "")), unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown(f"<div style='display:flex; justify-content:space-between; color:gray;'><div><b>Asesor:</b> {edit_ind.get('e','EDF')} | <b>Contacto:</b> {edit_ind.get('cont','')}</div><div><b>Fecha:</b> {edit_ind.get('fecha','')}</div></div>", unsafe_allow_html=True)

# --- PESTAÑA FLOTAS ---
with tab_flota:
    st.subheader("🚛 Cotizador Seguro de Flotas")
    edit_f = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Flota" else {}
    
    modo_impresion_fl = st.toggle("🖨️ ACTIVAR MODO IMPRESIÓN / VISTA PREVIA", value=False, key="toggle_print_flota")
    
    if not modo_impresion_fl:
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

        if st.button("💾 Guardar propuesta de Flota", key="btn_save_fl", use_container_width=True):
            nueva_f = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": f_asegurado, "e": f_cia_elegida, "e_nombre": f_asesor_nombre, "cont": f_contacto, "tab": t_flota.to_dict(orient='records'), "ben": f_obs, "tipo": "Flota"}
            st.session_state.historico.append(nueva_f)
            st.session_state.edit_data = nueva_f
            st.success("✅ ¡Propuesta guardada! Activá el interruptor de arriba para cambiar a la vista limpia.")
            st.rerun()
            
    else:
        # VISTA DE PROPUESTA LIMPIA INTERNA (FLOTAS)
        col_l, col_i = st.columns([1, 2])
        with col_l: st.image("https://rpyiditlookfcrgeterf.supabase.co/storage/v1/object/public/logos/EDF%20Logotipo%20PNG.png", width=180)
        with col_i:
            st.markdown(f"## Asegurado: {edit_f.get('n', 'Cliente Flota')}")
            st.markdown(f"### 🏦 Aseguradora: **{edit_f.get('e', 'Compañía')}**")
            
        t_html = """<table class="tabla-edf"><thead><tr><th>MARCA</th><th>MODELO</th><th>AÑO</th><th>MATRICULA</th><th>COBERTURA</th><th style="text-align: right;">CONTADO</th><th style="text-align: right;">DEDUCIBLE</th></tr></thead><tbody>"""
        for row in edit_f.get("tab", []):
            t_html += f"""<tr><td>{row.get('Marca','')}</td><td>{row.get('Modelo','')}</td><td>{row.get('Año','')}</td><td>{row.get('Matrícula','-')}</td><td>{row.get('Cobertura','')}</td><td class="der" style="color: #1E3A8A;">USD {f_num(row.get('Contado',0))}</td><td class="der">USD {f_num(row.get('Deducible',0))}</td></tr>"""
        t_html += "</tbody></table>"
        st.markdown(t_html, unsafe_allow_html=True)
        
        if edit_f.get("ben"):
            st.write("")
            st.markdown("### 📋 Comentarios EDF Seguros")
            st.info(edit_f.get("ben"))
        st.markdown("---")
        st.markdown(f"<div style='display:flex; justify-content:space-between; color:gray;'><div><b>Asesor:</b> {edit_f.get('e_nombre','')} | <b>Contacto:</b> {edit_f.get('cont','')}</div><div><b>Fecha:</b> {edit_f.get('fecha','')}</div></div>", unsafe_allow_html=True)

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
                    st.success(f"Propuesta de {reg.get('n')} cargada.")
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_{idx_real}"):
                    st.session_state.historico.pop(idx_real)
                    st.rerun()
    else: st.info("No hay propuestas en la memoria temporal todavía.")

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
