import streamlit as st
import pandas as pd
import psycopg2
import time
from datetime import date

# 1. Configuración de página
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    /* Título más grande, alineado a la izquierda y con más aire arriba */
    .left-title {
        font-size: 38px !important;
        font-weight: bold;
        text-align: left;
        margin-top: 10px;
        margin-bottom: 25px;
        color: #31333F;
    }
    /* Ajuste de contenedor principal */
    .block-container {
        padding-top: 2.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
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
# ⚙️ ENCABEZADO (Título a la izquierda y Usuario)
# ==========================================
col_tit, col_user_status = st.columns([7, 3])

with col_tit:
    st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)

with col_user_status:
    # Espaciador para alinear con el título más grande
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    c_text, c_btn = st.columns([2, 1])
    c_text.write(f"👤 **{st.session_state['usuario_actual']}**")
    if c_btn.button("Salir"):
        st.session_state['logueado'] = False
        st.rerun()

# --- URL DEL FORMULARIO ---
URL_GOOGLE_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" 

# --- FUNCIÓN DE LECTURA DE DATOS ---
def leer_datos(query):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return pd.DataFrame()

# --- FUNCIÓN WHATSAPP ---
def crear_link_wa(celular):
    if not celular: return None
    c = str(celular).replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    if c.startswith("09"): c = "598" + c[1:] 
    elif c.startswith("9"): c = "598" + c     
    return f"https://wa.me/{c}"

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS VIGENTES", "🔔 VENCIMIENTOS"])

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    st.link_button("➕ REGISTRAR NUEVO CLIENTE (Abrir Formulario)", URL_GOOGLE_FORM, type="primary", use_container_width=True)
    st.divider()
    col_h, col_s = st.columns([2, 1])
    col_h.subheader("🗂️ Cartera de Clientes")
    busqueda = col_s.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI")
    
    sql_cli = "SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes ORDER BY id DESC"
    if busqueda:
        sql_cli = f"SELECT * FROM clientes WHERE nombre_completo ILIKE '%%{busqueda}%%' OR documento_identidad ILIKE '%%{busqueda}%%' ORDER BY id DESC"
    
    st.dataframe(leer_datos(sql_cli), use_container_width=True, hide_index=True)
    if st.button("🔄 Actualizar Tabla Clientes"): st.rerun()

# ---------------- PESTAÑA 2: PÓLIZAS ----------------
with tab2:
    col_pol_h, col_pol_b = st.columns([4, 1])
    col_pol_h.subheader("📂 Pólizas Vigentes")
    if col_pol_b.button("🔄 Refrescar Pólizas"): st.rerun()
    
    sql_pol = """
        SELECT c.nombre_completo as "Cliente", s.aseguradora, s.ramo,
               TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vencimiento",
               s."premio_UYU", s."premio_USD", s.corredor, s.agente, s.archivo_url as "link_doc"
        FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.id DESC
    """
    df_p = leer_datos(sql_pol)
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True, hide_index=True,
            column_config={
                "link_doc": st.column_config.LinkColumn("Documento", display_text="📄 Ver Póliza"),
                "premio_UYU": st.column_config.NumberColumn