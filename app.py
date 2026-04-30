import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .stDataFrame { border: 1px solid #f0f2f6; border-radius: 5px; }
    
    /* Estilos para que el PDF no salga en blanco */
    @media print {
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], 
        .stTabs, button, [data-testid="stToolbar"] { 
            display: none !important; 
        }
        .section-to-print { display: block !important; width: 100%; }
    }
    .section-to-print { display: none; }
    
    .titulo-pdf { font-size: 32px; font-weight: bold; color: #1E1E1E; }
    .sub-pdf { font-size: 18px; color: #555; margin-bottom: 20px; }
    .cuadro-gris { background-color: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
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
# ⚙️ CARGA DE DATOS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    df = conn.read(spreadsheet=URL_HOJA, ttl=0)
    df.columns = df.columns.str.strip()
    df['Premio_Total_USD'] = pd.to_numeric(df['Premio USD (IVA inc)'], errors='coerce').fillna(0) + \
                             (pd.to_numeric(df['Premio UYU (IVA inc)'], errors='coerce').fillna(0) / TC_USD)
    df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce')
    return df

df_raw = cargar_datos()

# Sidebar con Filtros Globales
with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    f_ej = st.selectbox("Filtrar Ejecutivo", ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist()))
    f_as = st.selectbox("Filtrar Aseguradora", ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist()))
    f_ra = st.selectbox("Filtrar Ramo", ["Todos"] + sorted(df_raw['Ramo'].dropna().unique().tolist()))
    f_co = st.selectbox("Filtrar Corredor", ["Todos"] + sorted(df_raw['Corredor'].dropna().unique().tolist()))

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]

# ==========================================
# 📑 PESTAÑAS PRINCIPALES
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA (INTERACTIVA CON ÍCONO) ---
with tab1:
    busq = st.text_input("🔍 Buscar por cliente, matrícula o documento...")
    df_c = df_f.copy()
    if busq:
        df_c = df_c[df_c.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
    
    if 'Adjunto (póliza)' in df_c.columns:
        # Usamos LinkColumn para mantener el ordenamiento y filtros
        st.dataframe(
            df_c, use_container_width=True, hide_index=True,
            column_config={
                "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")
            }
        )
    else:
        st.dataframe(df_c, use_container_width=True, hide_index=True)

# --- TAB 3: COTIZADOR (TODO RESTAURADO) ---
with tab3:
    st.subheader("📝 Módulo de Cotización")
    
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1, 1])
        # Lógica de búsqueda por CI/RUT
        doc_input = c1.text_input("Documento (CI / RUT)")
        nombre_sugerido = ""
        if doc_input:
            busqueda_cli = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(doc_input)]
            if not busqueda_cli.empty:
                nombre_sugerido = busqueda_cli.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        nombre_cli = c2.text_input("Asegurado", value=nombre_sugerido)
        ejecutivo_cot = c3.selectbox("Ejecutivo Responsable", sorted(df_raw['Ejecutivo'].dropna().unique()))
        
        c4, c5 = st.columns(2)
        vehiculo_cot = c4.text_input("Vehículo (Marca, Modelo, Año)")
        zona_cot = c5.selectbox("Zona de Circulación", ["Montevideo", "Canelones", "Maldonado", "Interior", "Todo el País"])

    st.markdown("#### 📊 Comparativa de Seguros")
    df_propu = pd.DataFrame([
        {"Aseguradora": "BSE", "Contado": 0.0, "6 Cuotas": 0.0, "10 Cuotas": 0.0, "Deducible": "Global"},
        {"Aseguradora": "SURCO", "Contado": 0.0, "6 Cuotas": 0.0, "10 Cuotas": 0.0, "Deducible": "Global"}
    ])
    tabla_cot = st.data_editor(df_propu, num_rows="dynamic", use_container_width=True)

    st.markdown("#### ✅ Coberturas y Adicionales (Editables)")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("**Beneficios Base:**")
        beneficios = st.text_area("Incluidos en la propuesta", 
            "• Auxilio mecánico 24hs (Sin límite)\n• Cristales, Cerraduras y Espejos (Sin Deducible)\n• Responsabilidad Civil USD 500.000", height=120)
    
    with col_b:
        st.write("**Costos Adicionales:**")
        casa = st.text_input("Seguro de Casa (Costo)", "Incluido")
        alquiler = st.text_input("Vehículo de Alquiler", "15 días por choque/robo")
        bici = st.text_input("Seguro de Bicicleta", "Opcional USD 25/mes")

    if st.button("🔥 GENERAR VISTA DE IMPRESIÓN"):
        st.session_state['imprimir'] = True
        st.session_state['p_datos'] = {
            "cliente": nombre_cli, "vehiculo": vehiculo_cot, "ejecutivo": ejecutivo_cot,
            "zona": zona_cot, "tabla": tabla_cot, "beneficios": beneficios,
            "casa": casa, "alquiler": alquiler, "bici": bici
        }

    if st.session_state.get('imprimir'):
        d = st.session_state['p_datos']
        st.divider()
        # HTML para el PDF (Visible solo al imprimir)
        st.markdown(f"""
            <div class="section-to-print">
                <div class="titulo-pdf">🛡️ EDF SEGUROS</div>
                <div class="sub-pdf">Propuesta Comercial | {date.today().strftime('%d/%m/%Y')}</div>
                <hr>
                <p><b>Asegurado:</b> {d['cliente']} | <b>Ejecutivo:</b> {d['ejecutivo']}</p>
                <p><b>Vehículo:</b> {d['vehiculo']} | <b>Zona:</b> {d['zona']}</p>
                <br>
            </div>
        """, unsafe_allow_html=True)
        
        st.table(d['tabla']) # Tabla estática para el PDF
        
        st.markdown(f"""
            <div class="section-to-print">
                <div style="display: flex; gap: 20px; margin-top: 20px;">
                    <div class="cuadro-gris" style="flex: 1;">
                        <b>BENEFICIOS INCLUIDOS:</b><br>{d['beneficios'].replace('\\n', '<br>')}
                    </div>
                    <div class="cuadro-gris" style="flex: 1;">
                        <b>COBERTURAS ADICIONALES:</b><br>
                        • Casa: {d['casa']}<br>
                        • Alquiler: {d['alquiler']}<br>
                        • Bicicleta: {d['bici']}
                    </div>
                </div>
                <p style="text-align: center; margin-top: 30px; font-size: 12px; color: gray;">
                    Propuesta sujeta a inspección y políticas de la aseguradora.
                </p>
            </div>
        """, unsafe_allow_html=True)
        st.info("✅ Propuesta lista. Presiona **Ctrl + P** para guardar como PDF.")

# --- TAB 4: ANÁLISIS (GRÁFICA RESTAURADA) ---
with tab4:
    if not df_f.empty:
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Cartera Total (USD)", f"{df_f['Premio_Total_USD'].sum():,.0f}")
        col_m2.metric("Total Pólizas", len(df_f))
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Aseguradora"), use_container_width=True)
        with col_g2:
            # Gráfica de Barras por Ramo
            ramos_df = df_f['Ramo'].value_counts().reset_index()
            ramos_df.columns = ['Ramo', 'Cantidad']
            st.plotly_chart(px.bar(ramos_df, x='Ramo', y='Cantidad', color='Ramo', title="Pólizas por Ramo"), use_container_width=True)
