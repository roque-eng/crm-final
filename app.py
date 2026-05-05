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
    .titulo-bordo { color: #800020; font-size: 22px; font-weight: bold; border-bottom: 3px solid #800020; padding-bottom: 8px; margin-bottom: 20px; text-transform: uppercase; }
    .quote-card { background-color: #fdfdfd; padding: 20px; border-radius: 10px; border: 1px solid #eee; white-space: pre-wrap; font-family: sans-serif; font-size: 14px; line-height: 1.6; }
    [data-testid="stTable"] td { text-align: right !important; }
    [data-testid="stTable"] td:first-child { text-align: left !important; }
    .stDownloadButton button { background-color: #1D6F42 !important; color: white !important; border-radius: 8px !important; width: auto !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🕵️ LÓGICA DE VISTA DE CLIENTE (Individual y Flotas)
# ==========================================
query_params = st.query_params
if "q" in query_params or "f" in query_params:
    is_flota = "f" in query_params
    param = "f" if is_flota else "q"
    try:
        data_raw = base64.b64decode(query_params[param]).decode()
        q_data = json.loads(data_raw)
        st.markdown(f"<div class='titulo-bordo'>🛡️ EDF SEGUROS - {'PROPUESTA FLOTA' if is_flota else 'COTIZACIÓN VEHÍCULOS'}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Asegurado:** {q_data['n']}")
            if not is_flota: st.markdown(f"**Vehículo:** {q_data['v']}")
        with c2:
            st.markdown(f"**Fecha:** {date.today().strftime('%d/%m/%Y')}")
            st.markdown(f"**Asesor:** {q_data['e']}")
        
        st.write("### 💰 Detalle de la Propuesta")
        df_view = pd.DataFrame(q_data['tab'])
        # Formatear columnas de precio si existen
        for col in df_view.columns:
            if any(palabra in col.lower() for palabra in ["precio", "contado", "cuotas", "deducible"]):
                df_view[col] = df_view[col].apply(fmt_curr)
        st.table(df_view) 
        
        st.write("### ✅ Beneficios Incluidos")
        st.markdown(f"<div class='quote-card'>{q_data['ben']}</div>", unsafe_allow_html=True)
        
        if not is_flota: # Coberturas extras solo en individual
            st.write("### 🏠 Coberturas Complementarias")
            col_comp = st.columns(3)
            with col_comp[0]: st.info("**Hogar**"); st.caption(q_data['ch'])
            with col_comp[1]: st.info("**Alquiler**"); st.caption(q_data['ca'])
            with col_comp[2]: st.info("**Bici**"); st.caption(q_data['cb'])

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
    def get_list(col): return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
    f_ej = st.selectbox("Ejecutivo", get_list('Ejecutivo'))
    f_as = st.selectbox("Aseguradora", get_list('Aseguradora'))
    f_ra = st.selectbox("Ramo", get_list('Ramo'))
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False; st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]

tab1, tab2, tab3, tab_flota, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "🚛 FLOTAS", "📊 ANÁLISIS"])

# --- TAB 1 Y 2 SE MANTIENEN IGUAL QUE ANTES ---
with tab1:
    busq = st.text_input("🔍 Buscar cliente...")
    st.dataframe(df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty and "Fin de Vigencia" in df_f.columns:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Desde:", date.today().replace(day=1))
        f_fin = c_f2.date_input("Hasta:", date.today() + timedelta(days=90))
        df_venc_final = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')
        st.dataframe(df_venc_final, use_container_width=True, hide_index=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_venc_final.to_excel(writer, index=False)
        st.download_button(label="📥 EXCEL", data=output.getvalue(), file_name='vencimientos.xlsx')

# --- TAB 3: COTIZADOR INDIVIDUAL ---
with tab3:
    st.subheader("📝 Generador Individual")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc_in = c1.text_input("CI / RUT")
        n_cot = c1.text_input("Asegurado")
        v_cot = c2.text_input("Vehículo")
        cob_cot = c2.text_input("Cobertura")
        e_cot = c3.selectbox("Asesor", sorted(list(USUARIOS.keys())), index=0)
    t_edit = st.data_editor(pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}]), num_rows="dynamic", use_container_width=True)
    txt_ben = "• Auxilio mecánico 24hs:\nTodas las aseguradoras\n\n• Ayuda económica para cristales:\nSBI: USD 200\nBSE: USD 200\nSURA: USD 100\nSANCOR: USD 300\nMAPFRE: Ilimitado\n\n• Ayuda económica para granizo:\nPORTO: Sin deducible"
    b_cot = st.text_area("Beneficios:", value=txt_ben, height=200)
    datos = {"n": n_cot, "v": v_cot, "cob": cob_cot, "e": e_cot, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": "", "ca": "", "cb": ""}
    if st.button("Generar Link Individual"):
        b64 = base64.b64encode(json.dumps(datos).encode()).decode()
        st.code(f"https://dfseguros.streamlit.app/?q={b64}", language=None)

# --- NUEVA TAB: COTIZADOR FLOTAS ---
with tab_flota:
    st.subheader("🚛 Generador de Propuestas para Flotas")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        f_doc = c1.text_input("CI / RUT Flota")
        f_nom = c1.text_input("Asegurado Flota")
        f_as1 = c2.text_input("Aseguradora 1", value="SURA")
        f_as2 = c2.text_input("Aseguradora 2", value="BSE")
        f_as3 = c3.text_input("Aseguradora 3", value="PORTO")
        f_ase = c3.selectbox("Asesor Flota", sorted(list(USUARIOS.keys())), key="ase_flota")

    # Creamos la tabla dinámica para flotas
    df_flota_init = pd.DataFrame([
        {"Vehículo": "Auto 1", "Cobertura": "Todo Riesgo", f"Precio {f_as1}": 0, f"Ded. {f_as1}": 0, f"Precio {f_as2}": 0, f"Ded. {f_as2}": 0, f"Precio {f_as3}": 0, f"Ded. {f_as3}": 0}
    ])
    
    t_flota = st.data_editor(df_flota_init, num_rows="dynamic", use_container_width=True)
    
    f_ben = st.text_area("Beneficios Incluidos (Flota):", value=txt_ben, height=250)
    
    if st.button("Generar Link de Flota"):
        datos_f = {"n": f_nom, "e": f_ase, "tab": t_flota.to_dict(orient='records'), "ben": f_ben}
        b64_f = base64.b64encode(json.dumps(datos_f).encode()).decode()
        l_f = f"https://dfseguros.streamlit.app/?f={b64_f}"
        st.write("**Link para el Cliente:**")
        st.code(l_f, language=None)
        wa_flota = f"https://wa.me/?text={urllib.parse.quote(f'🛡️ *EDF SEGUROS - Propuesta Flota*\n\nHola {f_nom}, adjunto la comparativa:\n\n{l_f}')}"
        st.markdown(f'<a href="{wa_flota}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:10px;border-radius:8px;font-weight:bold;">🟢 ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)

with tab4:
    if not df_f.empty:
        st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía"), use_container_width=True)
