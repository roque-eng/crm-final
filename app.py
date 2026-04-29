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

# Estilos CSS para Pantalla e Impresión profesional
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .titulo-cuadro { background-color: #1E1E1E; color: white; padding: 5px 10px; font-weight: bold; margin-top: 15px; }
    .cuadro-beneficios { border: 1px solid #333; padding: 15px; margin-top: 10px; background-color: #fdfdfd; }
    @media print {
        .no-print, .stSidebar, .stTabs, button, header, footer, [data-testid="stToolbar"], .stCheckbox, .stNumberInput { display: none !important; }
        .print-only { display: block !important; position: absolute; left: 0; top: 0; width: 100%; }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Conexión única (usa la configuración de tus Secrets)
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
# ⚙️ CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=300) # Se actualiza cada 5 minutos
def cargar_cartera():
    try:
        df = conn.read(spreadsheet=URL_EMPRESA, ttl=0)
        df.columns = df.columns.str.strip()
        # Cálculo de premios para análisis
        u_col, p_col = 'Premio USD (IVA inc)', 'Premio UYU (IVA inc)'
        df['Premio_Total_USD'] = pd.to_numeric(df.get(u_col, 0), errors='coerce').fillna(0) + \
                                (pd.to_numeric(df.get(p_col, 0), errors='coerce').fillna(0) / TC_USD)
        return df
    except Exception as e:
        st.error(f"Error de conexión con la cartera: {e}")
        return pd.DataFrame()

df_raw = cargar_cartera()

# ==========================================
# 🎯 INTERFAZ DE PESTAÑAS
# ==========================================
st.title("🛡️ EDF SEGUROS")
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA ---
with tab1:
    busq = st.text_input("Filtrar cartera (Nombre, Matrícula o Documento)...")
    if not df_raw.empty:
        df_f = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_raw
        st.dataframe(df_f, use_container_width=True, hide_index=True)
    else:
        st.info("Cargando datos o cartera vacía...")

# --- TAB 3: COTIZADOR ---
with tab3:
    st.subheader("Generador de Cotizaciones")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            doc_in = st.text_input("CI / RUT para buscar cliente")
            n_auto = ""
            if doc_in and not df_raw.empty:
                # Buscador inteligente en columnas de documento
                for col in df_raw.columns:
                    if any(x in col.lower() for x in ['documento', 'ci', 'rut']):
                        m = df_raw[df_raw[col].astype(str).str.contains(doc_in, na=False)]
                        if not m.empty:
                            n_auto = m.iloc[0].get('Asegurado (Nombre/Razón Social)', '')
                            break
            n_cli = st.text_input("Nombre del Asegurado", value=n_auto)
        with c2:
            veh = st.text_input("Vehículo (Marca/Modelo/Año)")
            zn = st.selectbox("Zona", ["Montevideo", "Canelones", "Maldonado", "Interior"])
        with c3:
            eje_list = sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["Roque"]
            eje = st.selectbox("Ejecutivo responsable", eje_list)

    # Editor de costos
    st.write("💰 **Comparativa de Costos**")
    costos_df = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    costos_edit = st.data_editor(costos_df, num_rows="dynamic", use_container_width=True)

    col_i, col_d = st.columns(2)
    with col_i:
        inc = st.text_area("✅ Beneficios Incluidos", "• Auxilio Mecánico 24hs\n• Cristales, Cerraduras y Ópticas\n• RC USD 500.000\n• Asistencia en Viaje", height=150)
    with col_d:
        hog = st.text_area("🏠 Seguro de Hogar / Adicionales", "COBERTURA HOGAR SIN COSTO:\n- Incendio Edificio USD 100.000\n- Hurto Contenido USD 10.000\n- Responsabilidad Civil Hogar", height=150)

    if st.button("💾 Guardar y Preparar Impresión"):
        if not n_cli:
            st.error("❌ El nombre es obligatorio.")
        else:
            nueva = {
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), 
                "Cliente": n_cli, 
                "Documento": doc_in,
                "Vehiculo": veh, 
                "Zona": zn, 
                "Ejecutivo": eje,
                "Tabla_Costos": costos_edit.to_json(), 
                "Detalles": f"{inc}\n\n{hog}"
            }
            try:
                # Guardar en tu Drive Personal
                df_h = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", ttl=0)
                df_up = pd.concat([df_h, pd.DataFrame([nueva])], ignore_index=True)
                conn.update(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", data=df_up)
                st.session_state['ultima_cot'] = nueva
                st.success("✅ Cotización guardada en tu historial de Drive.")
            except Exception as e:
                st.error(f"Error al guardar: Verifica que la pestaña se llame 'Cotizaciones_Emitidas'. {e}")

    # Historial de las últimas 5
    st.divider()
    st.subheader("📂 Últimas Cotizaciones")
    try:
        df_hist = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", ttl=0).iloc[::-1]
        for i, r in df_hist.head(5).iterrows():
            if st.button(f"📄 {r['Cliente']} - {r['Vehiculo']} ({r['Fecha']})", key=f"hist_{i}"):
                st.session_state['ultima_cot'] = r.to_dict()
                st.rerun()
    except: st.info("Historial vacío.")

# --- TAB 2 y 4 (Funciones básicas) ---
with tab2: st.info("Módulo de Vencimientos: Filtra la cartera por fechas próximas.")
with tab4: 
    if not df_raw.empty:
        st.plotly_chart(px.pie(df_raw, names='Aseguradora', values='Premio_Total_USD', title="Distribución de Cartera por Compañía"))

# ==========================================
# 🖨️ VISTA DE IMPRESIÓN (Invisible en web)
# ==========================================
if 'ultima_cot' in st.session_state:
    c = st.session_state['ultima_cot']
    st.markdown(f"""
        <div class="print-only">
            <h1 style="text-align:center;">🛡️ EDF SEGUROS</h1>
            <hr>
            <p><b>FECHA:</b> {c['Fecha']}</p>
            <p><b>ASEGURADO:</b> {c['Cliente']} | <b>VEHÍCULO:</b> {c['Vehiculo']}</p>
            <div class="titulo-cuadro">DETALLES DE COBERTURA Y BENEFICIOS</div>
            <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Detalles']}</div>
            <p style="margin-top:20px; font-size:12px;"><i>Cotización sujeta a inspección y políticas de la aseguradora.</i></p>
        </div>
    """, unsafe_allow_html=True)
