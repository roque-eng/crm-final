import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# 🔗 CONFIGURACIÓN Y CONEXIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; }
    .left-title { font-size: 32px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 0px; }
    .user-info { text-align: right; font-weight: bold; font-size: 14px; color: #666; }
    div[data-testid="stMetricValue"] { font-size: 26px !important; color: #007bff; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "EH": "EHugo2025", "GS": "GSanchez2025", "JM": "JMokosce2025", "PG": "PGagliardi2025", "MDF": "MDeFreitas2025", "AC": "ACazarian2025", "MF": "MFlores2025"}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True; st.session_state['usuario_actual'] = u; st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ CARGA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        
        # Limpieza y cálculos
        df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
        df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
        df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
        
        # Fechas
        df['Fin_V_dt'] = pd.to_datetime(df['Fin de Vigencia'], errors='coerce').dt.date
        
        # Asegurar columna de gestión
        if 'Estado_Gestion' not in df.columns:
            df['Estado_Gestion'] = "Pendiente"
        else:
            df['Estado_Gestion'] = df['Estado_Gestion'].fillna("Pendiente")
            
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}"); return pd.DataFrame()

df_raw = cargar_datos()

# --- ENCABEZADO ---
col_tit, col_user_box = st.columns([8, 2])
with col_tit: st.markdown('<p class="left-title">🛡️ EDF SEGUROS</p>', unsafe_allow_html=True)
with col_user_box:
    st.markdown(f'<div class="user-info">👤 {st.session_state["usuario_actual"]}</div>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión", use_container_width=True): st.session_state['logueado'] = False; st.rerun()

st.divider()

# ==========================================
# 🎯 FILTROS SUPERIORES
# ==========================================
with st.expander("🔍 Filtros y Tiempo", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    f_ej = c1.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_co = c2.selectbox("Corredor", ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()))
    f_ag = c3.selectbox("Agente", ["Todos"] + sorted(df_raw['Agente'].dropna().unique().tolist()))
    f_as = c4.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    
    st.markdown("---")
    ct1, ct2 = st.columns([2, 1])
    dias_vista = ct1.slider("Ver vencimientos en los próximos (días):", 15, 365, 60)
    ver_gestionados = ct2.checkbox("Mostrar renovados/gestionados", value=False)

# Aplicar filtros
df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]

# ==========================================
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3 = st.tabs(["👥 CARTERA TOTAL", "🔄 VENCIMIENTOS PENDIENTES", "📊 ANÁLISIS"])

with tab1:
    busqueda = st.text_input("🔍 Buscar por Nombre, Documento o Matrícula...")
    df_tab1 = df_f.copy()
    if busqueda:
        mask = df_tab1.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        df_tab1 = df_tab1[mask]
    
    st.dataframe(df_tab1, use_container_width=True, hide_index=True,
        column_config={
            "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂 Ver"),
            "Fin de Vigencia": st.column_config.DateColumn("Vence")
        })
    
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Cant. Pólizas", len(df_tab1))
    m2.metric("Cartera Total (USD)", f"U$S {df_tab1['Premio_Total_USD'].sum():,.0f}")
    m3.metric("Tipo de Cambio", f"${TC_USD}")

with tab2:
    hoy = date.today()
    limite = hoy + timedelta(days=dias_vista)
    
    # Filtro de tiempo para vencimientos
    df_v = df_f[(df_f['Fin_V_dt'] >= hoy) & (df_f['Fin_V_dt'] <= limite)].copy()
    
    # Filtro de gestión: Ocultamos lo "Renovado" si el checkbox no está marcado
    if not ver_gestionados:
        df_v = df_v[df_v['Estado_Gestion'] != "Renovado"]
    
    st.subheader(f"📅 Pendientes de Renovación ({dias_vista} días)")
    
    if not df_v.empty:
        # El data_editor permite al ejecutivo marcar la gestión al vuelo
        st.data_editor(
            df_v.sort_values('Fin_V_dt'),
            column_config={
                "Estado_Gestion": st.column_config.SelectboxColumn("Estado de Gestión", options=["Pendiente", "Renovado", "No Renueva"], required=True),
                "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂"),
                "Fin de Vigencia": st.column_config.DateColumn("Vencimiento")
            },
            hide_index=True,
            use_container_width=True,
            key="editor_vencimientos"
        )
        st.info("💡 Tip: Para que los cambios en 'Estado' se guarden permanentemente en el Excel, edítalo directamente haciendo clic en el botón 'Editar Excel' de la pestaña Cartera.")
    else:
        st.success("🎉 ¡No hay vencimientos pendientes en el rango seleccionado!")

with tab3:
    st.subheader("📊 Análisis de Cartera Filtrada")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="USD por Compañía"), use_container_width=True)
    with col_chart2:
        st.plotly_chart(px.bar(df_f, x='Ramo', title="Cantidad por Ramo", color="Ramo"), use_container_width=True)
