import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# ⚙️ CONFIGURACIÓN DE PERFILES POR USUARIO
# ==========================================
PERFILES_DEFAULTS = {
    "RDF": ["Asegurado (Nombre/Razón Social)", "Documento de Identidad (Rut/Cédula/Otros)", "Ramo", "Aseguradora", "Inicio de Vigencia", "Fin de Vigencia", "Premio_Total_USD", "Adjunto (póliza)"],
    "JOE": ["Asegurado (Nombre/Razón Social)", "Detalle (Matrícula o Referencia)", "Ramo", "Inicio de Vigencia", "Fin de Vigencia", "Estado_Gestion", "Adjunto (póliza)"],
    "ANDRE": ["Asegurado (Nombre/Razón Social)", "Celular", "Aseguradora", "Inicio de Vigencia", "Fin de Vigencia", "Corredor", "Adjunto (póliza)"]
}

# ==========================================
# 🔗 CONFIGURACIÓN Y CONEXIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .left-title { font-size: 30px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 0px; }
    /* Resaltado del buscador */
    div[data-baseweb="input"] {
        border: 1.5px solid #1E1E1E !important;
        border-radius: 8px;
    }
    /* Estilo para los tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 5px 5px 0px 0px;
        padding: 8px 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", 
    "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", 
    "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", 
    "AC": "ACazarian2025", "MF": "MFlores2025", "JOE": "Joe2025", "ANDRE": "Andre2025"
}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False

if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = u
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        
        df['Inicio de Vigencia'] = pd.to_datetime(df['Inicio de Vigencia'], dayfirst=True, errors='coerce')
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
        df['Fin_V_dt'] = df['Fin de Vigencia'].dt.date
        
        if 'Estado_Gestion' not in df.columns: df['Estado_Gestion'] = "Pendiente"
        df['Estado_Gestion'] = df['Estado_Gestion'].fillna("Pendiente")
        
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

df_raw = cargar_datos()
user = st.session_state["usuario_actual"]
cols_default = PERFILES_DEFAULTS.get(user, ["Asegurado (Nombre/Razón Social)", "Ramo", "Fin de Vigencia", "Adjunto (póliza)"])

# ==========================================
# 🎯 BARRA LATERAL (SIDEBAR) - FILTROS Y USUARIO
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {user}")
    st.markdown("---")
    st.markdown("### 🔍 Filtros de Oficina")
    
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_co = st.selectbox("Corredor", ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()))
    f_ag = st.selectbox("Agente", ["Todos"] + sorted(df_raw['Agente'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    
    st.markdown("---")
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

# Filtrado de datos
df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]

# Título principal
st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)

# ==========================================
# 📑 PESTAÑAS PRINCIPALES
# ==========================================
tab1, tab2, tab3 = st.tabs(["👥 CARTERA TOTAL", "🔄 VENCIMIENTOS", "📊 ANÁLISIS"])

with tab1:
    # BUSCADOR RESALTADO
    st.markdown("### 🔎 Buscar Cliente")
    busqueda = st.text_input("Ingresa nombre, documento o número de póliza...", placeholder="Ej: Juan Perez o 123456", label_visibility="collapsed")
    
    df_tab1 = df_f.copy()
    if busqueda:
        mask = df_tab1.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_tab1 = df_tab1[mask]
    
    # Configuración de columnas
    config_columnas = {
        "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂", required=True),
        "Fin de Vigencia": st.column_config.DateColumn("Vencimiento", format="DD/MM/YYYY"),
        "Inicio de Vigencia": st.column_config.DateColumn("Inicio", format="DD/MM/YYYY"),
        "Premio_Total_USD": st.column_config.NumberColumn("Total USD", format="U$S %.2f")
    }
    
    # Ocultar columnas que no pertenecen al perfil
    cols_a_ocultar = [c for c in df_tab1.columns if c not in cols_default and c != "Fin_V_dt"]
    for col in cols_a_ocultar:
        config_columnas[col] = None

    st.dataframe(
        df_tab1.drop(columns=['Fin_V_dt'], errors='ignore'), 
        use_container_width=True, 
        hide_index=True,
        column_config=config_columnas
    )

with tab2:
    st.subheader("📅 Gestión de Renovaciones")
    dias_v = st.slider("Días a futuro:", 15, 365, 60)
    ver_gest = st.checkbox("Ver ya gestionados")
    
    hoy = date.today()
    limite = hoy + timedelta(days=dias_v)
    df_v = df_f.dropna(subset=['Fin_V_dt']).sort_values('Fin_V_dt')
    df_v = df_v[(df_v['Fin_V_dt'] >= hoy) & (df_v['Fin_V_dt'] <= limite)].copy()
    
    if not ver_gest:
        df_v = df_v[df_v['Estado_Gestion'] != "Renovado"]
    
    config_v = {
        "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂", required=True),
        "Fin de Vigencia": st.column_config.DateColumn("Vencimiento", format="DD/MM/YYYY"),
        "Estado_Gestion": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "En Gestión", "Renovado", "Anulado"])
    }
    
    # Ocultar lo que no es del perfil para esta pestaña también
    for col in [c for c in df_v.columns if c not in cols_default]:
        config_v[col] = None

    st.dataframe(df_v, use_container_width=True, hide_index=True, column_config=config_v)

with tab3:
    st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="USD por Compañía"), use_container_width=True)
