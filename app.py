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

TC_USD = 40.5 

st.markdown("""
    <style>
    .left-title { font-size: 30px !important; font-weight: bold; text-align: left; color: #31333F; margin-top: -15px; }
    .user-info { text-align: right; font-weight: bold; font-size: 14px; color: #555; margin-bottom: 5px; }
    .reg-btn { text-decoration: none !important; background-color: #333 !important; color: #FFFFFF !important; padding: 8px 12px; border-radius: 5px; font-weight: bold; font-size: 12px !important; display: inline-block; margin-top: 5px; border: 1px solid #000; }
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
# ⚙️ CONEXIÓN A GOOGLE SHEETS (MODO PRIVADO)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def cargar_datos():
    try:
        # IMPORTANTE: Usamos el conector para leer la hoja privada
        df = conn.read(spreadsheet=URL_HOJA)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# --- ENCABEZADO ---
col_tit, col_user_box = st.columns([8, 2])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - EDF SEGUROS</p>', unsafe_allow_html=True)
with col_user_box:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión"): st.session_state['logueado'] = False; st.rerun()

df_raw = cargar_datos()

if not df_raw.empty:
    tab1, tab2, tab3 = st.tabs(["👥 CARTERA TOTAL", "🔄 VENCIMIENTOS", "📊 ANÁLISIS"])

    with tab1:
        busqueda = st.text_input("🔍 Buscar por Asegurado, Ramo o Compañía...")
        df_display = df_raw.copy()
        if busqueda:
            mask = df_display.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
            df_display = df_display[mask]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True,
            column_config={
                "adjunto [póliza]": st.column_config.LinkColumn("Póliza", display_text="Ver"),
                "Fin de Vigencia": st.column_config.DateColumn("Vencimiento")
            })

    with tab2:
        st.subheader("📅 Próximas Renovaciones")
        if 'Fin de Vigencia' in df_raw.columns:
            df_raw['Fin_V_dt'] = pd.to_datetime(df_raw['Fin de Vigencia'], errors='coerce').dt.date
            hoy = date.today()
            df_v = df_raw[(df_raw['Fin_V_dt'] >= hoy) & (df_raw['Fin_V_dt'] <= hoy + timedelta(days=60))].sort_values('Fin_V_dt')
            st.dataframe(df_v.drop(columns=['Fin_V_dt']), use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📊 Resumen")
        st.metric("Pólizas Activas", len(df_raw))
        if 'Aseguradora' in df_raw.columns:
            st.plotly_chart(px.pie(df_raw, names='Aseguradora', title="Por Compañía"), use_container_width=True)
