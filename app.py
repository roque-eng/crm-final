import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import date, timedelta
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS REFINADOS ---
st.markdown("""
    <style>
    .left-title { font-size: 32px !important; font-weight: bold; text-align: left; margin-bottom: 20px; color: #31333F; }
    thead tr th { background-color: #d1d1d1 !important; color: #1a1a1a !important; font-weight: bold !important; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    .user-box { display: flex; align-items: center; justify-content: flex-end; gap: 15px; margin-top: 5px; }
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
    except Exception: return False

TC_USD = 40.5 

# --- ENCABEZADO ALINEADO (LOGO JUNTO A SALIR) ---
col_tit, col_user = st.columns([7, 3])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_user:
    st.markdown(f"""
        <div class="user-box">
            <span style="font-weight: bold; font-size: 16px;">👤 {st.session_state['usuario_actual']}</span>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Salir", key="btn_salir"): 
        st.session_state['logueado'] = False
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "📄 SEGUROS", "🔄 RENOVACIONES", "📊 ESTADÍSTICAS"])

# ... (Tablas de Clientes y Seguros se mantienen igual, usando SELECT id, nombre_completo, etc.) ...

# ---------------- PESTAÑA 4: ESTADÍSTICAS (TIEMPO Y GRÁFICOS CONECTADOS) ----------------
with tab4:
    st.header("📊 Tablero de Proyecciones y Control")
    df_st = leer_datos('SELECT s.aseguradora, s.ramo, s.ejecutivo, s.agente, s.vigencia_hasta, s."premio_UYU", s."premio_USD" FROM seguros s')

    if not df_st.empty:
        df_st['vigencia_hasta'] = pd.to_datetime(df_st['vigencia_hasta'])
        df_st['Año'] = df_st['vigencia_hasta'].dt.year.astype(str)
        df_st['Mes'] = df_st['vigencia_hasta'].dt.month_name()
        df_st['Total_USD'] = df_st['premio_USD'].fillna(0) + (df_st['premio_UYU'].fillna(0) / TC_USD)

        # --- FILTROS ALINEADOS (ROLLER DE TIEMPO) ---
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            lista_anos = sorted(df_st['Año'].unique().tolist())
            sel_ano = st.multiselect("⏳ Años (Tiempo)", lista_anos, default=lista_anos)

        with col_f2:
            meses_orden = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            lista_meses = [m for m in meses_orden if m in df_st['Mes'].unique()]
            sel_mes = st.multiselect("⏳ Meses (Tiempo)", lista_meses, default=lista_meses)

        with col_f3:
            list_eje = ["Todos"] + sorted([str(x) for x in df_st['ejecutivo'].unique() if x])
            sel_eje_st = st.selectbox("👤 Ejecutivo", list_eje)

        with col_f4:
            list_age = ["Todos"] + sorted([str(x) for x in df_st['agente'].unique() if x])
            sel_age_st = st.selectbox("🧑 Agente", list_age)

        # Aplicar filtros base
        df_f = df_st[df_st['Año'].isin(sel_ano) & df_st['Mes'].isin(sel_mes)]
        if sel_eje_st != "Todos": df_f = df_f[df_f['ejecutivo'] == sel_eje_st]
        if sel_age_st != "Todos": df_f = df_f[df_f['agente'] == sel_age_st]

        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Cartera Proyectada", f"U$S {df_f['Total_USD'].sum():,.0f}".replace(",", "."))
        m2.metric("Pólizas", len(df_f))
        
        st.divider()
        
        # --- GRÁFICOS CONECTADOS ---
        # 1. Gráfico de Aseguradoras
        df_aseg = df_f.groupby('aseguradora')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=False)
        fig_aseg = px.bar(df_aseg, x='aseguradora', y='Total_USD', title="Volumen por Aseguradora (USD)", color='aseguradora')
        st.plotly_chart(fig_aseg, use_container_width=True)

        # Filtro de conexión para Ramos
        st.markdown("### 🎯 Detalle por Ramo")
        aseguradoras_disponibles = sorted(df_f['aseguradora'].unique().tolist())
        target_aseg = st.selectbox("Seleccione Aseguradora para filtrar ramos:", ["Todas"] + aseguradoras_disponibles)

        df_ramo_plot = df_f.copy()
        if target_aseg != "Todas":
            df_ramo_plot = df_ramo_plot[df_ramo_plot['aseguradora'] == target_aseg]

        fig_ramo = px.bar(df_ramo_plot.groupby('ramo')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=False), 
                          x='ramo', y='Total_USD', title=f"Ramos en {target_aseg if target_aseg != 'Todas' else 'General'}", color='ramo')
        st.plotly_chart(fig_ramo, use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")