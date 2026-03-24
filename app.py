import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# 🔗 CONFIGURACIÓN DE LA FUENTE DE DATOS
# ==========================================
# PEGA AQUÍ EL LINK DE TU GOOGLE SHEETS (Asegúrate que diga "Cualquier persona con el enlace puede ver")
URL_HOJA = "https://docs.google.com/spreadsheets/d/TU_ID_DE_HOJA_AQUI/edit?usp=sharing"

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

TC_USD = 40.5 

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .left-title { font-size: 30px !important; font-weight: bold; text-align: left; color: #31333F; margin-top: -15px; }
    .user-info { text-align: right; font-weight: bold; font-size: 16px; color: #555; margin-bottom: 5px; }
    .reg-btn { text-decoration: none !important; background-color: #333 !important; color: #FFFFFF !important; padding: 8px 12px; border-radius: 5px; font-weight: bold; font-size: 12px !important; display: inline-block; margin-top: 5px; border: 1px solid #000; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", "AC": "ACazarian2025", "MF": "MFlores2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>☁️ CRM Grupo EDF</h1>", unsafe_allow_html=True)
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
# ⚙️ CONEXIÓN DIRECTA A GOOGLE SHEETS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # Lee la hoja principal. Si tienes varias pestañas, puedes usar ttl=600 para cache
        return conn.read(spreadsheet=URL_HOJA)
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

# --- ENCABEZADO ---
col_tit, col_user_box = st.columns([8.5, 1.5])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_user_box:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    if st.button("Salir"): st.session_state['logueado'] = False; st.rerun()

# CARGA DE DATOS ÚNICA
df_all = cargar_datos()

# PESTAÑAS
tab1, tab2, tab3 = st.tabs(["👥 CARTERA TOTAL", "🔄 RENOVACIONES PRÓXIMAS", "📊 ESTADÍSTICAS"])

if df_all.empty:
    st.warning("⚠️ No se encontraron datos en la hoja de Google Sheets.")
else:
    # ---------------- TAB 1: CARTERA ----------------
    with tab1:
        st.markdown('<a href="'+URL_HOJA+'" target="_blank" class="reg-btn">📝 EDITAR DATOS EN GOOGLE SHEETS</a>', unsafe_allow_html=True)
        busqueda = st.text_input("🔍 Buscar por Cliente o Documento")
        df_show = df_all.copy()
        if busqueda:
            df_show = df_show[df_show.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    # ---------------- TAB 2: RENOVACIONES ----------------
    with tab2:
        # Asumiendo que tu Excel tiene una columna 'vigencia_hasta'
        if 'vigencia_hasta' in df_all.columns:
            df_all['vigencia_hasta'] = pd.to_datetime(df_all['vigencia_hasta']).dt.date
            hoy = date.today()
            proximos = st.slider("Ver vencimientos en los próximos (días):", 15, 180, 60)
            df_renov = df_all[(df_all['vigencia_hasta'] >= hoy) & (df_all['vigencia_hasta'] <= hoy + timedelta(days=proximos))]
            st.dataframe(df_renov.sort_values('vigencia_hasta'), use_container_width=True)
        else:
            st.info("Columna 'vigencia_hasta' no encontrada para calcular renovaciones.")

    # ---------------- TAB 3: ESTADÍSTICAS ----------------
    with tab3:
        if 'premio_USD' in df_all.columns:
            total_usd = df_all['premio_USD'].sum()
            st.metric("Cartera Total (USD)", f"U$S {total_usd:,.0f}")
            if 'aseguradora' in df_all.columns:
                fig = px.pie(df_all, names='aseguradora', values='premio_USD', title="Distribución por Aseguradora")
                st.plotly_chart(fig, use_container_width=True)
