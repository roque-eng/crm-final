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

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    c1, c2, c3, c4, c5 = st.columns([1.6, 2, 0.4, 0.4, 0.4])
    with c1: st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" target="_blank" class="btn-registro"><span class="plus-blue">+</span> REGISTRAR NUEVO CLIENTE</a>', unsafe_allow_html=True)
    with c2: busqueda_cli = st.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI", label_visibility="collapsed", key="s_cli")
    
    df_cli = leer_datos("SELECT id, nombre_completo, documento_identidad, celular, email FROM clientes ORDER BY id DESC")
    if busqueda_cli and not df_cli.empty:
        df_cli = df_cli[df_cli['nombre_completo'].str.contains(busqueda_cli, case=False, na=False) | df_cli['documento_identidad'].str.contains(busqueda_cli, na=False)]

    with c4: st.button("🔄", key="ref_cli")
    
    st.divider()
    if not df_cli.empty:
        df_edit_cli = st.data_editor(df_cli, use_container_width=True, hide_index=True, disabled=["id"])
        if st.button("💾 Guardar Cambios en Clientes"):
            for idx, row in df_edit_cli.iterrows():
                ejecutar_query("UPDATE clientes SET nombre_completo=%s, documento_identidad=%s, celular=%s, email=%s WHERE id=%s", 
                               (row['nombre_completo'], row['documento_identidad'], row['celular'], row['email'], row['id']))
            st.rerun()

# ---------------- PESTAÑA 2: SEGUROS ----------------
with tab2:
    cp1, cp2, cp3, cp4, cp5 = st.columns([1.6, 2.5, 0.3, 0.3, 0.3])
    with cp1: st.subheader("📂 Gestión de Seguros")
    with cp2: busqueda_pol = st.text_input("🔍 Buscar...", placeholder="Nombre, CI o Matrícula", label_visibility="collapsed", key="s_pol")
    
    df_all = leer_datos('SELECT s.id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo/Matrícula", s.vigencia_hasta as "Hasta", s."premio_UYU", s."premio_USD", s.archivo_url FROM seguros s JOIN clientes c ON s.cliente_id = c.id ORDER BY s.vigencia_hasta DESC')
    if busqueda_pol and not df_all.empty:
         df_all = df_all[df_all['Cliente'].str.contains(busqueda_pol, case=False, na=False) | df_all['Riesgo/Matrícula'].str.contains(busqueda_pol, case=False, na=False)]

    with cp4: st.button("🔄", key="ref_pol")

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

# ---------------- PESTAÑA 3: RENOVACIONES ----------------
with tab3:
    cr1, cr2, cr3, cr4 = st.columns([3, 5, 0.4, 0.4])
    with cr1: st.header("🔄 Renovaciones")
    with cr2: dias_v = st.slider("📅 Próximos vencimientos (días):", 15, 180, 60)
    
    df_ren = leer_datos('SELECT s.id, s.cliente_id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo", s.ejecutivo, s.corredor, s.agente, s.vigencia_hasta as "Vence_Viejo", s."premio_UYU", s."premio_USD", s.archivo_url FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    
    if not df_ren.empty:
        df_ren['Vence_Viejo_dt'] = pd.to_datetime(df_ren['Vence_Viejo']).dt.date
        mask = (df_ren['Vence_Viejo_dt'] >= date.today()) & (df_ren['Vence_Viejo_dt'] <= date.today() + timedelta(days=dias_v))
        df_ren_f = df_ren[mask].copy()
        
        st.dataframe(df_ren_f.drop(columns=['Vence_Viejo_dt', 'id', 'cliente_id']), use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 4: ESTADÍSTICAS (MEJORADA CON TICKS) ----------------
with tab4:
    st.header("📊 Tablero de Proyecciones y Control")
    
    df_st = leer_datos('SELECT s.aseguradora, s.ramo, s.ejecutivo, s.agente, s.vigencia_hasta, s."premio_UYU", s."premio_USD" FROM seguros s')

    if not df_st.empty:
        df_st['vigencia_hasta'] = pd.to_datetime(df_st['vigencia_hasta'])
        df_st['Año'] = df_st['vigencia_hasta'].dt.year.astype(str)
        df_st['Mes'] = df_st['vigencia_hasta'].dt.month_name()
        df_st['Total_USD'] = df_st['premio_USD'].fillna(0) + (df_st['premio_UYU'].fillna(0) / TC_USD)

        # --- FILTROS CON TICKS (ST.POPOVER PARA NO OCUPAR TANTO ESPACIO) ---
        c_f1, c_f2, c_f3, c_f4 = st.columns(4)
        
        with c_f1:
            with st.popover("📅 Años"):
                lista_anos = sorted(df_st['Año'].unique().tolist())
                all_anos = st.checkbox("Seleccionar Todos", value=True, key="chk_all_anos")
                sel_ano = [a for a in lista_anos if st.checkbox(a, value=all_anos, key=f"ano_{a}")]

        with c_f2:
            with st.popover("📆 Meses"):
                meses_orden = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                lista_meses = [m for m in meses_orden if m in df_st['Mes'].unique()]
                all_meses = st.checkbox("Seleccionar Todos", value=True, key="chk_all_meses")
                sel_mes = [m for m in lista_meses if st.checkbox(m, value=all_meses, key=f"mes_{m}")]

        with c_f3: sel_eje_st = st.selectbox("👤 Ejecutivo", ["Todos"] + sorted(df_st['ejecutivo'].unique().tolist()))
        with c_f4: sel_age_st = st.selectbox("🧑 Agente", ["Todos"] + sorted(df_st['agente'].unique().tolist()))

        # Aplicar filtros
        df_f = df_st[df_st['Año'].isin(sel_ano) & df_st['Mes'].isin(sel_mes)]
        if sel_eje_st != "Todos": df_f = df_f[df_f['ejecutivo'] == sel_eje_st]
        if sel_age_st != "Todos": df_f = df_f[df_f['agente'] == sel_age_st]

        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Cartera Proyectada", f"U$S {df_f['Total_USD'].sum():, .0f}".replace(",", "."))
        m2.metric("Cant. Seguros", len(df_f))
        
        st.divider()
        # Gráficos de Barras (Aseguradoras primero)
        fig_aseg = px.bar(df_f.groupby('aseguradora')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=False), 
                          x='aseguradora', y='Total_USD', title="Volumen por Aseguradora", color='aseguradora')
        st.plotly_chart(fig_aseg, use_container_width=True)

        fig_ramo = px.bar(df_f.groupby('ramo')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=False), 
                          x='ramo', y='Total_USD', title="Volumen por Ramo", color='ramo')
        st.plotly_chart(fig_ramo, use_container_width=True)

    else: st.info("No hay datos para las estadísticas.")