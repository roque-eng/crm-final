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
# ⚙️ FUNCIONES BASE
# ==========================================
def leer_datos(query):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception: return pd.DataFrame()

def to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Datos')
    writer.close()
    return output.getvalue()

def fmt_moneda(valor, prefijo="$"):
    if pd.isna(valor) or valor == 0: return ""
    return f"{prefijo} {int(valor):,}".replace(",", ".")

TC_USD = 40.5 

# --- ENCABEZADO ---
col_tit, col_user = st.columns([7, 3])
with col_tit: st.markdown('<p class="left-title">Gestión de Cartera - Grupo EDF</p>', unsafe_allow_html=True)
with col_user:
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    c_t, c_b = st.columns([2, 1])
    c_t.write(f"👤 **{st.session_state['usuario_actual']}**")
    if c_b.button("Salir"): st.session_state['logueado'] = False; st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["👥 CLIENTES", "📄 PÓLIZAS E HISTORIAL", "🔔 VENCIMIENTOS", "📊 ESTADÍSTICAS"])

# ---------------- PESTAÑA 1: CLIENTES ----------------
with tab1:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.6, 2, 0.4, 0.4, 0.4])
    with c1: st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSc99wmgzTwNKGpQuzKQvaZ5Z8Qa17BqELGto5Vco96yFXYgfQ/viewform" target="_blank" class="btn-registro"><span class="plus-blue">+</span> REGISTRAR NUEVO CLIENTE</a>', unsafe_allow_html=True)
    with c2: busqueda_cli = st.text_input("🔍 Buscar cliente...", placeholder="Nombre o CI", label_visibility="collapsed", key="s_cli")
    with c4: 
        if st.button("🔄", help="Refrescar", key="ref_cli"): st.rerun()
    
    sql_cli = "SELECT id, nombre_completo, documento_identidad, celular, email, domicilio FROM clientes"
    if busqueda_cli: sql_cli += f" WHERE nombre_completo ILIKE '%%{busqueda_cli}%%' OR documento_identidad ILIKE '%%{busqueda_cli}%%'"
    df_cli = leer_datos(sql_cli + " ORDER BY id DESC")
    
    with c5: 
        if not df_cli.empty: st.download_button(label="📊", data=to_excel(df_cli), file_name=f'clientes_{date.today()}.xlsx')
    st.divider()
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

# ---------------- PESTAÑA 2: PÓLIZAS (ALINEACIÓN DERECHA) ----------------
with tab2:
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    cp1, cp2, cp3, cp4, cp5 = st.columns([1.6, 2, 0.4, 0.4, 0.4])
    with cp1: st.subheader("📂 Gestión de Pólizas")
    with cp2: busqueda_pol = st.text_input("🔍 Buscar...", placeholder="Nombre, CI o Matrícula", label_visibility="collapsed", key="s_pol")
    
    sql_pol = 'SELECT c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo/Matrícula", s.vigencia_hasta as "Hasta", s."premio_UYU", s."premio_USD", s.archivo_url FROM seguros s JOIN clientes c ON s.cliente_id = c.id'
    if busqueda_pol: sql_pol += f" WHERE c.nombre_completo ILIKE '%%{busqueda_pol}%%' OR c.documento_identidad ILIKE '%%{busqueda_pol}%%' OR s.detalle_riesgo ILIKE '%%{busqueda_pol}%%'"
    df_all = leer_datos(sql_pol + " ORDER BY s.vigencia_hasta DESC")

    with cp4: 
        if st.button("🔄", key="ref_pol"): st.rerun()
    with cp5