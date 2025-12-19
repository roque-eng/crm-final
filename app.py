import streamlit as st
import pandas as pd
import psycopg2
import time
from datetime import date

# 1. Configuración de página
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS PARA LOGO Y TÍTULO ---
st.markdown("""
    <style>
    /* Achicar y centrar el logo */
    [data-testid="stImage"] {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 140px !important;
    }
    /* Ajustar el título principal centrado y arriba */
    .main-title {
        font-size: 32px !important;
        font-weight: bold;
        text-align: center;
        margin-top: -30px;
        margin-bottom: 10px;
        color: #31333F;
    }
    /* Eliminar espacio superior excesivo */
    .block-container {
        padding-top: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428",
    "AB": "ABentancor2025",
    "GR": "GRobaina2025",
    "ER": "ERobaina.2025",
    "EH": "EHugo2025",
    "GS": "GSanchez2025",
    "JM": "JMokosce2025",
    "PG": "PGagliardi2025",
    "MDF": "MDeFreitas2025"
}

if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False
if 'usuario_actual' not in st.session_state:
    st.session_state['usuario_actual'] = ""

# --- PANTALLA DE LOGIN ---
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>☁️ CRM Grupo EDF</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            passwd = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            if submit:
                if user in USUARIOS and USUARIOS[user] == passwd:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = user
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ ENCABEZADO (Logo y Título)
# ==========================================

try:
    st.image("logo.png") 
except:
    st.markdown("<h2 style='text-align: center;'>🛡️</h2>", unsafe_allow_html=True)

st.markdown('<p class="main-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)

# Usuario y Salir (Corregido el error de 'size')
col_e, col_u = st.columns([8.5, 1.5])
with col_u:
    c_t, c_b = st.columns([1.5, 1])
    c_t.write(f"👤 **{st.session_state['usuario_actual']}**")
    if c_b.button("Salir"):
        st.session_state['logueado'] = False
        st.rerun()

URL_GOOGLE_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" 

def leer_datos(query):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS VIGENTES", "🔔 VENCIMIENTOS"])

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    # 1 y 3. Botón directo sin cartel informativo y sin expander
    st.link_button("➕ REGISTRAR NUEVO CLIENTE (Abrir Formulario)", URL_GOOGLE_FORM, type="primary", use_container_width=True)

    st.divider()

    col_h, col_s = st.columns([2, 1])
    col_h.subheader("🗂️ Cartera de Clientes")
    busqueda = col_s.text_input("🔍 Buscar...", placeholder="Nombre o CI")

    sql_cli = "SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes ORDER BY id DESC"
    if busqueda:
        sql_cli = f"SELECT * FROM clientes WHERE nombre_completo ILIKE '%%{busqueda}%%' OR documento_identidad ILIKE '%%{busqueda}%%' ORDER BY id DESC"
    
    st.dataframe(leer_datos(sql_cli), use_container_width=True, hide_index=True)
    if st.button("🔄 Actualizar Tabla"):
        st.rerun()

# ---------------- PESTAÑA 2: PÓLIZAS ----------------
with tab2:
    st.subheader("📂 Pólizas Vigentes")
    sql_pol = """
        SELECT c.nombre_completo as "Cliente", s.aseguradora, s.ramo,
               TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vencimiento",
               s."premio_UYU", s."premio_USD", s.archivo_url as "link_doc"
        FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.id DESC
    """
    df_p = leer_datos(sql_pol)
    st.dataframe(df_p, use_container_width=True, hide_index=True,
                 column_config={"link_doc": st.column_config.LinkColumn("Documento", display_text="📄 Ver Póliza")})

# ---------------- PESTAÑA 3: VENCIMIENTOS ----------------
with tab3:
    st.subheader("🔔 Monitor de Vencimientos")
    dias = st.slider("Días próximos:", 15, 180, 30, 15)
    sql_v = f"""
        SELECT c.nombre_completo as "Cliente", c.celular, s.aseguradora, s.ramo,
               TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vence"
        FROM seguros s JOIN clientes c ON s.cliente_id = c.id 
        WHERE s.vigencia_hasta BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '{dias} days')
        ORDER BY s.vigencia_hasta ASC
    """
    st.dataframe(leer_datos(sql_v), use_container_width=True, hide_index=True)