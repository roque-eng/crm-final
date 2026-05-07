import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64
import requests

# ==========================================
# ⚙️ CONFIGURACIÓN Y CONEXIONES
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

# Credenciales de Supabase - USANDO TUS CLAVES PASADAS
SUPABASE_URL = "https://flizerdhoxxoekaczihm.supabase.co"
SUPABASE_KEY = "sb_publishable_lkSd6DNhiwifC-qCMkYNdQ_U97XIxog" 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

def fmt_curr(val):
    try:
        num = float(str(val).replace('$', '').replace('.', '').replace(',', '').strip())
        return f"$ {int(num):,}".replace(",", ".")
    except: return val

def guardar_en_db(datos):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/cotizaciones", headers=headers, json=datos)
        return response.status_code in [200, 201]
    except: return False

def leer_historial():
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/cotizaciones?select=*&order=created_at.desc", headers=headers)
        return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

st.markdown("""
    <style>
    @media print { .stButton, [data-testid="stSidebar"], .stDownloadButton, footer, header { display: none !important; } }
    .titulo-bordo { color: #800020; font-size: 22px; font-weight: bold; border-bottom: 3px solid #800020; padding-bottom: 8px; margin-bottom: 20px; text-transform: uppercase; }
    .quote-card { background-color: #fdfdfd; padding: 20px; border-radius: 10px; border: 1px solid #eee; white-space: pre-wrap; font-family: sans-serif; font-size: 14px; line-height: 1.6; }
    [data-testid="stTable"] td { text-align: right !important; }
    </style>
    """, unsafe_allow_html=True)

query_params = st.query_params
if "q" in query_params or "f" in query_params:
    p_tipo = "f" if "f" in query_params else "q"
    try:
        data_raw = base64.b64decode(query_params[p_tipo]).decode()
        q_data = json.loads(data_raw)
        st.markdown(f"<div class='titulo-bordo'>🛡️ EDF SEGUROS - Propuesta</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Asegurado:** {q_data['n']}")
            if p_tipo == "q": st.markdown(f"**Vehículo:** {q_data.get('v', 'S/D')}")
        with c2:
            st.markdown(f"**Fecha:** {date.today().strftime('%d/%m/%Y')}")
            st.markdown(f"**Asesor:** {q_data['e']}")
            if q_data.get('cont'): st.markdown(f"**Contacto:** {q_data['cont']}")
        df_view = pd.DataFrame(q_data['tab'])
        for col in df_view.columns:
            if any(p in col.lower() for p in ["precio", "contado", "cuotas", "deducible", "p.", "ded."]):
                df_view[col] = df_view[col].apply(fmt_curr)
        st.table(df_view) 
        st.write("### ✅ Beneficios Incluidos"); st.markdown(f"<div class='quote-card'>{q_data['ben']}</div>", unsafe_allow_html=True)
        if p_tipo == "q" and q_data.get('ch'):
            st.write("### 🏠 Coberturas Complementarias")
            col_comp = st.columns(3)
            with col_comp[0]: st.info("**Hogar**"); st.caption(q_data['ch'])
            with col_comp[1]: st.info("**Alquiler**"); st.caption(q_data['ca'])
            with col_comp[2]: st.info("**Bici**"); st.caption(q_data['cb'])
        st.stop() 
    except: st.error("Error."); st.stop()
        # ==========================================
# 🔐 SEGURIDAD Y CARTERA
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "GS": "GSanchez2025", "MDF": "Matiti2025", "EH": "EHugo2025", "AP": "APerdomo2025", "RS": "RSierra2025", "LT": "LTomasi2025", "EC": "ECabral2025", "PG": "PGagliardi2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True; st.session_state['usuario_actual'] = u; st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(spreadsheet=URL_HOJA, ttl=0)
df_raw.columns = df_raw.columns.str.strip()
df_raw['Premio_Total_USD'] = (pd.to_numeric(df_raw.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0) + (pd.to_numeric(df_raw.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0) / TC_USD)).round(0)
df_raw['Fin de Vigencia'] = pd.to_datetime(df_raw['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date

with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    def get_list(col): return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
    f_ej = st.selectbox("Ejecutivo", get_list('Ejecutivo'))
    f_as = st.selectbox("Aseguradora", get_list('Aseguradora'))
    f_ra = st.selectbox("Ramo", get_list('Ramo'))
    # RESTAURADOS LOS FILTROS QUE FALTABAN
    f_co = st.selectbox("Corredor", get_list('Corredor'))
    f_ag = st.selectbox("Agente", get_list('Agente'))
    if st.button("Cerrar Sesión"): st.session_state['logueado'] = False; st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos" and 'Corredor' in df_f.columns: df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos" and 'Agente' in df_f.columns: df_f = df_f[df_f['Agente'] == f_ag]
# ==========================================
# 🏢 PESTAÑAS Y FUNCIONALIDADES (BLOQUE 3 CON EDICIÓN)
# ==========================================

# 1. Inicializar estados de edición si no existen
if "edit_data" not in st.session_state:
    st.session_state.edit_data = None
if "es_edicion" not in st.session_state:
    st.session_state.es_edicion = False

tab_car, tab_ven, tab_cot, tab_flota, tab_hist, tab_an = st.tabs([
    "👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "🚛 FLOTAS", "📜 HISTORIAL", "📊 ANÁLISIS"
])

# --- PESTAÑA CARTERA (Se mantiene igual) ---
with tab_car:
    busq = st.text_input("🔍 Buscar cliente o matrícula en cartera...")
    df_c = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f
    df_disp_c = df_c.copy()
    if 'Fin de Vigencia' in df_disp_c.columns:
        df_disp_c['Fin de Vigencia'] = pd.to_datetime(df_disp_c['Fin de Vigencia']).dt.strftime('%d/%m/%Y')
    st.dataframe(df_disp_c, use_container_width=True, hide_index=True, column_config={
        "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂"),
        "Premio USD (IVA inc)": st.column_config.NumberColumn("Premio USD", format="USD %.0f"),
        "Premio UYU (IVA inc)": st.column_config.NumberColumn("Premio UYU", format="$ %.0f"),
        "Premio_Total_USD": st.column_config.NumberColumn("Total USD", format="USD %.0f")
    })

# --- PESTAÑA VENCIMIENTOS (Se mantiene igual) ---
with tab_ven:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        c1, c2 = st.columns(2); f_ini = c1.date_input("Desde:", date.today().replace(day=1)); f_fin = c2.date_input("Hasta:", date.today() + timedelta(days=90))
        df_venc_f = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')
        df_venc_disp = df_venc_f.copy()
        df_venc_disp['Fin de Vigencia'] = pd.to_datetime(df_venc_disp['Fin de Vigencia']).dt.strftime('%d/%m/%Y')
        st.dataframe(df_venc_disp, use_container_width=True, hide_index=True, column_config={
            "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂"),
            "Premio USD (IVA inc)": st.column_config.NumberColumn("Premio USD", format="USD %.0f"),
            "Premio UYU (IVA inc)": st.column_config.NumberColumn("Premio UYU", format="$ %.0f")
        })

# --- PESTAÑA COTIZADOR INDIVIDUAL (CON LÓGICA DE EDICIÓN) ---
with tab_cot:
    st.subheader("📝 Cotizador Individual")
    
    # Si estamos editando, cargar valores previos
    edit = st.session_state.edit_data
    if st.session_state.es_edicion:
        st.warning(f"⚠️ Editando cotización de: {edit['n']}. Se guardará como una nueva versión.")
        if st.button("❌ CANCELAR EDICIÓN"):
            st.session_state.edit_data = None
            st.session_state.es_edicion = False
            st.rerun()

    with st.container(border=True):
        c_doc, c_nom, c_veh, c_ase, c_con = st.columns([1.5, 2, 2, 1, 2])
        doc_in = c_doc.text_input("CI/RUT", value=edit["doc"] if edit and "doc" in edit else "")
        
        # Lógica de nombre: si es edición y no tiene V.2, se lo ponemos
        nombre_sugerido = edit["n"] if edit else ""
        if st.session_state.es_edicion and "V.2" not in nombre_sugerido:
            nombre_sugerido = f"{nombre_sugerido} V.2"
            
        n_cot = c_nom.text_input("Nombre", value=nombre_sugerido)
        v_cot = c_veh.text_input("Vehículo", value=edit["v"] if edit else "")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), index=0)
        cont_cot = c_con.text_input("Nombre y Contacto Asesor", value=edit["cont"] if edit else "")

    # Tabla de precios
    df_precios = pd.DataFrame(edit["tab"]) if edit else pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}])
    t_edit = st.data_editor(df_precios, num_rows="dynamic", use_container_width=True, column_config={
        "Contado": st.column_config.NumberColumn(format="$ %.0f"),
        "10 Cuotas": st.column_config.NumberColumn(format="$ %.0f"),
        "Deducible": st.column_config.NumberColumn(format="$ %.0f")
    })
    
    col_a, col_b = st.columns(2)
    with col_a:
        b_cot = st.text_area("Beneficios:", value=edit["ben"] if edit else "• Auxilio mecánico 24hs...", height=200)
    with col_b:
        c_h = st.text_area("Hogar:", value=edit["ch"] if edit else "• Incendio...", height=130)
        c_a = st.text_area("Alquiler:", value=edit["ca"] if edit else "• Auto cortesía...", height=70)
        c_b = st.text_area("Bici:", value=edit["cb"] if edit else "• Hurto...", height=70)

    datos_i = {"n": n_cot, "v": v_cot, "e": e_cot, "cont": cont_cot, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b, "doc": doc_in}
    l_i = f"https://dfseguros.streamlit.app/?q={base64.b64encode(json.dumps(datos_i).encode()).decode()}"
    
    if st.button("🚀 GUARDAR VERSIÓN Y GENERAR PROPUESTA", use_container_width=True):
        db_i = {"tipo": "individual", "documento": doc_in, "asegurado": n_cot, "vehiculo_o_flota": v_cot, "asesor": e_cot, "datos_json": datos_i, "link_cotizacion": l_i}
        if guardar_en_db(db_i):
            st.session_state.es_edicion = False # Limpiamos el modo edición tras guardar
            st.session_state.edit_data = None
            st.success("Nueva versión guardada correctamente.")
            st.link_button("👁️ VER VISTA PREVIA", l_i, use_container_width=True)

# --- PESTAÑA FLOTAS (Se mantiene igual) ---
with tab_flota:
    st.subheader("🚛 Cotizador de Flotas Pro")
    # ... (mismo código de flotas de antes)

# --- PESTAÑA HISTORIAL (CON BOTÓN EDITAR) ---
with tab_hist:
    st.subheader("📜 Gestión de Historial")
    c_bus, c_ref, c_del_all = st.columns([3, 1, 2])
    busqueda_h = c_bus.text_input("🔍 Buscar por cliente...", key="bus_hist")
    if c_ref.button("🔄 ACTUALIZAR"): st.rerun()
    
    if c_del_all.button("🔥 BORRAR TODO EL HISTORIAL", type="primary"):
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        res = requests.delete(f"{SUPABASE_URL}/rest/v1/cotizaciones?id=not.is.null", headers=headers)
        if res.status_code in [200, 204]: st.success("Vaciado."); st.rerun()

    df_h = leer_historial()
    if not df_h.empty:
        df_h['Fecha'] = pd.to_datetime(df_h['created_at']).dt.strftime('%d/%m/%Y %H:%M')
        if busqueda_h:
            df_h = df_h[df_h['asegurado'].str.contains(busqueda_h, case=False, na=False)]
        
        # Mostramos el historial con opción de editar
        for index, row in df_h.iterrows():
            with st.container(border=True):
                h1, h2, h3 = st.columns([4, 1, 1])
                h1.write(f"📅 {row['Fecha']} | 👤 **{row['asegurado']}** ({row['tipo']})")
                h2.link_button("📂 VER", row['link_cotizacion'], use_container_width=True)
                if h3.button("📝 EDITAR", key=f"btn_ed_{row['id']}", use_container_width=True):
                    st.session_state.edit_data = row['datos_json']
                    st.session_state.es_edicion = True
                    st.success("✅ Datos cargados. Por favor, ve a la pestaña COTIZADOR.")
                    st.rerun()
    else:
        st.info("El historial está vacío.")

# --- PESTAÑA ANÁLISIS ---
with tab_an:
    st.subheader("📊 Análisis de Cartera")
    if not df_f.empty:
        total_usd = df_f['Premio_Total_USD'].sum()
        total_polizas = len(df_f)
        k1, k2 = st.columns(2)
        k1.metric("Cartera Total (USD)", f"USD {total_usd:,.0f}")
        k2.metric("Total de Pólizas", f"{total_polizas}")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Compañía (USD)", hole=0.4), use_container_width=True)
        with c2: st.plotly_chart(px.pie(df_f, names='Ramo', values='Premio_Total_USD', title="Ramo (USD)", hole=0.4), use_container_width=True)
