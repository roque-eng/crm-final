import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import json
from datetime import datetime, date, timedelta
import plotly.express as px

# ==========================================
# ⚙️ CONFIGURACIÓN DE ENLACES
# ==========================================
URL_EMPRESA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
URL_MI_DRIVE = "https://docs.google.com/spreadsheets/d/1rd_ZCEUxolcgr9WaNUxzqjJVsL7tFvOOS4CaMZOrR8E/edit#gid=0"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS para Pantalla e Impresión
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
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

# Conexión única usando los Secrets de Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

# ==========================================
# 🔐 SEGURIDAD (LOGIN)
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025"}
if 'logueado' not in st.session_state: st.session_state['logueado'] = False

if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = u
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA DE DATOS (CARTERA)
# ==========================================
@st.cache_data(ttl=600)
def cargar_cartera():
    try:
        df = conn.read(spreadsheet=URL_EMPRESA, ttl=0)
        df.columns = df.columns.str.strip()
        # Cálculo de premios
        df['Premio_Total_USD'] = pd.to_numeric(df.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0) + \
                                (pd.to_numeric(df.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0) / TC_USD)
        if 'Fin de Vigencia' in df.columns:
            df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
            df['Fin_V_dt'] = df['Fin de Vigencia'].dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_cartera()

# ==========================================
# 🎯 INTERFAZ PRINCIPAL
# ==========================================
st.title("🛡️ EDF SEGUROS")

tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA ---
with tab1:
    busq = st.text_input("Buscar en cartera...")
    if not df_raw.empty:
        df_f = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_raw
        st.dataframe(df_f, use_container_width=True, hide_index=True)

# --- TAB 2: VENCIMIENTOS ---
with tab2:
    if 'Fin_V_dt' in df_raw.columns:
        dias = st.slider("Días a futuro", 15, 120, 60)
        vence = df_raw[(df_raw['Fin_V_dt'] >= date.today()) & (df_raw['Fin_V_dt'] <= date.today() + timedelta(days=dias))]
        st.dataframe(vence.sort_values('Fin_V_dt'), use_container_width=True)

# --- TAB 3: COTIZADOR ---
with tab3:
    st.subheader("Generador de Cotizaciones")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            doc_input = st.text_input("CI / RUT para buscar cliente")
            nombre_auto = ""
            if doc_input and not df_raw.empty:
                col_doc = 'Documento de Identidad (Rut/Cédula/Otros)'
                if col_doc in df_raw.columns:
                    filtro = df_raw[df_raw[col_doc].astype(str).str.contains(doc_input, na=False)]
                    if not filtro.empty:
                        nombre_auto = filtro.iloc[0]['Asegurado (Nombre/Razón Social)']
            nombre_cli = st.text_input("Asegurado", value=nombre_auto)
        with c2:
            vehiculo = st.text_input("Vehículo")
            zona = st.selectbox("Zona", ["Montevideo", "Canelones", "Interior", "Maldonado"])
        with c3:
            eje_list = sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["Roque"]
            ejecutivo_cot = st.selectbox("Ejecutivo", eje_list)

    # Costos editables
    df_editor = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    costos_finales = st.data_editor(df_editor, num_rows="dynamic", use_container_width=True)

    # Beneficios y Hogar
    col_iz, col_de = st.columns(2)
    with col_iz:
        inc = st.text_area("✅ Beneficios Incluidos", "• Auxilio 24hs\n• Cristales/Cerraduras\n• RC USD 500.000", height=150)
    with col_de:
        hogar = st.text_area("🏠 Detalle de Cobertura (Hogar/Otros)", "Seguro Hogar:\n- Incendio Edificio USD 100.000\n- Hurto Contenido USD 10.000\nCosto: USD 150 anual", height=150)

    if st.button("Guardar"):
        if not nombre_cli:
            st.error("❌ Por favor ingresa el nombre.")
        else:
            nueva = {
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Cliente": nombre_cli, "Documento": doc_input,
                "Vehiculo": vehiculo, "Zona": zona, "Ejecutivo": ejecutivo_cot,
                "Tabla_Costos": costos_finales.to_json(), "Detalles": f"{inc}\n\n{hogar}"
            }
            try:
                df_h = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", ttl=0)
                df_up = pd.concat([df_h, pd.DataFrame([nueva])], ignore_index=True)
                conn.update(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", data=df_up)
                st.session_state['ultima_cot'] = nueva
                st.success("✅ Guardado en tu Drive personal.")
            except Exception as e:
                st.error(f"Error al guardar. Verifica permisos y encabezados. {e}")

    # Historial
    st.divider()
    st.subheader("📂 Historial de Cotizaciones")
    try:
        df_hist = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", ttl=0).iloc[::-1]
        for i, r in df_hist.head(10).iterrows():
            with st.expander(f"📄 {r['Fecha']} - {r['Cliente']}"):
                st.write(f"**Vehículo:** {r['Vehiculo']} | **Ejecutivo:** {r['Ejecutivo']}")
                if st.button("Seleccionar para Imprimir", key=f"h_{i}"):
                    st.session_state['ultima_cot'] = r.to_dict()
                    st.rerun()
    except: st.info("No hay historial disponible.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_raw.empty:
        st.plotly_chart(px.pie(df_raw, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía"))

# Vista Impresión
if 'ultima_cot' in st.session_state:
    c = st.session_state['ultima_cot']
    st.markdown(f"""
        <div class="print-only">
            <h1>🛡️ EDF SEGUROS</h1><hr>
            <p><b>Asegurado:</b> {c['Cliente']} | <b>Vehículo:</b> {c['Vehiculo']}</p>
            <div class="titulo-cuadro">DETALLE DE COBERTURA</div>
            <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Detalles']}</div>
        </div>
    """, unsafe_allow_html=True)
