import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import json
from datetime import datetime, date, timedelta
import plotly.express as px

# ==========================================
# ⚙️ CONFIGURACIÓN DE ENLACES
# ==========================================
# Planilla de la Empresa (Cartera para búsqueda y filtros)
URL_EMPRESA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"

# Tu Planilla Personal (Historial de Cotizaciones)
URL_MI_DRIVE = "https://docs.google.com/spreadsheets/d/1rd_ZCEUxolcgr9WaNUxzqjJVsL7tFvOOS4CaMZOrR8E/edit#gid=0"

TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS para Pantalla e Impresión
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .left-title { font-size: 30px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    .tabla-impresion { width: 100%; border-collapse: collapse; margin-top: 15px; }
    .tabla-impresion th, .tabla-impresion td { border: 1px solid #333 !important; padding: 10px; text-align: left; }
    .titulo-cuadro { background-color: #1E1E1E; color: white; padding: 5px 10px; font-weight: bold; margin-top: 15px; }
    .cuadro-beneficios { border: 1px solid #333; padding: 15px; margin-top: 10px; background-color: #fdfdfd; }
    @media print {
        .no-print, .stSidebar, .stTabs, button, header, footer, [data-testid="stToolbar"], .stCheckbox, .stNumberInput { display: none !important; }
        .print-only { display: block !important; position: absolute; left: 0; top: 0; width: 100%; }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD (LOGIN)
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", 
    "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", 
    "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", 
    "AC": "ACazarian2025", "MF": "MFlores2025", "JOE": "Joe2025", "ANDRE": "Andre2025"
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
# ⚙️ CARGA DE DATOS (CONEXIÓN GSHEETS)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_empresa():
    try:
        df = conn.read(spreadsheet=URL_EMPRESA, ttl=0)
        df.columns = df.columns.str.strip()
        # Cálculo de premios en USD
        u_col, p_col = 'Premio USD (IVA inc)', 'Premio UYU (IVA inc)'
        df['Premio_Total_USD'] = pd.to_numeric(df.get(u_col, 0), errors='coerce').fillna(0) + \
                                (pd.to_numeric(df.get(p_col, 0), errors='coerce').fillna(0) / TC_USD)
        if 'Fin de Vigencia' in df.columns:
            df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
            df['Fin_V_dt'] = df['Fin de Vigencia'].dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_empresa()

# ==========================================
# 🎯 FILTROS (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_actual']}")
    st.markdown("---")
    st.markdown("### 🔍 Filtros Globales")
    filtros = {}
    for col in ["Ejecutivo", "Aseguradora", "Corredor", "Agente", "Ramo"]:
        if col in df_raw.columns:
            opciones = ["Todos"] + sorted(df_raw[col].dropna().unique().tolist())
            filtros[col] = st.selectbox(col, opciones)
    
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
for col, val in filtros.items():
    if val != "Todos" and col in df_f.columns:
        df_f = df_f[df_f[col] == val]

st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA ---
with tab1:
    busq = st.text_input("Buscar en cartera...")
    if not df_f.empty:
        st.dataframe(df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f, use_container_width=True, hide_index=True)

# --- TAB 2: VENCIMIENTOS ---
with tab2:
    dias = st.slider("Vencimientos a (días):", 15, 120, 60)
    if 'Fin_V_dt' in df_f.columns:
        vence = df_f[(df_f['Fin_V_dt'] >= date.today()) & (df_f['Fin_V_dt'] <= date.today() + timedelta(days=dias))]
        st.dataframe(vence.sort_values('Fin_V_dt'), use_container_width=True, hide_index=True)

# --- TAB 3: COTIZADOR PROFESIONAL ---
with tab3:
    st.subheader("📝 Nueva Cotización")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            doc_input = st.text_input("CI / RUT del Cliente")
            nombre_auto = ""
            # BUSCADOR AUTOMÁTICO EN BASE EMPRESA
            if doc_input and not df_raw.empty:
                col_doc = 'Documento de Identidad (Rut/Cédula/Otros)'
                if col_doc in df_raw.columns:
                    match = df_raw[df_raw[col_doc].astype(str).str.contains(doc_input, na=False)]
                    if not match.empty:
                        nombre_auto = match.iloc[0]['Asegurado (Nombre/Razón Social)']
            nombre_cli = st.text_input("Asegurado", value=nombre_auto)
        with c2:
            vehiculo = st.text_input("Vehículo")
            zona = st.selectbox("Zona", ["Montevideo", "Canelones", "Maldonado", "Interior"])
        with c3:
            eje_list = sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["Oficina"]
            ejecutivo_cot = st.selectbox("Ejecutivo Responsable", eje_list)

    # Tabla de Costos
    if 'df_editor' not in st.session_state:
        st.session_state.df_editor = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    costos_finales = st.data_editor(st.session_state.df_editor, num_rows="dynamic", use_container_width=True)

    col_i, col_d = st.columns(2)
    with col_i:
        inc = st.text_area("✅ Beneficios Incluidos", "• Auxilio 24hs\n• Cristales/Cerraduras sin deducible\n• Responsabilidad Civil USD 500.000", height=150)
    with col_d:
        p_alq = st.number_input("Costo Alquiler", 3900)
        p_bici = st.number_input("Costo Bici", 70)
        det_text = f"- Vehículo de Alquiler: UYU {p_alq}\n- Seguro de Bicicleta: USD {p_bici}"
        det = st.text_area("➕ Detalle de Cobertura", value=det_text, height=100)

    if st.button("Guardar"):
        if not nombre_cli or not vehiculo:
            st.error("❌ Completa Nombre y Vehículo.")
        else:
            nueva = {
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Cliente": nombre_cli, "Documento": doc_input,
                "Vehiculo": vehiculo, "Zona": zona, "Ejecutivo": ejecutivo_cot, 
                "Tabla_Costos": costos_finales.to_json(orient='records'), "Detalles": f"Incluye: {inc}. Opcionales: {det}"
            }
            try:
                # GUARDADO EN TU DRIVE PERSONAL
                df_h = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", ttl=0)
                df_update = pd.concat([df_h, pd.DataFrame([nueva])], ignore_index=True)
                conn.update(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", data=df_update)
                st.session_state['cot_activa'] = nueva
                st.success("✅ Cotización guardada en tu Drive.")
            except Exception as e:
                st.error(f"Error al guardar: Verifica la pestaña 'Cotizaciones_Emitidas' en tu Drive. {e}")

    # Vista de Impresión
    if 'cot_activa' in st.session_state:
        c = st.session_state['cot_activa']
        tabla_html = pd.read_json(c['Tabla_Costos']).to_html(index=False, classes='tabla-impresion')
        st.markdown(f"""
            <div class="print-only">
                <h1>🛡️ EDF SEGUROS</h1><hr>
                <p><b>Asegurado:</b> {c['Cliente']} | <b>Vehículo:</b> {c['Vehiculo']}</p>
                {tabla_html}
                <div class="titulo-cuadro">DETALLES DE COBERTURA</div>
                <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Detalles']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.info("💡 Control + P para generar el PDF.")

    # HISTORIAL RECUPERADO
    st.divider()
    st.subheader("📂 Historial de Cotizaciones (Tu Drive)")
    busq_h = st.text_input("Filtrar historial...")
    try:
        df_hist = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", ttl=0).sort_index(ascending=False)
        if busq_h:
            df_hist = df_hist[df_hist.astype(str).apply(lambda x: x.str.contains(busq_h, case=False)).any(axis=1)]
        for i, r in df_hist.head(10).iterrows():
            ch1, ch2 = st.columns([0.85, 0.15])
            ch1.write(f"📄 {r['Fecha']} - **{r['Cliente']}** ({r['Vehiculo']})")
            if ch2.button("Ver", key=f"h_{i}"):
                st.session_state['cot_activa'] = r.to_dict()
                st.rerun()
    except: pass

# --- TAB 4: ANÁLISIS ---
with tab4:
    st.subheader("📊 Análisis de Cartera")
    if not df_f.empty:
        c1, c2 = st.columns(2)
        c1.metric("Cartera USD", f"{df_f['Premio_Total_USD'].sum():,.0f}")
        c2.metric("Pólizas", len(df_f))
        st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Distribución por Cía"), use_container_width=True)
