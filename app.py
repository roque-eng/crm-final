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

def sincronizar_borrados(df_editado, df_original, tabla_nombre):
    ids_originales = set(df_original['id'].astype(int))
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

# ---------------- PESTAÑA 1: CLIENTES (CON LINK A FORMS REINSTALADO) ----------------
with tab1:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    
    # Reinstalación del botón de Registro
    c_btn_form, c_search = st.columns([1.6, 2.4])
    with c_btn_form:
        st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" target="_blank" style="text-decoration:none; background-color:#333; color:white; padding:10px 20px; border-radius:5px; font-weight:bold;">+ REGISTRAR NUEVO CLIENTE</a>', unsafe_allow_html=True)
    
    with c_search:
        busqueda_cli = st.text_input("🔍 Buscar cliente por nombre o documento", key="s_cli")

    df_cli = leer_datos("SELECT id, nombre_completo, documento_identidad, celular, email FROM clientes ORDER BY id DESC")
    
    if busqueda_cli and not df_cli.empty:
        df_cli = df_cli[df_cli['nombre_completo'].str.contains(busqueda_cli, case=False, na=False) | df_cli['documento_identidad'].str.contains(busqueda_cli, na=False)]

    st.divider()
    if not df_cli.empty:
        st.info("💡 Para borrar: Selecciona la fila, presiona 'Supr' y luego el botón de Guardar.")
        df_edit_cli = st.data_editor(df_cli, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["id"])
        
        if st.button("💾 Guardar Cambios en Clientes"):
            borrados_c = sincronizar_borrados(df_edit_cli, df_cli, "clientes")
            for _, row in df_edit_cli.iterrows():
                if pd.notnull(row['id']):
                    ejecutar_query("UPDATE clientes SET nombre_completo=%s, documento_identidad=%s, celular=%s, email=%s WHERE id=%s", (row['nombre_completo'], row['documento_identidad'], row['celular'], row['email'], int(row['id'])))
            st.success(f"Cambios guardados. {borrados_c} cliente(s) eliminado(s).")
            st.rerun()

# ---------------- PESTAÑA 2: SEGUROS ----------------
with tab2:
    busqueda_pol = st.text_input("🔍 Buscar seguros...", placeholder="Nombre, CI o Matrícula")
    df_seg = leer_datos('SELECT s.id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo/Matrícula", s.vigencia_hasta as "Hasta", s."premio_UYU", s."premio_USD" FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.id DESC')
    if busqueda_pol and not df_seg.empty:
        df_seg = df_seg[df_seg['Cliente'].str.contains(busqueda_pol, case=False, na=False) | df_seg['Riesgo/Matrícula'].str.contains(busqueda_pol, case=False, na=False)]
    
    df_seg_edit = st.data_editor(df_seg, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["Cliente"])
    if st.button("💾 Guardar Cambios en Seguros"):
        borrados_s = sincronizar_borrados(df_seg_edit, df_seg, "seguros")
        for _, row in df_seg_edit.iterrows():
            if pd.notnull(row['id']):
                ejecutar_query('UPDATE seguros SET aseguradora=%s, ramo=%s, detalle_riesgo=%s, "premio_UYU"=%s, "premio_USD"=%s, vigencia_hasta=%s WHERE id=%s', (row['aseguradora'], row['ramo'], row['Riesgo/Matrícula'], row['premio_UYU'], row['premio_USD'], row['Hasta'], int(row['id'])))
        st.success(f"Cambios guardados. {borrados_s} registro(s) eliminado(s).")
        st.rerun()

# ---------------- PESTAÑA 3: RENOVACIONES (VENTANA AMPLIADA) ----------------
with tab3:
    st.header("🔄 Centro de Renovaciones")
    df_ren_raw = leer_datos('SELECT s.id, s.cliente_id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo", s.ejecutivo, s.corredor, s.agente, s.vigencia_hasta as "Vence_Original", s."premio_UYU", s."premio_USD" FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    
    if not df_ren_raw.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            ejes = sorted([str(x) for x in df_ren_raw['ejecutivo'].unique() if x])
            sel_eje = st.selectbox("👤 Ejecutivo", ["Todos"] + ejes)
        with c2:
            asegs = sorted([str(x) for x in df_ren_raw['aseguradora'].unique() if x])
            sel_aseg = st.selectbox("🏢 Aseguradora", ["Todos"] + asegs)
        with c3:
            dias_fut = st.slider("📅 Ver próximos (días):", 15, 180, 60)

        hoy = date.today()
        df_ren_raw['Vence_Original_dt'] = pd.to_datetime(df_ren_raw['Vence_Original']).dt.date
        
        # Filtro de 120 días atrás para capturar noviembre y diciembre
        mask = (df_ren_raw['Vence_Original_dt'] >= hoy - timedelta(days=120)) & (df_ren_raw['Vence_Original_dt'] <= hoy + timedelta(days=dias_fut))
        
        if sel_eje != "Todos": mask = mask & (df_ren_raw['ejecutivo'] == sel_eje)
        if sel_aseg != "Todos": mask = mask & (df_ren_raw['aseguradora'] == sel_aseg)
        
        df_ren_f = df_ren_raw[mask].copy()
        df_ren_f['Estado'] = df_ren_f['Vence_Original_dt'].apply(lambda x: f"⚠️ VENCIDO ({(hoy-x).days} días)" if x < hoy else f"⏳ Faltan {(x-hoy).days} días")
        df_ren_f = df_ren_f.sort_values("Vence_Original_dt")

        if not df_ren_f.empty:
            df_ren_edit = st.data_editor(df_ren_f, use_container_width=True, hide_index=True,
                column_order=["Estado", "Cliente", "aseguradora", "ramo", "Riesgo", "Vence_Original", "premio_UYU", "premio_USD"],
                column_config={"Vence_Original": st.column_config.DateColumn("Nueva Fecha"), "Estado": st.column_config.TextColumn("Situación")}, 
                disabled=["Cliente", "Estado"])
            
            if st.button("🚀 Confirmar y Crear Renovaciones"):
                for _, row in df_ren_edit.iterrows():
                    ejecutar_query('INSERT INTO seguros (cliente_id, aseguradora, ramo, detalle_riesgo, vigencia_hasta, "premio_UYU", "premio_USD", ejecutivo, corredor, agente) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (row['cliente_id'], row['aseguradora'], row['ramo'], row['Riesgo'], row['Vence_Original'], row['premio_UYU'], row['premio_USD'], row['ejecutivo'], row['corredor'], row['agente']))
                st.rerun()

# ---------------- PESTAÑA 4: ESTADÍSTICAS ----------------
with tab4:
    st.header("📊 Tablero de Control")
    # (Lógica de estadísticas idéntica a la anterior)