import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64
import urllib.request
import urllib.parse

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

def fmt_curr(val):
    try: return f"$ {int(float(val)):,}".replace(",", ".")
    except: return val

st.markdown("""
    <style>
    @media print {
        .stButton, [data-testid="stSidebar"], .stDownloadButton, footer, header { display: none !important; }
        .main .block-container { padding: 0 !important; margin: 0 !important; }
    }
    .titulo-bordo { color: #800020; font-size: 22px; font-weight: bold; border-bottom: 3px solid #800020; padding-bottom: 8px; margin-bottom: 20px; text-transform: uppercase; white-space: nowrap; }
    .quote-card { background-color: #fdfdfd; padding: 20px; border-radius: 10px; border: 1px solid #eee; white-space: pre-wrap; font-family: sans-serif; font-size: 14px; line-height: 1.6; }
    [data-testid="stTable"] td { text-align: right !important; }
    [data-testid="stTable"] td:first-child { text-align: left !important; }
    
    /* Botón Excel estilo compacto */
    .stDownloadButton button {
        background-color: #1D6F42 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: bold !important;
        border: none !important;
        width: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🕵️ LÓGICA DE VISTA DE CLIENTE
# ==========================================
query_params = st.query_params
if "q" in query_params:
    try:
        data_raw = base64.b64decode(query_params["q"]).decode()
        q_data = json.loads(data_raw)
        st.markdown("<div class='titulo-bordo'>🛡️ EDF SEGUROS - COTIZACIÓN SEGURO DE VEHÍCULOS</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Asegurado:** {q_data['n']}")
            st.markdown(f"**Vehículo:** {q_data['v']}")
            if 'cob' in q_data and q_data['cob']: st.markdown(f"**Cobertura:** {q_data['cob']}")
        with c2:
            st.markdown(f"**Fecha:** {date.today().strftime('%d/%m/%Y')}")
            st.markdown(f"**Asesor:** {q_data['e']}")
        
        st.write("### 💰 Comparativa de Opciones")
        df_view = pd.DataFrame(q_data['tab'])
        for col in ["Contado", "10 Cuotas", "Deducible"]:
            if col in df_view.columns: df_view[col] = df_view[col].apply(fmt_curr)
        st.table(df_view) 
        
        st.write("### ✅ Beneficios Incluidos")
        st.markdown(f"<div class='quote-card'>{q_data['ben']}</div>", unsafe_allow_html=True)
        
        st.write("### 🏠 Coberturas Complementarias")
        col_comp = st.columns(3)
        with col_comp[0]:
            st.info("**Hogar**"); st.caption(q_data['ch'])
        with col_comp[1]:
            st.info("**Alquiler**"); st.caption(q_data['ca'])
        with col_comp[2]:
            st.info("**Bici**"); st.caption(q_data['cb'])

        st.markdown("---")
        if st.button("🖨️ Imprimir / Guardar PDF", use_container_width=True):
            st.components.v1.html("<script>window.parent.print();</script>", height=0)
        st.stop() 
    except:
        st.error("Error al cargar la cotización."); st.stop()

# ==========================================
# 🔐 SEGURIDAD
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", 
    "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025",
    "GS": "GSanchez2025", "MDF": "Matiti2025", "EH": "EHugo2025",
    "AP": "APerdomo2025", "RS": "RSierra2025", "LT": "LTomasi2025",
    "EC": "ECabral2025", "PG": "PGagliardi2025"
}

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

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        df['Premio_Total_USD'] = (pd.to_numeric(df.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0) + (pd.to_numeric(df.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0) / TC_USD)).round(0)
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos()
# ==========================================
# 📊 INTERFAZ PRINCIPAL
# ==========================================
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    def get_list(col): 
        return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
    f_ej = st.selectbox("Ejecutivo", get_list('Ejecutivo'))
    f_as = st.selectbox("Aseguradora", get_list('Aseguradora'))
    f_ra = st.selectbox("Ramo", get_list('Ramo'))
    f_co = st.selectbox("Corredor", get_list('Corredor'))
    f_ag = st.selectbox("Agente", get_list('Agente'))
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False; st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]

config_simple = {}
if "Adjunto (póliza)" in df_f.columns: config_simple["Adjunto (póliza)"] = st.column_config.LinkColumn("Póliza", display_text="📂")
if "Premio_Total_USD" in df_f.columns: config_simple["Premio_Total_USD"] = st.column_config.NumberColumn("Total USD", format="U$S %d")

tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

with tab1:
    busq = st.text_input("🔍 Buscar cliente o matrícula...")
    df_cartera = df_f.copy()
    if busq:
        mask = df_cartera.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)
        df_cartera = df_cartera[mask]
    st.dataframe(df_cartera, use_container_width=True, hide_index=True, column_config=config_simple)

with tab2:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty and "Fin de Vigencia" in df_f.columns:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        df_v = df_v[(df_v['Fin de Vigencia'] >= date(2020, 1, 1)) & (df_v['Fin de Vigencia'] <= date(2040, 12, 31))]
        c_f1, c_f2 = st.columns(2)
        hoy = date.today()
        with c_f1: f_ini = st.date_input("Desde:", hoy.replace(day=1))
        with c_f2: f_fin = st.date_input("Hasta:", hoy + timedelta(days=90))
        df_venc_final = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')
        st.dataframe(df_venc_final, use_container_width=True, hide_index=True, column_config=config_simple)
        
        # EXCEL ABAJO Y CHICO
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_venc_final.to_excel(writer, index=False, sheet_name='Vencimientos')
        processed_data = output.getvalue()
        c_ex, _ = st.columns([1, 3])
        with c_ex:
            st.download_button(label="📥 EXCEL", data=processed_data, file_name=f'vencimientos.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

with tab3:
    st.subheader("📝 Generador de Cotizaciones")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc_in = c1.text_input("Documento (CI / RUT)")
        nom_sug = ""
        if doc_in and not df_raw.empty:
            match = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains(doc_in)).any(axis=1)]
            if not match.empty: nom_sug = match.iloc[0].get('Asegurado (Nombre/Razón Social)', "")
        n_cot = c1.text_input("Asegurado", value=nom_sug)
        v_cot = c2.text_input("Vehículo (Marca/Modelo/Año)")
        cob_cot = c2.text_input("Cobertura")
        e_cot = c3.selectbox("Hecha por:", sorted(list(USUARIOS.keys())), index=sorted(list(USUARIOS.keys())).index(st.session_state['usuario_actual']) if st.session_state['usuario_actual'] in USUARIOS else 0)

    t_edit = st.data_editor(pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}]), num_rows="dynamic", use_container_width=True)

    st.write("### ✅ Detalles de Cobertura")
    col_a, col_b = st.columns(2)
    with col_a:
        # CAMBIO: Quitamos los guiones para forzar alineación izquierda
        txt_ben = "• Auxilio mecánico 24hs:\nTodas las aseguradoras\n\n• Ayuda económica para cristales:\nSBI: USD 200\nBSE: USD 200\nSURA: USD 100\nSANCOR: USD 300\nMAPFRE: Ilimitado\n\n• Ayuda económica para granizo:\nPORTO: Sin deducible"
        b_cot = st.text_area("Beneficios Incluidos:", value=txt_ben, height=350)
    with col_b:
        txt_hog = "• Incendio Edificio: USD 100.000\n• Incendio Contenido: USD 20.000\n• Hurto Contenido: USD 5.000\n• COSTO ANUAL: USD 120"
        txt_alq = "• Auto cortesía 15 días por siniestro.\n• COSTO ANUAL: UYU 3.900"
        txt_bic = "• Hurto Bici valor hasta USD 1.000\n• Responsabilidad Civil: USD 10.000\n• COSTO ANUAL: USD 70"
        c_h = st.text_area("Hogar:", value=txt_hog, height=140)
        c_a = st.text_area("Alquiler:", value=txt_alq, height=100)
        c_b = st.text_area("Bici:", value=txt_bic, height=125)

    st.divider()
    datos = {"n": n_cot, "v": v_cot, "cob": cob_cot, "e": e_cot, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b}
    b64 = base64.b64encode(json.dumps(datos).encode()).decode()
    l_final = f"https://dfseguros.streamlit.app/?q={b64}"
    wa_url = f"https://wa.me/?text={urllib.parse.quote(f'🛡️ *EDF SEGUROS*\n\nHola {n_cot}, adjunto cotización para {v_cot}:\n\n{l_final}')}"
    c_btn1, c_btn2, _ = st.columns([1, 1, 2])
    with c_btn1: st.code(l_final, language=None)
    with c_btn2: st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%;background-color:#25D366;color:white;border:none;padding:10px;border-radius:8px;font-weight:bold;cursor:pointer;">🟢 WHATSAPP</button></a>', unsafe_allow_html=True)

with tab4:
    if not df_f.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Cartera (USD)", f"U$S {df_f['Premio_Total_USD'].sum():,.0f}")
        m2.metric("Pólizas", f"{len(df_f)} u.")
        m3.metric("Promedio", f"U$S {df_f['Premio_Total_USD'].mean():,.0f}")
        st.divider()
        c_g1, c_g2 = st.columns(2)
        with c_g1: st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía", hole=0.4), use_container_width=True)
        with c_g2: st.plotly_chart(px.bar(df_f['Ramo'].value_counts().reset_index(), x='Ramo', y='count', title="Pólizas por Ramo"), use_container_width=True)
