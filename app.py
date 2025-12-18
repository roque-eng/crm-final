import streamlit as st
import pandas as pd
import psycopg2
import time
from datetime import date

# 1. Configuración de página
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

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

def verificar_login(usuario, contrasena):
    if usuario in USUARIOS and USUARIOS[usuario] == contrasena:
        return True
    return False

# Inicializar estado
if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False
if 'usuario_actual' not in st.session_state:
    st.session_state['usuario_actual'] = ""

# --- PANTALLA DE LOGIN ---
if not st.session_state['logueado']:
    col_login_logo, col_login_text = st.columns([1, 4])
    with col_login_text:
        st.markdown("<h1 style='text-align: left;'>☁️ CRM Grupo EDF</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.info("Ingrese sus credenciales para continuar")
        with st.form("login_form"):
            user = st.text_input("Usuario")
            passwd = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit:
                if verificar_login(user, passwd):
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = user
                    st.success("✅ Acceso correcto")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

# ==========================================
# ⚙️ SISTEMA INTERNO
# ==========================================

# --- BARRA SUPERIOR ---
col_logo, col_titulo, col_user = st.columns([2, 6, 2])

with col_logo:
    try:
        st.image("logo.png", width=140) 
    except:
        st.write("🛡️")

with col_titulo:
    st.markdown("""
        <h1 style='
            text-align: center; 
            margin-top: 35px; 
            margin-bottom: 0px; 
            padding-bottom: 0px;
            font-size: 3rem;'>
            Gestión de Cartera - Grupo EDF
        </h1>
    """, unsafe_allow_html=True)

with col_user:
    st.markdown("<div style='margin-top: 35px;'></div>", unsafe_allow_html=True)
    c_user_text, c_user_btn = st.columns([2, 1])
    with c_user_text:
        st.write(f"👤 **{st.session_state['usuario_actual']}**")
    with c_user_btn:
        if st.button("Salir"):
            st.session_state['logueado'] = False
            st.rerun()

# --- VARIABLE PARA EL FORMULARIO DE GOOGLE ---
URL_GOOGLE_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" 

# --- FUNCIONES DE BASE DE DATOS ---
def get_db_connection():
    try:
        url_conexion = st.secrets["DB_URL"]
        conn = psycopg2.connect(url_conexion)
        return conn
    except Exception as e:
        st.error(f"⚠️ Error de conexión. Detalle: {e}")
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

# --- FUNCION EXTRA: Limpiar celular para WhatsApp ---
def crear_link_wa(celular):
    if not celular:
        return None
    # Convertimos a string y quitamos espacios, guiones, simbolos raros
    c = str(celular).replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    
    # Lógica básica para Uruguay
    if c.startswith("09"):
        c = "598" + c[1:] 
    elif c.startswith("9"):
        c = "598" + c     
    
    # Retorna el link oficial de la API de WhatsApp
    return f"https://wa.me/{c}"

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS VIG