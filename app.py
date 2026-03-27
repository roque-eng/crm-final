import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# 🔗 CONFIGURACIÓN DE LA FUENTE DE DATOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS PARA COMPACTAR INTERFAZ ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .left-title { font-size: 32px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 0px; }
    .user-info { text-align: right; font-weight: bold; font-size: 14px; color: #666; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 40px; border-radius: 4px 4px 0px 0px; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", "AC": "ACazarian2025", "MF": "MFlores2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True; st.session_state['usuario_actual'] = u; st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CONEXIÓN Y CARGA
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        if 'Fin de Vigencia' in df.columns:
            df['Fin_V_dt'] = pd.to_datetime(df['Fin de Vigencia'], errors='coerce').dt.date
        return df
    except Exception as e:
        st.error(f"Error: {e}"); return pd.DataFrame()

df_raw = cargar_datos()

# --- ENCABEZADO Y LOGIN ---
col_tit, col_user_box = st.columns([8, 2])
with col_tit: st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)
with col_user_box:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión", use_container_width=True): st.session_state['logueado'] = False; st.rerun()

st.divider()

# ==========================================
# 🎯 FILTROS ALINEADOS (SUPERIORES)
# ==========================================
with st.expander("🔍 Filtros", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    
    lista_ej = ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["Todos"]
    lista_co = ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()) if 'Corredor' in df_raw.columns else ["Todos"]
    lista_ag = ["Todos"] + sorted(df_raw['Agente'].dropna().unique().tolist()) if 'Agente' in df_raw.columns else ["Todos"]
    lista_as = ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()) if 'Aseguradora' in df_raw.columns else ["Todos"]

    f_ej = c1.selectbox("Ejecutivo", lista_ej)
    f_co = c2.selectbox("Corredor", lista_co)
    f_ag = c3.selectbox("Agente", lista_ag)
    f_as = c4.selectbox("Aseguradora", lista_as)

# Aplicar lógica de filtrado
df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]

# ==========================================
# 📑 CONTENIDO PRINCIPAL
# ==========================================
if not df_raw.empty:
    tab1, tab2, tab3 = st.tabs(["👥 CARTERA TOTAL", "🔄 VENCIMIENTOS", "📊 ANÁLISIS"])

    with tab1:
        busqueda = st.text_input("🔍 Buscar por Nombre o Documento en la lista filtrada...")
        df_tab1 = df_f.copy()
        if busqueda:
            mask = df_tab1.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
            df_tab1 = df_tab1[mask]
        
        # Ocultamos columnas que ya están en los filtros para ahorrar espacio
        ocultas = ['Ejecutivo', 'Corredor', 'Agente', 'Aseguradora', 'Fin_V_dt', 'Marca temporal', 'Dirección de correo electrónico']
        cols_visibles = [c for c in df_tab1.columns if c not in ocultas]
        
        st.dataframe(df_tab1[cols_visibles], use_container_width=True, hide_index=True,
            column_config={
                "adjunto [póliza]": st.column_config.LinkColumn("Póliza", display_text="📂"),
                "Fin de Vigencia": st.column_config.DateColumn("Vence")
            })

    with tab2:
        hoy = date.today()
        proximos = hoy + timedelta(days=60)
        df_v = df_f[(df_f['Fin_V_dt'] >= hoy) & (df_f['Fin_V_dt'] <= proximos)].sort_values('Fin_V_dt')
        
        cols_v = [c for c in df_v.columns if c not in ['Ejecutivo', 'Corredor', 'Agente', 'Marca temporal', 'Fin_V_dt', 'Dirección de correo electrónico']]
        st.dataframe(df_v[cols_v], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📊 Resumen del Segmento")
        st.metric("Pólizas encontradas", len(df_f))
        fig = px.pie(df_f, names='Ramo', title="Ramos en la selección actual")
        st.plotly_chart(fig, use_container_width=True)
