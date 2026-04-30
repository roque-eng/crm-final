import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS para Impresión y Diseño
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .tabla-impresion { width: 100%; border-collapse: collapse; margin-top: 15px; }
    .tabla-impresion th, .tabla-impresion td { border: 1px solid #333 !important; padding: 10px; text-align: left; }
    .cuadro-beneficios { border: 1px solid #333; padding: 15px; margin-top: 10px; background-color: #fdfdfd; }
    .titulo-cuadro { background-color: #1E1E1E; color: white; padding: 5px 10px; font-weight: bold; margin-top: 15px; }
    @media print {
        .no-print, .stSidebar, .stTabs, button, header, footer, [data-testid="stToolbar"], .stCheckbox, .stNumberInput { display: none !important; }
        .print-only { display: block !important; position: absolute; left: 0; top: 0; width: 100%; }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 USUARIOS
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
# ⚙️ CARGA DE DATOS ROBUSTA
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        # Limpieza básica para evitar errores de tipo
        if 'Premio USD (IVA inc)' in df.columns:
            df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        if 'Premio UYU (IVA inc)' in df.columns:
            df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df.get('Premio USD (IVA inc)', 0) + (df.get('Premio UYU (IVA inc)', 0) / TC_USD)
        
        if 'Fin de Vigencia' in df.columns:
            df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
            df['Fin_V_dt'] = df['Fin de Vigencia'].dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos()

# ==========================================
# 🎯 SIDEBAR - FILTROS DINÁMICOS
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_actual']}")
    st.markdown("---")
    st.markdown("### 🔍 Filtros de Cartera")
    
    filtros = {}
    # Lista de columnas que queremos filtrar si existen
    columnas_interes = ["Ejecutivo", "Aseguradora", "Corredor", "Agente", "Ramo"]
    
    for col in columnas_interes:
        if col in df_raw.columns:
            opciones = ["Todos"] + sorted(df_raw[col].dropna().unique().tolist())
            filtros[col] = st.selectbox(col, opciones)
        else:
            filtros[col] = "Todos"

    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

# Aplicar filtros
df_f = df_raw.copy()
for col, val in filtros.items():
    if val != "Todos" and col in df_f.columns:
        df_f = df_f[df_f[col] == val]

st.markdown('<h2 style="color: #1E1E1E;">🛡️ EDF SEGUROS</h2>', unsafe_allow_html=True)

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1 & 2: CARTERA Y VENCIMIENTOS ---
with tab1:
    busq = st.text_input("Buscar en cartera filtrada...")
    st.dataframe(df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f, use_container_width=True, hide_index=True)

with tab2:
    dias = st.slider("Vencimientos en los próximos (días):", 15, 120, 60)
    if 'Fin_V_dt' in df_f.columns:
        df_v = df_f[(df_f['Fin_V_dt'] >= date.today()) & (df_f['Fin_V_dt'] <= date.today() + timedelta(days=dias))]
        st.dataframe(df_v.sort_values('Fin_V_dt'), use_container_width=True)

# --- TAB 3: COTIZADOR CON FILTRO DE EJECUTIVO ---
with tab3:
    st.subheader("📝 Nueva Cotización")
    with st.container(border=True):
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            ci_bus = st.text_input("CI / RUT")
            nombre_cli = st.text_input("Cliente")
        with c2:
            vehiculo = st.text_input("Vehículo")
            zona = st.selectbox("Zona", ["Montevideo", "Canelones", "Maldonado", "Interior"])
        with c3:
            # Aquí asignamos el ejecutivo a la cotización
            ejes_list = sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["Sin Asignar"]
            ejecutivo_cot = st.selectbox("Ejecutivo Responsable", ejes_list)

    st.markdown("#### 💰 Costos")
    if 'data_cot' not in st.session_state:
        st.session_state.data_cot = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    cot_editada = st.data_editor(st.session_state.data_cot, num_rows="dynamic", use_container_width=True)

    col_i, col_d = st.columns(2)
    with col_i:
        st.markdown("#### ✅ Incluidos")
        inc = st.text_area("Fijos:", "• Auxilio 24hs\n• Cristales/Cerraduras\n• RC USD 500.000", height=150)
    with col_d:
        st.markdown("#### ➕ Detalle de Cobertura")
        ca, cb = st.columns(2)
        p_alq = ca.number_input("Precio Alquiler", 3900)
        p_bici = cb.number_input("Precio Bici", 70)
        t_opc = f"- Auxilio de Alquiler: UYU {p_alq}\n- Seguro Bici: USD {p_bici}"
        det_cob = st.text_area("Opcionales:", t_opc, height=100)

    if st.button("💾 Guardar Cotización", use_container_width=True):
        nueva = {
            "Fecha": date.today().strftime("%d/%m/%Y"), "Cliente": nombre_cli, "Documento": ci_bus,
            "Vehiculo": vehiculo, "Zona": zona, "Ejecutivo": ejecutivo_cot, # Guardamos el ejecutivo
            "Tabla": cot_editada.to_json(), "Incluidos": inc, "Opcionales": det_cob
        }
        try:
            df_h = conn.read(spreadsheet=URL_HOJA, worksheet="Cotizaciones_Emitidas")
            conn.update(spreadsheet=URL_HOJA, worksheet="Cotizaciones_Emitidas", data=pd.concat([df_h, pd.DataFrame([nueva])], ignore_index=True))
            st.session_state['cot_activa'] = nueva
            st.success(f"✅ Guardada por {ejecutivo_cot}")
        except: st.error("Error: ¿Existe la pestaña 'Cotizaciones_Emitidas'?")

    if 'cot_activa' in st.session_state:
        c = st.session_state['cot_activa']
        tabla_html = pd.read_json(c['Tabla']).to_html(index=False, classes='tabla-impresion')
        st.markdown(f"""
            <div class="print-only">
                <h1>🛡️ EDF SEGUROS</h1><hr>
                <p><b>Propuesta para:</b> {c['Cliente']} | <b>Ejecutivo:</b> {c['Ejecutivo']}</p>
                <p><b>Vehículo:</b> {c['Vehiculo']}</p>
                {tabla_html}
                <div class="titulo-cuadro">✅ BENEFICIOS INCLUIDOS</div>
                <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Incluidos']}</div>
                <div class="titulo-cuadro">➕ DETALLE DE COBERTURA</div>
                <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Opcionales']}</div>
            </div>
        """, unsafe_allow_html=True)

    # HISTORIAL CON BUSCADOR (FILTRO)
    st.markdown("---")
    st.subheader("📂 Historial de Cotizaciones")
    busqueda_hist = st.text_input("Filtrar historial por Ejecutivo o Cliente...")
    try:
        df_hist = conn.read(spreadsheet=URL_HOJA, worksheet="Cotizaciones_Emitidas").sort_index(ascending=False)
        if busqueda_hist:
            df_hist = df_hist[df_hist.astype(str).apply(lambda x: x.str.contains(busqueda_hist, case=False)).any(axis=1)]
        
        for i, r in df_hist.head(10).iterrows():
            colh1, colh2 = st.columns([0.8, 0.2])
            colh1.write(f"📄 {r['Fecha']} - **{r['Cliente']}** (Eje: {r.get('Ejecutivo', 'N/A')})")
            if colh2.button("Ver", key=f"btn_{i}"):
                st.session_state['cot_activa'] = r.to_dict()
                st.rerun()
    except: st.info("No hay historial.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    st.subheader("📊 Análisis General")
    if not df_f.empty:
        c1, c2 = st.columns(2)
        c1.metric("Cartera Total USD", f"{df_f['Premio_Total_USD'].sum():,.0f}")
        c2.metric("Pólizas", len(df_f))
        st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Distribución por Compañía"), use_container_width=True)
