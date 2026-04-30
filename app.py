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

# Estilos CSS: Web + Íconos + Lógica de Impresión Profesional
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .left-title { font-size: 30px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    
    /* Estilo para el link de carpeta clickeable */
    .folder-link {
        text-decoration: none;
        font-size: 1.3rem;
        cursor: pointer;
    }

    /* Estilos para la tabla de la cotización */
    .tabla-impresion {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    .tabla-impresion th, .tabla-impresion td {
        border: 1px solid #333 !important;
        padding: 8px;
        text-align: left;
    }
    .tabla-impresion th { background-color: #f2f2f2 !important; }
    
    .cuadro-beneficios {
        border: 1px solid #333;
        padding: 15px;
        margin-top: 10px;
        background-color: #fdfdfd;
    }
    .titulo-cuadro {
        background-color: #1E1E1E;
        color: white;
        padding: 5px 10px;
        font-weight: bold;
        margin-top: 15px;
    }

    /* LÓGICA DE IMPRESIÓN */
    @media print {
        /* Ocultar toda la interfaz de Streamlit */
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], 
        .stTabs, button, [data-testid="stToolbar"], .stCheckbox, .stMarkdown button { 
            display: none !important; 
        }
        
        /* El bloque 'print-only' DEBE ser visible y ocupar toda la hoja */
        .print-only { 
            display: block !important; 
            position: absolute;
            left: 0; top: 0; width: 100%;
            z-index: 9999;
            background-color: white;
        }
        
        .main .block-container { padding: 0; margin: 0; }
        .titulo-cuadro { -webkit-print-color-adjust: exact; }
    }

    /* En modo web normal, no mostrar el duplicado de impresión */
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025",
    "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025"
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
                else:
                    st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_principales():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        # Convertir a números
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        # Manejo de fechas
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
        df['Fin_V_dt'] = df['Fin de Vigencia'].dt.date
        return df
    except:
        return pd.DataFrame()

df_raw = cargar_datos_principales()

# ==========================================
# 🎯 SIDEBAR (FILTROS COMPLETOS)
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_actual']}")
    st.divider()
    st.markdown("### 🔍 Filtros Globales")
    
    # Filtros restaurados:
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    f_co = st.selectbox("Corredor", ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()))
    f_ag = st.selectbox("Agente", ["Todos"] + sorted(df_raw['Agente'].dropna().unique().tolist()))
    
    st.divider()
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

# Aplicación de filtros
df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]

st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA (Con ícono 📂) ---
with tab1:
    busqueda = st.text_input("Buscar cliente o matrícula...", placeholder="Ej: Juan Perez o ABC1234")
    df_tab1 = df_f.copy()
    if busqueda:
        mask = df_tab1.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_tab1 = df_tab1[mask]
    
    def format_icon(url):
        if pd.isna(url) or str(url).strip() == "": return ""
        return f'<a href="{url}" target="_blank" class="folder-link">📂</a>'

    if 'Link de la Poliza' in df_tab1.columns:
        df_tab1['Póliza'] = df_tab1['Link de la Poliza'].apply(format_icon)
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

# --- TAB 3: COTIZADOR (DISEÑO PROFESIONAL) ---
with tab3:
    st.subheader("📝 Generador de Cotizaciones")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ci_bus = st.text_input("CI / RUT del cliente")
            nombre_init = ""
            if ci_bus:
                match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(ci_bus, na=False)]
                if not match.empty: nombre_init = match.iloc[0]['Asegurado (Nombre/Razón Social)']
            nombre_cli = st.text_input("Asegurado", value=nombre_init)
        with c2:
            vehiculo = st.text_input("Vehículo (Marca/Modelo/Año)")
            zona = st.selectbox("Zona", ["Montevideo", "Canelones", "Maldonado", "Interior"])

    st.markdown("#### 💰 Tabla Comparativa")
    df_cot = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    cot_editada = st.data_editor(df_cot, num_rows="dynamic", use_container_width=True)

    izq, der = st.columns(2)
    inc = izq.text_area("✅ Beneficios Incluidos", value="• Auxilio mecánico 24hs.\n• Cristales, cerraduras y espejos sin deducible.\n• RC USD 500.000.", height=150)
    opc = der.text_area("➕ Adicionales", value="• Hogar: Incendio USD 100.000 / Hurto USD 5.000\n• Alquiler: 15 días por choque.", height=150)

    if st.button("👁️ Generar Vista de Impresión"):
        st.session_state['propuesta'] = {
            "Fecha": date.today().strftime("%d/%m/%Y"),
            "Cliente": nombre_cli, "Vehiculo": vehiculo,
            "Tabla": cot_editada.to_html(index=False, classes='tabla-impresion'),
            "Inc": inc, "Opc": opc
        }

    # BLOQUE EXCLUSIVO PARA IMPRESIÓN (Invisible en la web)
    if 'propuesta' in st.session_state:
        p = st.session_state['propuesta']
        st.markdown(f"""
            <div class="print-only">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h1 style="margin: 0;">🛡️ EDF SEGUROS</h1>
                    <p><b>Fecha:</b> {p['Fecha']}</p>
                </div>
                <hr>
                <p style="font-size: 1.2rem;"><b>Propuesta para:</b> {p['Cliente']}</p>
                <p><b>Vehículo:</b> {p['Vehiculo']}</p>
                <br>
                {p['Tabla']}
                <div class="titulo-cuadro">✅ BENEFICIOS INCLUIDOS</div>
                <div class="cuadro-beneficios" style="white-space: pre-wrap;">{p['Inc']}</div>
                <div class="titulo-cuadro">➕ COBERTURAS ADICIONALES</div>
                <div class="cuadro-beneficios" style="white-space: pre-wrap;">{p['Opc']}</div>
                <br>
                <p style="text-align: center; font-size: 0.8rem; color: #666;">Cotización sujeta a inspección y políticas de la aseguradora.</p>
            </div>
        """, unsafe_allow_html=True)
        st.success("Propuesta lista. Presiona **Control + P** para guardar PDF.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_f.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Cartera Total", f"USD {df_f['Premio_Total_USD'].sum():,.0f}")
        c2.metric("Pólizas", len(df_f))
        c3.metric("Promedio", f"USD {df_f['Premio_Total_USD'].mean():,.0f}")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Distribución por Cía", hole=0.3), use_container_width=True)
        with col_b:
            st.plotly_chart(px.bar(df_f['Ramo'].value_counts().reset_index(), x='Ramo', y='count', title="Pólizas por Ramo"), use_container_width=True)
