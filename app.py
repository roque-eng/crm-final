import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date, timedelta

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
        .no-print, header, footer, button, .stTabs, [data-testid="stSidebar"], [data-testid="stHeader"] { display: none !important; }
        .print-only { display: block !important; position: absolute; top: 0; left: 0; width: 100%; }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Conexión única
conn = st.connection("gsheets", type=GSheetsConnection)

# ==========================================
# 🔐 SEGURIDAD Y FILTROS (SIDEBAR)
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
                    st.session_state['usuario'] = u
                    st.rerun()
                else: st.error("Contraseña incorrecta")
    st.stop()

# --- SIDEBAR (Solo se ve logueado) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.write(f"👤 **Usuario:** {st.session_state['usuario']}")
    st.divider()
    st.subheader("🔎 Filtros Globales")
    filtro_cia = st.multiselect("Compañía", ["BSE", "SURA", "PORTO", "SANCOR", "MAPFRE", "SBI"])
    filtro_eje = st.multiselect("Ejecutivo", ["Roque de Freitas", "Joe", "Andre"])
    st.divider()
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

# ==========================================
# ⚙️ CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=300)
def cargar_cartera():
    try:
        df = conn.read(spreadsheet=URL_CARTERA, ttl=0)
        df.columns = df.columns.str.strip()
        # Limpieza de fechas para vencimientos
        if 'Fin de Vigencia' in df.columns:
            df['Fecha_Vence'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_cartera()

# Aplicar filtros del sidebar a la data
df_filtrada = df_raw.copy()
if filtro_cia:
    df_filtrada = df_filtrada[df_filtrada['Aseguradora'].isin(filtro_cia)]
if filtro_eje:
    # Ajustar según el nombre de tu columna de ejecutivos
    df_filtrada = df_filtrada[df_filtrada['Ejecutivo'].isin(filtro_eje)]

# ==========================================
# 🎯 INTERFAZ PRINCIPAL
# ==========================================
st.title("🛡️ EDF SEGUROS")
t1, t2, t3 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR"])

# --- TAB 1: CARTERA ---
with t1:
    busq = st.text_input("Buscar cliente...")
    if not df_filtrada.empty:
        df_ver = df_filtrada[df_filtrada.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_filtrada
        st.dataframe(df_ver, use_container_width=True, hide_index=True)

# --- TAB 2: VENCIMIENTOS ---
with t2:
    st.subheader("Próximos Vencimientos")
    dias = st.slider("Ver vencimientos en los próximos (días):", 7, 90, 30)
    if not df_filtrada.empty and 'Fecha_Vence' in df_filtrada.columns:
        hoy = date.today()
        futuro = hoy + timedelta(days=dias)
        df_vence = df_filtrada[(df_filtrada['Fecha_Vence'] >= hoy) & (df_filtrada['Fecha_Vence'] <= futuro)]
        st.dataframe(df_vence.sort_values('Fecha_Vence'), use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de vigencia disponibles.")

# --- TAB 3: COTIZADOR ---
with t3:
    st.subheader("Nueva Cotización")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        doc_in = c1.text_input("CI / RUT para búsqueda rápida")
        n_auto = ""
        if doc_in and not df_raw.empty:
            for col in df_raw.columns:
                if any(x in col.lower() for x in ['documento', 'ci', 'rut']):
                    m = df_raw[df_raw[col].astype(str).str.contains(doc_in, na=False)]
                    if not m.empty:
                        n_auto = m.iloc[0].get('Asegurado (Nombre/Razón Social)', '')
                        break
        cliente = c1.text_input("Nombre del Asegurado", value=n_auto)
        vehiculo = c2.text_input("Vehículo (Marca, Modelo, Año)")
        ejecutivo = c2.selectbox("Ejecutivo", ["Roque de Freitas", "Joe", "Andre"])

    st.write("💰 **Comparativa de Costos**")
    df_init = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    tabla_edit = st.data_editor(df_init, num_rows="dynamic", use_container_width=True)

    col_iz, col_de = st.columns(2)
    beneficios = col_iz.text_area("✅ Beneficios", "• Auxilio Mecánico 24hs\n• Cristales, Cerraduras y Ópticas\n• RC USD 500.000", height=250)
    
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
    detalles = col_de.text_area("DETALLE DE COBERTURA", value=txt_predef, height=250)

    if st.button("💾 GUARDAR COTIZACIÓN", use_container_width=True):
        if not cliente: st.error("Falta el nombre.")
        else:
            nueva = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Cliente": cliente, "Documento": doc_in, "Vehiculo": vehiculo,
                "Zona": "N/A", "Ejecutivo": ejecutivo,
                "Tabla_Costos": tabla_edit.to_json(orient='records'),
                "Detalles": f"{beneficios}\n\n{detalles}"
            }])
            try:
                hist = conn.read(spreadsheet=URL_COTIZACIONES, worksheet="Cotizaciones_Emitidas", ttl=0)
                final = pd.concat([hist, nueva], ignore_index=True)
                conn.update(spreadsheet=URL_COTIZACIONES, worksheet="Cotizaciones_Emitidas", data=final)
                st.success("✅ Guardado con éxito.")
                st.session_state['ultima_cot'] = nueva.iloc[0].to_dict()
            except Exception as e: st.error(f"Error: {e}")

# --- VISTA IMPRESIÓN ---
if 'ultima_cot' in st.session_state:
    c = st.session_state['ultima_cot']
    st.markdown(f"""
        <div class="print-only">
            <h2 style="text-align:center;">🛡️ EDF SEGUROS</h2><hr>
            <p><b>FECHA:</b> {c['Fecha']} | <b>EJECUTIVO:</b> {c['Ejecutivo']}</p>
            <p><b>ASEGURADO:</b> {c['Cliente']} | <b>VEHÍCULO:</b> {c['Vehiculo']}</p>
            <div class="titulo-cuadro">COBERTURA Y BENEFICIOS</div>
            <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Detalles']}</div>
        </div>
    """, unsafe_allow_html=True)
