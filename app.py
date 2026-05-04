import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

st.markdown("<style>.main .block-container { padding-top: 1.5rem; } .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }</style>", unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = u
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA Y PROCESAMIENTO
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos_completos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        # Procesar Premios
        df['Premio USD (IVA inc)'] = pd.to_numeric(df.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0)
        df['Premio_Total_USD'] = (df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)).round(0)
        # Procesar Fechas
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos_completos()

with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    def get_list(col): return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
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

# --- CONFIGURACIÓN DE COLUMNAS (DEFINIDA GLOBALMENTE) ---
COL_QUEREMOS = [
    "Asegurado (Nombre/Razón Social)", "Ramo", "Aseguradora", "Fin de Vigencia", 
    "Detalle (Matricula o Referencia)", "Premio USD (IVA inc)", "Premio UYU (IVA inc)", 
    "Premio_Total_USD", "Adjunto (póliza)"
]
config_final = {col: st.column_config.Column(visible=(col in COL_QUEREMOS)) for col in df_f.columns}
if "Adjunto (póliza)" in config_final: config_final["Adjunto (póliza)"] = st.column_config.LinkColumn("Póliza", display_text="📂")
if "Premio_Total_USD" in config_final: config_final["Premio_Total_USD"] = st.column_config.NumberColumn("Total USD", format="U$S %d")

st.markdown("# 🛡️ EDF SEGUROS")
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

st.markdown("<style>.main .block-container { padding-top: 1.5rem; } .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }</style>", unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = u
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA Y PROCESAMIENTO
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos_completos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        # Procesar Premios
        df['Premio USD (IVA inc)'] = pd.to_numeric(df.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0)
        df['Premio_Total_USD'] = (df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)).round(0)
        # Procesar Fechas
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos_completos()

with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    def get_list(col): return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
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

# --- CONFIGURACIÓN DE COLUMNAS (DEFINIDA GLOBALMENTE) ---
COL_QUEREMOS = [
    "Asegurado (Nombre/Razón Social)", "Ramo", "Aseguradora", "Fin de Vigencia", 
    "Detalle (Matricula o Referencia)", "Premio USD (IVA inc)", "Premio UYU (IVA inc)", 
    "Premio_Total_USD", "Adjunto (póliza)"
]
config_final = {col: st.column_config.Column(visible=(col in COL_QUEREMOS)) for col in df_f.columns}
if "Adjunto (póliza)" in config_final: config_final["Adjunto (póliza)"] = st.column_config.LinkColumn("Póliza", display_text="📂")
if "Premio_Total_USD" in config_final: config_final["Premio_Total_USD"] = st.column_config.NumberColumn("Total USD", format="U$S %d")

st.markdown("# 🛡️ EDF SEGUROS")
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])
