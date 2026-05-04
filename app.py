import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

st.markdown("<style>.main .block-container { padding-top: 1.5rem; } .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }</style>", unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD
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

# ==========================================
# ⚙️ CARGA Y PROCESAMIENTO (BÚSQUEDA FLEXIBLE)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos_completos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        col_usd = next((c for c in df.columns if "Premio USD" in c), None)
        col_uyu = next((c for c in df.columns if "Premio UYU" in c), None)
        col_fin = next((c for c in df.columns if "Fin de Vigencia" in c), "Fin de Vigencia")
        if col_usd: df[col_usd] = pd.to_numeric(df[col_usd], errors='coerce').fillna(0)
        if col_uyu: df[col_uyu] = pd.to_numeric(df[col_uyu], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = (df[col_usd if col_usd else df.columns[0]] + (df[col_uyu if col_uyu else df.columns[0]] / TC_USD)).round(0)
        df['Fin de Vigencia'] = pd.to_datetime(df[col_fin], dayfirst=True, errors='coerce').dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos_completos()

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

# --- CONFIGURACIÓN DE COLUMNAS (DEFINIDA AQUÍ PARA AMBAS PARTES) ---
COL_QUEREMOS = ["Asegurado (Nombre/Razón Social)", "Ramo", "Aseguradora", "Fin de Vigencia", "Detalle (Matricula o Referencia)", "Premio USD (IVA inc)", "Premio UYU (IVA inc)", "Premio_Total_USD", "Adjunto (póliza)"]
config_final = {col: st.column_config.Column(visible=(col in COL_QUEREMOS)) for col in df_f.columns}
if "Adjunto (póliza)" in config_final: config_final["Adjunto (póliza)"] = st.column_config.LinkColumn("Póliza", display_text="📂")
if "Premio_Total_USD" in config_final: config_final["Premio_Total_USD"] = st.column_config.NumberColumn("Total USD", format="U$S %d")

st.markdown("# 🛡️ EDF SEGUROS")
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])
# --- TAB 1: CARTERA ---
with tab1:
    busq = st.text_input("🔍 Buscar cliente o matrícula...")
    df_cartera = df_f.copy()
    if busq:
        mask = df_cartera.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)
        df_cartera = df_cartera[mask]
    
    st.dataframe(df_cartera, use_container_width=True, hide_index=True, column_config=config_final)

# --- TAB 2: VENCIMIENTOS (PROTEGIDO) ---
with tab2:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty:
        # Usamos la columna calculada de forma segura
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        # Limite de seguridad para evitar años erróneos del Excel
        df_v = df_v[(df_v['Fin de Vigencia'] >= date(2020, 1, 1)) & (df_v['Fin de Vigencia'] <= date(2040, 12, 31))]
        
        if not df_v.empty:
            c_f1, c_f2 = st.columns([1, 2])
            hoy = date.today()
            with c_f1:
                f_ini = st.date_input("Vencimientos desde:", hoy.replace(day=1))
                f_fin = st.date_input("Vencimientos hasta:", hoy + timedelta(days=90))
            
            df_venc_final = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)]
            st.dataframe(df_venc_final.sort_values('Fin de Vigencia'), use_container_width=True, hide_index=True, column_config=config_final)
    else:
        st.info("No hay datos de vencimientos disponibles.")

# --- TAB 3: COTIZADOR (CON TEXTOS PRE-ESCRITOS) ---
with tab3:
    st.subheader("📝 Generador de Cotizaciones")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc_in = c1.text_input("Documento (CI / RUT)")
        nom_sug = ""
        if doc_in:
            match = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains(doc_in)).any(axis=1)] if not df_raw.empty else pd.DataFrame()
            if not match.empty:
                nom_sug = match.iloc[0].get('Asegurado (Nombre/Razón Social)', "")
        
        n_cot = c1.text_input("Asegurado", value=nom_sug)
        v_cot = c2.text_input("Vehículo (Marca/Modelo/Año)")
        e_cot = c3.selectbox("Hecha por:", sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["RDF"])

    t_edit = st.data_editor(pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": "Global"}]), num_rows="dynamic", use_container_width=True)

    st.write("### ✅ Detalles de Cobertura")
    col_a, col_b = st.columns(2)
    with col_a:
        b_cot = st.text_area("Beneficios Incluidos:", "• Auxilio mecánico 24hs.\n• Ayuda económica para cristales:\n  - USD 200 SBI / USD 200 BSE\n  - USD 100 SURA / USD 300 SANCOR\n  - Ilimitado MAPFRE\n• RC USD 500.000", height=250)
    
    with col_b:
        st.write("**Coberturas Complementarias:**")
        h_txt = "• Incendio Edificio e Incendio Contenido.\n• Hurto Contenido.\n• Cristales.\n• Responsabilidad Civil.\n• Daños por Agua."
        a_txt = "• Auto de cortesía por 15 días en caso de siniestro con un tercero identificado."
        b_txt = "• Hurto e Incendio de bicicleta en República Oriental del Uruguay y el mundo.\n• Responsabilidad Civil."
        
        c_h = st.text_area("Hogar:", value=h_txt, height=150)
        c_a = st.text_area("Alquiler:", value=a_txt, height=100)
        c_b = st.text_area("Bici:", value=b_txt, height=130)

    def gen_ex():
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                workbook = writer.book
                ws = workbook.add_worksheet('Cotización')
                f_h = workbook.add_format({'bold': True, 'bg_color': '#1a4a7a', 'font_color': 'white', 'border': 1})
                ws.write('A1', '🛡️ EDF SEGUROS - PROPUESTA', workbook.add_format({'bold': True, 'font_size': 14}))
                ws.write('A3', f'Asegurado: {n_cot}'); ws.write('A4', f'Vehículo: {v_cot}'); ws.write('A5', f'Hecha por: {e_cot}')
                for c, col in enumerate(t_edit.columns): ws.write(7, c, col, f_h)
                for r, row in enumerate(t_edit.values):
                    for c, val in enumerate(row): ws.write(r+8, c, val, workbook.add_format({'border':1}))
                curr = 8 + len(t_edit) + 2
                ws.write(curr, 0, '✅ BENEFICIOS:', f_h); ws.write(curr+1, 0, b_cot)
                ws.write(curr+8, 0, '🏠 COMPLEMENTARIAS:', f_h)
                ws.write(curr+9, 0, f"Hogar:\n{c_h}\n\nAlquiler:\n{c_a}\n\nBici:\n{c_b}")
                ws.set_column('A:E', 30)
            return output.getvalue()
        except: return None

    st.download_button("📥 Descargar Propuesta (Excel)", data=gen_ex(), file_name=f"Cotizacion_{n_cot}.xlsx", use_container_width=True)

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_f.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Cartera Total (USD)", f"U$S {df_f['Premio_Total_USD'].sum():,.0f}")
        m2.metric("Pólizas", f"{len(df_f)} u.")
        m3.metric("Ticket Promedio", f"U$S {df_f['Premio_Total_USD'].mean():,.0f}")
        st.divider()
        c_g1, c_g2 = st.columns(2)
        with c_g1: st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía", hole=0.4), use_container_width=True)
        with c_g2:
            if 'Ramo' in df_f.columns:
                r_counts = df_f['Ramo'].value_counts().reset_index()
                r_counts.columns = ['Ramo', 'Cantidad']
                st.plotly_chart(px.bar(r_counts, x='Ramo', y='Cantidad', title="Pólizas por Ramo", color='Ramo'), use_container_width=True)
