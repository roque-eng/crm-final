import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime
import base64

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f0f2f6; 
        border-radius: 5px; 
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD (GESTIÓN DE USUARIOS)
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025",
    "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025"
}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False

if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = u
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA Y PROCESAMIENTO DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos_completos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        # Procesamiento de Importes
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        # Procesamiento de Fechas
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
        return df
    except Exception as e:
        return pd.DataFrame()

df_raw = cargar_datos_completos()

# ==========================================
# 🎯 SIDEBAR (FILTROS TOTALES RESTAURADOS)
# ==========================================
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    st.subheader("🔍 Filtros Globales")
    f_ej = st.selectbox("Filtrar Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Filtrar Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Filtrar Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    f_co = st.selectbox("Filtrar Corredor", ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()))
    
    st.divider()
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

# Aplicar Filtros
df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]

# ==========================================
# 📑 PESTAÑAS
# ==========================================
st.markdown("# 🛡️ EDF SEGUROS")
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA ---
with tab1:
    busq = st.text_input("🔍 Buscar cliente, matrícula o documento...")
    df_cartera = df_f.copy()
    if busq:
        mask = df_cartera.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)
        df_cartera = df_cartera[mask]
    
    st.dataframe(df_cartera, use_container_width=True, hide_index=True,
                 column_config={"Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")})

# --- TAB 2: VENCIMIENTOS ---
with tab2:
    st.subheader("📅 Control de Vencimientos")
    df_v = df_f.sort_values('Fin de Vigencia')
    st.dataframe(df_v, use_container_width=True, hide_index=True)

# --- TAB 3: COTIZADOR (SISTEMA DE IMPRESIÓN PRO) ---
with tab3:
    st.subheader("📝 Generador de Cotizaciones")
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc_in = c1.text_input("Documento (CI / RUT)")
        # Autocompletado
        nom_sug = ""
        if doc_in:
            match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(doc_in)]
            if not match.empty:
                nom_sug = match.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        nombre_cot = c1.text_input("Asegurado", value=nom_sug)
        vehi_cot = c2.text_input("Vehículo (Marca/Modelo/Año)")
        zona_cot = c2.selectbox("Zona de Circulación", ["Montevideo", "Interior", "Canelones", "Maldonado"])
        # Ejecutivos dinámicos
        lista_ejes = sorted(df_raw['Ejecutivo'].dropna().unique().tolist())
        ejecutivo_cot = c3.selectbox("Ejecutivo Responsable", lista_ejes)

    st.write("### 💰 Tabla Comparativa")
    df_init = pd.DataFrame([
        {"Aseguradora": "BSE", "Contado": 0.0, "6 Cuotas": 0.0, "10 Cuotas": 0.0, "Deducible": "Global"},
        {"Aseguradora": "SBI", "Contado": 0.0, "6 Cuotas": 0.0, "10 Cuotas": 0.0, "Deducible": "Global"}
    ])
    tabla_edit = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)

    col_a, col_b = st.columns(2)
    beneficios_cot = col_a.text_area("Beneficios Incluidos", 
        "• Auxilio mecánico 24hs.\n• Cristales, Cerraduras y Espejos sin deducible.\n• Responsabilidad Civil USD 500.000", height=150)
    casa_cot = col_b.text_input("Seguro Hogar", "Incluido - Incendio USD 100.000")
    alq_cot = col_b.text_input("Auto Alquiler", "15 días por choque")
    bici_cot = col_b.text_input("Seguro Bici", "Opcional")

    # --- FUNCIÓN DE IMPRESIÓN LIMPIA ---
    def generar_html_impresion():
        tabla_html = tabla_edit.to_html(index=False).replace('table', 'table style="width:100%; border-collapse:collapse; margin-top:20px;"').replace('th', 'th style="background:#1a4a7a; color:white; padding:10px; border:1px solid #ccc;"').replace('td', 'td style="padding:10px; border:1px solid #ccc;"')
        
        html_code = f"""
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family:sans-serif; padding:40px; color:#333;">
            <div style="border-bottom:3px solid #1a4a7a; padding-bottom:10px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">
                <div style="font-size:28px; font-weight:bold; color:#1a4a7a;">🛡️ EDF SEGUROS</div>
                <div style="text-align:right;">Propuesta Comercial<br>{date.today().strftime('%d/%m/%Y')}</div>
            </div>
            <div style="background:#f4f4f4; padding:20px; border-radius:10px; margin-bottom:20px;">
                <p><b>Asegurado:</b> {nombre_cot} <br>
                <b>Vehículo:</b> {vehi_cot} | <b>Zona:</b> {zona_cot} <br>
                <b>Ejecutivo:</b> {ejecutivo_cot}</p>
            </div>
            {tabla_html}
            <div style="display:flex; gap:20px; margin-top:30px;">
                <div style="flex:1; border:1px solid #ccc; padding:20px; border-radius:10px;">
                    <b style="color:#1a4a7a;">✅ BENEFICIOS INCLUIDOS:</b><br><br>{beneficios_cot.replace('\\n', '<br>')}
                </div>
                <div style="flex:1; border:1px solid #ccc; padding:20px; border-radius:10px;">
                    <b style="color:#1a4a7a;">🏠 COBERTURAS ADICIONALES:</b><br><br>
                    • Seguro de Hogar: {casa_cot}<br>
                    • Vehículo de Alquiler: {alq_cot}<br>
                    • Seguro de Bicicleta: {bici_cot}
                </div>
            </div>
            <div style="margin-top:50px; text-align:center; font-size:12px; color:#888;">
                Propuesta sujeta a inspección y políticas de la aseguradora.
            </div>
        </body>
        </html>
        """
        b64 = base64.b64encode(html_code.encode()).decode()
        return f'<a href="data:text/html;base64,{b64}" target="_blank" style="text-decoration:none;"><div style="background-color:#1a4a7a; color:white; padding:15px; text-align:center; border-radius:10px; font-weight:bold; font-size:18px;">🚀 GENERAR VISTA DE IMPRESIÓN (PDF)</div></a>'

    st.markdown(generar_html_impresion(), unsafe_allow_html=True)
    st.caption("Al hacer clic, se abrirá una pestaña nueva con el diseño profesional. Presiona Ctrl+P ahí.")

# --- TAB 4: ANÁLISIS (SUBTOTALES RESTAURADOS) ---
with tab4:
    if not df_f.empty:
        # Métricas de Subtotales
        m1, m2, m3 = st.columns(3)
        m1.metric("Cartera Total (USD)", f"U$S {df_f['Premio_Total_USD'].sum():,.2f}")
        m2.metric("Cantidad de Pólizas", f"{len(df_f)} u.")
        m3.metric("Ticket Promedio", f"U$S {df_f['Premio_Total_USD'].mean():,.2f}")
        
        st.divider()
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía", hole=0.4), use_container_width=True)
        with col_g2:
            df_ramos = df_f['Ramo'].value_counts().reset_index()
            df_ramos.columns = ['Ramo', 'Cantidad']
            st.plotly_chart(px.bar(df_ramos, x='Ramo', y='Cantidad', color='Ramo', title="Pólizas por Ramo"), use_container_width=True)
