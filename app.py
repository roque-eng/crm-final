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

# Estilos CSS mejorados para visualización y botones de enlace
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .left-title { font-size: 30px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    
    /* Estilos para impresión profesional */
    .tabla-impresion { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; margin-top: 15px; }
    .tabla-impresion th, .tabla-impresion td { border: 1px solid #333 !important; padding: 10px; text-align: left; }
    .tabla-impresion th { background-color: #f2f2f2 !important; }
    .cuadro-beneficios { border: 1px solid #333; padding: 15px; margin-top: 10px; background-color: #fdfdfd; }
    .titulo-cuadro { background-color: #1E1E1E; color: white; padding: 5px 10px; font-weight: bold; margin-top: 15px; }

    /* Estilo para el link de póliza tipo botón */
    .btn-poliza {
        display: inline-block; padding: 4px 8px; background-color: #f0f2f6; 
        color: #31333F; text-decoration: none; border-radius: 4px; border: 1px solid #dcdfe6;
        font-size: 12px; font-weight: 500;
    }
    .btn-poliza:hover { background-color: #e6e9ef; }

    @media print {
        .no-print, .stSidebar, .stTabs, button, header, footer, [data-testid="stToolbar"], .stCheckbox, .stMarkdown button { 
            display: none !important; 
        }
        .print-only { 
            display: block !important; 
            position: absolute; left: 0; top: 0; width: 100%;
        }
        table, tr, td, th { page-break-inside: avoid !important; }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428", "AB": "ABentancor2025", "JOE": "Joe2025", "ANDRE": "Andre2025"
}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False

if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
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
# ⚙️ CARGA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_principales():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
        df['Fin_V_dt'] = df['Fin de Vigencia'].dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos_principales()

# ==========================================
# 🎯 SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_actual']}")
    st.divider()
    st.subheader("🔍 Filtros")
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]

st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA (Con ícono de póliza) ---
with tab1:
    busqueda = st.text_input("Buscar cliente o matrícula...")
    df_tab1 = df_f.copy()
    if busqueda:
        mask = df_tab1.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_tab1 = df_tab1[mask]
    
    # Formatear link de póliza como botón
    def format_link(url):
        if pd.isna(url) or str(url) == "": return "N/A"
        return f'<a href="{url}" target="_blank" class="btn-poliza">📄 Abrir</a>'

    if 'Link de la Poliza' in df_tab1.columns:
        df_tab1['Póliza'] = df_tab1['Link de la Poliza'].apply(format_link)
        cols = ['Póliza'] + [c for c in df_tab1.columns if c not in ['Póliza', 'Link de la Poliza', 'Fin_V_dt', 'Premio_Total_USD']]
        st.write(df_tab1[cols].to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.dataframe(df_tab1, use_container_width=True, hide_index=True)

# --- TAB 2: VENCIMIENTOS ---
with tab2:
    dias_v = st.slider("Días a futuro:", 15, 120, 30)
    hoy = date.today()
    limite = hoy + timedelta(days=dias_v)
    df_v = df_f[(df_f['Fin_V_dt'] >= hoy) & (df_f['Fin_V_dt'] <= limite)].sort_values('Fin_V_dt')
    st.dataframe(df_v, use_container_width=True, hide_index=True)

# --- TAB 3: COTIZADOR (MODO IMPRESIÓN) ---
with tab3:
    st.subheader("📝 Generador de Cotizaciones")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ci_bus = st.text_input("CI / RUT para búsqueda rápida")
            nombre_init = ""
            if ci_bus:
                match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(ci_bus, na=False)]
                if not match.empty: nombre_init = match.iloc[0]['Asegurado (Nombre/Razón Social)']
            nombre_cli = st.text_input("Nombre y Apellido", value=nombre_init)
        with c2:
            vehiculo = st.text_input("Vehículo (Marca, Modelo, Año)")
            ejecutivo_firma = st.selectbox("Ejecutivo que firma", ["Roque de Freitas", "Joe", "Andre"])

    st.markdown("#### 💰 Comparativa")
    df_cot_base = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    cot_editada = st.data_editor(df_cot_base, num_rows="dynamic", use_container_width=True)

    col_izq, col_der = st.columns(2)
    with col_izq:
        def_inc = "• Auxilio mecánico 24hs.\n• Cristales, cerraduras y espejos sin deducible.\n• Responsabilidad Civil USD 500.000."
        beneficios_inc = st.text_area("✅ Beneficios Incluidos", value=def_inc, height=150)
    with col_der:
        def_opc = "• Vehículo de Alquiler por 15 días: UYU 3.900\n• Seguro de Hogar (Incendio/Hurto): USD 150 anual."
        beneficios_opc = st.text_area("➕ Adicionales/Opcionales", value=def_opc, height=150)

    if st.button("👁️ Generar Vista de Impresión"):
        st.session_state['imprimir_cot'] = {
            "Fecha": date.today().strftime("%d/%m/%Y"),
            "Cliente": nombre_cli, "Vehiculo": vehiculo, "Ejecutivo": ejecutivo_firma,
            "Tabla": cot_editada.to_html(index=False, classes='tabla-impresion'),
            "Inc": beneficios_inc, "Opc": beneficios_opc
        }

    if 'imprimir_cot' in st.session_state:
        ic = st.session_state['imprimir_cot']
        st.markdown(f"""
            <div class="print-only">
                <div style="display: flex; justify-content: space-between;">
                    <h1 style="margin:0;">🛡️ EDF SEGUROS</h1>
                    <p><b>Fecha:</b> {ic['Fecha']}</p>
                </div>
                <hr>
                <p><b>Asegurado:</b> {ic['Cliente']} | <b>Vehículo:</b> {ic['Vehiculo']}</p>
                <p><b>Ejecutivo:</b> {ic['Ejecutivo']}</p>
                {ic['Tabla']}
                <div class="titulo-cuadro">BENEFICIOS INCLUIDOS</div>
                <div class="cuadro-beneficios" style="white-space: pre-wrap;">{ic['Inc']}</div>
                <div class="titulo-cuadro">COBERTURAS ADICIONALES</div>
                <div class="cuadro-beneficios" style="white-space: pre-wrap;">{ic['Opc']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.success("✅ Propuesta generada abajo. Presiona **Ctrl + P** para guardar como PDF.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_f.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Cartera Total", f"USD {df_f['Premio_Total_USD'].sum():,.0f}")
        c2.metric("Pólizas", len(df_f))
        c3.metric("Ticket Promedio", f"USD {df_f['Premio_Total_USD'].mean():,.0f}")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía"), use_container_width=True)
        with col_b:
            st.plotly_chart(px.bar(df_f['Ramo'].value_counts().reset_index(), x='Ramo', y='count', title="Pólizas por Ramo"), use_container_width=True)
