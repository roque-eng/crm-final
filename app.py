import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import date
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .left-title { font-size: 38px !important; font-weight: bold; text-align: left; margin-top: 10px; margin-bottom: 25px; color: #31333F; }
    .block-container { padding-top: 2.5rem !important; }
    
    /* Encabezados de Tablas más oscuros */
    thead tr th {
        background-color: #e0e0e0 !important;
        color: #333333 !important;
        font-weight: bold !important;
    }
    
    /* Alineación vertical centrada */
    [data-testid="stHorizontalBlock"] { align-items: center; }

    /* Estilo del botón registro */
    .btn-registro {
        background-color: #333333 !important;
        color: white !important;
        padding: 10px 20px;
        border-radius: 5px;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        border: 1px solid #555;
    }
    .plus-blue { color: #007bff; font-weight: bold; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>☁️ CRM Grupo EDF</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
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
# ⚙️ FUNCIONES BASE
# ==========================================
def leer_datos(query):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e: return pd.DataFrame()

def to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Datos')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

TC_USD = 40.5 

# --- ENCABEZADO ---
col_tit, col_user = st.columns([7, 3])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_user:
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    c_t, c_b = st.columns([2, 1])
    c_t.write(f"👤 **{st.session_state['usuario_actual']}**")
    if c_b.button("Salir"): st.session_state['logueado'] = False; st.rerun()

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS Y HISTORIAL", "🔔 VENCIMIENTOS", "📊 ESTADÍSTICAS"])

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    col_reg, col_bus, col_ref, col_exc = st.columns([1.5, 2, 0.6, 0.6])
    with col_reg: st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" target="_blank" class="btn-registro"><span class="plus-blue">+</span> REGISTRAR NUEVO CLIENTE</a>', unsafe_allow_html=True)
    with col_bus: busqueda_cli = st.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI", label_visibility="collapsed", key="search_cli")
    with col_ref: 
        if st.button("🔄 Refrescar", key="ref_cli"): st.rerun()
    
    sql_cli = "SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes"
    if busqueda_cli: sql_cli += f" WHERE nombre_completo ILIKE '%%{busqueda_cli}%%' OR documento_identidad ILIKE '%%{busqueda_cli}%%'"
    df_cli = leer_datos(sql_cli + " ORDER BY id DESC")
    
    with col_exc:
        st.download_button(label="📥 Excel", data=to_excel(df_cli), file_name=f'clientes_edf_{date.today()}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    st.divider()
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 2: PÓLIZAS ----------------
with tab2:
    col_pol_h, col_pol_bus, col_pol_ref, col_pol_exc = st.columns([1.5, 2, 0.6, 0.6])
    with col_pol_h: st.subheader("📂 Gestión de Pólizas")
    with col_pol_bus: busqueda_pol = st.text_input("🔍 Buscar póliza...", placeholder="Nombre, CI o Matrícula", label_visibility="collapsed", key="search_pol")
    with col_pol_ref:
        if st.button("🔄 Refrescar", key="ref_pol"): st.rerun()

    sql_base = """
        SELECT c.nombre_completo as "Cliente", c.document_identidad as "CI", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo/Matrícula",
               s.vigencia_hasta as "Hasta", s."premio_UYU", s."premio_USD", s.archivo_url as "link_doc"
        FROM seguros s JOIN clientes c ON s.cliente_id = c.id
    """
    if busqueda_pol: sql_base += f" WHERE c.nombre_completo ILIKE '%%{busqueda_pol}%%' OR c.documento_identidad ILIKE '%%{busqueda_pol}%%' OR s.detalle_riesgo ILIKE '%%{busqueda_pol}%%'"
    df_all = leer_datos(sql_base + " ORDER BY s.vigencia_hasta DESC")

    with col_pol_exc:
        st.download_button(label="📥 Excel", data=to_excel(df_all.drop(columns=['link_doc'])), file_name=f'polizas_edf_{date.today()}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    if not df_all.empty:
        today = pd.Timestamp(date.today())
        df_all['Hasta_dt'] = pd.to_datetime(df_all['Hasta'])
        df_vig = df_all[df_all['Hasta_dt'] >= today].drop(columns=['Hasta_dt'])
        df_his = df_all[df_all['Hasta_dt'] < today].drop(columns=['Hasta_dt'])

        st.markdown("### ✅ Pólizas Vigentes")
        st.dataframe(df_vig, use_container_width=True, hide_index=True, column_config={"link_doc": st.column_config.LinkColumn("Documento", display_text="📄 Ver"), "premio_UYU": st.column_config.NumberColumn("Premio $", format="$ %.,d"), "premio_USD": st.column_config.NumberColumn("Premio U$S", format="U$S %.,d")})
        st.divider()
        st.markdown("### 📜 Historial")
        st.dataframe(df_his, use_container_width=True, hide_index=True, column_config={"link_doc": st.column_config.LinkColumn("Documento", display_text="📄 Ver"), "premio_UYU": st.column_config.NumberColumn("Premio $", format="$ %.,d"), "premio_USD": st.column_config.NumberColumn("Premio U$S", format="U$S %.,d")})

# ---------------- PESTAÑA 3: VENCIMIENTOS ----------------
with tab3:
    col_v_h, col_v_exc = st.columns([8, 2])
    with col_v_h: st.header("🔔 Monitor de Vencimientos")
    dias_v = st.slider("📅 Días próximos:", 15, 180, 30, 15)
    sql_v = f'SELECT c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo, TO_CHAR(s.vigencia_hasta, "DD/MM/YYYY") as "Vence" FROM seguros s JOIN clientes c ON s.cliente_id = c.id WHERE s.vigencia_hasta BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL "{dias_v} days") ORDER BY s.vigencia_hasta ASC'
    df_v = leer_datos(sql_v)
    with col_v_exc:
        st.download_button(label="📥 Exportar Vencimientos", data=to_excel(df_v), file_name=f'vencimientos_{date.today()}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
    st.dataframe(df_v, use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 4: ESTADÍSTICAS ----------------
with tab4:
    st.subheader(f"📊 Análisis de Cartera (TC: ${TC_USD})")
    df_stats = leer_datos('SELECT aseguradora, ramo, "premio_UYU", "premio_USD" FROM seguros')
    if not df_stats.empty:
        df_stats['total_usd'] = df_stats['premio_USD'].fillna(0) + (df_stats['premio_UYU'].fillna(0) / TC_USD)
        st.metric("Cartera Total Estimada", f"U$S {df_stats['total_usd'].sum():,.0f}".replace(",", "."))
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_r = px.bar(df_stats.groupby('ramo')['total_usd'].sum().reset_index(), x='ramo', y='total_usd', title="USD por Ramo", color='ramo', text_auto='.s')
            fig_r.update_traces(hovertemplate='Total: U$S %{y:,.0f}')
            st.plotly_chart(fig_r, use_container_width=True)
        with col_g2:
            fig_a = px.bar(df_stats.groupby('aseguradora')['total_usd'].sum().reset_index(), x='aseguradora', y='total_usd', title="USD por Aseguradora", color='aseguradora', text_auto='.s')
            fig_a.update_traces(hovertemplate='Total: U$S %{y:,.0f}')
            st.plotly_chart(fig_a, use_container_width=True)