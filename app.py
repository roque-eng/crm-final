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

# Estilos CSS
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

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# ==========================================
# 🔐 SEGURIDAD
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", "AC": "ACazarian2025", "MF": "MFlores2025", "JOE": "Joe2025", "ANDRE": "Andre2025"}

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
# ⚙️ CARGA DE DATOS
# ==========================================
def cargar_empresa():
    try:
        df = conn.read(spreadsheet=URL_EMPRESA, ttl=0)
        df.columns = df.columns.str.strip()
        u_col, p_col = 'Premio USD (IVA inc)', 'Premio UYU (IVA inc)'
        df['Premio_Total_USD'] = pd.to_numeric(df.get(u_col, 0), errors='coerce').fillna(0) + (pd.to_numeric(df.get(p_col, 0), errors='coerce').fillna(0) / TC_USD)
        if 'Fin de Vigencia' in df.columns:
            df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
            df['Fin_V_dt'] = df['Fin de Vigencia'].dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_empresa()

# ==========================================
# 🎯 SIDEBAR E INTERFAZ
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_actual']}")
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

st.title("🛡️ EDF SEGUROS")

tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- COTIZADOR (TAB 3) ---
with tab3:
    st.subheader("Generador de Cotizaciones")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            doc_input = st.text_input("CI / RUT para buscar")
            nombre_auto = ""
            if doc_input and not df_raw.empty:
                # Búsqueda flexible en la columna de documento
                filtro_doc = df_raw[df_raw.iloc[:, 1].astype(str).str.contains(doc_input, na=False)] # Busca en la 2da columna usualmente el doc
                if not filtro_doc.empty:
                    nombre_auto = filtro_doc.iloc[0]['Asegurado (Nombre/Razón Social)']
            nombre_cli = st.text_input("Nombre Asegurado", value=nombre_auto)
        with c2:
            vehiculo = st.text_input("Vehículo")
            zona = st.selectbox("Zona", ["Montevideo", "Canelones", "Maldonado", "Interior"])
        with c3:
            ejecutivo_cot = st.selectbox("Ejecutivo", sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["Roque"])

    # Tabla de Costos
    costos_df = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    costos_edit = st.data_editor(costos_df, num_rows="dynamic", use_container_width=True)

    # Beneficios
    col_a, col_b = st.columns(2)
    with col_a:
        inc = st.text_area("✅ Beneficios Incluidos", "• Auxilio 24hs\n• Cristales/Cerraduras\n• RC USD 500.000")
    with col_b:
        hogar = st.text_area("🏠 Seguro de Hogar / Adicionales", "- USD 100.000 Incendio Edificio\n- USD 10.000 Hurto Contenido\n- Costo: USD 150 anual")

    if st.button("Guardar"):
        if not nombre_cli:
            st.error("Por favor, ingresa el nombre del cliente.")
        else:
            nueva_cot = {
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Cliente": nombre_cli,
                "Documento": doc_input,
                "Vehiculo": vehiculo,
                "Zona": zona,
                "Ejecutivo": ejecutivo_cot,
                "Tabla_Costos": costos_edit.to_json(),
                "Detalles": f"Beneficios: {inc}\n\nHogar/Otros: {hogar}"
            }
            try:
                df_h = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", ttl=0)
                df_up = pd.concat([df_h, pd.DataFrame([nueva_cot])], ignore_index=True)
                conn.update(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", data=df_up)
                st.session_state['ultima_cot'] = nueva_cot
                st.success("✅ Guardado con éxito")
            except:
                st.error("Error al guardar. Revisa el nombre de la pestaña en tu Drive.")

    # Historial
    st.divider()
    st.subheader("📂 Historial de Cotizaciones")
    try:
        df_hist = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", ttl=0).sort_index(ascending=False)
        for i, r in df_hist.head(5).iterrows():
            with st.expander(f"📄 {r['Fecha']} - {r['Cliente']}"):
                st.write(f"**Vehículo:** {r['Vehiculo']}")
                st.write(f"**Detalles:** {r['Detalles']}")
                if st.button("Ver para imprimir", key=f"v_{i}"):
                    st.session_state['ultima_cot'] = r.to_dict()
                    st.rerun()
    except: pass

# --- VISTAS RESTANTES ---
with tab1:
    st.dataframe(df_raw, use_container_width=True)
with tab2:
    if 'Fin_V_dt' in df_raw.columns:
        v = df_raw[df_raw['Fin_V_dt'] <= date.today() + timedelta(days=60)]
        st.dataframe(v.sort_values('Fin_V_dt'), use_container_width=True)
with tab4:
    if not df_raw.empty:
        st.plotly_chart(px.pie(df_raw, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Compañía"))

# Vista de impresión (al final de todo)
if 'ultima_cot' in st.session_state:
    c = st.session_state['ultima_cot']
    st.markdown(f"""
        <div class="print-only">
            <h1>🛡️ EDF SEGUROS</h1><hr>
            <p><b>Cliente:</b> {c['Cliente']} | <b>Vehículo:</b> {c['Vehiculo']}</p>
            <div class="titulo-cuadro">COBERTURAS Y BENEFICIOS</div>
            <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Detalles']}</div>
        </div>
    """, unsafe_allow_html=True)
