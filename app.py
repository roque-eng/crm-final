import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS: Configuración para que el PDF NO salga en blanco
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    
    /* DISEÑO PROFESIONAL DE COTIZACIÓN */
    .cotizacion-box {
        border: 2px solid #1a4a7a;
        padding: 30px;
        border-radius: 10px;
        background-color: white;
        color: #333;
        font-family: Arial, sans-serif;
    }
    .header-cot {
        border-bottom: 3px solid #1a4a7a;
        padding-bottom: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
    }
    
    /* LÓGICA DE IMPRESIÓN */
    @media print {
        /* Oculta la interfaz de Streamlit */
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], 
        .stTabs, button, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
            display: none !important; 
        }
        
        /* Muestra solo el bloque de la cotización ocupando toda la hoja */
        .print-area { 
            display: block !important; 
            position: absolute;
            left: 0; top: 0; width: 100%;
        }
    }
    .print-area { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD (USUARIOS)
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
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos_completos()

# ==========================================
# 🎯 SIDEBAR (FILTROS COMPLETOS)
# ==========================================
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    f_co = st.selectbox("Corredor", ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()))
    
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

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
    busq = st.text_input("Buscar cliente o matrícula...")
    df_cartera = df_f.copy()
    if busq:
        df_cartera = df_cartera[df_cartera.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
    st.dataframe(df_cartera, use_container_width=True, hide_index=True,
                 column_config={"Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")})

# --- TAB 3: COTIZADOR ---
with tab3:
    st.subheader("📝 Generar Propuesta Comercial")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        ci_in = col1.text_input("Documento (CI / RUT)")
        # Autocompletado
        nom_s = ""
        if ci_in:
            m = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(ci_in)]
            if not m.empty: nom_s = m.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        nombre = col1.text_input("Asegurado", value=nom_s)
        vehi = col2.text_input("Vehículo")
        ejec = col2.selectbox("Ejecutivo Firma", sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))

    st.write("### Comparativa")
    df_propu = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    tabla = st.data_editor(df_propu, num_rows="dynamic", use_container_width=True)

    c_iz, c_de = st.columns(2)
    ben = c_iz.text_area("Beneficios", "• Auxilio mecánico 24hs.\n• Cristales y Cerraduras.\n• RC USD 500.000", height=150)
    extra = c_de.text_area("Adicionales", "• Hogar: Incluido\n• Alquiler: 15 días", height=150)

    if st.button("🔥 GENERAR VISTA DE IMPRESIÓN", use_container_width=True):
        st.session_state['ver_pdf'] = True
        st.session_state['datos'] = {
            "nom": nombre, "vehi": vehi, "ejec": ejec, "tabla": tabla, "ben": ben, "extra": extra
        }

    if st.session_state.get('ver_pdf'):
        d = st.session_state['datos']
        # Bloque de visualización que el navegador captura al imprimir
        st.markdown(f"""
            <div class="print-area cotizacion-box">
                <div class="header-cot">
                    <div style="font-size:24px; font-weight:bold; color:#1a4a7a;">🛡️ EDF SEGUROS</div>
                    <div style="text-align:right;">Propuesta Comercial<br>{date.today().strftime('%d/%m/%Y')}</div>
                </div>
                <p><b>Asegurado:</b> {d['nom']} | <b>Vehículo:</b> {d['vehi']}</p>
                <p><b>Ejecutivo:</b> {d['ejec']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabla reconocida por el motor de impresión
        st.table(d['tabla'])
        
        st.markdown(f"""
            <div class="print-area cotizacion-box">
                <div style="display: flex; gap: 20px; margin-top: 20px;">
                    <div style="flex: 1; border: 1px solid #ccc; padding: 15px;">
                        <b>BENEFICIOS INCLUIDOS:</b><br>{d['ben'].replace('\\n', '<br>')}
                    </div>
                    <div style="flex: 1; border: 1px solid #ccc; padding: 15px;">
                        <b>COBERTURAS ADICIONALES:</b><br>{d['extra'].replace('\\n', '<br>')}
                    </div>
                </div>
                <p style="text-align: center; margin-top: 40px; font-size: 12px; color: #888;">
                    Propuesta sujeta a políticas de la aseguradora.
                </p>
            </div>
        """, unsafe_allow_html=True)
        st.success("✅ Propuesta generada. Presiona Ctrl + P para guardar el PDF.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_f.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Cartera Total (USD)", f"U$S {df_f['Premio_Total_USD'].sum():,.2f}")
        m2.metric("Pólizas", len(df_f))
        m3.metric("Promedio", f"U$S {df_f['Premio_Total_USD'].mean():,.2f}")
        
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía"), use_container_width=True)
        with c2: st.plotly_chart(px.bar(df_f['Ramo'].value_counts().reset_index(), x='Ramo', y='count', title="Pólizas por Ramo"), use_container_width=True)
