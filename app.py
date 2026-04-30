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

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f0f2f6; border-radius: 5px; padding: 10px 20px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD
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
        df['Premio_Total_USD'] = (df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)).round(0)
        df['Inicio de Vigencia'] = pd.to_datetime(df['Inicio de Vigencia'], dayfirst=True, errors='coerce').dt.date
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos_completos()

# ==========================================
# 🎯 SIDEBAR (FILTROS Y TIEMPO)
# ==========================================
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    st.subheader("📅 Rango de Vencimientos")
    if not df_raw.empty:
        f_min = df_raw['Fin de Vigencia'].min()
        f_max = df_raw['Fin de Vigencia'].max()
        rango_s = st.date_input("Filtrar fechas:", [f_min, f_max])
    
    st.subheader("🔍 Otros Filtros")
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
if not df_raw.empty and isinstance(rango_s, list) and len(rango_s) == 2:
    df_f = df_f[(df_f['Fin de Vigencia'] >= rango_s[0]) & (df_f['Fin de Vigencia'] <= rango_s[1])]
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]

st.markdown("# 🛡️ EDF SEGUROS")
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])
# --- TAB 1: CARTERA ---
with tab1:
    busq = st.text_input("🔍 Buscar cliente o matrícula...")
    df_cartera = df_f.copy()
    if busq:
        mask = df_cartera.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)
        df_cartera = df_cartera[mask]
    
    st.dataframe(
        df_cartera, use_container_width=True, hide_index=True,
        column_config={"Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")}
    )

# --- TAB 2: VENCIMIENTOS ---
with tab2:
    st.subheader("🔄 Control de Vencimientos")
    st.dataframe(df_f.sort_values('Fin de Vigencia'), use_container_width=True, hide_index=True)

# --- TAB 3: COTIZADOR (AJUSTADO SEGÚN TUS PEDIDOS) ---
with tab3:
    st.subheader("📝 Generador de Cotizaciones")
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc_in = c1.text_input("Documento (CI / RUT)")
        
        # Autocompletado inteligente
        nom_sug = ""
        if doc_in:
            match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(doc_in)]
            if not match.empty:
                nom_sug = match.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        nombre_cot = c1.text_input("Asegurado", value=nom_sug)
        vehi_cot = c2.text_input("Vehículo (Marca/Modelo/Año)")
        ejecutivo_cot = c3.selectbox("Hecha por:", sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))

    st.write("### 💰 Tabla Comparativa de Costos")
    df_init = pd.DataFrame([
        {"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": "Global"},
        {"Aseguradora": "SBI", "Contado": 0, "10 Cuotas": 0, "Deducible": "Global"}
    ])
    tabla_edit = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)

    st.write("### ✅ Beneficios y Coberturas Complementarias")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("**Beneficios Incluidos:**")
        beneficios_cot = st.text_area("Editar Beneficios", 
            "• Auxilio mecánico 24hs.\n• Ayuda económica para cristales:\n  - USD 200 SBI / USD 200 BSE\n  - USD 100 SURA / USD 300 SANCOR\n  - Ilimitado MAPFRE\n• RC USD 500.000", height=200)
    
    with col_b:
        st.write("**Coberturas Complementarias:**")
        c_hogar = st.text_input("Seguro Hogar (Precio/Detalle)", "Incluido")
        c_alq = st.text_input("Auto Alquiler (Precio/Detalle)", "15 días por choque")
        c_bici = st.text_input("Seguro Bici", "Opcional")

    # Función para generar el Excel Profesional
    def generar_excel_format():
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            ws = workbook.add_worksheet('Cotización')
            
            # Formatos de diseño
            f_tit = workbook.add_format({'bold': True, 'font_size': 14})
            f_header = workbook.add_format({'bold': True, 'bg_color': '#1a4a7a', 'font_color': 'white', 'border': 1})
            f_sub = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1})
            f_border = workbook.add_format({'border': 1})

            ws.write('A1', '🛡️ EDF SEGUROS - PROPUESTA', f_tit)
            ws.write('A3', f'Asegurado: {nombre_cot}')
            ws.write('A4', f'Vehículo: {vehi_cot}')
            ws.write('A5', f'Hecha por: {ejecutivo_cot}')

            # Tabla de Precios
            start_row = 7
            for col_num, value in enumerate(tabla_edit.columns.values):
                ws.write(start_row, col_num, value, f_header)
            for row_num, row_data in enumerate(tabla_edit.values):
                for col_num, cell_data in enumerate(row_data):
                    ws.write(start_row + 1 + row_num, col_num, cell_data, f_border)

            # Coberturas
            curr = start_row + len(tabla_edit) + 2
            ws.write(curr, 0, '✅ BENEFICIOS:', f_sub)
            ws.write(curr + 1, 0, beneficios_cot)
            ws.write(curr + 6, 0, '🏠 COMPLEMENTARIAS:', f_sub)
            ws.write(curr + 7, 0, f"Hogar: {c_hogar} | Alquiler: {c_alq} | Bici: {c_bici}")
            ws.set_column('A:E', 25)
        return output.getvalue()

    st.download_button(
        label="📥 Descargar Propuesta Profesional (Excel)",
        data=generar_excel_format(),
        file_name=f"Cotizacion_{nombre_cot}.xlsx",
        use_container_width=True
    )

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_f.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Cartera Total (USD)", f"U$S {df_f['Premio_Total_USD'].sum():,.0f}")
        m2.metric("Pólizas", f"{len(df_f)} u.")
        m3.metric("Ticket Promedio", f"U$S {df_f['Premio_Total_USD'].mean():,.0f}")
        
        st.divider()
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía", hole=0.4), use_container_width=True)
        with col_g2:
            ramos = df_f['Ramo'].value_counts().reset_index()
            ramos.columns = ['Ramo', 'Cantidad']
            st.plotly_chart(px.bar(ramos, x='Ramo', y='Cantidad', color='Ramo', title="Pólizas por Ramo"), use_container_width=True)
