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
USUARIOS = {
    "RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", 
    "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", 
    "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", 
    "AC": "ACazarian2025", "MF": "MFlores2025"
}

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
        st.error(f"Error en base de datos: {e}")
        return False

def sincronizar_borrados(df_editado, df_original, tabla_nombre):
    """Ejecuta el DELETE real en Neon comparando IDs"""
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

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    busqueda_cli = st.text_input("🔍 Buscar cliente por nombre o documento", key="s_cli")
    df_cli = leer_datos("SELECT id, nombre_completo, documento_identidad, celular, email FROM clientes ORDER BY id DESC")
    
    if busqueda_cli and not df_cli.empty:
        df_cli = df_cli[df_cli['nombre_completo'].str.contains(busqueda_cli, case=False, na=False) | df_cli['documento_identidad'].str.contains(busqueda_cli, na=False)]

    if not df_cli.empty:
        st.info("💡 Para borrar: Selecciona la fila, presiona 'Supr' y luego el botón de Guardar.")
        df_edit_cli = st.data_editor(df_cli, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["id"])
        if st.button("💾 Guardar Cambios en Clientes"):
            sincronizar_borrados(df_edit_cli, df_cli, "clientes")
            for _, row in df_edit_cli.iterrows():
                if pd.notnull(row['id']):
                    ejecutar_query("UPDATE clientes SET nombre_completo=%s, documento_identidad=%s, celular=%s, email=%s WHERE id=%s", (row['nombre_completo'], row['documento_identidad'], row['celular'], row['email'], int(row['id'])))
            st.rerun()

# ---------------- PESTAÑA 2: SEGUROS (LIMPIEZA DE DUPLICADOS) ----------------
with tab2:
    busqueda_pol = st.text_input("🔍 Buscar por Cliente o Matrícula", placeholder="Ej: Ruglio o SLN194")
    df_seg = leer_datos('SELECT s.id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo/Matrícula", s.vigencia_hasta as "Hasta", s."premio_UYU", s."premio_USD" FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.id DESC')
    
    if busqueda_pol and not df_seg.empty:
        df_seg = df_seg[df_seg['Cliente'].str.contains(busqueda_pol, case=False, na=False) | df_seg['Riesgo/Matrícula'].str.contains(busqueda_pol, case=False, na=False)]

    if not df_seg.empty:
        st.warning("⚠️ Selecciona los IDs duplicados, presiona 'Supr' y luego 'Guardar' para eliminarlos permanentemente.")
        df_seg_edit = st.data_editor(df_seg, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["Cliente"])
        
        if st.button("💾 Guardar Cambios en Seguros"):
            # Realiza el borrado físico en Neon de los registros que quitaste de la tabla
            borrados = sincronizar_borrados(df_seg_edit, df_seg, "seguros")
            for _, row in df_seg_edit.iterrows():
                if pd.notnull(row['id']):
                    ejecutar_query('UPDATE seguros SET aseguradora=%s, ramo=%s, detalle_riesgo=%s, "premio_UYU"=%s, "premio_USD"=%s, vigencia_hasta=%s WHERE id=%s', 
                                   (row['aseguradora'], row['ramo'], row['Riesgo/Matrícula'], row['premio_UYU'], row['premio_USD'], row['Hasta'], int(row['id'])))
            st.success(f"Proceso finalizado. Se eliminaron {borrados} registros duplicados.")
            st.rerun()

# ---------------- PESTAÑA 3: RENOVACIONES (FILTROS INDEPENDIENTES Y CASOS VENCIDOS) ----------------
with tab3:
    st.header("🔄 Centro de Renovaciones")
    df_ren_raw = leer_datos('SELECT s.id, s.cliente_id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo", s.ejecutivo, s.corredor, s.agente, s.vigencia_hasta as "Vence_Viejo", s."premio_UYU", s."premio_USD" FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    
    if not df_ren_raw.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            ejes = sorted([str(x) for x in df_ren_raw['ejecutivo'].unique() if x])
            sel_eje = st.selectbox("👤 Ejecutivo", ["Todos"] + ejes, key="ren_eje_final")
        with c2:
            asegs = sorted([str(x) for x in df_ren_raw['aseguradora'].unique() if x])
            sel_aseg = st.selectbox("🏢 Aseguradora", ["Todos"] + asegs, key="ren_aseg_final")
        with c3:
            dias_v = st.slider("📅 Ventana de tiempo (días futuros):", 15, 180, 60)

        # Lógica: Muestra desde hace 90 días (pendientes) hasta días_v en el futuro
        today = date.today()
        df_ren_raw['Vence_Viejo_dt'] = pd.to_datetime(df_ren_raw['Vence_Viejo']).dt.date
        mask = (df_ren_raw['Vence_Viejo_dt'] >= today - timedelta(days=90)) & (df_ren_raw['Vence_Viejo_dt'] <= today + timedelta(days=dias_v))
        
        if sel_eje != "Todos": mask = mask & (df_ren_raw['ejecutivo'] == sel_eje)
        if sel_aseg != "Todos": mask = mask & (df_ren_raw['aseguradora'] == sel_aseg)
        
        df_ren_f = df_ren_raw[mask].copy().sort_values("Vence_Viejo_dt")
        
        if not df_ren_f.empty:
            st.info(f"Se encontraron {len(df_ren_f)} seguros vencidos o próximos a vencer.")
            df_ren_edit = st.data_editor(df_ren_f, use_container_width=True, hide_index=True,
                column_order=["Cliente", "aseguradora", "ramo", "Riesgo", "Vence_Viejo", "premio_UYU", "premio_USD"],
                column_config={"Vence_Viejo": st.column_config.DateColumn("Nueva Fecha de Vigencia")}, disabled=["Cliente"])
            
            if st.button("🚀 Confirmar y Crear Renovaciones"):
                for _, row in df_ren_edit.iterrows():
                    ejecutar_query('INSERT INTO seguros (cliente_id, aseguradora, ramo, detalle_riesgo, vigencia_hasta, "premio_UYU", "premio_USD", ejecutivo, corredor, agente) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (row['cliente_id'], row['aseguradora'], row['ramo'], row['Riesgo'], row['Vence_Viejo'], row['premio_UYU'], row['premio_USD'], row['ejecutivo'], row['corredor'], row['agente']))
                st.success("✅ Los nuevos registros han sido creados exitosamente.")
                st.rerun()

# ---------------- PESTAÑA 4: ESTADÍSTICAS ----------------
with tab4:
    st.header("📊 Tablero de Control y Proyecciones")
    df_st = leer_datos('SELECT aseguradora, ramo, ejecutivo, vigencia_hasta, "premio_UYU", "premio_USD" FROM seguros')
    if not df_st.empty:
        df_st['vigencia_hasta'] = pd.to_datetime(df_st['vigencia_hasta'])
        df_st['Año'] = df_st['vigencia_hasta'].dt.year.astype(str)
        df_st['Total_USD'] = df_st['premio_USD'].fillna(0) + (df_st['premio_UYU'].fillna(0) / TC_USD)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1: sel_ano = st.multiselect("Año", sorted(df_st['Año'].unique()), default=sorted(df_st['Año'].unique()))
        
        # Limpieza de nulos para evitar errores en el filtro
        ejes_stats = sorted([str(x) for x in df_st['ejecutivo'].unique() if x])
        with col_f2: sel_eje_st = st.selectbox("Ejecutivo (Filtro Global)", ["Todos"] + ejes_stats)

        df_f = df_st[df_st['Año'].isin(sel_ano)]
        if sel_eje_st != "Todos": df_f = df_f[df_f['ejecutivo'] == sel_eje_st]

        m1, m2 = st.columns(2)
        m1.metric("Cartera Proyectada", f"U$S {df_f['Total_USD'].sum():,.0f}")
        m2.metric("Pólizas", len(df_f))
        st.plotly_chart(px.bar(df_f.groupby('aseguradora')['Total_USD'].sum().reset_index(), x='aseguradora', y='Total_USD', title="Volumen por Compañía (USD)"), use_container_width=True)