import streamlit as st
import pandas as pd
import psycopg2
import os
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
    "PG": "PGagliardi2025"
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
# Aquí iría el link al Form de Pólizas si existiera uno separado, o el mismo de clientes
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

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS VIGENTES", "🔔 VENCIMIENTOS"])

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    st.info("💡 Para ingresar un nuevo cliente, utilice el formulario oficial. Los datos se sincronizarán automáticamente.")
    
    with st.expander("➕ ALTA DE NUEVO CLIENTE (Abrir Formulario)", expanded=True):
        st.write("Por seguridad y para evitar errores de conexión, el formulario se abrirá en una ventana nueva.")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.link_button("🚀 Abrir Formulario de Alta de Cliente", URL_GOOGLE_FORM, type="primary", use_container_width=True)

    st.divider()

    col_header, col_search = st.columns([2, 1])
    with col_header:
        st.subheader("🗂️ Cartera de Clientes")
    with col_search:
        busqueda = st.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI")

    sql_cli = "SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes ORDER BY id DESC"
    
    if busqueda:
        sql_cli = f"SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes WHERE nombre_completo ILIKE '%%{busqueda}%%' OR documento_identidad ILIKE '%%{busqueda}%%'"
    
    st.dataframe(leer_datos(sql_cli), use_container_width=True, hide_index=True)

    if st.button("🔄 Actualizar Tabla Clientes"):
        st.rerun()

# ---------------- PESTAÑA 2: PÓLIZAS (SOLO VISUALIZACIÓN) ----------------
with tab2:
    # Header y Botón de refresco alineados
    col_pol_header, col_pol_btn = st.columns([4, 1])
    
    with col_pol_header:
        st.subheader("📂 Pólizas Vigentes")
        st.caption("Los datos se cargan automáticamente desde el Formulario Oficial.")
    
    with col_pol_btn:
        st.write("") # Espaciador para alinear verticalmente
        if st.button("🔄 Refrescar Pólizas"):
            st.rerun()

    # QUERY DE VISUALIZACIÓN
    # Eliminado 'numero_poliza' de la vista si ya no existe en la BD
    sql_view_polizas = """
        SELECT 
            c.nombre_completo as "Cliente", 
            s.aseguradora, 
            s.ramo,
            TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vencimiento",
            s."premio_UYU" as "Premio $",
            s."premio_USD" as "Premio U$S",
            s.corredor,
            s.agente,
            CASE WHEN s.archivo_url IS NOT NULL THEN '✅ SÍ' ELSE '❌ NO' END as "PDF" 
        FROM seguros s 
        JOIN clientes c ON s.cliente_id = c.id 
        ORDER BY s.id DESC
    """
    
    df_polizas = leer_datos(sql_view_polizas)
    
    if df_polizas.empty:
        st.info("Aún no hay pólizas cargadas en el sistema.")
    else:
        st.dataframe(df_polizas, use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 3: VENCIMIENTOS ----------------
with tab3:
    st.header("🔔 Vencimientos (Próximos 30 días)")
    
    sql_venc = """SELECT c.nombre_completo, c.celular, s.aseguradora, s.vigencia_hasta 
                  FROM seguros s JOIN clientes c ON s.cliente_id = c.id 
                  WHERE s.vigencia_hasta BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '30 days') 
                  ORDER BY s.vigencia_hasta ASC"""
    df_venc = leer_datos(sql_venc)
    
    if not df_venc.empty:
        st.warning(f"⚠️ ¡Atención! {len(df_venc)} Pólizas vencen pronto.")
        st.dataframe(df_venc, use_container_width=True)
    else:
        st.success("✅ No hay vencimientos próximos. Todo tranquilo.")