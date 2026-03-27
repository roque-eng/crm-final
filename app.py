import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# 🔗 CONFIGURACIÓN DE LA FUENTE DE DATOS
# ==========================================
# URL corregida y verificada
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# --- VARIABLE GLOBAL DE TIPO DE CAMBIO ---
TC_USD = 40.5 

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .left-title { font-size: 30px !important; font-weight: bold; text-align: left; color: #31333F; margin-top: -15px; }
    .user-info { text-align: right; font-weight: bold; font-size: 14px; color: #555; margin-bottom: 5px; }
    .reg-btn { 
        text-decoration: none !important; 
        background-color: #333 !important; 
        color: #FFFFFF !important; 
        padding: 8px 12px; 
        border-radius: 5px; 
        font-weight: bold; 
        font-size: 12px !important; 
        display: inline-block; 
        margin-top: 5px; 
        border: 1px solid #000; 
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
    "AC": "ACazarian2025", "MF": "MFlores2025"
}

if 'logueado' not in st.session_state: 
    st.session_state['logueado'] = False

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
# ⚙️ CONEXIÓN A GOOGLE SHEETS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def cargar_datos():
    try:
        # Leemos la hoja (por defecto la primera pestaña activa)
        df = conn.read(spreadsheet=URL_HOJA)
        # Limpieza básica de nombres de columnas (quitar espacios locos)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# --- ENCABEZADO APP LOGUEADA ---
col_tit, col_user_box = st.columns([8, 2])
with col_tit: 
    st.markdown('<p class="left-title">Gestión de Cartera - EDF SEGUROS</p>', unsafe_allow_html=True)

with col_user_box:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

# Cargar los datos del Excel
df_raw = cargar_datos()

if df_raw.empty:
    st.warning("⚠️ No se detectaron datos. Verifica que el Google Sheets sea público.")
else:
    # PESTAÑAS
    tab1, tab2, tab3 = st.tabs(["👥 CARTERA TOTAL", "🔄 VENCIMIENTOS", "📊 ANÁLISIS"])

    with tab1:
        col_bus, col_link = st.columns([3, 1])
        busqueda = col_bus.text_input("🔍 Buscar por Asegurado, Ramo o Compañía...")
        col_link.markdown(f"<br><a href='{URL_HOJA}' target='_blank' class='reg-btn'>📝 EDITAR EXCEL</a>", unsafe_allow_html=True)
        
        df_display = df_raw.copy()
        if busqueda:
            mask = df_display.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
            df_display = df_display[mask]
        
        st.dataframe(
            df_display, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "adjunto [póliza]": st.column_config.LinkColumn("Póliza", display_text="Ver Archivo"),
                "Fin de Vigencia": st.column_config.DateColumn("Vencimiento")
            }
        )

    with tab2:
        st.subheader("📅 Próximas Renovaciones")
        if 'Fin de Vigencia' in df_raw.columns:
            # Convertir a fecha real para filtrar
            df_raw['Fin_Vence_dt'] = pd.to_datetime(df_raw['Fin de Vigencia'], errors='coerce').dt.date
            hoy = date.today()
            dias_filtro = st.select_slider("Días a futuro:", options=[15, 30, 60, 90, 180], value=60)
            
            df_vencimientos = df_raw[
                (df_raw['Fin_Vence_dt'] >= hoy) & 
                (df_raw['Fin_Vence_dt'] <= hoy + timedelta(days=dias_filtro))
            ].sort_values('Fin_Vence_dt')
            
            if not df_vencimientos.empty:
                st.info(f"Se encontraron {len(df_vencimientos)} pólizas por vencer.")
                st.dataframe(df_vencimientos.drop(columns=['Fin_Vence_dt']), use_container_width=True, hide_index=True)
            else:
                st.success("¡Todo al día! No hay vencimientos próximos.")
        else:
            st.error("No se encontró la columna 'Fin de Vigencia'.")

    with tab3:
        st.subheader("📊 Resumen Ejecutivo")
        # Cálculos rápidos
        total_polizas = len(df_raw)
        
        # Intentar sumar premios si existen las columnas
        m1, m2 = st.columns(2)
        m1.metric("Pólizas en Cartera", total_polizas)
        
        if 'Aseguradora' in df_raw.columns:
            fig = px.pie(df_raw, names='Aseguradora', title="Distribución por Compañía")
            st.plotly_chart(fig, use_container_width=True)
