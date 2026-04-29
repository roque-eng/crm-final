import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import datetime, date, timedelta

# ==========================================
# ⚙️ CONFIGURACIÓN Y ENLACES
# ==========================================
# 1. Excel de la Empresa (Cartera)
URL_EMPRESA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"

# 2. Tu Excel Personal (Cotizaciones)
URL_MI_DRIVE = "https://docs.google.com/spreadsheets/d/1rd_ZCEUxolcgr9WaNUxzqjJVsL7tFvOOS4CaMZOrR8E/edit#gid=0"

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

def cargar_cartera():
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

df_raw = cargar_cartera()

# ==========================================
# 🎯 FILTROS (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_actual']}")
    st.markdown("---")
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

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

with tab1:
    busq = st.text_input("Buscar en cartera...")
    if not df_f.empty:
        st.dataframe(df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f, use_container_width=True, hide_index=True)

with tab2:
    dias = st.slider("Vencimientos a (días):", 15, 120, 60)
    if 'Fin_V_dt' in df_f.columns:
        vence = df_f[(df_f['Fin_V_dt'] >= date.today()) & (df_f['Fin_V_dt'] <= date.today() + timedelta(days=dias))]
        st.dataframe(vence.sort_values('Fin_V_dt'), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("📝 Generador de Cotizaciones")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            ci_bus = st.text_input("CI / RUT")
            nombre_cli = st.text_input("Asegurado")
        with c2:
            vehiculo = st.text_input("Vehículo")
            zona = st.selectbox("Zona", ["Montevideo", "Canelones", "Interior"])
        with c3:
            eje_list = sorted(df_raw['Ejecutivo'].dropna().unique().tolist()) if 'Ejecutivo' in df_raw.columns else ["Roque"]
            ejecutivo_cot = st.selectbox("Ejecutivo", eje_list)

    st.session_state.data_cot = st.data_editor(pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}]), num_rows="dynamic", use_container_width=True)

    col_i, col_d = st.columns(2)
    with col_i:
        inc = st.text_area("Beneficios Incluidos:", "• Auxilio 24hs\n• Cristales/Cerraduras\n• Responsabilidad Civil USD 500.000")
    with col_d:
        p_alq = st.number_input("Costo Alquiler", 3900)
        p_bici = st.number_input("Costo Bici", 70)
        det = st.text_area("Detalle de Cobertura:", f"- Alquiler: UYU {p_alq}\n- Seguro Bici: USD {p_bici}")

    if st.button("💾 Guardar en Mi Drive"):
        nueva = {
            "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Cliente": nombre_cli, "Documento": ci_bus,
            "Vehiculo": vehiculo, "Zona": zona, "Ejecutivo": ejecutivo_cot, 
            "Detalle_Costos": st.session_state.data_cot.to_json(), "Beneficios_Incluidos": f"{inc} | {det}"
        }
        try:
            df_h = conn.read(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas")
            conn.update(spreadsheet=URL_MI_DRIVE, worksheet="Cotizaciones_Emitidas", data=pd.concat([df_h, pd.DataFrame([nueva])], ignore_index=True))
            st.session_state['cot_activa'] = nueva
            st.success("✅ Guardado en tu unidad personal.")
        except: st.error("Error: Revisa que la pestaña en tu Drive se llame 'Cotizaciones_Emitidas'")

    if 'cot_activa' in st.session_state:
        c = st.session_state['cot_activa']
        tabla_html = pd.read_json(c['Detalle_Costos']).to_html(index=False, classes='tabla-impresion')
        st.markdown(f"""<div class="print-only"><h1>🛡️ EDF SEGUROS</h1><hr><p><b>Cliente:</b> {c['Cliente']} | <b>Vehículo:</b> {c['Vehiculo']}</p>{tabla_html}<div class="titulo-cuadro">DETALLES</div><div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Beneficios_Incluidos']}</div></div>""", unsafe_allow_html=True)
        st.info("💡 Control + P para PDF.")

with tab4:
    st.subheader("📊 Análisis de Cartera")
    if not df_f.empty:
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Cartera USD", f"{df_f['Premio_Total_USD'].sum():,.0f}")
        col_m2.metric("Pólizas", len(df_f))
        st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Distribución por Cía"), use_container_width=True)
