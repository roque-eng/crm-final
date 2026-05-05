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

# Credenciales Supabase (Usa las de tu captura image_e811dd.jpg)
SUPABASE_URL = "https://flizerdhoxxoekaczihm.supabase.co"
SUPABASE_KEY = "TU_KEY_ANON_PUBLICA_AQUI" 

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
    [data-testid="stTable"] td:first-child { text-align: left !important; }
    </style>
    """, unsafe_allow_html=True)

# VISTA CLIENTE
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
    except: st.error("Error al cargar la vista."); st.stop()
        # ==========================================
# 🔐 SEGURIDAD Y DATOS
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
    if st.button("Cerrar Sesión"): st.session_state['logueado'] = False; st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
    # ==========================================
# 🏢 PESTAÑAS Y FUNCIONALIDADES
# ==========================================
tab1, tab2, tab3, tab_flota, tab_hist, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "🚛 FLOTAS", "📜 HISTORIAL", "📊 ANÁLISIS"])

with tab3:
    st.subheader("📝 Cotizador Individual")
    with st.container(border=True):
        c_doc, c_nom, c_veh, c_ase, c_con = st.columns([1.5, 2, 2, 1, 2])
        doc_in = c_doc.text_input("CI/RUT")
        n_sug = ""
        if doc_in and not df_raw.empty:
            match = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains(doc_in, na=False)).any(axis=1)]
            if not match.empty:
                for c in ["Asegurado", "Cliente", "Asegurado (Nombre/Razón Social)"]:
                    if c in df_raw.columns: n_sug = match.iloc[0][c]; break
        n_cot = c_nom.text_input("Nombre", value=n_sug)
        v_cot = c_veh.text_input("Vehículo")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), index=0)
        cont_cot = c_con.text_input("Nombre y Contacto Asesor")

    t_edit = st.data_editor(pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}]), num_rows="dynamic", use_container_width=True)
    col_a, col_b = st.columns(2)
    with col_a:
        txt_ben = "• Auxilio mecánico 24hs: Todas las aseguradoras\n• Cristales: BSE/SBI USD 200, SURA USD 100, MAPFRE ílimitado, SANCOR USD 300\n• Granizo: PORTO sin deducible"
        b_cot = st.text_area("Beneficios:", value=txt_ben, height=200)
    with col_b:
        txt_h = "• Incendio Edificio: USD 100.000\n• Incendio Contenido: USD 50.000\n• Hurto Contenido: USD 5.000\n• Remoción de Escombros: USD 5.000\nCosto Anual Apartamentos: USD 120\nCosto Anual Casas: USD 190"
        c_h = st.text_area("Hogar:", value=txt_h, height=150)
        c_a = st.text_area("Alquiler:", value="• Auto cortesía 15 días\nCosto: UYU 3.500", height=70); c_b = st.text_area("Bici:", value="• Hurto USD 1.000\nCosto: USD 110", height=70)

    if st.button("💾 Guardar y Ver", key="sv_ind"):
        datos = {"n": n_cot, "v": v_cot, "e": e_cot, "cont": cont_cot, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b}
        l_final = f"https://dfseguros.streamlit.app/?q={base64.b64encode(json.dumps(datos).encode()).decode()}"
        db_data = {"tipo": "individual", "documento": doc_in, "asegurado": n_cot, "vehiculo_o_flota": v_cot, "asesor": e_cot, "datos_json": datos, "link_cotizacion": l_final}
        if guardar_en_db(db_data):
            st.success("Guardado con éxito"); st.link_button("👉 VER VISTA PREVIA", l_final)
            st.components.v1.html(f'<script>window.open("{l_final}", "_blank");</script>', height=0)

with tab_flota:
    st.subheader("🚛 Cotizador de Flotas")
    with st.container(border=True):
        f1, f2, f3, f4, f5, f6 = st.columns([2, 1.2, 1.2, 1.2, 1, 2])
        f_nom = f1.text_input("Asegurado Flota")
        f_as1 = f2.text_input("Cía 1", value="SURA"); f_as2 = f3.text_input("Cía 2", value="BSE"); f_as3 = f4.text_input("Cía 3", value="SBI")
        f_ase = f5.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="f_ase"); f_cont = f6.text_input("Contacto", key="f_cont")
    t_flota = st.data_editor(pd.DataFrame([{"Vehículo": "Unidad 1", f"Precio {f_as1}": 0, f"Ded {f_as1}": 0, f"Precio {f_as2}": 0, f"Ded {f_as2}": 0, f"Precio {f_as3}": 0, f"Ded {f_as3}": 0}]), num_rows="dynamic", use_container_width=True)
    if st.button("💾 Guardar y Ver Flota", key="sv_fl"):
        datos_f = {"n": f_nom, "e": f_ase, "cont": f_cont, "tab": t_flota.to_dict(orient='records'), "ben": txt_ben}
        l_f = f"https://dfseguros.streamlit.app/?f={base64.b64encode(json.dumps(datos_f).encode()).decode()}"
        db_data = {"tipo": "flota", "asegurado": f_nom, "vehiculo_o_flota": "Flota", "asesor": f_ase, "datos_json": datos_f, "link_cotizacion": l_f}
        if guardar_en_db(db_data):
            st.success("Flota guardada"); st.link_button("👉 VER VISTA PREVIA", l_f)
            st.components.v1.html(f'<script>window.open("{l_f}", "_blank");</script>', height=0)

with tab_hist:
    st.subheader("📜 Historial")
    df_h = leer_historial()
    if not df_h.empty:
        df_h['created_at'] = pd.to_datetime(df_h['created_at']).dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(df_h[['created_at', 'tipo', 'asegurado', 'asesor', 'link_cotizacion']], use_container_width=True, hide_index=True)

with tab1:
    busq = st.text_input("🔍 Buscar...")
    df_c = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f
    st.dataframe(df_c, use_container_width=True, hide_index=True, column_config={"Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")})

with tab4:
    c1, c2 = st.columns(2)
    with c1: st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cía (USD)", hole=0.4), use_container_width=True)
    with c2: st.plotly_chart(px.pie(df_f, names='Ramo', values='Premio_Total_USD', title="Ramo (USD)", hole=0.4), use_container_width=True)
