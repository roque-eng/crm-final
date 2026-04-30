import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS DE IMPRESIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* Estilo Web Normal */
    .main .block-container { padding-top: 1.5rem; }
    
    /* LÓGICA DE IMPRESIÓN: SOLUCIÓN AL PDF EN BLANCO */
    @media print {
        /* Oculta absolutamente todo Streamlit */
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], 
        .stTabs, button, [data-testid="stToolbar"], [data-testid="stDecoration"],
        .stSpinner, .stException { 
            display: none !important; 
        }
        
        /* Fuerza la visualización del área de cotización */
        .print-area { 
            display: block !important; 
            visibility: visible !important;
            width: 100% !important;
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            background-color: white !important;
            color: black !important;
        }
        
        body { background-color: white !important; }
        .titulo-pdf { border-bottom: 2px solid #000; padding-bottom: 10px; }
    }

    /* Oculto en la web para no duplicar datos */
    .print-area { display: none; }
    
    .caja-pdf { border: 1px solid #000; padding: 15px; background-color: #fff; margin-top: 10px; }
    .tabla-estatica { width: 100%; border-collapse: collapse; margin: 20px 0; }
    .tabla-estatica th, .tabla-estatica td { border: 1px solid #000; padding: 8px; text-align: left; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025"}
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
                else: st.error("Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    df = conn.read(spreadsheet=URL_HOJA, ttl=0)
    df.columns = df.columns.str.strip()
    df['Premio_Total_USD'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0) + \
                             (pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0) / TC_USD)
    df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
    return df

df_raw = cargar_datos()

# Sidebar con Filtros Globales
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA ---
with tab1:
    busq = st.text_input("🔍 Buscar cliente o matrícula...")
    df_c = df_f.copy()
    if busq:
        df_c = df_c[df_c.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
    st.dataframe(df_c, use_container_width=True, hide_index=True,
                 column_config={"Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")})

# --- TAB 3: COTIZADOR (TODO RECUPERADO) ---
with tab3:
    st.subheader("📝 Generar Cotización")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc_in = c1.text_input("CI / RUT")
        nombre_sugerido = ""
        if doc_in:
            match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(doc_in)]
            if not match.empty: nombre_sugerido = match.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        nombre_cli = c1.text_input("Asegurado", value=nombre_sugerido)
        vehiculo = c2.text_input("Vehículo")
        zona = c2.selectbox("Zona", ["Montevideo", "Interior", "Canelones", "Maldonado"])
        ejecutivo = c3.selectbox("Ejecutivo", ["Roque de Freitas", "Joe", "Andre"])

    df_edit = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    tabla_cot = st.data_editor(df_edit, num_rows="dynamic", use_container_width=True)

    col_a, col_b = st.columns(2)
    ben = col_a.text_area("Beneficios Incluidos", "• Auxilio mecánico 24hs.\n• Cristales y Cerraduras.\n• RC USD 500.000", height=150)
    
    with col_b:
        casa = st.text_input("Seguro Hogar", "Incluido")
        alquiler = st.text_input("Auto Alquiler", "15 días por choque")
        bici = st.text_input("Seguro Bici", "Opcional")

    if st.button("🔥 GENERAR VISTA DE IMPRESIÓN"):
        st.session_state['imprimir'] = True
        # Convertimos la tabla a HTML para que el navegador la pueda imprimir
        tabla_html = tabla_cot.to_html(index=False, border=1).replace('class="dataframe"', 'class="tabla-estatica"')
        st.session_state['html_pdf'] = f"""
            <div class="print-area">
                <h1 class="titulo-pdf">🛡️ EDF SEGUROS</h1>
                <p><b>Fecha:</b> {date.today().strftime('%d/%m/%Y')} | <b>Ejecutivo:</b> {ejecutivo}</p>
                <p><b>Asegurado:</b> {nombre_cli} | <b>Vehículo:</b> {vehiculo} | <b>Zona:</b> {zona}</p>
                {tabla_html}
                <div style="display: flex; gap: 20px; margin-top: 20px;">
                    <div class="caja-pdf" style="flex: 1;"><b>BENEFICIOS:</b><br>{ben.replace('\\n', '<br>')}</div>
                    <div class="caja-pdf" style="flex: 1;">
                        <b>COBERTURAS ADICIONALES:</b><br>
                        • Hogar: {casa}<br>• Alquiler: {alquiler}<br>• Bici: {bici}
                    </div>
                </div>
            </div>
        """

    if st.session_state.get('imprimir'):
        st.markdown(st.session_state['html_pdf'], unsafe_allow_html=True)
        st.success("✅ Propuesta lista. Ahora presiona **Ctrl + P** para guardar el PDF.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_f.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1: st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía"), use_container_width=True)
        with col_g2: st.plotly_chart(px.bar(df_f['Ramo'].value_counts().reset_index(), x='Ramo', y='count', title="Pólizas por Ramo"), use_container_width=True)
