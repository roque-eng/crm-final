import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date, timedelta
import json

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
        .no-print, header, footer, button, .stTabs, [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
        .print-only { display: block !important; position: absolute; top: 0; left: 0; width: 100%; }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Conexión única
conn = st.connection("gsheets", type=GSheetsConnection)

# ==========================================
# 🔐 SEGURIDAD (LOGIN)
# ==========================================
if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False

if not st.session_state['logueado']:
    with st.columns([1,1,1])[1]:
        with st.form("login"):
            st.subheader("🛡️ Acceso EDF SEGUROS")
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u == "RDF" and p == "Rockuda.4428":
                    st.session_state['logueado'] = True
                    st.session_state['usuario'] = "Roque de Freitas"
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA Y LIMPIEZA DE DATOS
# ==========================================
@st.cache_data(ttl=300)
def cargar_datos_base():
    try:
        df = conn.read(spreadsheet=URL_CARTERA, ttl=0)
        df.columns = df.columns.str.strip()
        if 'Fin de Vigencia' in df.columns:
            df['Fecha_Vence_DT'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date
        return df
    except:
        return pd.DataFrame()

df_cartera_raw = cargar_datos_base()

# ==========================================
# 🔎 BARRA LATERAL (FILTROS Y SESIÓN)
# ==========================================
with st.sidebar:
    st.write(f"👤 **Conectado:** {st.session_state.get('usuario')}")
    st.divider()
    st.subheader("Filtros de Cartera")
    
    cias_disponibles = sorted(df_cartera_raw['Aseguradora'].dropna().unique()) if not df_cartera_raw.empty else []
    filtro_cia = st.multiselect("Filtrar Compañía", cias_disponibles)
    
    ejes_disponibles = sorted(df_cartera_raw['Ejecutivo'].dropna().unique()) if not df_cartera_raw.empty else []
    filtro_eje = st.multiselect("Filtrar Ejecutivo", ejes_disponibles)
    
    st.divider()
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False
        st.rerun()

# Aplicar filtros
df_f = df_cartera_raw.copy()
if filtro_cia:
    df_f = df_f[df_f['Aseguradora'].isin(filtro_cia)]
if filtro_eje:
    df_f = df_f[df_f['Ejecutivo'].isin(filtro_eje)]

# ==========================================
# 🎯 PESTAÑAS DE TRABAJO
# ==========================================
st.title("🛡️ EDF SEGUROS")
tab_cartera, tab_vence, tab_cotizador = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR"])

# --- PESTAÑA CARTERA ---
with tab_cartera:
    st.subheader("Consulta de Clientes")
    busq_txt = st.text_input("Buscador (Nombre, Matrícula o RUT)...")
    if not df_f.empty:
        if busq_txt:
            df_v = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq_txt, case=False)).any(axis=1)]
            st.dataframe(df_v, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_f, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos cargados.")

# --- PESTAÑA VENCIMIENTOS ---
with tab_vence:
    st.subheader("Renovaciones Próximas")
    rango_dias = st.slider("Ver vencimientos en los próximos (días):", 7, 90, 30)
    if not df_f.empty and 'Fecha_Vence_DT' in df_f.columns:
        hoy = date.today()
        limite = hoy + timedelta(days=rango_dias)
        df_vencimientos = df_f[(df_f['Fecha_Vence_DT'] >= hoy) & (df_f['Fecha_Vence_DT'] <= limite)]
        st.dataframe(df_vencimientos.sort_values('Fecha_Vence_DT'), use_container_width=True, hide_index=True)
    else:
        st.info("Sin datos de vigencia.")

# --- PESTAÑA COTIZADOR ---
with tab_cotizador:
    st.subheader("Generador de Propuestas")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            doc_busq = st.text_input("CI o RUT (Búsqueda automática)")
            nombre_sugerido = ""
            if doc_busq and not df_cartera_raw.empty:
                for c in df_cartera_raw.columns:
                    if any(x in c.lower() for x in ['documento', 'ci', 'rut']):
                        match = df_cartera_raw[df_cartera_raw[c].astype(str).str.contains(doc_busq, na=False)]
                        if not match.empty:
                            nombre_sugerido = match.iloc[0].get('Asegurado (Nombre/Razón Social)', '')
                            break
            nombre_cliente = st.text_input("Asegurado", value=nombre_sugerido)
        with col2:
            vehiculo_desc = st.text_input("Vehículo (Marca, Modelo, Año)")
            ejecutivo_firma = st.selectbox("Ejecutivo que firma", ["Roque de Freitas", "Joe", "Andre"])

    st.write("💰 **Comparativa de Costos**")
    base_costos = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    tabla_costos = st.data_editor(base_costos, num_rows="dynamic", use_container_width=True)

    c_izq, c_der = st.columns(2)
    with c_izq:
        texto_beneficios = st.text_area("✅ Beneficios Incluidos", "• Auxilio Mecánico 24hs\n• Cristales, Cerraduras y Ópticas\n• RC USD 500.000", height=280)
    with c_der:
        # Texto editado sin icono y sin palabra repetida
        texto_hogar_alq = (
            "INCLUYA SEGURO DE HOGAR:\n"
            "- Incendio Edificio USD 100.000\n"
            "- Incendio Contenido USD 50.000\n"
            "- Hurto Contenido USD 10.000\n"
            "Costo Anual:\n\n"
            "INCLUYA VEHÍCULO DE ALQUILER:\n"
            "- En caso de choque de su vehículo asegurado, hasta 15 días de vehículo de alquiler.\n"
            "Costo Anual:"
        )
        detalles_propuesta = st.text_area("DETALLE DE COBERTURA", value=texto_hogar_alq, height=280)

    if st.button("💾 GUARDAR Y FINALIZAR", use_container_width=True):
        if not nombre_cliente:
            st.error("El nombre del asegurado es obligatorio.")
        else:
            fila_cot = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Cliente": nombre_cliente,
                "Documento": doc_busq,
                "Vehiculo": vehiculo_desc,
                "Zona": "N/A",
                "Ejecutivo": ejecutivo_firma,
                "Tabla_Costos": tabla_costos.to_json(orient='records'),
                "Detalles": f"{texto_beneficios}\n\n{detalles_propuesta}"
            }])
            try:
                df_drive = conn.read(spreadsheet=URL_COTIZACIONES, worksheet="Cotizaciones_Emitidas", ttl=0)
                df_final_save = pd.concat([df_drive, fila_cot], ignore_index=True)
                conn.update(spreadsheet=URL_COTIZACIONES, worksheet="Cotizaciones_Emitidas", data=df_final_save)
                st.success("✅ Guardado en Drive.")
                st.session_state['ultima_impresion'] = fila_cot.iloc[0].to_dict()
            except Exception as err:
                st.error(f"Error al guardar: {err}")

    # Historial para recuperación
    st.divider()
    st.subheader("📂 Recuperar Cotizaciones Guardadas")
    try:
        df_historial = conn.read(spreadsheet=URL_COTIZACIONES, worksheet="Cotizaciones_Emitidas", ttl=0).iloc[::-1]
        for idx, row in df_historial.head(5).iterrows():
            if st.button(f"📄 {row['Cliente']} - {row['Vehiculo']} ({row['Fecha']})", key=f"hist_{idx}"):
                st.session_state['ultima_impresion'] = row.to_dict()
                st.rerun()
    except:
        st.info("Sin historial.")

# ==========================================
# 🖨️ VISTA DE IMPRESIÓN (Solo visible al imprimir)
# ==========================================
if 'ultima_impresion' in st.session_state:
    cot = st.session_state['ultima_impresion']
    st.markdown(f"""
        <div class="print-only">
            <h2 style="text-align:center;">🛡️ EDF SEGUROS</h2>
            <hr>
            <p><b>EMISIÓN:</b> {cot['Fecha']} | <b>EJECUTIVO:</b> {cot['Ejecutivo']}</p>
            <p><b>ASEGURADO:</b> {cot['Cliente']} | <b>VEHÍCULO:</b> {cot['Vehiculo']}</p>
            <div class="titulo-cuadro">DETALLES DE COBERTURA Y BENEFICIOS</div>
            <div class="cuadro-beneficios" style="white-space: pre-wrap;">{cot['Detalles']}</div>
        </div>
    """, unsafe_allow_html=True)
