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
        width: 120px !important;
    }
    /* Ajustar el título principal */
    .main-title {
        font-size: 28px !important;
        font-weight: bold;
        text-align: center;
        margin-top: -40px;
        margin-bottom: 20px;
        color: #31333F;
    }
    /* Eliminar espacio superior excesivo */
    .block-container {
        padding-top: 1.5rem !important;
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

def verificar_login(usuario, contrasena):
    if usuario in USUARIOS and USUARIOS[usuario] == contrasena:
        return True
    return False

if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False
if 'usuario_actual' not in st.session_state:
    st.session_state['usuario_actual'] = ""

# --- PANTALLA DE LOGIN ---
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>☁️ CRM Grupo EDF</h1>", unsafe_allow_html=True)
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

# --- ENCABEZADO ESTILIZADO (Logo y Título) ---
try:
    st.image("logo.png") 
except:
    st.markdown("<h2 style='text-align: center;'>🛡️</h2>", unsafe_allow_html=True)

st.markdown('<p class="main-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)

# Información de usuario y botón salir
col_empty, col_user_info = st.columns([8, 2])
with col_user_info:
    c_text, c_btn = st.columns([2, 1])
    c_text.write(f"👤 **{st.session_state['usuario_actual']}**")
    if c_btn.button("Salir", size="small"):
        st.session_state['logueado'] = False
        st.rerun()

# --- VARIABLE PARA EL FORMULARIO DE GOOGLE ---
URL_GOOGLE_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" 

# --- FUNCIONES DE BASE DE DATOS ---
def get_db_connection():
    try:
        url_conexion = st.secrets["DB_URL"]
        return psycopg2.connect(url_conexion)
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
    # Botón directo (Cambio pedido: Sin cartel info y sin expander)
    st.link_button("➕ REGISTRAR NUEVO CLIENTE", URL_GOOGLE_FORM, type="primary", use_container_width=True)

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

# ---------------- PESTAÑA 2: PÓLIZAS ----------------
with tab2:
    col_pol_header, col_pol_btn = st.columns([4, 1])
    with col_pol_header:
        st.subheader("📂 Pólizas Vigentes")
    with col_pol_btn:
        if st.button("🔄 Refrescar Pólizas"):
            st.rerun()

    sql_view_polizas = """
        SELECT c.nombre_completo as "Cliente", s.aseguradora, s.ramo,
               TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vencimiento",
               s."premio_UYU", s."premio_USD", s.corredor, s.agente, s.archivo_url as "link_doc"
        FROM seguros s 
        JOIN clientes c ON s.cliente_id = c.id ORDER BY s.id DESC
    """
    df_polizas = leer_datos(sql_view_polizas)
    if df_polizas.empty:
        st.info("Aún no hay pólizas cargadas.")
    else:
        st.dataframe(df_polizas, use_container_width=True, hide_index=True,
            column_config={
                "link_doc": st.column_config.LinkColumn("Documento", display_text="📄 Ver Póliza"),
                "premio_UYU": st.column_config.NumberColumn("Premio $", format="$ %.2f"),
                "premio_USD": st.column_config.NumberColumn("Premio U$S", format="U$S %.2f")
            })

# ---------------- PESTAÑA 3: VENCIMIENTOS ----------------
with tab3:
    st.header("🔔 Monitor de Vencimientos")
    df_opciones = leer_datos("SELECT DISTINCT ejecutivo, aseguradora, ramo, agente FROM seguros")
    
    with st.expander("🔍 Filtros de Vencimiento", expanded=True):
        col_dias, c_f1, c_f2 = st.columns([2, 1, 1])
        dias_select = col_dias.slider("📅 Días próximos:", 15, 180, 30, 15)
        
    condiciones = [f"s.vigencia_hasta BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '{dias_select} days')"]
    where_clause = " AND ".join(condiciones)
    
    sql_venc = f"""
        SELECT c.nombre_completo as "Cliente", c.celular, s.aseguradora, s.ramo, s.ejecutivo,
               TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vence"
        FROM seguros s JOIN clientes c ON s.cliente_id = c.id 
        WHERE {where_clause} ORDER BY s.vigencia_hasta ASC
    """
    df_venc = leer_datos(sql_venc)
    if not df_venc.empty:
        df_venc['link_wa'] = df_venc['celular'].apply(crear_link_wa)
        st.dataframe(df_venc, use_container_width=True, hide_index=True,
            column_config={"link_wa": st.column_config.LinkColumn("WhatsApp", display_text="📲")})
    else:
        st.success("✅ Todo al día.")