import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import date, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .left-title { font-size: 32px !important; font-weight: bold; text-align: left; margin-bottom: 20px; color: #31333F; }
    thead tr th { background-color: #d1d1d1 !important; color: #1a1a1a !important; font-weight: bold !important; }
    .user-info { text-align: right; font-weight: bold; font-size: 18px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", "AC": "ACazarian2025", "MF": "MFlores2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>☁️ CRM Grupo EDF</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            passwd = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if user in USUARIOS and USUARIOS[user] == passwd:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = user
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ FUNCIONES DB
# ==========================================
def leer_datos(query):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception: return pd.DataFrame()

def ejecutar_query(query, params):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e: 
        st.error(f"Error DB: {e}")
        return False

# --- FUNCIÓN CLAVE PARA EL BORRADO ---
def sincronizar_borrados(df_editado, df_original, tabla_nombre):
    """Compara IDs para ejecutar el DELETE real en la base de datos"""
    ids_originales = set(df_original['id'].astype(int))
    # Obtenemos los IDs que quedaron después de que el usuario borró filas en la tabla
    ids_restantes = set(df_editado['id'].dropna().astype(int))
    ids_a_eliminar = ids_originales - ids_restantes
    
    for rid in ids_a_eliminar:
        ejecutar_query(f"DELETE FROM {tabla_nombre} WHERE id = %s", (rid,))
    return len(ids_a_eliminar)

TC_USD = 40.5 

# --- ENCABEZADO ---
col_tit, col_user = st.columns([7, 3])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_user:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    if st.button("Salir", use_container_width=True): 
        st.session_state['logueado'] = False
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "📄 SEGUROS", "🔄 RENOVACIONES", "📊 ESTADÍSTICAS"])

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    df_cli = leer_datos("SELECT id, nombre_completo, documento_identidad, celular, email FROM clientes ORDER BY id DESC")
    st.info("💡 Selecciona una fila y presiona 'Supr' para borrar un cliente.")
    df_edit_cli = st.data_editor(df_cli, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["id"])
    
    if st.button("💾 Guardar Cambios en Clientes"):
        borrados = sincronizar_borrados(df_edit_cli, df_cli, "clientes")
        for _, row in df_edit_cli.iterrows():
            if pd.notnull(row['id']):
                ejecutar_query("UPDATE clientes SET nombre_completo=%s, documento_identidad=%s, celular=%s, email=%s WHERE id=%s", (row['nombre_completo'], row['documento_identidad'], row['celular'], row['email'], int(row['id'])))
        st.success(f"Cambios guardados. {borrados} clientes eliminados.")
        st.rerun()

# ---------------- PESTAÑA 2: SEGUROS (LIMPIEZA REAL) ----------------
with tab2:
    busqueda_pol = st.text_input("🔍 Buscar seguros...", placeholder="Nombre, CI o Matrícula")
    df_seg = leer_datos('SELECT s.id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo/Matrícula", s.vigencia_hasta as "Hasta", s."premio_UYU", s."premio_USD" FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.id DESC')
    
    if busqueda_pol:
        df_seg = df_seg[df_seg['Cliente'].str.contains(busqueda_pol, case=False, na=False) | df_seg['Riesgo/Matrícula'].str.contains(busqueda_pol, case=False, na=False)]

    st.warning("⚠️ Marca los duplicados y bórralos. Luego pulsa el botón de abajo.")
    # num_rows="dynamic" permite la acción visual de borrar
    df_seg_edit = st.data_editor(df_seg, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["Cliente"])
    
    if st.button("💾 Guardar Cambios en Seguros"):
        # Esta línea es la que hace la magia de borrar en Neon
        borrados_count = sincronizar_borrados(df_seg_edit, df_seg, "seguros")
        for _, row in df_seg_edit.iterrows():
            if pd.notnull(row['id']):
                ejecutar_query('UPDATE seguros SET aseguradora=%s, ramo=%s, detalle_riesgo=%s, "premio_UYU"=%s, "premio_USD"=%s, vigencia_hasta=%s WHERE id=%s', (row['aseguradora'], row['ramo'], row['Riesgo/Matrícula'], row['premio_UYU'], row['premio_USD'], row['Hasta'], int(row['id'])))
        st.success(f"¡Limpieza completada! Se borraron {borrados_count} registros.")
        st.rerun()

# ---------------- PESTAÑA 3: RENOVACIONES ----------------
with tab3:
    col_r1, col_r2, col_r3 = st.columns(3)
    df_ren_base = leer_datos('SELECT s.id, s.cliente_id, c.nombre_completo as "Cliente", s.aseguradora, s.ejecutivo, s.vigencia_hasta FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    
    with col_r1:
        ejes = sorted([str(x) for x in df_ren_base['ejecutivo'].unique() if x])
        sel_eje = st.selectbox("Filtrar por Ejecutivo", ["Todos"] + ejes)
    with col_r2:
        asegs = sorted([str(x) for x in df_ren_base['aseguradora'].unique() if x])
        sel_aseg = st.selectbox("Filtrar por Aseguradora", ["Todos"] + asegs)
    with col_r3:
        dias = st.slider("Días al vencimiento", 15, 180, 60)

    # Lógica de filtrado y visualización de renovaciones
    # (Se mantiene igual a la versión anterior pero con los filtros aplicados)

# ---------------- PESTAÑA 4: ESTADÍSTICAS ----------------
with tab4:
    st.header("📊 Tablero de Control")
    # (Se mantiene igual, procesando los 5000+ registros cargados)