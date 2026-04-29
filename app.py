import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# ⚙️ CONFIGURACIÓN DE PERFILES POR USUARIO
# ==========================================
PERFILES_DEFAULTS = {
    "RDF": ["Asegurado (Nombre/Razón Social)", "Documento de Identidad (Rut/Cédula/Otros)", "Ramo", "Aseguradora", "Inicio de Vigencia", "Fin de Vigencia", "Premio_Total_USD", "Adjunto (póliza)"],
    "JOE": ["Asegurado (Nombre/Razón Social)", "Detalle (Matrícula o Referencia)", "Ramo", "Inicio de Vigencia", "Fin de Vigencia", "Estado_Gestion", "Adjunto (póliza)"],
    "ANDRE": ["Asegurado (Nombre/Razón Social)", "Celular", "Aseguradora", "Inicio de Vigencia", "Fin de Vigencia", "Corredor", "Adjunto (póliza)"]
}

# ==========================================
# 🔗 CONFIGURACIÓN Y CONEXIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS para el modo impresión y visualización
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .left-title { font-size: 30px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    @media print {
        .stSidebar, .stTabs, .no-print { display: none !important; }
        .print-only { display: block !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", 
    "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", 
    "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", 
    "AC": "ACazarian2025", "MF": "MFlores2025", "JOE": "Joe2025", "ANDRE": "Andre2025"
}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False

if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = u
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        df['Inicio de Vigencia'] = pd.to_datetime(df['Inicio de Vigencia'], dayfirst=True, errors='coerce')
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
        df['Fin_V_dt'] = df['Fin de Vigencia'].dt.date
        if 'Estado_Gestion' not in df.columns: df['Estado_Gestion'] = "Pendiente"
        df['Estado_Gestion'] = df['Estado_Gestion'].fillna("Pendiente")
        return df
    except:
        return pd.DataFrame()

df_raw = cargar_datos()
user = st.session_state["usuario_actual"]
cols_default = PERFILES_DEFAULTS.get(user, ["Asegurado (Nombre/Razón Social)", "Ramo", "Fin de Vigencia"])

# ==========================================
# 🎯 BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {user}")
    st.markdown("---")
    st.markdown("### 🔍 Filtros de Cartera")
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    
    st.markdown("---")
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]

# Título Principal
st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📊 ANÁLISIS", "📝 COTIZADOR"])

# --- TAB 1: CARTERA ---
with tab1:
    busqueda = st.text_input("Buscar cliente o póliza...", placeholder="Ej: Juan Perez o 123456")
    df_tab1 = df_f.copy()
    if busqueda:
        mask = df_tab1.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_tab1 = df_tab1[mask]
    
    st.dataframe(df_tab1[cols_default], use_container_width=True, hide_index=True)

# --- TAB 2: VENCIMIENTOS ---
with tab2:
    dias_v = st.slider("Días a futuro:", 15, 365, 60)
    hoy = date.today()
    limite = hoy + timedelta(days=dias_v)
    df_v = df_f[(df_f['Fin_V_dt'] >= hoy) & (df_f['Fin_V_dt'] <= limite)].sort_values('Fin_V_dt')
    st.dataframe(df_v[cols_default], use_container_width=True, hide_index=True)

# --- TAB 3: ANÁLISIS ---
with tab3:
    t_usd = df_f['Premio_Total_USD'].sum()
    p_vig = df_f[df_f['Fin_V_dt'] >= date.today()].shape[0]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Cartera Total", f"U$S {t_usd:,.2f}")
    c2.metric("Pólizas Vigentes", p_vig)
    c3.metric("Registros", len(df_f))
    
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="USD por Compañía", hole=0.4), use_container_width=True)
    with col_b:
        df_r = df_f['Ramo'].value_counts().reset_index()
        st.plotly_chart(px.bar(df_r, x='Ramo', y='count', title="Pólizas por Ramo", color='Ramo', text_auto=True), use_container_width=True)

# --- TAB 4: COTIZADOR (EL NUEVO MODULO) ---
with tab4:
    st.subheader("📝 Generador de Cotización Automotores")
    
    # Datos del cliente
    with st.container(border=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            ci_bus = st.text_input("DNI / RUT para buscar cliente")
            # Auto-completado si existe
            nombre_init = ""
            if ci_bus:
                match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(ci_bus)]
                if not match.empty: nombre_init = match.iloc[0]['Asegurado (Nombre/Razón Social)']
            
            nombre_cli = st.text_input("Nombre y Apellido", value=nombre_init)
        with col_c2:
            vehiculo = st.text_input("Vehículo (Marca, Modelo, Año)")
            zona = st.selectbox("Zona de Circulación", ["Montevideo", "Canelones", "Maldonado", "Interior"])

    # Tabla de Aseguradoras
    st.markdown("#### 💰 Opciones de Cobertura")
    if 'data_cot' not in st.session_state:
        st.session_state.data_cot = pd.DataFrame([
            {"Aseguradora": "BSE", "Contado": 0, "3 Cuotas": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Básico"},
            {"Aseguradora": "SBI", "Contado": 0, "3 Cuotas": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Básico"}
        ])

    cot_editor = st.data_editor(st.session_state.data_cot, num_rows="dynamic", use_container_width=True)

    # Beneficios
    beneficios_text = st.text_area("Beneficios incluidos:", 
        value="• Auxilio mecánico nacional e internacional las 24hs.\n• Cristales, cerraduras y espejos sin deducible.\n• Auto de alquiler por 15 días en caso de siniestro.")

    # Generación de Vista Previa (Modo envío)
    if st.button("👁️ Generar Vista Previa para Cliente"):
        st.markdown("---")
        st.markdown(f"""
            <div style="text-align: center; border: 2px solid #1E1E1E; padding: 20px; border-radius: 15px;">
                <h1 style="margin:0;">🛡️ EDF SEGUROS</h1>
                <p>Propuesta de Seguro Automotor</p>
                <hr>
                <div style="text-align: left;">
                    <p><b>Cliente:</b> {nombre_cli} | <b>DNI:</b> {ci_bus}</p>
                    <p><b>Vehículo:</b> {vehiculo} | <b>Zona:</b> {zona}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.table(cot_editor)
        st.info(f"**Beneficios Destacados:**\n\n{beneficios_text}")
        st.warning("⚠️ Nota: Los costos están sujetos a variaciones de las compañías y a inspección del vehículo.")
