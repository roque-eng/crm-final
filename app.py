import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import date, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS REFINADOS ---
st.markdown("""
    <style>
    .left-title { font-size: 30px !important; font-weight: bold; text-align: left; color: #31333F; margin-top: -15px; }
    thead tr th { background-color: #f0f2f6 !important; color: #1a1a1a !important; font-weight: bold !important; cursor: pointer !important; }
    .user-info { text-align: right; font-weight: bold; font-size: 16px; color: #555; margin-bottom: 5px; }
    .exit-container { display: flex; justify-content: flex-end; }
    .stButton > button { width: 80px !important; height: 32px !important; padding: 0px !important; }
    .action-btn-container > div > button { 
        width: 50px !important; height: 50px !important; border-radius: 50% !important; 
        font-size: 22px !important; background-color: #ffffff !important; border: 2px solid #333 !important;
        display: flex; align-items: center; justify-content: center;
    }
    .no-renueva-btn > div > button { border-color: #d32f2f !important; color: #d32f2f !important; }
    .reg-btn {
        text-decoration: none !important; background-color: #333 !important; color: #FFFFFF !important; 
        padding: 8px 12px; border-radius: 5px; font-weight: bold; font-size: 11px !important;
        display: inline-block; margin-top: 5px; border: 1px solid #000;
    }
    </style>
    """, unsafe_allow_html=True)

# 🔐 GESTIÓN DE USUARIOS (Credenciales Grupo EDF)
USUARIOS = {"RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", "AC": "ACazarian2025", "MF": "MFlores2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>☁️ CRM Grupo EDF</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True; st.session_state['usuario_actual'] = u; st.rerun()
    st.stop()

def leer_datos(q):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        df = pd.read_sql(q, conn); conn.close(); return df
    except: return pd.DataFrame()

def ejecutar_q(q, p):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        cur = conn.cursor(); cur.execute(q, p); conn.commit(); cur.close(); conn.close(); return True
    except: return False

def sincronizar_borrados(df_e, df_o, tabla):
    ids_o = set(df_o['id'].astype(int))
    ids_r = set(df_e['id'].dropna().astype(int))
    ids_del = ids_o - ids_r
    for rid in ids_del: ejecutar_q(f"DELETE FROM {tabla} WHERE id = %s", (rid,))
    return len(ids_del)

# --- ENCABEZADO (SALIR A LA DERECHA) ---
col_t, col_u = st.columns([8.5, 1.5])
with col_t: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_u:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="exit-container">', unsafe_allow_html=True)
    if st.button("Salir"): st.session_state['logueado'] = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 CLIENTES", "📄 SEGUROS", "🔄 RENOVACIONES", "🚫 EX SEGUROS", "📊 ESTADÍSTICAS"])

# ---------------- TAB 1: CLIENTES (BOTÓN ESTILIZADO) ----------------
with tab1:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    c_btn, c_search = st.columns([1.3, 2.7])
    with c_btn:
        st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" target="_blank" class="reg-btn">+ REGISTRAR NUEVO CLIENTE</a>', unsafe_allow_html=True)
    with c_search: b_cli = st.text_input("🔍 Buscar cliente...", key="s_cli")
    df_cli = leer_datos("SELECT * FROM clientes ORDER BY id DESC")
    if b_cli: df_cli = df_cli[df_cli['nombre_completo'].str.contains(b_cli, case=False, na=False)]
    if not df_cli.empty:
        df_e_cli = st.data_editor(df_cli, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["id"])
        st.markdown('<div class="action-btn-container">', unsafe_allow_html=True)
        if st.button("💾", help="Guardar cambios", key="sv_cli"):
            sincronizar_borrados(df_e_cli, df_cli, "clientes"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- TAB 2: SEGUROS (ORDENAMIENTO ACTIVO) ----------------
with tab2:
    b_seg = st.text_input("🔍 Buscar seguros...", key="s_pol")
    df_seg = leer_datos('SELECT s.id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo, s.vigencia_hasta as "Hasta", s."premio_UYU", s."premio_USD" FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.id DESC')
    if b_seg: df_seg = df_seg[df_seg['Cliente'].str.contains(b_seg, case=False, na=False)]
    if not df_seg.empty:
        df_e_seg = st.data_editor(df_seg, use_container_width=True, hide_index=True, num_rows="dynamic", disabled=["Cliente"])
        st.markdown('<div class="action-btn-container">', unsafe_allow_html=True)
        if st.button("💾", help="Guardar cambios", key="sv_seg"):
            sincronizar_borrados(df_e_seg, df_seg, "seguros"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- TAB 3: RENOVACIONES (120 DÍAS ATRÁS) ----------------
with tab3:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    b_ren = st.text_input("🔍 Buscar para renovar...")
    df_ren = leer_datos('SELECT s.id, s.cliente_id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo, s.vigencia_hasta, s."premio_UYU", s."premio_USD", s.ejecutivo FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    if not df_ren.empty:
        hoy = date.today()
        df_ren['Vence_dt'] = pd.to_datetime(df_ren['vigencia_hasta']).dt.date
        mask = (df_ren['Vence_dt'] >= hoy - timedelta(days=120)) & (df_ren['Vence_dt'] <= hoy + timedelta(days=180))
        if b_ren: mask = mask & (df_ren['Cliente'].str.contains(b_ren, case=False, na=False))
        df_f = df_ren[mask].copy().sort_values("Vence_dt")
        df_f['Situación'] = df_f['Vence_dt'].apply(lambda x: f"⚠️ VENCIDO ({(hoy-x).days} días)" if x < hoy else f"⏳ Vence en {(x-hoy).days} días")

        df_e_ren = st.data_editor(df_f, use_container_width=True, hide_index=True,
            column_order=["Situación", "Cliente", "aseguradora", "ramo", "detalle_riesgo", "vigencia_hasta", "premio_UYU", "premio_USD"],
            column_config={"vigencia_hasta": st.column_config.DateColumn("Nueva Fecha"), "Situación": st.column_config.TextColumn("Situación")}, disabled=["Cliente", "Situación"])
        
        col_r1, col_r2, _ = st.columns([1, 1, 10])
        with col_r1:
            st.markdown('<div class="action-btn-container">', unsafe_allow_html=True)
            if st.button("💾", help="Confirmar Renovación", key="btn_ren_ok"):
                for _, r in df_e_ren.iterrows():
                    ejecutar_q('INSERT INTO seguros (cliente_id, aseguradora, ramo, detalle_riesgo, vigencia_hasta, "premio_UYU", "premio_USD", ejecutivo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', (r['cliente_id'], r['aseguradora'], r['ramo'], r['detalle_riesgo'], r['vigencia_hasta'], r['premio_UYU'], r['premio_USD'], r['ejecutivo']))
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_r2:
            st.markdown('<div class="action-btn-container no-renueva-btn">', unsafe_allow_html=True)
            if st.button("🚫", help="Marcar como NO RENUEVA", key="btn_no_ren"):
                for _, r in df_e_ren.iterrows():
                    ejecutar_q('INSERT INTO ex_seguros (cliente_id, aseguradora, ramo, detalle_riesgo, vigencia_hasta, "premio_UYU", "premio_USD", ejecutivo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', (r['cliente_id'], r['aseguradora'], r['ramo'], r['detalle_riesgo'], r['vigencia_hasta'], r['premio_UYU'], r['premio_USD'], r['ejecutivo']))
                    ejecutar_q('DELETE FROM seguros WHERE id = %s', (int(r['id']),))
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- TAB 4: EX SEGUROS (HISTÓRICO) ----------------
with tab4:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    df_ex = leer_datos('SELECT e.*, c.nombre_completo as "Cliente" FROM ex_seguros e JOIN clientes c ON e.cliente_id = c.id ORDER BY fecha_baja DESC')
    st.dataframe(df_ex, use_container_width=True, hide_index=True)

# ---------------- TAB 5: ESTADÍSTICAS ----------------
with tab5:
    df_st = leer_datos('SELECT aseguradora, "premio_UYU", "premio_USD" FROM seguros')
    if not df_st.empty:
        df_st['Total_USD'] = df_st['premio_USD'].fillna(0) + (df_st['premio_UYU'].fillna(0) / TC_USD)
        st.metric("Cartera Proyectada Total (USD)", f"U$S {df_st['Total_USD'].sum():,.0f}")
        st.plotly_chart(px.pie(df_st, names='aseguradora', values='Total_USD', title="Distribución por Compañía"), use_container_width=True)