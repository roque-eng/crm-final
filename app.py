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

# ... (Pestañas 1 y 2 se mantienen iguales a la versión anterior) ...

# ---------------- PESTAÑA 3: RENOVACIONES (CON CARGA DE ARCHIVO) ----------------
with tab3:
    st.header("🔄 Centro de Renovaciones")
    # Simulación de punto 3: Carga de archivo
    with st.expander("📁 Subir nueva póliza firmada"):
        archivo_nuevo = st.file_uploader("Selecciona el PDF de la renovación", type=["pdf", "jpg", "png"])
        if archivo_nuevo:
            st.success(f"Archivo '{archivo_nuevo.name}' listo para procesar.")

    dias_v = st.slider("📅 Próximos vencimientos (días):", 15, 180, 60)
    df_ren = leer_datos('SELECT s.*, c.nombre_completo as "Cliente" FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    
    # ... (Resto de la lógica de filtros y tabla editable de Renovaciones) ...

# ---------------- PESTAÑA 4: ESTADÍSTICAS DINÁMICAS (PUNTO 4) ----------------
with tab4:
    st.header("📊 Tablero de Proyecciones y Control")
    
    # Carga de datos base
    df_st = leer_datos('''
        SELECT s.aseguradora, s.ramo, s.ejecutivo, s.agente, 
               s.vigencia_hasta, s."premio_UYU", s."premio_USD" 
        FROM seguros s
    ''')

    if not df_st.empty:
        # Preparación de fechas y moneda
        df_st['vigencia_hasta'] = pd.to_datetime(df_st['vigencia_hasta'])
        df_st['Año'] = df_st['vigencia_hasta'].dt.year
        df_st['Mes'] = df_st['vigencia_hasta'].dt.month_name()
        df_st['Total_USD'] = df_st['premio_USD'].fillna(0) + (df_st['premio_UYU'].fillna(0) / TC_USD)

        # --- FILTROS SUPERIORES ---
        filt1, filt2, filt3, filt4 = st.columns(4)
        
        with filt1:
            lista_años = sorted(df_st['Año'].unique().tolist())
            sel_año = st.multiselect("📅 Año de Vencimiento", lista_años, default=lista_años)
        
        with filt2:
            meses_orden = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            lista_meses = [m for m in meses_orden if m in df_st['Mes'].unique()]
            sel_mes = st.multiselect("📆 Mes de Vencimiento", lista_meses, default=lista_meses)

        with filt3:
            lista_eje = ["Todos"] + sorted(df_st['ejecutivo'].unique().astype(str).tolist())
            sel_eje_st = st.selectbox("👤 Filtrar Ejecutivo", lista_eje)

        with filt4:
            lista_age = ["Todos"] + sorted(df_st['agente'].unique().astype(str).tolist())
            sel_age_st = st.selectbox("🧑 Filtrar Agente", lista_age)

        # Aplicar filtros
        df_filtrado = df_st[df_st['Año'].isin(sel_año) & df_st['Mes'].isin(sel_mes)]
        if sel_eje_st != "Todos": df_filtrado = df_filtrado[df_filtrado['ejecutivo'] == sel_eje_st]
        if sel_age_st != "Todos": df_filtrado = df_filtrado[df_filtrado['agente'] == sel_age_st]

        st.divider()

        # Métricas Generales
        m1, m2, m3 = st.columns(3)
        total_cartera = df_filtrado['Total_USD'].sum()
        m1.metric("Cartera Proyectada (USD)", f"U$S {total_cartera:,.0f}".replace(",", "."))
        m2.metric("Cant. de Seguros", len(df_filtrado))
        m3.metric("Promedio por Póliza", f"U$S {total_cartera/len(df_filtrado) if len(df_filtrado)>0 else 0:,.0f}".replace(",", "."))

        st.divider()

        # --- GRÁFICOS CONECTADOS ---
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            # Gráfico 1: Aseguradoras (Primero)
            fig_aseg = px.pie(df_filtrado, names='aseguradora', values='Total_USD', 
                              title="Distribución por Aseguradora", hole=0.4,
                              color_discrete_sequence=px.colors.qualitative.Pastel)
            
            # Capturar selección (Streamlit detecta si haces clic en el gráfico)
            selected_aseg = st.selectbox("🎯 Haz foco en una Aseguradora:", ["Todas"] + sorted(df_filtrado['aseguradora'].unique().tolist()))
            st.plotly_chart(fig_aseg, use_container_width=True)

        with col_g2:
            # Filtrar el segundo gráfico basado en el primero
            df_ramo = df_filtrado.copy()
            if selected_aseg != "Todas":
                df_ramo = df_ramo[df_ramo['aseguradora'] == selected_aseg]
                titulo_ramo = f"Ramos en {selected_aseg}"
            else:
                titulo_ramo = "Distribución por Ramos (General)"

            fig_ramo = px.bar(df_ramo.groupby('ramo')['Total_USD'].sum().reset_index(), 
                              x='ramo', y='Total_USD', title=titulo_ramo,
                              color='ramo', text_auto='.2s')
            st.plotly_chart(fig_ramo, use_container_width=True)

    else:
        st.info("No hay datos suficientes para generar estadísticas.")