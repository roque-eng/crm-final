import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date
import io

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

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
            if st.form_submit_button("Ingresar"):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = u
                    st.rerun()
                else: st.error("Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA Y PROCESAMIENTO DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    df = conn.read(spreadsheet=URL_HOJA, ttl=0)
    df.columns = df.columns.str.strip()
    # Cálculos de premios
    df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
    df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
    df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
    df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
    return df

df_raw = cargar_datos()

# Sidebar con TODOS los filtros
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    f_co = st.selectbox("Corredor", ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()))
    
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

# Aplicar filtros
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

# --- CARTERA ---
with tab1:
    busq = st.text_input("🔍 Buscar cliente o matrícula...")
    if busq:
        df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
    
    st.dataframe(df_f, use_container_width=True, hide_index=True,
                 column_config={"Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")})

# --- VENCIMIENTOS ---
with tab2:
    df_v = df_f.sort_values('Fin de Vigencia')
    st.dataframe(df_v, use_container_width=True, hide_index=True)

# --- COTIZADOR ---
with tab3:
    st.subheader("📝 Módulo de Cotización")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc = c1.text_input("Documento (CI / RUT)")
        # Autocompletar nombre
        sug_nom = ""
        if doc:
            match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(doc)]
            if not match.empty: sug_nom = match.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        nombre = c1.text_input("Asegurado", value=sug_nom)
        vehi = c2.text_input("Vehículo")
        zona = c2.selectbox("Zona", ["Montevideo", "Interior", "Canelones", "Maldonado"])
        # EJECUTIVOS DINÁMICOS: Aparecen todos los de la cartera
        lista_ejecutivos = sorted(df_raw['Ejecutivo'].dropna().unique().tolist())
        ejec_cot = c3.selectbox("Ejecutivo Responsable", lista_ejecutivos)

    df_propu = pd.DataFrame([
        {"Aseguradora": "BSE", "Contado": 0.0, "6 Cuotas": 0.0, "10 Cuotas": 0.0, "Deducible": "Global"},
        {"Aseguradora": "SBI", "Contado": 0.0, "6 Cuotas": 0.0, "10 Cuotas": 0.0, "Deducible": "Global"}
    ])
    tabla_final = st.data_editor(df_propu, num_rows="dynamic", use_container_width=True)

    col_a, col_b = st.columns(2)
    ben = col_a.text_area("Beneficios Incluidos", "• Auxilio mecánico 24hs.\n• Cristales, Cerraduras y Espejos.\n• RC USD 500.000")
    casa = col_b.text_input("Seguro Hogar", "Incluido")
    alquiler = col_b.text_input("Auto Alquiler", "15 días por choque")
    bici = col_b.text_input("Seguro Bici", "Opcional")

    # Función Excel
    def descargar_excel():
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Cotización')
            f_bold = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1})
            worksheet.write('A1', '🛡️ EDF SEGUROS - COTIZACIÓN', workbook.add_format({'bold': True, 'font_size': 14}))
            worksheet.write('A3', f'Cliente: {nombre}')
            worksheet.write('A4', f'Vehículo: {vehi}')
            worksheet.write('A5', f'Ejecutivo: {ejec_cot}')
            # Escribir tabla
            tabla_final.to_excel(writer, sheet_name='Cotización', startrow=7, index=False)
            worksheet.set_column('A:E', 18)
        return output.getvalue()

    st.download_button("📥 Descargar Cotización (Excel)", data=descargar_excel(), file_name=f"Cotizacion_{nombre}.xlsx", use_container_width=True)

# --- ANÁLISIS (SUBTOTALES RESTAURADOS) ---
with tab4:
    if not df_f.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Cartera Total (USD)", f"{df_f['Premio_Total_USD'].sum():,.2f}")
        m2.metric("Cantidad de Pólizas", len(df_f))
        m3.metric
