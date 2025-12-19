import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import date

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .left-title { font-size: 38px !important; font-weight: bold; text-align: left; margin-top: 10px; margin-bottom: 25px; color: #31333F; }
    .block-container { padding-top: 2.5rem !important; }
    [data-testid="stMetricValue"] { font-size: 40px; color: #28a745; }
    
    /* Estilo del botón gris oscuro con + azul */
    div.stButton > button {
        background-color: #333333 !important;
        color: white !important;
        border-radius: 5px;
        border: none;
    }
    .plus-sign { color: #007bff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS (Login)
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>☁️ CRM Grupo EDF</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            passwd = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if user in USUARIOS and USUARIOS[user] == passwd:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = user
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ ENCABEZADO Y FUNCIONES
# ==========================================
col_tit, col_user = st.columns([7, 3])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_user:
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    c_t, c_b = st.columns([2, 1])
    c_t.write(f"👤 **{st.session_state['usuario_actual']}**")
    if c_b.button("Salir"): st.session_state['logueado'] = False; st.rerun()

TC_USD = 40.5 

def leer_datos(query):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e: return pd.DataFrame()

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS VIGENTES", "🔔 VENCIMIENTOS", "📊 ESTADÍSTICAS"])

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    # Fila superior: Botón a la izquierda, buscador a la derecha
    col_btn, col_spacer, col_search = st.columns([1, 1, 1])
    with col_btn:
        st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" target="_blank" style="text-decoration:none;"><button style="background-color:#333333; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer;"><span style="color:#007bff; font-weight:bold;">+</span> REGISTRAR NUEVO CLIENTE</button></a>', unsafe_allow_html=True)
    
    with col_search:
        busqueda_cli = st.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI", label_visibility="collapsed", key="search_cli_tab1")

    st.divider()
    sql_cli = "SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes"
    if busqueda_cli:
        sql_cli += f" WHERE nombre_completo ILIKE '%%{busqueda_cli}%%' OR documento_identidad ILIKE '%%{busqueda_cli}%%'"
    sql_cli += " ORDER BY id DESC"
    
    st.dataframe(leer_datos(sql_cli), use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 2: PÓLIZAS ----------------
with tab2:
    col_h, col_s = st.columns([2, 1])
    col_h.subheader("📂 Pólizas Vigentes")
    busqueda_pol = col_s.text_input("🔍 Buscar póliza...", placeholder="Nombre o CI", key="search_p_tab2")
    
    sql_pol = """
        SELECT c.nombre_completo as "Cliente", c.documento_identidad as "CI", s.aseguradora, s.ramo,
               TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vencimiento",
               s."premio_UYU", s."premio_USD", s.agente, s.archivo_url as "link_doc"
        FROM seguros s JOIN clientes c ON s.cliente_id = c.id
    """
    if busqueda_pol:
        sql_pol += f" WHERE c.nombre_completo ILIKE '%%{busqueda_pol}%%' OR c.documento_identidad ILIKE '%%{busqueda_pol}%%'"
    sql_pol += " ORDER BY s.id DESC"

    df_p = leer_datos(sql_pol)
    if not df_p.empty:
        # Formato de miles forzado con separador de miles y sin decimales
        st.dataframe(df_p, use_container_width=True, hide_index=True,
            column_config={
                "link_doc": st.column_config.LinkColumn("Documento", display_text="📄 Ver Póliza"),
                "premio_UYU": st.column_config.NumberColumn("Premio $", format="$ %,.0f"),
                "premio_USD": st.column_config.NumberColumn("Premio U$S", format="U$S %,.0f")
            })
    if st.button("🔄 Refrescar Pólizas"): st.rerun()

# ---------------- PESTAÑA 3: VENCIMIENTOS ----------------
with tab3:
    st.header("🔔 Monitor de Vencimientos")
    dias_v = st.slider("📅 Días próximos:", 15, 180, 30, 15)
    sql_v = f'SELECT c.nombre_completo as "Cliente", c.celular, s.aseguradora, s.ramo, TO_CHAR(s.vigencia_hasta, "DD/MM/YYYY") as "Vence" FROM seguros s JOIN clientes c ON s.cliente_id = c.id WHERE s.vigencia_hasta BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL "{dias_v} days") ORDER BY s.vigencia_hasta ASC'
    st.dataframe(leer_datos(sql_v), use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 4: ESTADÍSTICAS ----------------
with tab4:
    st.subheader(f"📊 Análisis de Cartera (TC Estimado: ${TC_USD})")
    df_stats = leer_datos('SELECT aseguradora, ramo, "premio_UYU", "premio_USD" FROM seguros')
    
    if not df_stats.empty:
        df_stats['total_usd'] = df_stats['premio_USD'].fillna(0) + (df_stats['premio_UYU'].fillna(0) / TC_USD)
        st.metric("Cartera Total Estimada", f"U$S {df_stats['total_usd'].sum():,.0f}")
        
        st.divider()
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            df_ramo = df_stats.groupby('ramo')['total_usd'].sum().reset_index()
            fig_r = px.bar(df_ramo, x='ramo', y='total_usd', title="Primas por Ramo (USD)", labels={'total_usd':'Total USD'}, color='ramo')
            st.plotly_chart(fig_r, use_container_width=True)
            
        with col_g2:
            df_aseg = df_stats.groupby('aseguradora')['total_usd'].sum().reset_index()
            fig_a = px.bar(df_aseg, x='aseguradora', y='total_usd', title="Primas por Aseguradora (USD)", labels={'total_usd':'Total USD'}, color='aseguradora')
            st.plotly_chart(fig_a, use_container_width=True)