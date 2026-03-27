import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# 🔗 CONFIGURACIÓN DE LA FUENTE DE DATOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit"

st.set_page_config(page_title="CRM - Grupo EDF", layout="wide", page_icon="🛡️")

TC_USD = 40.5 

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .left-title { font-size: 30px !important; font-weight: bold; text-align: left; color: #31333F; margin-top: -15px; }
    .user-info { text-align: right; font-weight: bold; font-size: 14px; color: #555; }
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
# ⚙️ CARGA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600) # Se actualiza cada 10 min o al dar F5
def cargar_datos():
    df = conn.read(spreadsheet=URL_HOJA, worksheet="Respuestas de formulario 2")
    # Limpieza de fechas
    df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], errors='coerce').dt.date
    # Limpieza de premios (quitar NaN y convertir a número)
    df['Premio USD [sin iva]'] = pd.to_numeric(df['Premio USD [sin iva]'], errors='coerce').fillna(0)
    df['Premio UYU [con iva]'] = pd.to_numeric(df['Premio UYU [con iva]'], errors='coerce').fillna(0)
    # Crear columna unificada en USD para estadísticas
    df['Total_USD'] = df['Premio USD [sin iva]'] + (df['Premio UYU [con iva]'] / TC_USD)
    return df

# --- ENCABEZADO ---
col_tit, col_user_box = st.columns([8, 2])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_user_box:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión"): st.session_state['logueado'] = False; st.rerun()

df = cargar_datos()

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["👥 CARTERA TOTAL", "🔄 VENCIMIENTOS", "📊 ANÁLISIS"])

with tab1:
    col_a, col_b = st.columns([3, 1])
    busqueda = col_a.text_input("🔍 Buscar por Asegurado, Documento o Ramo")
    col_b.markdown(f"<br><a href='{URL_HOJA}' target='_blank'>📝 Editar en Google Sheets</a>", unsafe_allow_html=True)
    
    df_filtered = df.copy()
    if busqueda:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]
    
    # Configuración de columnas para que el link de póliza sea clickeable
    st.data_editor(
        df_filtered,
        column_config={
            "adjunto [póliza]": st.column_config.LinkColumn("Póliza", display_text="Ver Archivo"),
            "Fin de Vigencia": st.column_config.DateColumn("Vence"),
        },
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.subheader("⏳ Próximas Renovaciones")
    dias = st.slider("Ver vencimientos en los próximos (días):", 15, 180, 60)
    hoy = date.today()
    futuro = hoy + timedelta(days=dias)
    
    df_vence = df[(df['Fin de Vigencia'] >= hoy) & (df['Fin de Vigencia'] <= futuro)].copy()
    df_vence = df_vence.sort_values('Fin de Vigencia')
    
    if not df_vence.empty:
        st.warning(f"Hay {len(df_vence)} pólizas venciendo en los próximos {dias} días.")
        st.table(df_vence[['Asegurado (Nombre/Razón Social)', 'Aseguradora', 'Ramo', 'Fin de Vigencia', 'Ejecutivo']])
    else:
        st.success("No hay vencimientos próximos en el rango seleccionado.")

with tab3:
    st.subheader("📈 Resumen de Cartera")
    c1, c2, c3 = st.columns(3)
    c1.metric("Pólizas Activas", len(df))
    c2.metric("Total Cartera (est. USD)", f"U$S {df['Total_USD'].sum():,.0f}")
    c3.metric("Tipo de Cambio", f"${TC_USD}")
    
    fig1 = px.pie(df, names='Aseguradora', values='Total_USD', title="Cartera por Aseguradora (USD)")
    st.plotly_chart(fig1, use_container_width=True)
    
    fig2 = px.bar(df, x='Ramo', y='Total_USD', color='Aseguradora', title="Distribución por Ramo y Compañía")
    st.plotly_chart(fig2, use_container_width=True)
