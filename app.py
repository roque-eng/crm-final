import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date
from fpdf import FPDF

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
    st.stop()

# ==========================================
# ⚙️ CARGA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(spreadsheet=URL_HOJA, ttl=0)
df_raw.columns = df_raw.columns.str.strip()
df_raw['Premio_Total_USD'] = pd.to_numeric(df_raw['Premio USD (IVA inc)'], errors='coerce').fillna(0) + \
                             (pd.to_numeric(df_raw['Premio UYU (IVA inc)'], errors='coerce').fillna(0) / TC_USD)

# ==========================================
# 🎯 FILTROS Y SIDEBAR
# ==========================================
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_ra = st.selectbox("Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

with tab1:
    st.dataframe(df_f, use_container_width=True, hide_index=True,
                 column_config={"Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")})

with tab3:
    st.subheader("📝 Generador de Cotización PDF")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc = c1.text_input("CI / RUT")
        sug_nom = ""
        if doc:
            match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(doc)]
            if not match.empty: sug_nom = match.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        nombre = c1.text_input("Asegurado", value=sug_nom)
        vehi = c2.text_input("Vehículo")
        zona = c2.selectbox("Zona", ["Montevideo", "Interior", "Maldonado"])
        eje_firma = c3.selectbox("Ejecutivo Firma", sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))

    df_init = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0.0, "6 Cuotas": 0.0, "10 Cuotas": 0.0, "Deducible": "Global"}])
    tabla_edit = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)

    c_iz, c_de = st.columns(2)
    ben = c_iz.text_area("Beneficios", "• Auxilio mecánico 24hs.\n• Cristales, Cerraduras y Espejos sin deducible.\n• RC USD 500.000", height=150)
    extra = c_de.text_area("Adicionales", f"• Hogar: Incluido\n• Alquiler: 15 días", height=150)

    # --- FUNCIÓN PARA GENERAR EL ARCHIVO PDF REAL ---
    def crear_pdf_binario(datos):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "EDF SEGUROS - PROPUESTA COMERCIAL", 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, f"Fecha: {date.today().strftime('%d/%m/%Y')}", 0, 1, 'R')
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, f"Asegurado: {datos['nom']}", 0, 1)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Vehiculo: {datos['vehi']} | Zona: {datos['zona']}", 0, 1)
        pdf.cell(0, 8, f"Ejecutivo: {datos['eje']}", 0, 1)
        pdf.ln(10)

        # Tabla de Precios
        pdf.set_fill_color(26, 74, 122)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 10)
        cols = ["Aseguradora", "Contado", "6 Cuotas", "10 Cuotas", "Deducible"]
        for col in cols:
            pdf.cell(38, 10, col, 1, 0, 'C', True)
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 10)
        for _, row in datos['tabla'].iterrows():
            pdf.cell(38, 10, str(row['Aseguradora']), 1)
            pdf.cell(38, 10, str(row['Contado']), 1)
            pdf.cell(38, 10, str(row['6 Cuotas']), 1)
            pdf.cell(38, 10, str(row['10 Cuotas']), 1)
            pdf.cell(38, 10, str(row['Deducible']), 1)
            pdf.ln()

        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "BENEFICIOS INCLUIDOS:", 0, 1)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, datos['ben'])
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "COBERTURAS ADICIONALES:", 0, 1)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, datos['extra'])

        return pdf.output(dest='S').encode('latin-1')

    # BOTÓN DE DESCARGA DIRECTA
    pdf_output = crear_pdf_binario({
        "nom": nombre, "vehi": vehi, "zona": zona, "eje": eje_firma,
        "tabla": tabla_edit, "ben": ben, "extra": extra
    })
    
    st.download_button(
        label="📥 Descargar Cotización en PDF",
        data=pdf_output,
        file_name=f"Cotizacion_{nombre}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

with tab4:
    m1, m2 = st.columns(2)
    m1.metric("Cartera Total (USD)", f"U$S {df_f['Premio_Total_USD'].sum():,.2f}")
    m2.metric("Total Pólizas", len(df_f))
    st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía"), use_container_width=True)
