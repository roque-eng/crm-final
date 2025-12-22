import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import date, timedelta
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .left-title { font-size: 38px !important; font-weight: bold; text-align: left; margin-top: 10px; margin-bottom: 25px; color: #31333F; }
    .block-container { padding-top: 2.5rem !important; }
    thead tr th { background-color: #d1d1d1 !important; color: #1a1a1a !important; font-weight: bold !important; }
    [data-testid="stHorizontalBlock"] { align-items: center; }
    .btn-registro {
        background-color: #333333 !important; color: white !important;
        padding: 8px 16px; border-radius: 5px; text-decoration: none;
        display: inline-block; font-size: 14px; border: 1px solid #444;
    }
    .plus-blue { color: #007bff; font-weight: bold; font-size: 18px; margin-right: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025"}

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
        st.error(f"Error: {e}")
        return False

def to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Datos')
    writer.close()
    return output.getvalue()

TC_USD = 40.5 

# --- ENCABEZADO ---
col_tit, col_user = st.columns([7, 3])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_user:
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    c_t, c_b = st.columns([2, 1])
    c_t.write(f"👤 **{st.session_state['usuario_actual']}**")
    if c_b.button("Salir"): st.session_state['logueado'] = False; st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "📄 SEGUROS", "🔄 RENOVACIONES", "📊 ESTADÍSTICAS"])

# ---------------- PESTAÑA 1: CLIENTES (EDITABLE) ----------------
with tab1:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.6, 2, 0.4, 0.4, 0.4])
    with c1: st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" target="_blank" class="btn-registro"><span class="plus-blue">+</span> REGISTRAR NUEVO CLIENTE</a>', unsafe_allow_html=True)
    with c2: busqueda_cli = st.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI", label_visibility="collapsed", key="s_cli")
    
    df_cli = leer_datos("SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes ORDER BY id DESC")
    if busqueda_cli:
        df_cli = df_cli[df_cli['nombre_completo'].str.contains(busqueda_cli, case=False, na=False) | df_cli['documento_identidad'].str.contains(busqueda_cli, na=False)]

    with c4: 
        if st.button("🔄", key="ref_cli"): st.rerun()
    with c5: 
        if not df_cli.empty: st.download_button(label="📊", data=to_excel(df_cli), file_name='clientes.xlsx')
    
    st.divider()
    if not df_cli.empty:
        df_edit_cli = st.data_editor(df_cli, use_container_width=True, hide_index=True, disabled=["id"])
        if st.button("💾 Guardar Cambios Clientes"):
            for idx, row in df_edit_cli.iterrows():
                ejecutar_query("UPDATE clientes SET nombre_completo=%s, celular=%s, email=%s, domicilio=%s WHERE id=%s", (row['nombre_completo'], row['celular'], row['email'], row['domicilio'], row['id']))
            st.rerun()

# ---------------- PESTAÑA 2: SEGUROS ----------------
with tab2:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    cp1, cp2, cp3, cp4, cp5 = st.columns([1.6, 2.5, 0.3, 0.3, 0.3])
    with cp1: st.subheader("📂 Gestión de Seguros")
    with cp2: busqueda_pol = st.text_input("🔍 Buscar...", placeholder="Nombre, CI o Matrícula", label_visibility="collapsed", key="s_pol")
    
    df_all = leer_datos('SELECT s.id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo/Matrícula", s.vigencia_hasta as "Hasta", s."premio_UYU", s."premio_USD", s.archivo_url FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.vigencia_hasta DESC')
    
    with cp4: 
        if st.button("🔄", key="ref_pol"): st.rerun()
    with cp5:
        if not df_all.empty: st.download_button(label="📊", data=to_excel(df_all), file_name='seguros.xlsx')

    st.divider()
    if not df_all.empty:
        today = pd.Timestamp(date.today())
        df_all['Hasta_dt'] = pd.to_datetime(df_all['Hasta'])
        
        st.markdown("### ✅ Seguros Vigentes")
        st.dataframe(df_all[df_all['Hasta_dt'] >= today].drop(columns=['Hasta_dt', 'id']), use_container_width=True, hide_index=True, 
                     column_config={"archivo_url": st.column_config.LinkColumn("Documento", display_text="📄 Ver")})
        
        st.divider()
        st.markdown("### 📜 Historial")
        st.dataframe(df_all[df_all['Hasta_dt'] < today].drop(columns=['Hasta_dt', 'id']), use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 3: RENOVACIONES (CENTRO DE OPERACIONES) ----------------
with tab3:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    cr1, cr2, cr3, cr4 = st.columns([3, 5, 0.4, 0.4])
    with cr1: st.header("🔄 Renovaciones")
    with cr2: dias_v = st.slider("📅 Próximos vencimientos (días):", 15, 180, 60)
    with cr3: 
        if st.button("🔄", key="ref_ren"): st.rerun()

    # Query completa con campos ocultos para procesar la renovación
    df_ren = leer_datos('SELECT s.id, s.cliente_id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo", s.ejecutivo, s.corredor, s.agente, s.vigencia_hasta as "Vence_Viejo", s."premio_UYU", s."premio_USD", s.archivo_url FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    
    st.divider()
    # Filtros (Ejecutivo, Corredor y Agente ocultos de la tabla pero vivos aquí)
    f1, f2, f3, f4, f5 = st.columns(5)
    def clean_list(df, col): return ["Todos"] + sorted([str(x) for x in df[col].unique() if x])
    
    sel_eje = f1.selectbox("👤 Ejecutivo", clean_list(df_ren, "ejecutivo"))
    sel_ase = f2.selectbox("🏢 Aseguradora", clean_list(df_ren, "aseguradora"))
    sel_ram = f3.selectbox("🛡️ Ramo", clean_list(df_ren, "ramo"))
    sel_cor = f4.selectbox("💼 Corredor", clean_list(df_ren, "corredor"))
    sel_age = f5.selectbox("🧑 Agente", clean_list(df_ren, "agente"))

    if not df_ren.empty:
        today_date = date.today()
        df_ren['Vence_Viejo'] = pd.to_datetime(df_ren['Vence_Viejo']).dt.date
        mask = (df_ren['Vence_Viejo'] >= today_date) & (df_ren['Vence_Viejo'] <= today_date + timedelta(days=dias_v))
        df_ren_f = df_ren[mask].copy()

        if sel_eje != "Todos": df_ren_f = df_ren_f[df_ren_f["ejecutivo"] == sel_eje]
        if sel_ase != "Todos": df_ren_f = df_ren_f[df_ren_f["aseguradora"] == sel_ase]
        if sel_ram != "Todos": df_ren_f = df_ren_f[df_ren_f["ramo"] == sel_ram]
        if sel_cor != "Todos": df_ren_f = df_ren_f[df_ren_f["corredor"] == sel_cor]
        if sel_age != "Todos": df_ren_f = df_ren_f[df_ren_f["agente"] == sel_age]

        st.warning("👉 Modifica los datos de la renovación abajo y haz clic en 'Confirmar Nueva Póliza'.")
        
        # TABLA EDITABLE: Ocultamos los filtros y mostramos Premios y Doc
        df_ren_edit = st.data_editor(
            df_ren_f, 
            use_container_width=True, 
            hide_index=True,
            column_order=["Cliente", "aseguradora", "ramo", "Riesgo", "Vence_Viejo", "premio_UYU", "premio_USD", "archivo_url"],
            column_config={
                "Vence_Viejo": st.column_config.DateColumn("Nueva Vigencia Hasta", format="DD/MM/YYYY"),
                "premio_UYU": st.column_config.NumberColumn("Nuevo Premio $"),
                "premio_USD": st.column_config.NumberColumn("Nuevo Premio U$S"),
                "archivo_url": st.column_config.TextColumn("URL Nuevo Documento")
            },
            disabled=["Cliente"]
        )

        if st.button("🚀 Confirmar Renovación (Crea nueva póliza)"):
            for idx, row in df_ren_edit.iterrows():
                orig = df_ren_f.loc[idx]
                # Si algo cambió, insertamos una NUEVA fila
                if row['premio_UYU'] != orig['premio_UYU'] or row['Vence_Viejo'] != orig['Vence_Viejo'] or row['archivo_url'] != orig['archivo_url']:
                    ejecutar_query(
                        'INSERT INTO seguros (cliente_id, aseguradora, ramo, detalle_riesgo, vigencia_hasta, "premio_UYU", "premio_USD", archivo_url, ejecutivo, corredor, agente) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (row['cliente_id'], row['aseguradora'], row['ramo'], row['Riesgo'], row['Vence_Viejo'], row['premio_UYU'], row['premio_USD'], row['archivo_url'], row['ejecutivo'], row['corredor'], row['agente'])
                    )
            st.success("✅ Renovación procesada. La póliza anterior ahora es Historial y la nueva está Vigente.")
            st.rerun()

# ---------------- PESTAÑA 4: ESTADÍSTICAS ----------------
with tab4:
    st.subheader(f"📊 Análisis de Cartera (TC: ${TC_USD})")
    df_st = leer_datos('SELECT aseguradora, ramo, "premio_UYU", "premio_USD" FROM seguros')
    if not df_st.empty:
        df_st['total_usd'] = df_st['premio_USD'].fillna(0) + (df_st['premio_UYU'].fillna(0) / TC_USD)
        st.metric("Cartera Total Estimada", f"U$S {int(df_st['total_usd'].sum()):,}".replace(",", "."))
        g1, g2 = st.columns(2)
        with g1:
            fig_r = px.bar(df_st.groupby('ramo')['total_usd'].sum().reset_index(), x='ramo', y='total_usd', title="USD por Ramo", color='ramo')
            st.plotly_chart(fig_r, use_container_width=True)
        with g2:
            fig_a = px.bar(df_st.groupby('aseguradora')['total_usd'].sum().reset_index(), x='aseguradora', y='total_usd', title="USD por Aseguradora", color='aseguradora')
            st.plotly_chart(fig_a, use_container_width=True)