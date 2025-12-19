Sí, aquí tienes el código total, de punta a punta, sin recortes y listo para funcionar con tu nuevo archivo requirements.txt.

Este bloque incluye el sistema de Login, los buscadores en ambas pestañas, el formato de moneda corregido (separador de miles y sin decimales) y el nuevo tablero de Estadísticas con gráficos de Plotly.

Python

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import time
from datetime import date

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .left-title {
        font-size: 38px !important;
        font-weight: bold;
        text-align: left;
        margin-top: 10px;
        margin-bottom: 25px;
        color: #31333F;
    }
    .block-container {
        padding-top: 2.5rem !important;
    }
    /* Estilo para métricas destacadas */
    [data-testid="stMetricValue"] {
        font-size: 40px;
        color: #28a745;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS (Login)
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025",
    "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025",
    "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025"
}

if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False
if 'usuario_actual' not in st.session_state:
    st.session_state['usuario_actual'] = ""

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
                else:
                    st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ ENCABEZADO Y FUNCIONES BASE
# ==========================================
col_tit, col_user_status = st.columns([7, 3])
with col_tit:
    st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)

with col_user_status:
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    c_text, c_btn = st.columns([2, 1])
    c_text.write(f"👤 **{st.session_state['usuario_actual']}**")
    if c_btn.button("Salir"):
        st.session_state['logueado'] = False
        st.rerun()

# Tipo de Cambio (TC) para estadísticas - Ajustable según mercado
TC_USD = 40.5 

def leer_datos(query):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return pd.DataFrame()

def crear_link_wa(celular):
    if not celular: return None
    c = str(celular).replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    if c.startswith("09"): c = "598" + c[1:] 
    elif c.startswith("9"): c = "598" + c     
    return f"https://wa.me/{c}"

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS VIGENTES", "🔔 VENCIMIENTOS", "📊 ESTADÍSTICAS"])

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    st.link_button("➕ REGISTRAR NUEVO CLIENTE (Abrir Formulario)", "https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform", type="primary", use_container_width=True)
    st.divider()
    col_h, col_s = st.columns([2, 1])
    col_h.subheader("🗂️ Cartera de Clientes")
    busqueda_cli = col_s.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI", key="search_cli")
    
    sql_cli = "SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes"
    if busqueda_cli:
        sql_cli += f" WHERE nombre_completo ILIKE '%%{busqueda_cli}%%' OR documento_identidad ILIKE '%%{busqueda_cli}%%'"
    sql_cli += " ORDER BY id DESC"
    
    st.dataframe(leer_datos(sql_cli), use_container_width=True, hide_index=True)
    if st.button("🔄 Actualizar Tabla Clientes"): st.rerun()

# ---------------- PESTAÑA 2: PÓLIZAS (Formato de moneda corregido) ----------------
with tab2:
    col_pol_h, col_pol_s = st.columns([2, 1])
    col_pol_h.subheader("📂 Pólizas Vigentes")
    busqueda_pol = col_pol_s.text_input("🔍 Buscar póliza...", placeholder="Nombre o CI", key="search_pol")
    
    sql_pol = """
        SELECT c.nombre_completo as "Cliente", c.documento_identidad as "CI", s.aseguradora, s.ramo,
               TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vencimiento",
               s.premio_uyu, s.premio_usd, s.agente, s.archivo_url as "link_doc"
        FROM seguros s JOIN clientes c ON s.cliente_id = c.id
    """
    
    if busqueda_pol:
        sql_pol += f" WHERE c.nombre_completo ILIKE '%%{busqueda_pol}%%' OR c.documento_identidad ILIKE '%%{busqueda_pol}%%'"
    sql_pol += " ORDER BY s.id DESC"

    df_p = leer_datos(sql_pol)
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True, hide_index=True,
            column_config={
                "link_doc": st.column_config.LinkColumn("Documento", display_text="📄 Ver Póliza"),
                "premio_uyu": st.column_config.NumberColumn("Premio $", format="$ %,.0f"),
                "premio_usd": st.column_config.NumberColumn("Premio U$S", format="U$S %,.0f")
            })
    if st.button("🔄 Refrescar Pólizas"): st.rerun()

# ---------------- PESTAÑA 3: VENCIMIENTOS ----------------
with tab3:
    st.header("🔔 Monitor de Vencimientos")
    dias_v = st.slider("📅 Días próximos:", 15, 180, 30, 15, key="slider_venc")
    sql_v = f"SELECT c.nombre_completo as 'Cliente', c.celular, s.aseguradora, s.ramo, TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as 'Vence' FROM seguros s JOIN clientes c ON s.cliente_id = c.id WHERE s.vigencia_hasta BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '{dias_v} days') ORDER BY s.vigencia_hasta ASC"
    df_v = leer_datos(sql_v)
    if not df_v.empty:
        df_v['WhatsApp'] = df_v['celular'].apply(crear_link_wa)
        st.dataframe(df_v, use_container_width=True, hide_index=True, column_config={"WhatsApp": st.column_config.LinkColumn("Contacto", display_text="📲")})

# ---------------- PESTAÑA 4: ESTADÍSTICAS (Dashboards) ----------------
with tab4:
    st.subheader(f"📊 Análisis Financiero de Cartera (TC Estimado: ${TC_USD})")
    
    # Obtenemos los datos técnicos de seguros
    df_stats = leer_datos("SELECT aseguradora, ramo, premio_uyu, premio_usd FROM seguros")
    
    if not df_stats.empty:
        # Unificamos a USD: Valor directo USD + (UYU / Tipo de Cambio)
        df_stats['total_usd'] = df_stats['premio_usd'].fillna(0) + (df_stats['premio_uyu'].fillna(0) / TC_USD)
        
        # Métrica de Cartera Total
        st.metric("Cartera Total (USD)", f"U$S {df_stats['total_usd'].sum():,.0f}")
        
        st.divider()
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Gráfico de Ramos
            df_ramo = df_stats.groupby('ramo')['total_usd'].sum().reset_index()
            fig_r = px.bar(df_ramo, x='ramo', y='total_usd', title="Producción por Ramo (USD)", 
                           labels={'total_usd':'Premios USD', 'ramo':'Ramo'},
                           color='ramo', color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_r, use_container_width=True)
            
        with col_g2:
            # Gráfico de Aseguradoras
            df_aseg = df_stats.groupby('aseguradora')['total_usd'].sum().reset_index()
            fig_a = px.bar(df_aseg, x='aseguradora', y='total_usd', title="Producción por Compañía (USD)",
                           labels={'total_usd':'Premios USD', 'aseguradora':'Compañía'},
                           color='aseguradora', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_a, use_container_width=True)
    else:
        st.info("No hay datos cargados para generar estadísticas.")