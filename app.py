import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# ⚙️ CONFIGURACIÓN Y CONEXIÓN
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS: Ajustados para los dos cuadros de beneficios
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .tabla-impresion {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    .tabla-impresion th, .tabla-impresion td {
        border: 1px solid #333 !important;
        padding: 8px;
        text-align: left;
    }
    .cuadro-beneficios {
        border: 1px solid #333;
        padding: 15px;
        margin-top: 10px;
        background-color: #fdfdfd;
    }
    .titulo-cuadro {
        background-color: #1E1E1E;
        color: white;
        padding: 5px 10px;
        font-weight: bold;
        margin-top: 15px;
    }
    @media print {
        .no-print, .stSidebar, .stTabs, button, header, footer, [data-testid="stToolbar"] { display: none !important; }
        .print-only { display: block !important; width: 100%; }
        .cuadro-beneficios { background-color: white !important; }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_html=True)

# [BLOQUES DE LOGIN Y CARGA DE DATOS SE MANTIENEN IGUAL]
# ... (Asumiendo que ya tienes configurada la conexión 'conn' y el login)

# --- TAB 4: COTIZADOR PROFESIONAL ---
# (Ubicado dentro de tus tabs existentes)
with st.expander("📝 NUEVA COTIZACIÓN", expanded=True):
    # 1. Datos del Cliente
    c1, c2 = st.columns(2)
    with c1:
        ci_bus = st.text_input("CI / RUT")
        nombre_cli = st.text_input("Asegurado")
    with c2:
        vehiculo = st.text_input("Vehículo")
        zona = st.selectbox("Zona", ["Montevideo", "Interior", "Canelones", "Maldonado"])

    # 2. Tabla de Costos
    st.markdown("#### 💰 Comparativa de Aseguradoras")
    if 'data_cot' not in st.session_state:
        st.session_state.data_cot = pd.DataFrame([
            {"Aseguradora": "BSE", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"},
            {"Aseguradora": "SBI", "Contado": 0, "6 Cuotas": 0, "10 Cuotas": 0, "Deducible": "Global"}
        ])
    cot_editada = st.data_editor(st.session_state.data_cot, num_rows="dynamic", use_container_width=True)

    # 3. CONFIGURACIÓN DE LOS 2 CUADROS
    col_b1, col_b2 = st.columns(2)
    
    with col_b1:
        st.markdown("#### ✅ Beneficios Incluidos")
        def_incluidos = "• Auxilio mecánico nacional e internacional 24hs.\n• Cristales, cerraduras y espejos sin deducible.\n• Responsabilidad Civil hasta USD 500.000."
        beneficios_incluidos = st.text_area("Ya vienen con el seguro:", value=def_incluidos, height=120)

    with col_b2:
        st.markdown("#### ➕ Beneficios a Incluir (Opcionales)")
        b1 = st.checkbox("Alquiler 15 días (UYU 3.900)")
        b2 = st.checkbox("Bici USD 1.000 (USD 70)")
        b3 = st.checkbox("Casa (Incendio/Hurto) (USD 150)")
        
        texto_opc = ""
        if b1: texto_opc += "- Vehículo de Alquiler (15 días): UYU 3.900 anual.\n"
        if b2: texto_opc += "- Seguro para tu bicicleta (hasta USD 1000): USD 70 anual.\n"
        if b3: texto_opc += "- Seguro de Hogar completo (Incendio/Hurto): USD 150 anual.\n"
        beneficios_opcionales = st.text_area("Sugerencias para el cliente:", value=texto_opc, height=80)

    # 4. Botón Guardar
    if st.button("💾 Guardar y Generar PDF", use_container_width=True):
        cot_actual = {
            "Fecha": date.today().strftime("%d/%m/%Y"),
            "Cliente": nombre_cli, "Documento": ci_bus, "Vehiculo": vehiculo, "Zona": zona,
            "Tabla": cot_editada.to_json(),
            "Incluidos": beneficios_incluidos,
            "Opcionales": beneficios_opcionales
        }
        # Aquí iría tu lógica de 'conn.update' para la pestaña Cotizaciones_Emitidas
        st.session_state['cot_final'] = cot_actual
        st.success("¡Cotización guardada!")

# 5. VISTA DE IMPRESIÓN (Lo que sale con Control + P)
if 'cot_final' in st.session_state:
    c = st.session_state['cot_actual'] if 'cot_actual' in st.session_state else st.session_state['cot_final']
    st.markdown("---")
    tabla_html = pd.read_json(c['Tabla']).to_html(index=False, classes='tabla-impresion')
    
    st.markdown(f"""
        <div class="print-only">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h1 style="margin:0;">🛡️ EDF SEGUROS</h1>
                <p>Fecha: {c['Fecha']}</p>
            </div>
            <hr>
            <p><b>Propuesta para:</b> {c['Cliente']} | <b>CI:</b> {c['Documento']}</p>
            <p><b>Vehículo:</b> {c['Vehiculo']} | <b>Zona:</b> {c['Zona']}</p>
            
            {tabla_html}
            
            <div class="titulo-cuadro">✅ BENEFICIOS INCLUIDOS EN TU PÓLIZA</div>
            <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Incluidos']}</div>
            
            <div class="titulo-cuadro">➕ MEJORÁ TU COBERTURA (OPCIONALES)</div>
            <div class="cuadro-beneficios" style="white-space: pre-wrap;">{c['Opcionales'] if c['Opcionales'] else 'Consultar por otros beneficios adicionales.'}</div>
            
            <br>
            <p style="text-align: center; font-size: 12px;">Gracias por confiar en EDF SEGUROS</p>
        </div>
    """, unsafe_allow_html=True)
    st.info("Presiona **Control + P** para ver la vista previa con los dos cuadros.")
