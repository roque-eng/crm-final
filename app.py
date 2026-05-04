import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS - Cotización", layout="wide", page_icon="🛡️")

# Estilos mejorados para impresión y vista de cliente
st.markdown("""
    <style>
    @media print {
        .stButton, .stDownloadButton, [data-testid="stSidebar"] { display: none !important; }
        .main .block-container { padding: 0; }
    }
    .quote-card { background-color: white; padding: 30px; border-radius: 15px; border: 2px solid #1a4a7a; margin-bottom: 20px; }
    .header-quote { color: #1a4a7a; font-size: 28px; font-weight: bold; border-bottom: 3px solid #1a4a7a; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🕵️ LÓGICA DE VISTA DE CLIENTE (MODO SIN LOGIN)
# ==========================================
# Intentamos leer datos del link (URL parameters)
query_params = st.query_params
is_client_view = "q" in query_params

if is_client_view:
    try:
        # Descomprimimos los datos del link
        data_raw = base64.b64decode(query_params["q"]).decode()
        q_data = json.loads(data_raw)
        
        # DISEÑO DE LA COTIZACIÓN PARA EL CLIENTE
        st.markdown(f"<div class='header-quote'>🛡️ EDF SEGUROS - PROPUESTA COMERCIAL</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Asegurado:** {q_data['n']}")
            st.write(f"**Vehículo:** {q_data['v']}")
        with c2:
            st.write(f"**Fecha:** {date.today().strftime('%d/%m/%Y')}")
            st.write(f"**Asesor:** {q_data['e']}")
        
        st.write("### 💰 Comparativa de Opciones")
        df_view = pd.DataFrame(q_data['tab'])
        st.table(df_view) # Tabla fija, más estética para el cliente
        
        st.write("### ✅ Beneficios Incluidos")
        st.info(q_data['ben'])
        
        st.write("### 🏠 Coberturas Complementarias")
        col_comp = st.columns(3)
        col_comp[0].metric("Hogar", "Incluido", help=q_data['ch'])
        col_comp[1].metric("Alquiler", "15 días", help=q_data['ca'])
        col_comp[2].metric("Bici", "Opcional", help=q_data['cb'])
        
        with st.expander("Ver detalles de complementarias"):
            st.write(f"**Hogar:** {q_data['ch']}")
            st.write(f"**Alquiler:** {q_data['ca']}")
            st.write(f"**Bici:** {q_data['cb']}")

        st.markdown("---")
        st.caption("Esta es una propuesta sujeta a inspección y aprobación de la compañía aseguradora.")
        if st.button("🖨️ Imprimir / Guardar PDF"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        st.stop() # Detiene la ejecución aquí para que el cliente no vea el resto
    except:
        st.error("El link de la cotización no es válido o ha expirado.")
        st.stop()

# ==========================================
# 🔐 SEGURIDAD (SOLO PARA VOS)
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = u
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# (Sigue el código de carga de datos igual que antes...)
conn = st.connection("gsheets", type=GSheetsConnection)
@st.cache_data(ttl=60)
def cargar_datos_completos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        df['Premio USD (IVA inc)'] = pd.to_numeric(df.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0)
        df['Premio_Total_USD'] = (df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)).round(0)
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos_completos()
# ... resto de la sidebar ...
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    def get_list(col): return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
    f_ej = st.selectbox("Ejecutivo", get_list('Ejecutivo'))
    f_as = st.selectbox("Aseguradora", get_list('Aseguradora'))
    f_ra = st.selectbox("Ramo", get_list('Ramo'))
    f_co = st.selectbox("Corredor", get_list('Corredor'))
    f_ag = st.selectbox("Agente", get_list('Agente'))
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False; st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]

config_simple = {}
if "Adjunto (póliza)" in df_f.columns: config_simple["Adjunto (póliza)"] = st.column_config.LinkColumn("Póliza", display_text="📂")
if "Premio_Total_USD" in df_f.columns: config_simple["Premio_Total_USD"] = st.column_config.NumberColumn("Total USD", format="U$S %d")

tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1 y 2 (IGUAL QUE ANTES) ---
with tab1:
    busq = st.text_input("🔍 Buscar cliente o matrícula...")
    df_cartera = df_f.copy()
    if busq:
        mask = df_cartera.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)
        df_cartera = df_cartera[mask]
    st.dataframe(df_cartera, use_container_width=True, hide_index=True, column_config=config_simple)

with tab2:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty and "Fin de Vigencia" in df_f.columns:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        df_v = df_v[(df_v['Fin de Vigencia'] >= date(2020, 1, 1)) & (df_v['Fin de Vigencia'] <= date(2040, 12, 31))]
        if not df_v.empty:
            c_f1, c_f2 = st.columns([1, 2])
            hoy = date.today()
            with c_f1:
                f_ini = st.date_input("Vencimientos desde:", hoy.replace(day=1))
                f_fin = st.date_input("Vencimientos hasta:", hoy + timedelta(days=90))
            df_venc_final = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)]
            st.dataframe(df_venc_final.sort_values('Fin de Vigencia'), use_container_width=True, hide_index=True, column_config=config_simple)

# --- TAB 3: COTIZADOR CON GENERADOR DE LINK ---
with tab3:
    st.subheader("📝 Generador de Cotizaciones")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc_in = c1.text_input("Documento (CI / RUT)")
        nom_sug = ""
        if doc_in and not df_raw.empty:
            match = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains(doc_in)).any(axis=1)]
            if not match.empty: nom_sug = match.iloc[0].get('Asegurado (Nombre/Razón Social)', "")
        n_cot = c1.text_input("Asegurado", value=nom_sug)
        v_cot = c2.text_input("Vehículo (Marca/Modelo/Año)")
        e_cot = c3.selectbox("Hecha por:", sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["RDF"])

    t_edit = st.data_editor(pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": "Global"}]), num_rows="dynamic", use_container_width=True)

    st.write("### ✅ Detalles de Cobertura")
    col_a, col_b = st.columns(2)
    with col_a:
        b_cot = st.text_area("Beneficios Incluidos:", "• Auxilio mecánico 24hs.\n• Ayuda económica para cristales:\n  - USD 200 SBI / USD 200 BSE\n  - USD 100 SURA / USD 300 SANCOR\n  - Ilimitado MAPFRE\n• RC USD 500.000", height=250)
    with col_b:
        h_txt = "• Incendio Edificio e Incendio Contenido.\n• Hurto Contenido.\n• Cristales.\n• Responsabilidad Civil.\n• Daños por Agua."
        a_txt = "• Auto de cortesía por 15 días en caso de siniestro con un tercero identificado."
        b_txt = "• Hurto e Incendio de bicicleta en República Oriental del Uruguay y el mundo.\n• Responsabilidad Civil."
        c_h = st.text_area("Hogar:", value=h_txt, height=150)
        c_a = st.text_area("Alquiler:", value=a_txt, height=100)
        c_b = st.text_area("Bici:", value=b_txt, height=120)

    st.divider()
    
    # BOTÓN PARA GENERAR EL LINK
    if st.button("🔗 GENERAR LINK PARA CLIENTE", use_container_width=True, type="primary"):
        # Empaquetamos todo en un JSON y luego a Base64
        datos_enviar = {
            "n": n_cot, "v": v_cot, "e": e_cot,
            "tab": t_edit.to_dict(orient='records'),
            "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b
        }
        b64_data = base64.b64encode(json.dumps(datos_enviar).encode()).decode()
        # Generamos la URL (Streamlit Cloud detecta su propia URL base)
        url_cliente = f"https://edf-seguros.streamlit.app/?q={b64_data}" # Reemplaza con tu URL real si es distinta
        
        st.success("¡Link generado con éxito!")
        st.code(url_cliente, language=None)
        st.info("Copiá el link de arriba y envíaselo al cliente por WhatsApp.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_f.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Cartera Total (USD)", f"U$S {df_f['Premio_Total_USD'].sum():,.0f}")
        m2.metric("Pólizas", f"{len(df_f)} u.")
        m3.metric("Ticket Promedio", f"U$S {df_f['Premio_Total_USD'].mean():,.0f}")
        st.divider()
        c_g1, c_g2 = st.columns(2)
        with c_g1: st.plotly_chart(px.pie(df_f, names='Aseguradora' if 'Aseguradora' in df_f.columns else df_f.columns[0], values='Premio_Total_USD', title="Cartera por Cía", hole=0.4), use_container_width=True)
        with c_g2:
            if 'Ramo' in df_f.columns:
                r_counts = df_f['Ramo'].value_counts().reset_index(); r_counts.columns = ['Ramo', 'Cantidad']
                st.plotly_chart(px.bar(r_counts, x='Ramo', y='Cantidad', title="Pólizas por Ramo", color='Ramo'), use_container_width=True)
