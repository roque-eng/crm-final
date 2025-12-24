import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import date, timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- VARIABLE GLOBAL DE TIPO DE CAMBIO (EVITA ERROR EN ESTADÍSTICAS) ---
TC_USD = 40.5 

# --- ESTILOS CSS FINALES (BOTONES, CONTRASTE Y ALINEACIÓN) ---
st.markdown("""
    <style>
    .left-title { font-size: 30px !important; font-weight: bold; text-align: left; color: #31333F; margin-top: -15px; }
    /* Encabezados ordenables */
    thead tr th { background-color: #f0f2f6 !important; color: #1a1a1a !important; font-weight: bold !important; cursor: pointer !important; }
    .user-info { text-align: right; font-weight: bold; font-size: 16px; color: #555; margin-bottom: 5px; }
    
    /* Botón Salir a la derecha */
    .exit-container { display: flex; justify-content: flex-end; }
    .stButton > button { width: 80px !important; height: 32px !important; padding: 0px !important; }

    /* Botones de Acción Circulares (Disquete y Prohibido) */
    .action-btn-container > div > button { 
        width: 50px !important; height: 50px !important; border-radius: 50% !important; 
        font-size: 22px !important; background-color: #ffffff !important; border: 2px solid #333 !important;
        display: flex; align-items: center; justify-content: center;
    }
    
    /* Botón No Renueva (Rojo) */
    .no-renueva-btn > div > button { border-color: #d32f2f !important; color: #d32f2f !important; }

    /* Estilo del botón de registro: Fondo oscuro, letras BLANCAS y tamaño chico */
    .reg-btn {
        text-decoration: none !important; 
        background-color: #333 !important; 
        color: #FFFFFF !important; 
        padding: 8px 12px; 
        border-radius: 5px; 
        font-weight: bold; 
        font-size: 12px !important;
        display: inline-block;
        margin-top: 5px;
        border: 1px solid #000;
    }
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
            user = st.text_input("Usuario"); passwd = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if user in USUARIOS and USUARIOS[user] == passwd:
                    st.session_state['logueado'] = True; st.session_state['usuario_actual'] = user; st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ FUNCIONES DB
# ==========================================
def leer_datos(query):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        df = pd.read_sql(query, conn); conn.close(); return df
    except Exception: return pd.DataFrame()

def ejecutar_query(query, params=None):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        cur = conn.cursor(); cur.execute(query, params); conn.commit(); cur.close(); conn.close(); return True
    except Exception: return False

def sincronizar_borrados(df_editado, df_original, tabla_nombre):
    ids_originales = set(df_original['id'].astype(int))
    ids_restantes = set(df_editado['id'].dropna().astype(int))
    ids_a_eliminar = ids_originales - ids_restantes
    for rid in ids_a_eliminar: ejecutar_query(f"DELETE FROM {tabla_nombre} WHERE id = %s", (rid,))
    return len(ids_a_eliminar)

# --- ENCABEZADO ---
col_tit, col_user_box = st.columns([8.5, 1.5])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_user_box:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="exit-container">', unsafe_allow_html=True)
    if st.button("Salir", key="exit_btn"): st.session_state['logueado'] = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# PESTAÑAS (ORDEN SOLICITADO)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 CLIENTES", "📄 SEGUROS", "🔄 RENOVACIONES", "🚫 EX SEGUROS", "📊 ESTADÍSTICAS"])

# ---------------- TAB 1: CLIENTES ----------------
with tab1:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    c_form, c_search = st.columns([1.3, 2.7])
    with c_form:
        st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" target="_blank" class="reg-btn">+ REGISTRAR NUEVO CLIENTE</a>', unsafe_allow_html=True)
    with c_search: b_cli = st.text_input("🔍 Buscar cliente...", key="s_cli")
    df_cli = leer_datos("SELECT * FROM clientes ORDER BY id DESC")
    if b_cli: df_cli = df_cli[df_cli['nombre_completo'].str.contains(b_cli, case=False, na=False)]
    if not df_cli.empty:
        df_e_cli = st.data_editor(df_cli, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["id"])
        st.markdown('<div class="action-btn-container">', unsafe_allow_html=True)
        if st.button("💾", help="Guardar cambios", key="save_cli"):
            sincronizar_borrados(df_e_cli, df_cli, "clientes"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- TAB 2: SEGUROS ----------------
with tab2:
    b_seg = st.text_input("🔍 Buscar seguros...", key="s_pol")
    df_seg = leer_datos('SELECT s.id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo, s.vigencia_hasta, s."premio_UYU", s."premio_USD" FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.id DESC')
    if b_seg: df_seg = df_seg[df_seg['Cliente'].str.contains(b_seg, case=False, na=False)]
    if not df_seg.empty:
        df_e_seg = st.data_editor(df_seg, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["Cliente"])
        st.markdown('<div class="action-btn-container">', unsafe_allow_html=True)
        if st.button("💾", help="Guardar cambios", key="save_seg"):
            sincronizar_borrados(df_e_seg, df_seg, "seguros"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- TAB 3: RENOVACIONES (FILTROS REINTEGRADOS) ----------------
with tab3:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    b_ren = st.text_input("🔍 Buscar por nombre...", placeholder="Cliente a renovar")
    df_ren_raw = leer_datos('SELECT s.id, s.cliente_id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo, s.vigencia_hasta, s."premio_UYU", s."premio_USD", s.ejecutivo, s.corredor, s.agente FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    
    if not df_ren_raw.empty:
        # Filtros de Ejecutivo y Aseguradora
        c1, c2, c3 = st.columns(3)
        with c1: 
            ejes = sorted([str(x) for x in df_ren_raw['ejecutivo'].unique() if x])
            sel_eje = st.selectbox("👤 Filtrar Ejecutivo", ["Todos"] + ejes, key="ren_eje")
        with c2: 
            asegs = sorted([str(x) for x in df_ren_raw['aseguradora'].unique() if x])
            sel_aseg = st.selectbox("🏢 Filtrar Aseguradora", ["Todos"] + asegs, key="ren_aseg")
        with c3: 
            dias_v = st.slider("📅 Ver próximos (días):", 15, 180, 180)

        hoy = date.today()
        df_ren_raw['Vence_dt'] = pd.to_datetime(df_ren_raw['vigencia_hasta']).dt.date
        mask = (df_ren_raw['Vence_dt'] >= hoy - timedelta(days=120)) & (df_ren_raw['Vence_dt'] <= hoy + timedelta(days=dias_v))
        
        if b_ren: mask = mask & (df_ren_raw['Cliente'].str.contains(b_ren, case=False, na=False))
        if sel_eje != "Todos": mask = mask & (df_ren_raw['ejecutivo'] == sel_eje)
        if sel_aseg != "Todos": mask = mask & (df_ren_raw['aseguradora'] == sel_aseg)
        
        df_f = df_ren_raw[mask].copy().sort_values("Vence_dt")
        df_f['Situación'] = df_f['Vence_dt'].apply(lambda x: f"⚠️ VENCIDO ({(hoy-x).days} días)" if x < hoy else f"⏳ Vence en {(x-hoy).days} días")

        df_e_ren = st.data_editor(df_f, use_container_width=True, hide_index=True,
            column_order=["Situación", "Cliente", "aseguradora", "ramo", "detalle_riesgo", "vigencia_hasta", "premio_UYU", "premio_USD"],
            column_config={"vigencia_hasta": st.column_config.DateColumn("Nueva Fecha")}, disabled=["Cliente", "Situación"])
        
        col_r1, col_r2, _ = st.columns([1, 1, 10])
        with col_r1:
            st.markdown('<div class="action-btn-container">', unsafe_allow_html=True)
            if st.button("💾", help="Renovar Seleccionados", key="btn_ren_ok"):
                for _, r in df_e_ren.iterrows():
                    ejecutar_query('INSERT INTO seguros (cliente_id, aseguradora, ramo, detalle_riesgo, vigencia_hasta, "premio_UYU", "premio_USD", ejecutivo, corredor, agente) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (r['cliente_id'], r['aseguradora'], r['ramo'], r['detalle_riesgo'], r['vigencia_hasta'], r['premio_UYU'], r['premio_USD'], r['ejecutivo'], r['corredor'], r['agente']))
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_r2:
            st.markdown('<div class="action-btn-container no-renueva-btn">', unsafe_allow_html=True)
            if st.button("🚫", help="Mover a EX SEGUROS", key="btn_no_ren"):
                for _, r in df_e_ren.iterrows():
                    ejecutar_query('INSERT INTO ex_seguros (cliente_id, aseguradora, ramo, detalle_riesgo, vigencia_hasta, "premio_UYU", "premio_USD", ejecutivo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', (r['cliente_id'], r['aseguradora'], r['ramo'], r['detalle_riesgo'], r['vigencia_hasta'], r['premio_UYU'], r['premio_USD'], r['ejecutivo']))
                    ejecutar_query('DELETE FROM seguros WHERE id = %s', (int(r['id']),))
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- TAB 4: EX SEGUROS ----------------
with tab4:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    df_ex = leer_datos('SELECT e.*, c.nombre_completo as "Cliente" FROM ex_seguros e JOIN clientes c ON e.cliente_id = c.id ORDER BY fecha_baja DESC')
    st.dataframe(df_ex, use_container_width=True, hide_index=True)

# ---------------- TAB 5: ESTADÍSTICAS ----------------
with tab5:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    df_st = leer_datos('SELECT aseguradora, ramo, ejecutivo, vigencia_hasta, "premio_UYU", "premio_USD" FROM seguros')
    if not df_st.empty:
        df_st['vigencia_hasta'] = pd.to_datetime(df_st['vigencia_hasta'])
        df_st['Año'] = df_st['vigencia_hasta'].dt.year.astype(str)
        df_st['Total_USD'] = df_st['premio_USD'].fillna(0) + (df_st['premio_UYU'].fillna(0) / TC_USD)
        
        cf1, cf2 = st.columns(2)
        with cf1: anos = sorted(df_st['Año'].unique()); sel_ano = st.multiselect("Filtrar Año", anos, default=anos[-2:] if len(anos)>1 else anos)
        with cf2: ejes_st = sorted([str(x) for x in df_st['ejecutivo'].unique() if x]); sel_eje_st = st.selectbox("Filtrar Ejecutivo", ["Todos"] + ejes_st)

        df_f_st = df_st[df_st['Año'].isin(sel_ano)]
        if sel_eje_st != "Todos": df_f_st = df_f_st[df_f_st['ejecutivo'] == sel_eje_st]

        m1, m2 = st.columns(2)
        m1.metric("Cartera Total (USD)", f"U$S {df_f_st['Total_USD'].sum():,.0f}")
        m2.metric("Pólizas Activas", len(df_f_st))
        
        df_plot = df_f_st.groupby('aseguradora')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=False)
        st.plotly_chart(px.bar(df_plot, x='aseguradora', y='Total_USD', title="Volumen por Compañía", color='aseguradora'), use_container_width=True)