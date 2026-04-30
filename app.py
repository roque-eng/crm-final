import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS corregidos para no interferir con la impresión
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .titulo-pdf { font-size: 28px; font-weight: bold; color: #1E1E1E; border-bottom: 2px solid #1E1E1E; }
    
    @media print {
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], 
        .stTabs, button, [data-testid="stToolbar"], .stCheckbox { 
            display: none !important; 
        }
        .print-area { display: block !important; }
    }
    .print-area { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD
# ==========================================
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025"}
if 'logueado' not in st.session_state: st.session_state['logueado'] = False

if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = u
                    st.rerun()
                else: st.error("Credenciales incorrectas")
    st.stop()

# ==========================================
# ⚙️ DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    df = conn.read(spreadsheet=URL_HOJA, ttl=0)
    df.columns = df.columns.str.strip()
    df['Premio USD (IVA inc)'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0)
    df['Premio UYU (IVA inc)'] = pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0)
    df['Premio_Total_USD'] = df['Premio USD (IVA inc)'] + (df['Premio UYU (IVA inc)'] / TC_USD)
    df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
    return df

df_raw = cargar_datos()

# Sidebar con todos los filtros restaurados
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    f_ej = st.selectbox("Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    f_co = st.selectbox("Corredor", ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()))
    f_ag = st.selectbox("Agente", ["Todos"] + sorted(df_raw['Agente'].dropna().unique().tolist()))

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]

# ==========================================
# 📑 TABS
# ==========================================
st.markdown('# 🛡️ EDF SEGUROS')
t1, t2, t3, t4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA INTERACTIVA ---
with t1:
    busq = st.text_input("Buscar cliente o matrícula...")
    df_c = df_f.copy()
    if busq:
        df_c = df_c[df_c.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
    
    # Creamos la columna "Ver" que Streamlit reconoce como link
    if 'Adjunto (póliza)' in df_c.columns:
        # Transformamos el link largo en un emoji de carpeta para que Streamlit lo muestre limpio
        df_c['📂'] = df_c['Adjunto (póliza)']
        cols_final = ['📂'] + [c for c in df_c.columns if c not in ['📂', 'Adjunto (póliza)']]
        
        st.dataframe(
            df_c[cols_final],
            use_container_width=True,
            hide_index=True,
            column_config={
                "📂": st.column_config.LinkColumn("Póliza", display_text="📂")
            }
        )
    else:
        st.dataframe(df_c, use_container_width=True, hide_index=True)

# --- TAB 2: VENCIMIENTOS ---
with t2:
    dias = st.slider("Días a vencer:", 15, 120, 30)
    hoy = date.today()
    df_v = df_f[(df_f['Fin de Vigencia'].dt.date >= hoy) & (df_f['Fin de Vigencia'].dt.date <= hoy + timedelta(days=dias))]
    st.dataframe(df_v.sort_values('Fin de Vigencia'), use_container_width=True, hide_index=True)

# --- TAB 3: COTIZADOR + IMPRESIÓN ---
with t3:
    st.subheader("📝 Nueva Cotización")
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Nombre del Asegurado")
    vehiculo = col2.text_input("Vehículo (Marca/Modelo/Año)")
    
    df_cot = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}])
    cot_edit = st.data_editor(df_cot, num_rows="dynamic", use_container_width=True)
    
    c_iz, c_de = st.columns(2)
    inc = c_iz.text_area("✅ Beneficios", value="• Auxilio 24hs\n• Cristales y Cerraduras\n• RC USD 500.000", height=150)
    adj = c_de.text_area("➕ Adicionales", value="• Hogar Incendio USD 100.000\n• Alquiler 15 días", height=150)

    if st.button("🚀 PREPARAR VISTA DE IMPRESIÓN"):
        st.session_state['ver_pdf'] = True
        st.session_state['datos_pdf'] = {
            "cliente": cliente, "vehiculo": vehiculo, "tabla": cot_edit, "inc": inc, "adj": adj
        }

    if st.session_state.get('ver_pdf'):
        d = st.session_state['datos_pdf']
        st.divider()
        # Esta sección se marca como 'print-area' para el navegador
        st.markdown(f"""
            <div class="print-area">
                <div class="titulo-pdf">🛡️ EDF SEGUROS - PROPUESTA</div>
                <p><b>Fecha:</b> {date.today().strftime('%d/%m/%Y')}<br>
                <b>Asegurado:</b> {d['cliente']}<br>
                <b>Vehículo:</b> {d['vehiculo']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabla simple para que el PDF no falle
        st.table(d['tabla'])
        
        st.markdown(f"""
            <div class="print-area">
                <div style="display:flex; gap:20px;">
                    <div style="flex:1; border:1px solid #ddd; padding:10px;">
                        <b>BENEFICIOS:</b><br>{d['inc'].replace('\\n', '<br>')}
                    </div>
                    <div style="flex:1; border:1px solid #ddd; padding:10px;">
                        <b>ADICIONALES:</b><br>{d['adj'].replace('\\n', '<br>')}
                    </div>
                </div>
                <p style="text-align:center; font-size:10px; color:gray;">Propuesta sujeta a inspección.</p>
            </div>
        """, unsafe_allow_html=True)
        st.info("💡 Ahora presiona **Ctrl + P** (o Comando + P en Mac) y selecciona 'Guardar como PDF'.")

# --- TAB 4: ANÁLISIS ---
with t4:
    if not df_f.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Compañía"), use_container_width=True)
        with c2:
            # Gráfico de barras por Ramos restaurado
            ramo_counts = df_f['Ramo'].value_counts().reset_index()
            ramo_counts.columns = ['Ramo', 'Cantidad']
            st.plotly_chart(px.bar(ramo_counts, x='Ramo', y='Cantidad', title="Pólizas por Ramo", color='Ramo'), use_container_width=True)
