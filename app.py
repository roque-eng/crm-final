import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================


aca encontre la versión del código que me gustaba antes de hacer los mil intentos de guardado en un sheets en mi drive personal....arranquemos de esta base nuevamente y veamos la forma de que la cotización quede en versión imprimible para poder adjuntarle a un cliente por mail y guardar las cotizaciones en pdf en drive...ya que no pudimos configurar que se escriba en un sheets automáticamente.
# ⚙️ CONFIGURACIÓN Y CONEXIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS para Impresión y Diseño
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .left-title { font-size: 30px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    
    /* Estilos para la tabla e informes */
    .tabla-impresion {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        margin-top: 15px;
    }
    .tabla-impresion th, .tabla-impresion td {
        border: 1px solid #333 !important;
        padding: 10px;
        text-align: left;
    }
    .tabla-impresion th { background-color: #f2f2f2 !important; }
    
    .cuadro-beneficios {
        border: 1px solid #333;
        padding: 15px;
        margin-top: 10px;
        background-color: #fdfdfd;
        font-family: sans-serif;
    }
    .titulo-cuadro {
        background-color: #1E1E1E;
        color: white;
        padding: 5px 10px;
        font-weight: bold;
        margin-top: 15px;
    }

    @media print {
        .no-print, .stSidebar, .stTabs, button, header, footer, [data-testid="stToolbar"], .stCheckbox { 
            display: none !important; 
        }
        .print-only { 
            display: block !important; 
            position: absolute;
            left: 0; top: 0; width: 100%;
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
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
        df['Fin_V_dt'] = df['Fin de Vigencia'].dt.date
        return df
    except:
        return pd.DataFrame()

df_raw = cargar_datos_principales()

# ==========================================
# 🎯 SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_actual']}")
    st.markdown("---")
    st.markdown("### 🔍 Filtros de Cartera")
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    
    st.markdown("---")
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]

# Título Principal
st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)

# ==========================================
# 📑 PESTAÑAS (Orden: Cartera, Vencimientos, Cotizador, Análisis)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA ---
with tab1:
    busqueda = st.text_input("Buscar cliente o póliza...", placeholder="Ej: Juan Perez o 123456")
    df_tab1 = df_f.copy()
    if busqueda:
        mask = df_tab1.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_tab1 = df_tab1[mask]
    st.dataframe(df_tab1, use_container_width=True, hide_index=True)

# --- TAB 2: VENCIMIENTOS ---
with tab2:
    dias_v = st.slider("Días a futuro:", 15, 365, 60)
    hoy = date.today()
    limite = hoy + timedelta(days=dias_v)
    df_v = df_f[(df_f['Fin_V_dt'] >= hoy) & (df_f['Fin_V_dt'] <= limite)].sort_values('Fin_V_dt')
    st.dataframe(df_v, use_container_width=True, hide_index=True)

# --- TAB 3: COTIZADOR ---
with tab3:
    st.subheader("📝 Generador de Cotizaciones")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ci_bus = st.text_input("CI / RUT del cliente")
            nombre_init = ""
            if ci_bus:
                match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(ci_bus)]
                if not match.empty: nombre_init = match.iloc[0]['Asegurado (Nombre/Razón Social)']
            nombre_cli = st.text_input("Nombre y Apellido", value=nombre_init)
        with c2:
            vehiculo = st.text_input("Vehículo (Marca, Modelo, Año)")
            zona = st.selectbox("Zona de Circulación", ["Montevideo", "Canelones", "Maldonado", "Interior"])

    st.markdown("#### 💰 Comparativa de Aseguradoras")
    if 'data_cot' not in st.session_state:
        st.session_state.data_cot = pd.DataFrame([
            {"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"},
            {"Aseguradora": "SBI", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}
        ])
    cot_editada = st.data_editor(st.session_state.data_cot, num_rows="dynamic", use_container_width=True)

    col_izq, col_der = st.columns(2)
    with col_izq:
        st.markdown("#### ✅ Beneficios Incluidos")
        def_incluidos = "• Auxilio mecánico nacional e internacional 24hs.\n• Cristales, cerraduras y espejos sin deducible.\n• Responsabilidad Civil hasta USD 500.000."
        beneficios_incluidos = st.text_area("Ya vienen con el seguro:", value=def_incluidos, height=200)

    with col_der:
        st.markdown("#### ➕ Detalle de Cobertura (Opcionales)")
        cc1, cc2, cc3 = st.columns(3)
        costo_alq = cc1.number_input("Alquiler (UYU)", value=3900)
        costo_bici = cc2.number_input("Bici (USD)", value=70)
        costo_casa = cc3.number_input("Casa (USD)", value=150)

        b1 = st.checkbox(f"Incluir Alquiler (UYU {costo_alq})")
        b2 = st.checkbox(f"Incluir Bici (USD {costo_bici})")
        b3 = st.checkbox(f"Incluir Casa (USD {costo_casa})")
        
        texto_opc = ""
        if b1: texto_opc += f"a) Vehículo de Alquiler por 15 días: costo anual UYU {costo_alq}.\n"
        if b2: texto_opc += f"b) Seguro para tu bici (hasta USD 1000): costo anual USD {costo_bici}.\n"
        if b3: texto_opc += f"c) Seguro para tu casa (Incendio USD 100.000 Edificio, Incendio USD 50.000 contenido, Hurto USD 5.000 contenido): costo anual USD {costo_casa}.\n"
        beneficios_opcionales = st.text_area("Texto Detalle de Cobertura:", value=texto_opc, height=100)

    if st.button("💾 Guardar y Generar PDF", use_container_width=True):
        nueva_cot = {
            "Fecha": date.today().strftime("%d/%m/%Y"), "Cliente": nombre_cli, "Documento": ci_bus,
            "Vehiculo": vehiculo, "Zona": zona, "Detalle_Costos": cot_editada.to_json(),
            "Incluidos": beneficios_incluidos, "Opcionales": beneficios_opcionales
        }
        try:
            df_historial = conn.read(spreadsheet=URL_HOJA, worksheet="Cotizaciones_Emitidas")
            df_nuevo = pd.concat([df_historial, pd.DataFrame([nueva_cot])], ignore_index=True)
            conn.update(spreadsheet=URL_HOJA, worksheet="Cotizaciones_Emitidas", data=df_nuevo)
            st.session_state['cot_activa'] = nueva_cot
            st.success("✅ Guardado en Historial")
        except: st.error("Error al guardar. Revisa la pestaña 'Cotizaciones_Emitidas'")

    if 'cot_activa' in st.session_state:
        c = st.session_state['cot_activa']
        st.markdown("---")
        tabla_html = pd.read_json(c['Detalle_Costos']).to_html(index=False, classes='tabla-impresion')
        st.markdown(f"""
            <div class="print-only">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h1 style="color: #1E1E1E; margin: 0;">🛡️ EDF SEGUROS</h1>
                    <p style="margin: 0;"><b>Fecha:</b> {c['Fecha']}</p>
                </div>
                <hr style="border: 1px solid #1E1E1E;">
                <p style="font-size: 18px;"><b>Propuesta para:</b> {c['Cliente']} | <b>CI:</b> {c['Documento']}</p>
                <p><b>Vehículo:</b> {c['Vehiculo']} | <b>Zona:</b> {c['Zona']}</p>
                <br>
                <h4 style="margin-bottom: 5px;">Comparativa de Aseguradoras:</h4>
                {tabla_html}
                <br>
                <div class="titulo-cuadro">✅ BENEFICIOS INCLUIDOS EN TU PÓLIZA</div>
                <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Incluidos']}</div>
                <div class="titulo-cuadro">➕ DETALLE DE COBERTURA</div>
                <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Opcionales'] if c['Opcionales'] else 'Consultar por otros beneficios adicionales.'}</div>
            </div>
        """, unsafe_allow_html=True)
        st.info("Presioná **Control + P** para guardar el PDF.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    st.subheader("📈 Resumen de Cartera")
    t_usd = df_f['Premio_Total_USD'].sum()
    p_vig = df_f[df_f['Fin_V_dt'] >= date.today()].shape[0]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Cartera Total", f"U$S {t_usd:,.2f}")
    c2.metric("Pólizas Vigentes", p_vig)
    c3.metric("Total en Filtro", len(df_f))
    
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="USD por Compañía", hole=0.4), use_container_width=True)
    with col_b:
        df_r = df_f['Ramo'].value_counts().reset_index()
        st.plotly_chart(px.bar(df_r, x='Ramo', y='count', title="Pólizas por Ramo", color='Ramo', text_auto=True), use_container_width=True)

# Historial de carpetitas (Fuera de tabs para que esté siempre abajo del cotizador)
if st.session_state['logueado']:
    with tab3:
        st.markdown("---")
        st.subheader("📂 Cotizaciones Guardadas")
        try:
            df_h = conn.read(spreadsheet=URL_HOJA, worksheet="Cotizaciones_Emitidas").sort_index(ascending=False)
            for i, r in df_h.head(10).iterrows():
                col_h1, col_h2 = st.columns([0.9, 0.1])
                col_h1.write(f"📄 {r['Fecha']} - **{r['Cliente']}** - {r['Vehiculo']}")
                if col_h2.button("📂", key=f"hist_{i}"):
                    st.session_state['cot_activa'] = r.to_dict()
                    st.rerun()
        except: st.info("Sin historial.")
