import streamlit as st
import pandas as pd
import psycopg2
import os
import time
from datetime import date

# 1. Configuración de página
st.set_page_config(page_title="Sistema Seguros", layout="wide", page_icon="🛡️")

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {
    "RDF": "claveRockuda.4428",
    "AB": "claveABentancor2025",
    "GR": "claveGRobaina2025"
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
    st.markdown("<h1 style='text-align: center;'>☁️ CRM Seguros</h1>", unsafe_allow_html=True)
    
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
col_logo, col_user = st.columns([8, 2])
with col_logo:
    st.title("🛡️ Gestión de Corredor de Seguros")
with col_user:
    st.write(f"👤 **{st.session_state['usuario_actual']}**")
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

# --- FUNCIONES DE BASE DE DATOS (MODIFICADO PARA USAR SECRETOS) ---
def get_db_connection():
    try:
        # Aquí es donde ocurre la magia: busca la clave en el "Bolsillo Secreto"
        url_conexion = st.secrets["DB_URL"]
        conn = psycopg2.connect(url_conexion)
        return conn
    except Exception as e:
        # Si estamos en local y no hay secretos, mostramos un mensaje amigable
        st.error(f"⚠️ Error de conexión. Si estás en la web, revisa los 'Secrets'. Si estás en local, falta el archivo secrets.toml. Detalle: {e}")
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

def guardar_archivo(archivo_pdf, numero_poliza):
    carpeta = "documentos_polizas"
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    nombre_archivo = f"POLIZA_{numero_poliza}_{archivo_pdf.name}"
    ruta_completa = os.path.join(carpeta, nombre_archivo)
    with open(ruta_completa, "wb") as f:
        f.write(archivo_pdf.getbuffer())
    return ruta_completa

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS (CON PDF)", "🔔 VENCIMIENTOS"])

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    col_form, col_tabla = st.columns([1, 2])
    with col_form:
        st.subheader("Nuevo Cliente")
        with st.form("form_cliente"):
            nombre = st.text_input("Nombre / Razón Social")
            doc_id = st.text_input("CI / RUT")
            email = st.text_input("Email")
            celular = st.text_input("Celular")
            domicilio = st.text_area("Domicilio")
            submitted_cliente = st.form_submit_button("Guardar Cliente")
            
            if submitted_cliente:
                if nombre and doc_id:
                    sql = "INSERT INTO clientes (nombre_completo, documento_identidad, email, celular, domicilio) VALUES (%s, %s, %s, %s, %s)"
                    if ejecutar_consulta(sql, (nombre, doc_id, email, celular, domicilio)):
                        st.success(f"✅ Cliente {nombre} guardado.")
                        st.rerun()
                else:
                    st.warning("Nombre y Documento son obligatorios.")

    with col_tabla:
        st.subheader("Cartera de Clientes")
        busqueda = st.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI")
        sql_cli = "SELECT id, nombre_completo, documento_identidad, celular, email FROM clientes ORDER BY id DESC"
        if busqueda:
            sql_cli = f"SELECT id, nombre_completo, documento_identidad, celular, email FROM clientes WHERE nombre_completo ILIKE '%%{busqueda}%%' OR documento_identidad ILIKE '%%{busqueda}%%'"
        
        st.dataframe(leer_datos(sql_cli), use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 2: PÓLIZAS ----------------
with tab2:
    df_lista_clientes = leer_datos("SELECT id, nombre_completo FROM clientes ORDER BY nombre_completo")
    opciones_clientes = {row['nombre_completo']: row['id'] for index, row in df_lista_clientes.iterrows()} if not df_lista_clientes.empty else {}

    st.subheader("📝 Alta de Nueva Póliza")
    
    with st.expander("Abrir Formulario de Póliza", expanded=True):
        with st.form("form_poliza"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nombre_seleccionado = st.selectbox("Cliente", options=list(opciones_clientes.keys()))
                aseguradora = st.selectbox("Aseguradora", ["Sancor", "BSE", "Mapfre", "Porto", "HDI", "SBI", "Barbus", "Berkley", "SURA", "Otras"])
                ramo = st.text_input("Ramo (Ej: Automotor)")
            with c2:
                nro_poliza = st.text_input("Número de Póliza")
                vigencia_desde = st.date_input("Vigencia Desde", value=date.today())
                vigencia_hasta = st.date_input("Vence", value=date.today().replace(year=date.today().year + 1))
            with c3:
                moneda = st.radio("Moneda", ["USD", "UYU"], horizontal=True)
                monto = st.number_input("Monto Prima", min_value=0.0, format="%.2f")
                archivo_pdf = st.file_uploader("📂 Subir PDF", type=["pdf", "docx", "xlsx"])
            
            ejecutivo = st.text_input("Ejecutivo / Vendedor")
            submitted_poliza = st.form_submit_button("💾 Guardar Póliza")

            if submitted_poliza:
                if nombre_seleccionado and nro_poliza:
                    cliente_id = opciones_clientes[nombre_seleccionado]
                    ruta_guardada = None
                    if archivo_pdf is not None:
                        ruta_guardada = guardar_archivo(archivo_pdf, nro_poliza)
                    
                    sql_pol = """INSERT INTO seguros (cliente_id, aseguradora, ramo, numero_poliza, vigencia_desde, vigencia_hasta, moneda, monto_prima, ejecutivo, archivo_url) 
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    datos = (cliente_id, aseguradora, ramo, nro_poliza, vigencia_desde, vigencia_hasta, moneda, monto, ejecutivo, ruta_guardada)
                    
                    if ejecutar_consulta(sql_pol, datos):
                        st.success("✅ Póliza guardada exitosamente.")
                        st.rerun()
                else:
                    st.error("Faltan datos obligatorios (Cliente o Número Póliza).")

    st.divider()
    st.subheader("📂 Pólizas Vigentes")
    sql_view_polizas = """SELECT c.nombre_completo as Cliente, s.aseguradora, s.numero_poliza, s.vigencia_hasta as Vencimiento, 
                          CASE WHEN s.archivo_url IS NOT NULL THEN '✅ SÍ' ELSE '❌ NO' END as "PDF Adjunto" 
                          FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.id DESC"""
    st.dataframe(leer_datos(sql_view_polizas), use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 3: VENCIMIENTOS ----------------
with tab3:
    st.header("🔔 Vencimientos (Próximos 30 días)")
    sql_venc = """SELECT c.nombre_completo, c.celular, s.aseguradora, s.numero_poliza, s.vigencia_hasta 
                  FROM seguros s JOIN clientes c ON s.cliente_id = c.id 
                  WHERE s.vigencia_hasta BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '30 days') 
                  ORDER BY s.vigencia_hasta ASC"""
    df_venc = leer_datos(sql_venc)
    
    if not df_venc.empty:
        st.warning(f"⚠️ ¡Atención! {len(df_venc)} Pólizas vencen pronto.")
        st.dataframe(df_venc, use_container_width=True)
    else:
        st.success("✅ No hay vencimientos próximos. Todo tranquilo.")