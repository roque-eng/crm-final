import streamlit as st
import pd as pd
import psycopg2
import time
from datetime import date

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS PERSONALIZADOS (Visual corregida y aire superior) ---
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
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    c_text, c_btn = st.columns([2, 1])
    c_text.write(f"👤 **{st.session_state['usuario_actual']}**")
    if c_btn.button("Salir"):
        st.session_state['logueado'] = False
        st.rerun()

# --- URL DEL FORMULARIO OFICIAL ---
URL_GOOGLE_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" 

# --- FUNCIONES DE BASE DE DATOS ---
def get_db_connection():
    try:
        return psycopg2.connect(st.secrets["DB_URL"])
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {e}")
        return None

def leer_datos(query):
    try:
        conn = get_db_connection()
        if conn:
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error leyendo datos: {e}")
        return pd.DataFrame()

# --- FUNCIÓN WHATSAPP (Formato Uruguay) ---
def crear_link_wa(celular):
    if not celular: return None
    c = str(celular).replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    if c.startswith("09"): c = "598" + c[1:]