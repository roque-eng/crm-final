import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta, datetime

# ==========================================
# ⚙️ CONFIGURACIÓN Y CONEXIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# ==========================================
# 🎨 ESTILOS CSS (SOLUCIÓN PDF + ICONO 📂)
# ==========================================
st.markdown("""
    <style>
    /* Estilo para que el icono sea clickeable y se vea bien */
    .folder-link {
        text-decoration: none;
        font-size: 1.5rem;
        color: #007bff;
        cursor: pointer;
    }
    
    /* ESTILOS PARA EL PDF (TABLA Y CAJAS) */
    .tabla-pdf { width: 100%; border-collapse: collapse; margin: 20px 0; }
    .tabla-pdf th, .tabla-pdf td { border: 1px solid #000 !important; padding: 10px; text-align: left; }
    .tabla-pdf th { background-color: #f2f2f2 !important; }
    .titulo-seccion { background-color: #1E1E1E; color: white; padding: 8px 12px; font-weight: bold; margin-top: 20px; }
    .caja-texto { border: 1px solid #000; padding: 15px; background-color: #fff; }

    /* LÓGICA DE IMPRESIÓN DEFINITIVA (EVITA HOJA EN BLANCO) */
    @media print {
        /* Ocultar interfaz de Streamlit */
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], 
        .stTabs, button, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
            display: none !important; 
        }
        
        /* Forzar visualización del área de impresión */
        .print-area { 
            display: block !important; 
            visibility: visible !important;
            width: 100% !important;
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            background-color: white !important;
            z-index: 99999;
        }
        
        body { background-color: white !important; }
    }

    /* Ocultar área de impresión en la web */
    .print-area { display: none; }
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

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos()

# --- SIDEBAR (FILTROS) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_actual']}")
    st.divider()
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    f_co = st.selectbox("Corredor", ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()))
    f_ag = st.selectbox("Agente", ["Todos"] + sorted(df_raw['Agente'].dropna().unique().tolist()))
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]

st.markdown('<p style="font-size:30px; font-weight:bold;">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA (CON ICONO 📂) ---
with tab1:
    busq = st.text_input("Buscar cliente o matrícula...")
    df_cartera = df_f.copy()
    if busq:
        df_cartera = df_cartera[df_cartera.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
    
    # Lógica del icono
    def icono_link(url):
        if pd.isna(url) or str(url).strip() == "": return ""
        return f'<a href="{url}" target="_blank" class="folder-link">📂</a>'

    if 'Adjunto (póliza)' in df_cartera.columns:
        df_cartera['Ver'] = df_cartera['Adjunto (póliza)'].apply(icono_link)
        # Reordenar para que "Ver" sea la primera columna
        cols = ['Ver'] + [c for c in df_cartera.columns if c not in ['Ver', 'Adjunto (póliza)']]
        st.write(df_cartera[cols].to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.dataframe(df_cartera, use_container_width=True, hide_index=True)

# --- TAB 3: COTIZADOR ---
with tab3:
    st.subheader("📝 Generar Cotización")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        n_cli = c1.text_input("Nombre Asegurado")
        vehiculo = c2.text_input("Vehículo")

    df_prop = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    tabla_edit = st.data_editor(df_prop, num_rows="dynamic", use_container_width=True)

    iz, de = st.columns(2)
    ben = iz.text_area("✅ Beneficios", value="• Auxilio mecánico 24hs.\n• Cristales, cerraduras y espejos.\n• RC USD 500.000.", height=150)
    ad = de.text_area("➕ Adicionales", value="INCLUYE HOGAR:\n- Incendio Edificio USD 100.000\n- Hurto USD 5.000\n\nINCLUYE ALQUILER:\n- 15 días por choque.", height=150)

    if st.button("👁️ Generar Vista para Impresión"):
        st.session_state['pdf_ready'] = {
            "Fecha": date.today().strftime("%d/%m/%Y"),
            "Cliente": n_cli, "Vehiculo": vehiculo, 
            "Tabla": tabla_edit.to_html(index=False, classes='tabla-pdf'),
            "Inc": ben, "Opc": ad
        }

    if 'pdf_ready' in st.session_state:
        p = st.session_state['pdf_ready']
        # ESTE BLOQUE ES EL QUE APARECERÁ EN EL PDF
        st.markdown(f"""
            <div class="print-area">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h1 style="margin: 0;">🛡️ EDF SEGUROS</h1>
                    <p><b>Fecha:</b> {p['Fecha']}</p>
                </div>
                <hr style="border: 1px solid #000;">
                <p style="font-size: 1.3rem;"><b>Propuesta para:</b> {p['Cliente']}</p>
                <p><b>Vehículo:</b> {p['Vehiculo']}</p>
                {p['Tabla']}
                <div class="titulo-seccion">✅ BENEFICIOS INCLUIDOS</div>
                <div class="caja-texto" style="white-space: pre-wrap;">{p['Inc']}</div>
                <div class="titulo-seccion">➕ COBERTURAS ADICIONALES</div>
                <div class="caja-texto" style="white-space: pre-wrap;">{p['Opc']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.success("✅ Vista de impresión lista. Ahora presiona **Control + P**.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_f.empty:
        st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Compañía", hole=0.3), use_container_width=True)
