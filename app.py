import streamlit as st
import pandas as pd
import psycopg2
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
# ⚙️ ENCABEZADO
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
    busqueda_cli = col_s.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI", key="input_busqueda_clientes")
    sql_cli = "SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes"
    if busqueda_cli:
        sql_cli += f" WHERE nombre_completo ILIKE '%%{busqueda_cli}%%' OR documento_identidad ILIKE '%%{busqueda_cli}%%'"
    sql_cli += " ORDER BY id DESC"
    st.dataframe(leer_datos(sql_cli), use_container_width=True, hide_index=True)
    if st.button("🔄 Actualizar Tabla Clientes"): st.rerun()

# ---------------- PESTAÑA 2: PÓLIZAS ----------------
with tab2:
    col_pol_h, col_pol_s = st.columns([2, 1])
    col_pol_h.subheader("📂 Pólizas Vigentes")
    busqueda_pol = col_pol_s.text_input("🔍 Buscar póliza...", placeholder="Nombre o CI", key="input_busqueda_polizas")
    
    df_op_pol = leer_datos("SELECT DISTINCT aseguradora, ramo, agente FROM seguros")
    with st.expander("🔍 Filtros Avanzados"):
        c1, c2, c3 = st.columns(3)
        f_aseg_p = c1.multiselect("Aseguradora", options=df_op_pol["aseguradora"].unique() if not df_op_pol.empty else [], key="filter_aseg_pol")
        f_ramo_p = c2.multiselect("Ramo", options=df_op_pol["ramo"].unique() if not df_op_pol.empty else [], key="filter_ramo_pol")
        f_agente_p = c3.multiselect("Agente", options=df_op_pol["agente"].unique() if not df_op_pol.empty else [], key="filter_agente_pol")

    sql_pol = """
        SELECT c.nombre_completo as "Cliente", c.documento_identidad as "CI", s.aseguradora, s.ramo,
               TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vencimiento",
               s."premio_UYU", s."premio_USD", s.corredor, s.agente, s.archivo_url as "link_doc"
        FROM seguros s JOIN clientes c ON s.cliente_id = c.id
    """
    cond_p = []
    if busqueda_pol:
        cond_p.append(f"(c.nombre_completo ILIKE '%%{busqueda_pol}%%' OR c.documento_identidad ILIKE '%%{busqueda_pol}%%')")
    if f_aseg_p: cond_p.append(f"s.aseguradora IN ('" + "','".join(f_aseg_p) + "')")
    if f_ramo_p: cond_p.append(f"s.ramo IN ('" + "','".join(f_ramo_p) + "')")
    if f_agente_p: cond_p.append(f"s.agente IN ('" + "','".join(f_agente_p) + "')")
    if cond_p: sql_pol += " WHERE " + " AND ".join(cond_p)
    sql_pol += " ORDER BY s.id DESC"

    df_p = leer_datos(sql_pol)
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True, hide_index=True,
            column_config={
                "link_doc": st.column_config.LinkColumn("Documento", display_text="📄 Ver Póliza"),
                "premio_UYU": st.column_config.NumberColumn("Premio $", format="$ %.2f"),
                "premio_USD": st.column_config.NumberColumn("Premio U$S", format="U$S %.2f")
            })
    if st.button("🔄 Refrescar Pólizas"): st.rerun()

# ---------------- PESTAÑA 3: VENCIMIENTOS ----------------
with tab3:
    st.header("🔔 Monitor de Vencimientos")
    df_op_v = leer_datos("SELECT DISTINCT ejecutivo, aseguradora, ramo FROM seguros")
    with st.expander("🔍 Configuración de Alertas", expanded=True):
        col_d, cf1, cf2, cf3 = st.columns([2, 1, 1, 1])
        dias_s = col_d.slider("📅 Días próximos:", 15, 180, 30, 15, key="slider_vencimientos")
        f_ej_v = cf1.multiselect("Ejecutivo", options=df_op_v["ejecutivo"].dropna().unique() if not df_op_v.empty else [], key="filter_ejec_venc")
        f_as_v = cf2.multiselect("Aseguradora", options=df_op_v["aseguradora"].dropna().unique() if not df_op_v.empty else [], key="filter_aseg_venc")
        f_rm_v = cf3.multiselect("Ramo", options=df_op_v["ramo"].dropna().unique() if not df_op_v.empty else [], key="filter_ramo_venc")
    
    cond_v = [f"s.vigencia_hasta BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '{dias_s} days')"]
    if f_ej_v: cond_v.append(f"s.ejecutivo IN ('" + "','".join(f_ej_v) + "')")
    if f_as_v: cond_v.append(f"s.aseguradora IN ('" + "','".join(f_as_v) + "')")
    if f_rm_v: cond_v.append(f"s.ramo IN ('" + "','".join(f_rm_v) + "')")
    
    sql_v = f"""
        SELECT c.nombre_completo as "Cliente", c.celular, s.aseguradora, s.ramo, s.ejecutivo, 
               TO_CHAR(s.vigencia_hasta, 'DD/MM/YYYY') as "Vence" 
        FROM seguros s JOIN clientes c ON s.cliente_id = c.id 
        WHERE {" AND ".join(cond_v)} 
        ORDER BY s.vigencia_hasta ASC
    """
    df_v = leer_datos(sql_v)
    if not df_v.empty:
        df_v["WhatsApp"] = df_v["celular"].apply(crear_link_wa)
        st.dataframe(df_v, use_container_width=True, hide_index=True, column_config={"WhatsApp": st.column_config.LinkColumn("Contacto", display_text="📲")})
    else: st.success("✅ Todo al día.")