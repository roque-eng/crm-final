import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime
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
        # Precios sin decimales
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = (df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)).round(0)
        
        # Formato de Fechas (Solo fecha, sin hora)
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
    
    # Filtro de Tiempo
    fecha_min = df_raw['Fin de Vigencia'].min() if not df_raw.empty else date.today()
    fecha_max = df_raw['Fin de Vigencia'].max() if not df_raw.empty else date.today()
    rango_fecha = st.date_input("Filtrar por Vencimiento", [fecha_min, fecha_max])
    
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

# Aplicar Filtros
df_f = df_raw.copy()
if len(rango_fecha) == 2:
    df_f = df_f[(df_f['Fin de Vigencia'] >= rango_fecha[0]) & (df_f['Fin de Vigencia'] <= rango_fecha[1])]
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]

# ==========================================
# 📑 PESTAÑAS
# ==========================================
st.markdown("# 🛡️ EDF SEGUROS")
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

with tab1:
    busq = st.text_input("🔍 Buscar cliente o matrícula...")
    if busq:
        df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
    st.dataframe(df_f, use_container_width=True, hide_index=True,
                 column_config={"Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")})

with tab2:
    st.subheader("📅 Próximos Vencimientos")
    st.dataframe(df_f.sort_values('Fin de Vigencia'), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("📝 Generar Cotización")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        doc = c1.text_input("CI / RUT")
        # Autocompletado
        nom_s = ""
        if doc:
            m = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(doc)]
            if not m.empty: nom_s = m.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        nombre = c1.text_input("Asegurado", value=nom_s)
        vehi = c2.text_input("Vehículo")
        zona = c2.selectbox("Zona", ["Montevideo", "Interior", "Maldonado"])
        eje = c3.selectbox("Hecha por:", sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))

    tabla_edit = st.data_editor(pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": "Global"}]), num_rows="dynamic", use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Beneficios Incluidos:**")
        texto_ben = st.text_area("Editar Beneficios", 
            "• Auxilio mecánico 24hs.\n• Ayuda económica para cristales:\n  - USD 200 SBI / USD 200 BSE\n  - USD 100 SURA / USD 300 SANCOR\n  - Ilimitado MAPFRE\n• RC USD 500.000", height=180)
    
    with col_b:
        st.write("**Coberturas Complementarias:**")
        pre_hogar = st.text_input("Precio Hogar (ej: Incluido o USD 50)", "Incluido")
        pre_alq = st.text_input("Precio Alquiler (ej: 15 días o USD 30)", "15 días")
        pre_bici = st.text_input("Precio Bici", "Opcional")

    def generar_excel_cot():
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            ws = workbook.add_worksheet('Cotización')
            f_h = workbook.add_format({'bold': True, 'bg_color': '#1a4a7a', 'font_color': 'white', 'border': 1})
            ws.write('A1', '🛡️ EDF SEGUROS - PROPUESTA', workbook.add_format({'bold': True, 'font_size': 14}))
            ws.write('A3', f'Asegurado: {nombre}')
            ws.write('A4', f'Vehículo: {vehi}')
            ws.write('A5', f'Hecha por: {eje}')
            # Escribir Tabla
            for c, col in enumerate(tabla_edit.columns): ws.write(7, c, col, f_h)
            for r, row in enumerate(tabla_edit.values):
                for c, val in enumerate(row): ws.write(r+8, c, val)
            
            curr = 8 + len(tabla_edit) + 2
            ws.write(curr, 0, 'BENEFICIOS:', f_h)
            ws.write(curr+1, 0, texto_ben)
            ws.write(curr+5, 0, 'COBERTURAS COMPLEMENTARIAS:', f_h)
            ws.write(curr+6, 0, f"Hogar: {pre_hogar} | Alquiler: {pre_alq} | Bici: {pre_bici}")
            ws.set_column('A:E', 20)
        return output.getvalue()

    st.download_button("📥 Descargar Cotización Profesional", data=generar_excel_cot(), file_name=f"Cotizacion_{nombre}.xlsx", use_container_width=True)

with tab4:
    m1, m2 = st.columns(2)
    m1.metric("Cartera Total (USD)", f"{df_f['Premio_Total_USD'].sum():,.0f}")
    m2.metric("Pólizas", len(df_f))
    st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Compañía"), use_container_width=True)
