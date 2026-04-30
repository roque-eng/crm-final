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

# Estilos CSS críticos para evitar el PDF en blanco
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    
    /* Lógica de Impresión Profesional */
    @media print {
        /* Oculta la interfaz de Streamlit que causa el error de página en blanco */
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], 
        .stTabs, button, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
            display: none !important; 
        }
        
        /* Fuerza la visibilidad del contenido de la cotización */
        .section-to-print { 
            display: block !important; 
            visibility: visible !important;
            position: absolute;
            left: 0; top: 0; width: 100%;
        }
    }
    /* Oculta el bloque de impresión en la vista web normal */
    .section-to-print { display: none; }
    
    .titulo-pdf { font-size: 32px; font-weight: bold; color: #1E1E1E; border-bottom: 2px solid #1E1E1E; }
    .cuadro-gris { background-color: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 SEGURIDAD (Login)
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

# Sidebar con Filtros Globales (Restaurados)
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
# 📑 PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "📊 ANÁLISIS"])

# --- TAB 1: CARTERA ---
with tab1:
    busq = st.text_input("🔍 Buscar por cliente, matrícula o documento...")
    df_c = df_f.copy()
    if busq:
        df_c = df_c[df_c.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
    
    # Icono de carpetita funcional y tabla ordenable
    st.dataframe(
        df_c, use_container_width=True, hide_index=True,
        column_config={
            "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂")
        }
    )

# --- TAB 3: COTIZADOR (TODO RESTAURADO) ---
with tab3:
    st.subheader("📝 Módulo de Cotización")
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1, 1])
        doc_input = c1.text_input("Documento (CI / RUT)")
        
        # Lógica de autocompletado por CI/RUT
        nombre_sugerido = ""
        if doc_input:
            match = df_raw[df_raw['Documento de Identidad (Rut/Cédula/Otros)'].astype(str).str.contains(doc_input)]
            if not match.empty:
                nombre_sugerido = match.iloc[0]['Asegurado (Nombre/Razón Social)']
        
        nombre_cli = c2.text_input("Asegurado", value=nombre_sugerido)
        ejecutivo_cot = c3.selectbox("Ejecutivo Responsable", ["Roque de Freitas", "Joe", "Andre"])
        
        cx, cy = st.columns(2)
        vehiculo_cot = cx.text_input("Vehículo (Marca, Modelo, Año)")
        zona_cot = cy.selectbox("Zona de Circulación", ["Montevideo", "Canelones", "Maldonado", "Interior"])

    st.markdown("#### 📊 Comparativa de Seguros")
    df_propu = pd.DataFrame([
        {"Aseguradora": "BSE", "Contado": 0.0, "6 Cuotas": 0.0, "10 Cuotas": 0.0, "Deducible": "Global"},
        {"Aseguradora": "SBI", "Contado": 0.0, "6 Cuotas": 0.0, "10 Cuotas": 0.0, "Deducible": "Global"}
    ])
    tabla_cot = st.data_editor(df_propu, num_rows="dynamic", use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        beneficios = st.text_area("Beneficios Incluidos", 
            "• Auxilio mecánico 24hs.\n• Cristales, Cerraduras y Espejos sin deducible.\n• RC USD 500.000", height=150)
    with col_b:
        casa = st.text_input("Seguro Hogar", "Incluido - Incendio USD 100.000")
        alquiler = st.text_input("Auto Alquiler", "15 días por choque")
        bici = st.text_input("Seguro Bici", "Opcional USD 20/mes")

    if st.button("🔥 GENERAR VISTA DE IMPRESIÓN"):
        st.session_state['imprimir'] = True
        st.session_state['datos_p'] = {
            "cliente": nombre_cli, "vehiculo": vehiculo_cot, "ejecutivo": ejecutivo_cot,
            "zona": zona_cot, "tabla": tabla_cot, "beneficios": beneficios,
            "casa": casa, "alquiler": alquiler, "bici": bici
        }

    # SECCIÓN QUE SE ACTIVA PARA EL PDF
    if st.session_state.get('imprimir'):
        d = st.session_state['datos_p']
        st.divider()
        st.markdown(f"""
            <div class="section-to-print">
                <div class="titulo-pdf">🛡️ EDF SEGUROS</div>
                <p><b>Fecha:</b> {date.today().strftime('%d/%m/%Y')} | <b>Asegurado:</b> {d['cliente']}</p>
                <p><b>Vehículo:</b> {d['vehiculo']} | <b>Ejecutivo:</b> {d['ejecutivo']}</p>
                <br>
            </div>
        """, unsafe_allow_html=True)
        
        # Mostramos una tabla estática (st.table) que sí es reconocida por el motor de impresión
        st.table(d['tabla'])
        
        st.markdown(f"""
            <div class="section-to-print">
                <div style="display: flex; gap: 20px;">
                    <div class="cuadro-gris" style="flex: 1;">
                        <b>BENEFICIOS:</b><br>{d['beneficios'].replace('\\n', '<br>')}
                    </div>
                    <div class="cuadro-gris" style="flex: 1;">
                        <b>ADICIONALES:</b><br>
                        • Hogar: {d['casa']}<br>
                        • Alquiler: {d['alquiler']}<br>
                        • Bicicleta: {d['bici']}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.info("✅ Propuesta lista. Ahora presiona **Ctrl + P** para guardar el PDF.")

# --- TAB 4: ANÁLISIS ---
with tab4:
    if not df_f.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía"), use_container_width=True)
        with col_g2:
            ramos_df = df_f['Ramo'].value_counts().reset_index()
            st.plotly_chart(px.bar(ramos_df, x='Ramo', y='count', title="Pólizas por Ramo"), use_container_width=True)
