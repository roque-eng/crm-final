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

def ejecutar_consulta(query, params=None):
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            conn.close()
            return True
        return False
    except Exception as e:
        st.error(f"Error en base de datos: {e}")
        return False

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

# AJUSTE: Ahora usamos el ID del cliente para nombrar el archivo, ya que no hay nro de póliza
def guardar_archivo(archivo_pdf, cliente_id):
    carpeta = "documentos_polizas"
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    # Nombre del archivo: DOC_ClienteID_NombreOriginal
    nombre_archivo = f"DOC_Cliente{cliente_id}_{archivo_pdf.name}"
    ruta_completa = os.path.join(carpeta, nombre_archivo)
    with open(ruta_completa, "wb") as f:
        f.write(archivo_pdf.getbuffer())
    return ruta_completa

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS (CON PDF)", "🔔 VENCIMIENTOS"])

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

# ---------------- PESTAÑA 2: PÓLIZAS ----------------
with tab2:
    # Cargar lista de clientes
    df_lista_clientes = leer_datos("SELECT id, nombre_completo FROM clientes ORDER BY nombre_completo")
    opciones_clientes = {row['nombre_completo']: row['id'] for index, row in df_lista_clientes.iterrows()} if not df_lista_clientes.empty else {}

    st.subheader("📝 Alta de Nueva Póliza (Manual)")
    
    with st.expander("Abrir Formulario de Póliza", expanded=False):
        with st.form("form_poliza"):
            st.write("--- Datos Principales ---")
            c1, c2, c3 = st.columns(3)
            with c1:
                nombre_seleccionado = st.selectbox("Cliente", options=list(opciones_clientes.keys()))
                aseguradora = st.selectbox("Aseguradora", ["Sancor", "BSE", "Mapfre", "Porto", "HDI", "SBI", "Barbus", "Berkley", "SURA", "Otras"])
            with c2:
                # YA NO SE PIDE NUMERO DE POLIZA
                ramo = st.text_input("Ramo (Ej: Automotor)")
            with c3:
                ejecutivo = st.text_input("Ejecutivo / Vendedor")
            
            st.write("--- Vigencia y Costos ---")
            c4, c5, c6, c7 = st.columns(4)
            with c4:
                vigencia_desde = st.date_input("Vigencia Desde", value=date.today())
            with c5:
                vigencia_hasta = st.date_input("Vence", value=date.today().replace(year=date.today().year + 1))
            with c6:
                premio_uyu = st.number_input("Premio $ (UYU)", min_value=0.0, format="%.2f")
            with c7:
                premio_usd = st.number_input("Premio U$S (USD)", min_value=0.0, format="%.2f")

            st.write("--- Intermediarios y Documentos ---")
            c8, c9, c10 = st.columns(3)
            with c8:
                corredor = st.text_input("Corredor")
            with c9:
                agente = st.text_input("Agente")
            with c10:
                archivo_pdf = st.file_uploader("📂 Subir PDF", type=["pdf", "docx", "xlsx"])
            
            submitted_poliza = st.form_submit_button("💾 Guardar Póliza", use_container_width=True)

            if submitted_poliza:
                # Validación simplificada (ya no validamos nro_poliza)
                if nombre_seleccionado:
                    cliente_id = opciones_clientes[nombre_seleccionado]
                    ruta_guardada = None
                    
                    if archivo_pdf is not None:
                        # Pasamos el cliente_id para nombrar el archivo
                        ruta_guardada = guardar_archivo(archivo_pdf, cliente_id)
                    
                    # QUERY ACTUALIZADA: Eliminado 'numero_poliza'
                    sql_pol = """INSERT INTO seguros 
                                (cliente_id, aseguradora, ramo, vigencia_desde, vigencia_hasta, 
                                 "premio_UYU", "premio_USD", corredor, agente, ejecutivo, archivo_url) 
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    
                    datos = (cliente_id, aseguradora, ramo, vigencia_desde, vigencia_hasta, 
                             premio_uyu, premio_usd, corredor, agente, ejecutivo, ruta_guardada)
                    
                    if ejecutar_consulta(sql_pol, datos):
                        st.success("✅ Póliza guardada exitosamente.")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Debe seleccionar un cliente.")

    st.divider()
    
    # Visualización de la Tabla
    c_head, c_btn = st.columns([4, 1])
    with c_head:
        st.subheader("📂 Pólizas Vigentes")
    with c_btn:
        if st.button("🔄 Refrescar Pólizas"):
            st.rerun()

    # QUERY DE VISUALIZACIÓN ACTUALIZADA: Eliminado 'numero_poliza'
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
    st.dataframe(df_polizas, use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 3: VENCIMIENTOS ----------------
with tab3:
    st.header("🔔 Vencimientos (Próximos 30 días)")
    # Query actualizada: Eliminado 'numero_poliza'
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