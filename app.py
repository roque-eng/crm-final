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

# --- VARIABLE GLOBAL DE TIPO DE CAMBIO ---
TC_USD = 40.5 

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; }
    .left-title { font-size: 32px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 0px; }
    .user-info { text-align: right; font-weight: bold; font-size: 14px; color: #666; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; }
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
# ⚙️ CARGA Y LIMPIEZA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        
        # Convertir premios a números para poder sumarlos
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        
        # Cálculo de Total en USD unificado
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        
        if 'Fin de Vigencia' in df.columns:
            df['Fin_V_dt'] = pd.to_datetime(df['Fin de Vigencia'], errors='coerce').dt.date
        return df
    except Exception as e:
        st.error(f"Error: {e}"); return pd.DataFrame()

df_raw = cargar_datos()

# --- ENCABEZADO ---
col_tit, col_user_box = st.columns([8, 2])
with col_tit: st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)
with col_user_box:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión", use_container_width=True): st.session_state['logueado'] = False; st.rerun()

st.divider()

# ==========================================
# 🎯 FILTROS
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

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]

# ==========================================
# 📑 TABS Y CONTENIDO
# ==========================================
tab1, tab2, tab3 = st.tabs(["👥 CARTERA TOTAL", "🔄 VENCIMIENTOS", "📊 ANÁLISIS"])

with tab1:
    busqueda = st.text_input("🔍 Buscar por Nombre o Documento...")
    df_tab1 = df_f.copy()
    if busqueda:
        mask = df_tab1.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_tab1 = df_tab1[mask]
    
    # Mostrar tabla
    ocultas = ['Ejecutivo', 'Corredor', 'Agente', 'Aseguradora', 'Fin_V_dt', 'Marca temporal', 'Dirección de correo electrónico', 'Premio_Total_USD']
    cols_visibles = [c for c in df_tab1.columns if c not in ocultas]
    
    st.dataframe(df_tab1[cols_visibles], use_container_width=True, hide_index=True,
        column_config={
            "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="Ver Póliza"),
            "Fin de Vigencia": st.column_config.DateColumn("Vence")
        })
    
    # --- CONTADORES ABAJO DE LA TABLA ---
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Cantidad de Pólizas", len(df_tab1))
    total_usd = df_tab1['Premio_Total_USD'].sum()
    m2.metric("Premio Total (USD)", f"U$S {total_usd:,.2f}")
    promedio = total_usd / len(df_tab1) if len(df_tab1) > 0 else 0
    m3.metric("Premio Promedio (USD)", f"U$S {promedio:,.2f}")

with tab2:
    hoy = date.today()
    proximos = hoy + timedelta(days=60)
    df_v = df_f[(df_f['Fin_V_dt'] >= hoy) & (df_f['Fin_V_dt'] <= proximos)].sort_values('Fin_V_dt')
    st.dataframe(df_v, use_container_width=True, hide_index=True,
        column_config={"Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="Ver Póliza")})

with tab3:
    st.subheader("📊 Análisis del Segmento")
    fig = px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Compañía (USD)")
    st.plotly_chart(fig, use_container_width=True)
