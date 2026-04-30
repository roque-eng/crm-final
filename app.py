import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURACIÓN DE ENLACES
# ==========================================
URL_CARTERA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
URL_COTIZACIONES = "https://docs.google.com/spreadsheets/d/1rd_ZCEUxolcgr9WaNUxzqjJVsL7tFvOOS4CaMZOrR8E/edit#gid=0"

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# ==========================================
# 🎨 ESTILOS CSS E IMPRESIÓN
# ==========================================
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .titulo-cuadro { background-color: #1E1E1E; color: white; padding: 5px 10px; font-weight: bold; margin-top: 15px; text-transform: uppercase; }
    .cuadro-beneficios { border: 1px solid #333; padding: 15px; margin-top: 10px; background-color: #fdfdfd; font-size: 14px; }
    @media print {
        .no-print, header, footer, button, .stTabs, [data-testid="stSidebar"] { display: none !important; }
        .print-only { display: block !important; position: absolute; top: 0; left: 0; width: 100%; }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Conexión principal
conn = st.connection("gsheets", type=GSheetsConnection)

# ==========================================
# 🔐 SEGURIDAD (LOGIN)
# ==========================================
if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    with st.columns([1,1,1])[1]:
        with st.form("login"):
            st.subheader("🛡️ Acceso EDF")
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u == "RDF" and p == "Rockuda.4428":
                    st.session_state['logueado'] = True
                    st.rerun()
                else: st.error("Contraseña incorrecta")
    st.stop()

# ==========================================
# ⚙️ CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=300)
def cargar_cartera():
    try:
        df = conn.read(spreadsheet=URL_CARTERA, ttl=0)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

df_raw = cargar_cartera()

# ==========================================
# 🎯 INTERFAZ PRINCIPAL
# ==========================================
st.title("🛡️ EDF SEGUROS")
t1, t2 = st.tabs(["👥 CARTERA DE CLIENTES", "📝 GENERADOR DE COTIZACIÓN"])

# --- TAB 1: CARTERA ---
with t1:
    busq_cartera = st.text_input("Buscador rápido (Nombre, CI, RUT o Matrícula)...")
    if not df_raw.empty:
        if busq_cartera:
            df_res = df_raw[df_raw.astype(str).apply(lambda x: x.str.contains(busq_cartera, case=False)).any(axis=1)]
            st.dataframe(df_res, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_raw, use_container_width=True, hide_index=True)
    else: st.warning("No se pudo cargar la cartera. Revisa los permisos del archivo.")

# --- TAB 2: COTIZADOR ---
with t2:
    st.subheader("Nueva Cotización")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            doc_in = st.text_input("CI / RUT para búsqueda rápida")
            n_auto = ""
            if doc_in and not df_raw.empty:
                # Buscamos en cualquier columna que parezca ser de identificación
                for col in df_raw.columns:
                    if any(x in col.lower() for x in ['documento', 'ci', 'rut']):
                        m = df_raw[df_raw[col].astype(str).str.contains(doc_in, na=False)]
                        if not m.empty:
                            n_auto = m.iloc[0].get('Asegurado (Nombre/Razón Social)', '')
                            break
            cliente = st.text_input("Nombre del Asegurado", value=n_auto)
        with col2:
            vehiculo = st.text_input("Vehículo (Marca, Modelo, Año)")
            zona = st.selectbox("Zona", ["Montevideo", "Interior", "Canelones", "Maldonado"])

    st.write("💰 **Comparativa de Costos**")
    df_init = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    tabla_edit = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)

    c_iz, c_de = st.columns(2)
    with c_iz:
        beneficios = st.text_area("✅ Beneficios Incluidos", "• Auxilio Mecánico 24hs\n• Cristales, Cerraduras y Ópticas\n• RC USD 500.000", height=280)
    with c_de:
        # Texto editado según tu pedido (sin icono de casa y sin la palabra 'Adicionales:')
        txt_predef = (
            "INCLUYA SEGURO DE HOGAR:\n"
            "- Incendio Edificio USD 100.000\n"
            "- Incendio Contenido USD 50.000\n"
            "- Hurto Contenido USD 10.000\n"
            "Costo Anual:\n\n"
            "INCLUYA VEHÍCULO DE ALQUILER:\n"
            "- En caso de choque de su vehículo asegurado, hasta 15 días de vehículo de alquiler.\n"
            "Costo Anual:"
        )
        adicionales = st.text_area("DETALLE DE COBERTURA", value=txt_predef, height=280)

    if st.button("💾 GUARDAR COTIZACIÓN", use_container_width=True):
        if not cliente:
            st.error("Por favor completa el nombre del asegurado.")
        else:
            nueva_fila = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Cliente": cliente,
                "Documento": doc_in,
                "Vehiculo": vehiculo,
                "Zona": zona,
                "Ejecutivo": "Roque de Freitas",
                "Tabla_Costos": tabla_edit.to_json(orient='records'),
                "Detalles": f"{beneficios}\n\n{adicionales}"
            }])
            try:
                df_hist = conn.read(spreadsheet=URL_COTIZACIONES, worksheet="Cotizaciones_Emitidas", ttl=0)
                df_final = pd.concat([df_hist, nueva_fila], ignore_index=True)
                conn.update(spreadsheet=URL_COTIZACIONES, worksheet="Cotizaciones_Emitidas", data=df_final)
                st.success("✅ Guardado con éxito en tu Drive personal.")
                st.session_state['ultima_cot'] = nueva_fila.iloc[0].to_dict()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # --- HISTORIAL ---
    st.divider()
    st.subheader("📂 Historial de Cotizaciones (Tu Drive)")
    try:
        df_ver_hist = conn.read(spreadsheet=URL_COTIZACIONES, worksheet="Cotizaciones_Emitidas", ttl=0).iloc[::-1]
        for i, r in df_ver_hist.head(5).iterrows():
            if st.button(f"Ver {r['Cliente']} - {r['Vehiculo']} ({r['Fecha']})", key=f"h_{i}"):
                st.session_state['ultima_cot'] = r.to_dict()
                st.rerun()
    except: st.info("No hay registros previos.")

# ==========================================
# 🖨️ VISTA DE IMPRESIÓN
# ==========================================
if 'ultima_cot' in st.session_state:
    c = st.session_state['ultima_cot']
    st.markdown(f"""
        <div class="print-only">
            <h2 style="text-align:center;">🛡️ EDF SEGUROS</h2>
            <hr>
            <p><b>FECHA:</b> {c['Fecha']} | <b>EJECUTIVO:</b> {c['Ejecutivo']}</p>
            <p><b>ASEGURADO:</b> {c['Cliente']} | <b>VEHÍCULO:</b> {c['Vehiculo']}</p>
            <div class="titulo-cuadro">DETALLES DE COBERTURA Y BENEFICIOS</div>
            <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Detalles']}</div>
        </div>
    """, unsafe_allow_html=True)
