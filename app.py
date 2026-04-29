import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# ⚙️ CONFIGURACIÓN Y CONEXIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS: El "Santo Grial" para que la impresión salga perfecta
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .left-title { font-size: 30px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    
    /* Estilos para la tabla HTML que se imprime */
    .tabla-impresion {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        margin-top: 20px;
    }
    .tabla-impresion th, .tabla-impresion td {
        border: 1px solid #333 !important;
        padding: 10px;
        text-align: left;
    }
    .tabla-impresion th { background-color: #f2f2f2 !important; }

    @media print {
        /* Escondemos todo lo que no sea la cotización */
        .no-print, .stSidebar, .stTabs, button, header, footer, [data-testid="stToolbar"] { 
            display: none !important; 
        }
        /* Forzamos que se vea el contenido de impresión */
        .print-only { 
            display: block !important; 
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
        }
        /* Evitamos que se corten las tablas a la mitad entre páginas */
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
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

# Título Principal
st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📊 ANÁLISIS", "📝 COTIZADOR"])

# --- TAB 1, 2, 3 (Se mantienen igual para no alargar el código) ---
with tab1: st.write("Módulo de Cartera activo.")
with tab2: st.write("Módulo de Vencimientos activo.")
with tab3: st.write("Módulo de Análisis activo.")

# --- TAB 4: COTIZADOR (EL CORAZÓN DEL SISTEMA) ---
with tab4:
    st.subheader("📝 Generador de Cotizaciones")
    
    # 1. Ingreso de Datos
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            ci_bus = st.text_input("CI / RUT del cliente")
            nombre_init = ""
            if ci_bus:
                match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(ci_bus)]
                if not match.empty: nombre_init = match.iloc[0]['Asegurado (Nombre/Razón Social)']
            nombre_cli = st.text_input("Nombre y Apellido", value=nombre_init)
        with col2:
            vehiculo = st.text_input("Vehículo (Marca, Modelo, Año)")
            zona = st.selectbox("Zona de Circulación", ["Montevideo", "Canelones", "Maldonado", "Interior"])

    # 2. Tabla Editable
    st.markdown("#### 💰 Comparativa de Aseguradoras")
    if 'data_cot' not in st.session_state:
        st.session_state.data_cot = pd.DataFrame([
            {"Aseguradora": "BSE", "Contado": 0, "3 Cuotas": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"},
            {"Aseguradora": "SBI", "Contado": 0, "3 Cuotas": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}
        ])
    
    cot_editada = st.data_editor(st.session_state.data_cot, num_rows="dynamic", use_container_width=True)

    # 3. Beneficios Adicionales (Checkboxes automáticos)
    st.markdown("#### ➕ Beneficios a Incluir")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        b1 = c1.checkbox("Alquiler 15 días (UYU 3.900)", value=True)
        b2 = c2.checkbox("Bici USD 1.000 (USD 70)", value=True)
        b3 = c3.checkbox("Casa (Incendio/Hurto) (USD 150)", value=True)
        
        texto_beneficios = ""
        if b1: texto_beneficios += "a) Vehículo de Alquiler por 15 días: costo anual UYU 3.900.\n"
        if b2: texto_beneficios += "b) Seguro para tu bici (hasta USD 1000): costo anual USD 70.\n"
        if b3: texto_beneficios += "c) Seguro para tu casa (Incendio USD 100.000 Edificio, Incendio USD 50.000 contenido, Hurto USD 5.000 contenido): costo anual USD 150.\n"
        
        beneficios_final = st.text_area("Revisión de Beneficios:", value=texto_beneficios, height=120)

    # 4. Botón de Guardar
    if st.button("💾 Guardar Cotización y Generar Vista de Impresión", use_container_width=True):
        nueva_cot = {
            "Fecha": date.today().strftime("%d/%m/%Y"),
            "Cliente": nombre_cli,
            "Documento": ci_bus,
            "Vehiculo": vehiculo,
            "Zona": zona,
            "Detalle_Costos": cot_editada.to_json(), 
            "Beneficios_Incluidos": beneficios_final,
            "ID_Cotizacion": str(int(pd.Timestamp.now().timestamp()))
        }
        
        try:
            # Guardamos en la pestaña nueva
            df_historial = conn.read(spreadsheet=URL_HOJA, worksheet="Cotizaciones_Emitidas")
            df_nuevo = pd.concat([df_historial, pd.DataFrame([nueva_cot])], ignore_index=True)
            conn.update(spreadsheet=URL_HOJA, worksheet="Cotizaciones_Emitidas", data=df_nuevo)
            st.success("✅ ¡Guardado en Historial!")
            st.session_state['cot_activa'] = nueva_cot
        except Exception as e:
            st.error(f"Error al guardar: Asegurate que la pestaña se llame 'Cotizaciones_Emitidas'")

    # 5. VISTA DE IMPRESIÓN (Lo que el cliente ve)
    if 'cot_activa' in st.session_state:
        c = st.session_state['cot_activa']
        st.markdown("---")
        # Generamos la tabla HTML para que no salga vacía al imprimir
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
                <h4 style="margin-bottom: 5px;">Beneficios Incluidos:</h4>
                <div style="background-color: #f9f9f9; padding: 15px; border: 1px solid #ddd; white-space: pre-wrap; font-family: sans-serif;">{c['Beneficios_Incluidos']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.info("💡 **LISTO PARA ENVIAR:** Presioná **Control + P** (o Imprimir en tu navegador) para guardar el PDF.")

    # 6. HISTORIAL DE CARPETITAS
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
    except:
        st.info("Todavía no hay historial para mostrar.")
