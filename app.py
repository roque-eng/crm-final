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
    thead tr th { background-color: #d1d1d1 !important; color: #1a1a1a !important; font-weight: bold !important; }
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
    except Exception as e:
        return pd.DataFrame()

def ejecutar_query(query, params):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False

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

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    c1, c2, c4 = st.columns([1.6, 2, 0.4])
    with c1: st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" target="_blank" style="text-decoration:none; background-color:#333; color:white; padding:8px 16px; border-radius:5px;">+ REGISTRAR NUEVO CLIENTE</a>', unsafe_allow_html=True)
    with c2: busqueda_cli = st.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI", label_visibility="collapsed", key="s_cli")
    
    # Query limpia sin domicilio
    df_cli = leer_datos("SELECT id, nombre_completo, documento_identidad, celular, email FROM clientes ORDER BY id DESC")
    if busqueda_cli and not df_cli.empty:
        df_cli = df_cli[df_cli['nombre_completo'].str.contains(busqueda_cli, case=False, na=False) | df_cli['documento_identidad'].str.contains(busqueda_cli, na=False)]

    st.divider()
    if not df_cli.empty:
        df_edit_cli = st.data_editor(df_cli, use_container_width=True, hide_index=True, disabled=["id"])
        if st.button("💾 Guardar Cambios en Clientes"):
            for idx, row in df_edit_cli.iterrows():
                ejecutar_query("UPDATE clientes SET nombre_completo=%s, documento_identidad=%s, celular=%s, email=%s WHERE id=%s", 
                               (row['nombre_completo'], row['documento_identidad'], row['celular'], row['email'], row['id']))
            st.rerun()
    else: st.info("No se encontraron clientes.")

# ---------------- PESTAÑA 2: SEGUROS ----------------
with tab2:
    cp1, cp2, cp4 = st.columns([1.6, 2.5, 0.3])
    with cp1: st.subheader("📂 Gestión de Seguros")
    with cp2: busqueda_pol = st.text_input("🔍 Buscar seguros...", placeholder="Nombre, CI o Matrícula", label_visibility="collapsed", key="s_pol")
    
    df_all = leer_datos('SELECT s.id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo/Matrícula", s.vigencia_hasta as "Hasta", s."premio_UYU", s."premio_USD", s.archivo_url FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.vigencia_hasta DESC')
    if busqueda_pol and not df_all.empty:
         df_all = df_all[df_all['Cliente'].str.contains(busqueda_pol, case=False, na=False) | df_all['Riesgo/Matrícula'].str.contains(busqueda_pol, case=False, na=False)]

    st.divider()
    if not df_all.empty:
        today = pd.Timestamp(date.today())
        df_all['Hasta_dt'] = pd.to_datetime(df_all['Hasta'])
        
        st.markdown("### ✅ Seguros Vigentes")
        df_vig_edit = st.data_editor(df_all[df_all['Hasta_dt'] >= today].drop(columns=['Hasta_dt']), 
                                     use_container_width=True, hide_index=True, 
                                     disabled=["id", "Cliente", "archivo_url"], 
                                     column_config={"archivo_url": st.column_config.LinkColumn("Documento", display_text="📄 Ver")})
        
        if st.button("💾 Guardar Cambios en Seguros"):
            for idx, row in df_vig_edit.iterrows():
                ejecutar_query('UPDATE seguros SET aseguradora=%s, ramo=%s, detalle_riesgo=%s, "premio_UYU"=%s, "premio_USD"=%s, vigencia_hasta=%s WHERE id=%s', 
                               (row['aseguradora'], row['ramo'], row['Riesgo/Matrícula'], row['premio_UYU'], row['premio_USD'], row['Hasta'], row['id']))
            st.rerun()
        
        st.divider()
        st.markdown("### 📜 Historial")
        st.dataframe(df_all[df_all['Hasta_dt'] < today].drop(columns=['Hasta_dt', 'id']), use_container_width=True, hide_index=True)
    else: st.info("No se encontraron seguros cargados.")

# ---------------- PESTAÑA 3: RENOVACIONES ----------------
with tab3:
    st.header("🔄 Centro de Renovaciones")
    dias_v = st.slider("📅 Próximos vencimientos (días):", 15, 180, 60)
    
    df_ren = leer_datos('SELECT s.id, s.cliente_id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo", s.ejecutivo, s.corredor, s.agente, s.vigencia_hasta as "Vence_Viejo", s."premio_UYU", s."premio_USD", s.archivo_url FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    
    if not df_ren.empty:
        today_date = date.today()
        df_ren['Vence_Viejo_dt'] = pd.to_datetime(df_ren['Vence_Viejo']).dt.date
        mask = (df_ren['Vence_Viejo_dt'] >= today_date) & (df_ren['Vence_Viejo_dt'] <= today_date + timedelta(days=dias_v))
        df_ren_f = df_ren[mask].copy()
        
        if not df_ren_f.empty:
            df_ren_edit = st.data_editor(
                df_ren_f, use_container_width=True, hide_index=True,
                column_order=["Cliente", "aseguradora", "ramo", "Riesgo", "Vence_Viejo", "premio_UYU", "premio_USD", "archivo_url"],
                column_config={
                    "Vence_Viejo": st.column_config.DateColumn("Nueva Fecha Venc."),
                    "archivo_url": st.column_config.TextColumn("URL Nuevo Doc.")
                },
                disabled=["Cliente"]
            )
            if st.button("🚀 Confirmar Renovación"):
                for idx, row in df_ren_edit.iterrows():
                    ejecutar_query('INSERT INTO seguros (cliente_id, aseguradora, ramo, detalle_riesgo, vigencia_hasta, "premio_UYU", "premio_USD", archivo_url, ejecutivo, corredor, agente) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (row['cliente_id'], row['aseguradora'], row['ramo'], row['Riesgo'], row['Vence_Viejo'], row['premio_UYU'], row['premio_USD'], row['archivo_url'], row['ejecutivo'], row['corredor'], row['agente']))
                st.rerun()
        else: st.info("No hay vencimientos en este rango.")

# ---------------- PESTAÑA 4: ESTADÍSTICAS (ORDEN Y FILTROS CORREGIDOS) ----------------
with tab4:
    st.header("📊 Tablero de Proyecciones y Control")
    df_st = leer_datos('SELECT s.aseguradora, s.ramo, s.ejecutivo, s.agente, s.vigencia_hasta, s."premio_UYU", s."premio_USD" FROM seguros s')

    if not df_st.empty:
        df_st['vigencia_hasta'] = pd.to_datetime(df_st['vigencia_hasta'])
        df_st['Año'] = df_st['vigencia_hasta'].dt.year.astype(str)
        df_st['Mes'] = df_st['vigencia_hasta'].dt.month_name()
        df_st['Total_USD'] = df_st['premio_USD'].fillna(0) + (df_st['premio_UYU'].fillna(0) / TC_USD)

        # Filtros con Checkboxes y Ticks
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            with st.popover("📅 Años"):
                lista_anos = sorted(df_st['Año'].unique().tolist())
                all_anos = st.checkbox("Seleccionar Todos", value=True, key="all_anos")
                sel_ano = [a for a in lista_anos if st.checkbox(a, value=all_anos, key=f"a_{a}")]

        with col_f2:
            with st.popover("📆 Meses"):
                meses_orden = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                lista_meses = [m for m in meses_orden if m in df_st['Mes'].unique()]
                all_meses = st.checkbox("Seleccionar Todas", value=True, key="all_meses")
                sel_mes = [m for m in lista_meses if st.checkbox(m, value=all_meses, key=f"m_{m}")]

        with col_f3:
            # Corrección de TypeError: removemos None antes de ordenar
            list_eje = ["Todos"] + sorted([str(x) for x in df_st['ejecutivo'].unique() if x])
            sel_eje_st = st.selectbox("👤 Ejecutivo", list_eje)

        with col_f4:
            list_age = ["Todos"] + sorted([str(x) for x in df_st['agente'].unique() if x])
            sel_age_st = st.selectbox("🧑 Agente", list_age)

        # Aplicar filtros
        df_f = df_st[df_st['Año'].isin(sel_ano) & df_st['Mes'].isin(sel_mes)]
        if sel_eje_st != "Todos": df_f = df_f[df_f['ejecutivo'] == sel_eje_st]
        if sel_age_st != "Todos": df_f = df_f[df_f['agente'] == sel_age_st]

        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Cartera Proyectada", f"U$S {df_f['Total_USD'].sum():,.0f}".replace(",", "."))
        m2.metric("Pólizas", len(df_f))
        
        st.divider()
        # Gráficos en orden: 1. Aseguradoras, 2. Ramos
        fig_aseg = px.bar(df_f.groupby('aseguradora')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=False), 
                          x='aseguradora', y='Total_USD', title="Volumen por Aseguradora (USD)", color='aseguradora')
        st.plotly_chart(fig_aseg, use_container_width=True)

        fig_ramo = px.bar(df_f.groupby('ramo')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=False), 
                          x='ramo', y='Total_USD', title="Volumen por Ramo (USD)", color='ramo')
        st.plotly_chart(fig_ramo, use_container_width=True)
    else: st.info("Carga datos para ver estadísticas.")