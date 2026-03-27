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

# --- ESTILOS CSS ---
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
# ⚙️ CONEXIÓN Y CARGA
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        # Convertir fecha a datetime
        if 'Fin de Vigencia' in df.columns:
            df['Fin_V_dt'] = pd.to_datetime(df['Fin de Vigencia'], errors='coerce').dt.date
        return df
    except Exception as e:
        st.error(f"Error: {e}"); return pd.DataFrame()

df_raw = cargar_datos()

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("🎯 Filtros Globales")
lista_ejecutivos = ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["Todos"]
lista_corredores = ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()) if 'Corredor' in df_raw.columns else ["Todos"]
lista_agentes = ["Todos"] + sorted(df_raw['Agente'].dropna().unique().tolist()) if 'Agente' in df_raw.columns else ["Todos"]
lista_aseguradoras = ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()) if 'Aseguradora' in df_raw.columns else ["Todos"]

f_ejecutivo = st.sidebar.selectbox("Ejecutivo", lista_ejecutivos)
f_corredor = st.sidebar.selectbox("Corredor", lista_corredores)
f_agente = st.sidebar.selectbox("Agente", lista_agentes)
f_aseguradora = st.sidebar.selectbox("Aseguradora", lista_aseguradoras)

# Aplicar Filtros
df_filtrado = df_raw.copy()
if f_ejecutivo != "Todos": df_filtrado = df_filtrado[df_filtrado['Ejecutivo'] == f_ejecutivo]
if f_corredor != "Todos": df_filtrado = df_filtrado[df_filtrado['Corredor'] == f_corredor]
if f_agente != "Todos": df_filtrado = df_filtrado[df_filtrado['Agente'] == f_agente]
if f_aseguradora != "Todos": df_filtrado = df_filtrado[df_filtrado['Aseguradora'] == f_aseguradora]

# --- ENCABEZADO ---
col_tit, col_user_box = st.columns([8, 2])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - EDF SEGUROS</p>', unsafe_allow_html=True)
with col_user_box:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión"): st.session_state['logueado'] = False; st.rerun()

if not df_raw.empty:
    tab1, tab2, tab3 = st.tabs(["👥 CARTERA TOTAL", "🔄 VENCIMIENTOS", "📊 ANÁLISIS"])

    with tab1:
        busqueda = st.text_input("🔍 Buscar por Nombre o Documento...")
        df_tab1 = df_filtrado.copy()
        if busqueda:
            mask = df_tab1.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
            df_tab1 = df_tab1[mask]
        
        # Columnas a ocultar para que la tabla sea más corta (ya que están en los filtros)
        cols_a_mostrar = [c for c in df_tab1.columns if c not in ['Ejecutivo', 'Corredor', 'Agente', 'Aseguradora', 'Fin_V_dt', 'Marca temporal']]
        
        st.dataframe(df_tab1[cols_a_mostrar], use_container_width=True, hide_index=True,
            column_config={
                "adjunto [póliza]": st.column_config.LinkColumn("Póliza", display_text="📂"),
                "Fin de Vigencia": st.column_config.DateColumn("Vencimiento")
            })

    with tab2:
        st.subheader("📅 Próximas Renovaciones (60 días)")
        hoy = date.today()
        proximos = hoy + timedelta(days=60)
        df_v = df_filtrado[(df_filtrado['Fin_V_dt'] >= hoy) & (df_filtrado['Fin_V_dt'] <= proximos)].sort_values('Fin_V_dt')
        
        cols_vence = [c for c in df_v.columns if c not in ['Ejecutivo', 'Corredor', 'Agente', 'Marca temporal', 'Fin_V_dt']]
        st.dataframe(df_v[cols_vence], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📊 Resumen del Segmento Seleccionado")
        c1, c2 = st.columns(2)
        c1.metric("Pólizas Filtradas", len(df_filtrado))
        fig = px.pie(df_filtrado, names='Ramo', title="Distribución por Ramo")
        st.plotly_chart(fig, use_container_width=True)
