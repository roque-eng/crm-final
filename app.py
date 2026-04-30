import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURACIÓN DE ENLACES
# ==========================================
URL_EMPRESA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
URL_MI_DRIVE = "https://docs.google.com/spreadsheets/d/1rd_ZCEUxolcgr9WaNUxzqjJVsL7tFvOOS4CaMZOrR8E/edit#gid=0"

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .titulo-cuadro { background-color: #1E1E1E; color: white; padding: 5px 10px; font-weight: bold; margin-top: 15px; }
    .cuadro-beneficios { border: 1px solid #333; padding: 15px; margin-top: 10px; background-color: #fdfdfd; }
    @media print {
        .no-print, .stSidebar, .stTabs, button, header, footer, [data-testid="stToolbar"], .stCheckbox, .stNumberInput { display: none !important; }
        .print-only { display: block !important; position: absolute; left: 0; top: 0; width: 100%; }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Conexión principal
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGIN ---
if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    with st.columns([1,1,1])[1]:
        with st.form("login"):
            st.markdown("### 🛡️ Acceso EDF")
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u == "RDF" and p == "Rockuda.4428":
                    st.session_state['logueado'] = True
                    st.rerun()
                else: st.error("Credenciales incorrectas")
    st.stop()

# --- CARGA DE CARTERA ---
@st.cache_data(ttl=300)
def cargar_cartera():
    try:
        df = conn.read(spreadsheet=URL_EMPRESA, ttl=0)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

df_raw = cargar_cartera()

st.title("🛡️ EDF SEGUROS")
t1, t2 = st.tabs(["👥 CARTERA", "📝 COTIZADOR"])

with t1:
    busq = st.text_input("Buscar cliente...")
    if not df_raw.empty:
        df_f = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_raw
        st.dataframe(df_f, use_container_width=True, hide_index=True)

with t2:
    st.subheader("📝 Nueva Cotización")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        doc_in = col1.text_input("CI / RUT")
        n_auto = ""
        if doc_in and not df_raw.empty:
            col_doc = 'Documento de Identidad (Rut/Cédula/Otros)'
            if col_doc in df_raw.columns:
                m = df_raw[df_raw[col_doc].astype(str).str.contains(doc_in, na=False)]
                if not m.empty: n_auto = m.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        n_cli = col1.text_input("Asegurado", value=n_auto)
        veh = col2.text_input("Vehículo")
        zn = col2.selectbox("Zona", ["Montevideo", "Interior", "Canelones", "Maldonado"])

    st.write("💰 **Costos**")
    df_c = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    costos_edit = st.data_editor(df_c, num_rows="dynamic", use_container_width=True)

    c_iz, c_de = st.columns(2)
    inc = c_iz.text_area("✅ Beneficios", "• Auxilio Mecánico 24hs\n• Cristales, Cerraduras y Ópticas\n• RC USD 500.000", height=250)
    
    txt_adicionales = (
        "Adicionales:\n\n"
        "INCLUYA SEGURO DE HOGAR:\n"
        "- Incendio Edificio USD 100.000\n"
        "- Incendio Contenido USD 50.000\n"
        "- Hurto Contenido USD 10.000\n"
        "Costo Anual:\n\n"
        "INCLUYA VEHÍCULO DE ALQUILER:\n"
        "- En caso de choque de su vehículo asegurado, hasta 15 días de vehículo de alquiler.\n"
        "Costo Anual:"
    )
    hog = c_de.text_area("🏠 Adicionales", value=txt_adicionales, height=250)

    if st.button("Guardar Cotización", use_container_width=True):
        if not n_cli: st.error("Falta el nombre")
        else:
            nueva_fila = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Cliente": n_cli,
                "Documento": doc_in,
                "Vehiculo": veh,
                "Zona": zn,
                "Ejecutivo": "Roque de Freitas",
                "Tabla_Costos": costos_edit.to_json(orient='records'),
                "Detalles": f"{inc}\n\n{hog}"
            }])
            try:
                # 1. Leer lo que hay (ahora está vacío pero traerá los encabezados)
                df_existente = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", ttl=0)
                # 2. Unir
                df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
                # 3. Escribir
                conn.update(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", data=df_final)
                st.success("✅ Guardado con éxito en tu Drive")
                st.session_state['ultima_cot'] = nueva_fila.iloc[0].to_dict()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# Vista para imprimir
if 'ultima_cot' in st.session_state:
    c = st.session_state['ultima_cot']
    st.markdown(f"""<div class="print-only"><h1>🛡️ EDF SEGUROS</h1><hr><p><b>Cliente:</b> {c['Cliente']}</p><div class="titulo-cuadro">COBERTURA</div><div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Detalles']}</div></div>""", unsafe_allow_html=True)
