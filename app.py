import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64
import requests

# --- INICIALIZACIÓN DE MEMORIA (HISTORIAL) ---
if "historico" not in st.session_state:
    st.session_state.historico = []

if "edit_data" not in st.session_state:
    st.session_state.edit_data = {}
# ---------------------------------------------

# 1. Definición Global de Usuarios
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "GS": "GSanchez2025", "MDF": "Matiti2025", "EH": "EHugo2025", "AP": "APerdomo2025", "RS": "RSierra2025", "LT": "LTomasi2025", "EC": "ECabral2025", "PG": "PGagliardi2025"}

# 2. Red de seguridad para el Session State
if 'usuario_actual' not in st.session_state:
    st.session_state['usuario_actual'] = "Invitado" # O podés poner "RDF" por defecto para que no falle nunca

# ==========================================
# ⚙️ CONFIGURACIÓN Y CONEXIONES
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

# Credenciales de Supabase - USANDO TUS CLAVES PASADAS
SUPABASE_URL = "https://flizerdhoxxoekaczihm.supabase.co"
SUPABASE_KEY = "sb_publishable_lkSd6DNhiwifC-qCMkYNdQ_U97XIxog" 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

def fmt_curr(val):
    try:
        num = float(str(val).replace('$', '').replace('.', '').replace(',', '').strip())
        return f"$ {int(num):,}".replace(",", ".")
    except: return val

def guardar_en_db(datos):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/cotizaciones", headers=headers, json=datos)
        return response.status_code in [200, 201]
    except: return False

def leer_historial():
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/cotizaciones?select=*&order=created_at.desc", headers=headers)
        return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# Estilos CSS - Cambiados de Bordo a Azul Profesional y Celeste para tablas
# Estilos CSS - Solo Vista Cliente en Azul Profesional
st.markdown("""
    <style>
    @media print { .stButton, [data-testid="stSidebar"], .stDownloadButton, footer, header { display: none !important; } }
    
    /* Línea principal debajo del título en la vista del cliente */
    .linea-azul { 
        border-bottom: 4px solid #1E3A8A !important; 
        margin-bottom: 30px; 
    }
    
    /* Encabezados de la tabla en la vista del cliente */
    thead tr th { 
        background-color: #f0f7ff !important; 
        color: #1E3A8A !important; 
        padding: 18px; 
        font-size: 20px; 
        text-align: center !important; 
    }
    
    /* Líneas laterales de los beneficios */
    .ben-fila { 
        background-color: #f8f9fa; 
        padding: 12px 20px; 
        border-radius: 8px; 
        margin-bottom: 10px; 
        border-left: 6px solid #1E3A8A !important; 
        width: 100%; 
        font-size: 16px; 
        color: #333; 
    }
    
    /* Cajones de Coberturas Complementarias (Borde superior azul) */
    .caja-azul { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        height: 100%; 
        border: 1px solid #e0e0e0; 
        border-top: 5px solid #1E3A8A !important; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05); 
    }
    
    /* Resaltado de costos dentro de los cajones */
    .costo-res { 
        color: #1E3A8A !important; 
        font-weight: bold; 
        display: block; 
        margin-top: 10px; 
        font-size: 19px; 
        background: #f0f7ff !important; 
        padding: 5px 10px; 
        border-radius: 5px; 
    }

    /* Firma del asesor al final */
    .firma-asesor {
        border-top: 1px solid #1E3A8A !important;
        padding-top: 10px;
        color: #1E3A8A;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. RECEPCIÓN DE DATOS ---
query_params = st.query_params
p = None

# Buscar en la Nube (Link Seguro)
if "f_id" in query_params:
    f_id = query_params["f_id"]
    headers_sp = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    url_get = f"{SUPABASE_URL}/rest/v1/cotizaciones?id=eq.{f_id}&select=data"
    try:
        response = requests.get(url_get, headers=headers_sp).json()
        if response: p = response[0]["data"]
    except: pass

# Buscar en el Link (Método viejo)
if not p:
    if "f" in query_params:
        p = json.loads(base64.b64decode(query_params["f"]).decode())
    elif "q" in query_params:
        p = json.loads(base64.b64decode(query_params["q"]).decode())

# --- 2. VISTA DEL CLIENTE ---
if p:
# --- 1. ENCABEZADO ---
    # Buscamos cliente y aseguradora con nombres simples
    cliente = p.get('cliente') or "CABLEX"
    aseguradora = p.get('aseguradora') or "SBI"
    
    col_logo, col_info = st.columns([1, 2])
    with col_logo:
        st.image("https://rpyiditlookfcrgeterf.supabase.co/storage/v1/object/public/logos/EDF%20Logotipo%20PNG.png", width=180)
    with col_info:
        st.markdown(f"## Asegurado: {cliente}")
        st.markdown(f"### 🏦 Aseguradora: **{aseguradora}**")

    # --- 2. TABLA DE VEHÍCULOS (VERSIÓN FINAL RESISTENTE) ---
    # Intentamos capturar la lista de vehículos de cualquier forma
    lista_v = []
    if 'vehiculos' in p: lista_v = p['vehiculos']
    elif 'items' in p: lista_v = p['items']
    elif 'data' in p and isinstance(p['data'], dict): lista_v = p['data'].get('vehiculos', [])

    if lista_v:
        tabla_html = """
        <table style="width:100%; border-collapse: collapse; margin-top: 20px; font-family: sans-serif;">
            <thead>
                <tr style="background-color: #333; color: white;">
                    <th style="padding: 10px; border: 1px solid #ddd;">MARCA</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">MODELO</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">AÑO</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">MATRICULA</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">COBERTURA</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">CONTADO</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">DEDUCIBLE</th>
                </tr>
            </thead>
            <tbody>
        """
        for v in lista_v:
            # Limpiamos decimales de los números
            def a_entero(valor):
                try: return f"{int(float(valor)):,}"
                except: return str(valor)

            p_fmt = f"USD {a_entero(v.get('cuota') or v.get('precio', 0))}"
            d_fmt = a_entero(v.get('deducible', 0))
            
            tabla_html += f"""
                <tr style="text-align: center; border-bottom: 1px solid #eee;">
                    <td style="padding: 8px; border: 1px solid #ddd;">{v.get('marca', '')}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{v.get('modelo', '')}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{v.get('anio') or v.get('año', '')}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{v.get('matricula', '-')}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{v.get('cobertura', '')}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{p_fmt}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{d_fmt}</td>
                </tr>
            """
        tabla_html += "</tbody></table>"
        st.markdown(tabla_html, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No se encontraron vehículos en esta cotización. Probá generar un link nuevo.")

    # --- 3. COMENTARIOS ---
    obs = p.get('beneficios') or p.get('observaciones') or "Revisar condiciones de póliza."
    st.markdown('<br><p style="color: #333; font-size: 24px; font-weight: bold;">Comentarios EDF Seguros</p>', unsafe_allow_html=True)
    st.markdown('<div style="border-bottom: 4px solid #333; margin-bottom: 15px;"></div>', unsafe_allow_html=True)
    st.info(obs)
    
# --- PIE DE PÁGINA DINÁMICO ---
    fecha_val = p.get('fecha', datetime.now().strftime("%d/%m/%Y"))
    
    if not es_flota:
        # INDIVIDUAL
        st.markdown(f"""
            <div class="footer-cliente">
                <div><b>Fecha de Cotización:</b> {fecha_val}</div>
                <div><b>Asesor:</b> {p.get('e', 'EDF SEGUROS')} | <b>Contacto:</b> {p.get('cont', '099 635 244')}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # FLOTA
        st.markdown(f'<div class="footer-cliente" style="justify-content: flex-end;">Fecha de Cotización: {fecha_val}</div>', unsafe_allow_html=True)
    
    # ESTO ES LO MÁS IMPORTANTE:
    st.stop()
    
    # --- FORMATEO DE PRECIOS ($ y miles) ---
    for col in ["Contado", "10 Cuotas", "Deducible"]:
        if col in df_p.columns:
            # Convertimos a número y aplicamos formato
            df_p[col] = pd.to_numeric(df_p[col], errors='coerce').fillna(0)
            df_p[col] = df_p[col].apply(lambda x: f"$ {int(x):,}".replace(",", "."))
    # 1. Definimos todas las columnas de texto posibles (Individual y Flota)
    cols_texto = ["Aseguradora", "Marca", "Modelo", "Matrícula", "Cobertura", "Vehículo"]
    
    # 2. Identificamos cuáles de estas están realmente en los datos cargados
    existentes = [c for c in cols_texto if c in df_p.columns]
    
    # 3. Identificamos todas las demás (precios, deducibles, etc.)
    precios_y_otros = [c for c in df_p.columns if c not in cols_texto]
    
    # 4. Mostramos la tabla final con el orden correcto
    st.markdown('<div class="tabla-container">', unsafe_allow_html=True)
    st.write(df_p[existentes + precios_y_otros].to_html(index=False, escape=False), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ... (El resto de beneficios y coberturas complementarias que ya tenés) ...
    # 5. Beneficios en filas separadas
    st.write("")
    st.markdown("### ✅ Beneficios Incluidos")
    for b in p.get("ben", "").split('\n'):
        if b.strip():
            st.markdown(f'<div class="ben-fila">{b.strip()}</div>', unsafe_allow_html=True)

    # 6. Coberturas Complementarias (Signo ⚠️ y Cajones Azules)
    st.write("")
    st.markdown("### ⚠️ Coberturas Complementarias")
    col1, col2, col3 = st.columns(3)

    def bloque_html(titulo, icono, texto, es_hogar=False):
        html = f'<div class="caja-azul"><span class="sub-tit">{icono} {titulo}</span>'
        
        # Si el texto tiene un signo $ o la palabra Costo, lo resaltamos
        lineas = texto.split('\n')
        for linea in lineas:
            linea = linea.strip()
            if not linea: continue
            
            # Si la línea tiene $ o dice Costo, le ponemos la clase "costo-res"
            if "$" in linea or "Costo" in linea:
                # Quitamos puntos previos si los hay para que no se dupliquen iconos
                l_limpia = linea.replace("•", "").strip()
                html += f'<span class="costo-res">💰 {l_limpia}</span>'
            else:
                html += f'<span>{linea}</span>'
        
        html += '</div>'
        return html

    col1.markdown(bloque_html("Hogar", "🏠", p.get("ch", ""), True), unsafe_allow_html=True)
    col2.markdown(bloque_html("Alquiler", "🚗", p.get("ca", "")), unsafe_allow_html=True)
    col3.markdown(bloque_html("Bici", "🚲", p.get("cb", "")), unsafe_allow_html=True)

    # 7. Firma del Asesor
    st.markdown("---")
    st.markdown(f"**Asesor:** {p.get('e', '')} | **Contacto:** {p.get('cont', '')}")
    st.stop()

    # 5. Beneficios en filas separadas
    st.write("")
    st.markdown("### ✅ Beneficios Incluidos")
    for b in p.get("ben", "").split('\n'):
        if b.strip():
            st.markdown(f'<div class="ben-fila">{b.strip()}</div>', unsafe_allow_html=True)

    # 6. Coberturas Complementarias (Signo ⚠️ y Cajones Azules)
    st.write("")
    st.markdown("### ⚠️ Coberturas Complementarias")
    col1, col2, col3 = st.columns(3)
    
    def bloque_html(titulo, icono, texto, es_hogar=False):
        html = f'<div class="caja-azul"><span class="sub-tit">{icono} {titulo}</span>'
        if es_hogar:
            # Lógica para resaltar los dos costos de Hogar
            partes = texto.split("Costo Anual")
            html += f'<span>{partes[0].strip()}</span>'
            for pc in partes[1:]:
                html += f'<span class="costo-res">💰 Costo Anual {pc.strip()}</span>'
        else:
            if "Costo:" in texto:
                partes = texto.split("Costo:")
                html += f'<span>{partes[0].strip()}</span>'
                html += f'<span class="costo-res">💰 Costo: {partes[1].strip()}</span>'
            else:
                html += f'<span>{texto}</span>'
        html += '</div>'
        return html

    col1.markdown(bloque_html("Hogar", "🏠", p.get("ch", ""), True), unsafe_allow_html=True)
    col2.markdown(bloque_html("Alquiler", "🚗", p.get("ca", "")), unsafe_allow_html=True)
    col3.markdown(bloque_html("Bici", "🚲", p.get("cb", "")), unsafe_allow_html=True)

    # 7. Firma del Asesor
    st.markdown("---")
    st.markdown(f"**Asesor:** {p.get('e', '')} | **Contacto:** {p.get('cont', '')}")
    
    # Detenemos la ejecución para que el cliente no vea el panel de control
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(spreadsheet=URL_HOJA, ttl=0)
df_raw.columns = df_raw.columns.str.strip()
df_raw['Premio_Total_USD'] = (pd.to_numeric(df_raw.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0) + (pd.to_numeric(df_raw.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0) / TC_USD)).round(0)
df_raw['Fin de Vigencia'] = pd.to_datetime(df_raw['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date

with st.sidebar:
# --- BLOQUE CORREGIDO (Líneas 187-203) ---
        nombre_asesor = USUARIOS.get(st.session_state.get('usuario_actual', 'RDF'), "Asesor")
        st.title(f"👤 {nombre_asesor}")

        def get_list(col): 
            return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
        
        f_ej = st.selectbox("Ejecutivo", get_list('Ejecutivo'))
        f_as = st.selectbox("Aseguradora", get_list('Aseguradora'))
        f_ra = st.selectbox("Ramo", get_list('Ramo'))
        f_co = st.selectbox("Corredor", get_list('Corredor'))
        f_ag = st.selectbox("Agente", get_list('Agente'))
        
        if st.button("Cerrar Sesión"): 
            st.session_state['logueado'] = False
            st.rerun()

    # Importante: Esta línea debe estar al mismo nivel que el "with st.sidebar:" de arriba
df_f = df_raw.copy()

    # --- Lógica de filtrado (Pegar debajo de df_f = df_raw.copy()) ---
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]
    
# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTADOS (BLOQUE 3)
# ==========================================

# Definición de Usuarios (asegurate de tener esto arriba si no estaba)

# Inicializar estados para Edición V.2
if "edit_data" not in st.session_state:
    st.session_state.edit_data = None
if "es_edicion" not in st.session_state:
    st.session_state.es_edicion = False

# Crear Pestañas
tab_car, tab_ven, tab_cot, tab_flota, tab_historial, tab_an = st.tabs([
    "👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "🚛 FLOTAS", "📜 HISTORIAL", "📊 ANÁLISIS"
])

# --- PESTAÑA CARTERA ---
with tab_car:
    busq = st.text_input("🔍 Buscar cliente o matrícula en cartera...")
    df_c = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f
    df_disp_c = df_c.copy()
    if 'Fin de Vigencia' in df_disp_c.columns:
        df_disp_c['Fin de Vigencia'] = pd.to_datetime(df_disp_c['Fin de Vigencia']).dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        df_disp_c, use_container_width=True, hide_index=True, 
        column_config={
            "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂"),
            "Premio USD (IVA inc)": st.column_config.NumberColumn("Premio USD", format="USD %.0f"),
            "Premio UYU (IVA inc)": st.column_config.NumberColumn("Premio UYU", format="$ %.0f"),
            "Premio_Total_USD": st.column_config.NumberColumn("Total USD", format="USD %.0f")
        }
    )

# --- PESTAÑA VENCIMIENTOS ---
with tab_ven:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        c1, c2 = st.columns(2)
        f_ini = c1.date_input("Desde:", date.today().replace(day=1))
        f_fin = c2.date_input("Hasta:", date.today() + timedelta(days=90))
        df_venc_f = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')
        df_venc_disp = df_venc_f.copy()
        df_venc_disp['Fin de Vigencia'] = pd.to_datetime(df_venc_disp['Fin de Vigencia']).dt.strftime('%d/%m/%Y')
        
        st.dataframe(
            df_venc_disp, use_container_width=True, hide_index=True,
            column_config={
                "Adjunto (póliza)": st.column_config.LinkColumn("Póliza", display_text="📂"),
                "Premio USD (IVA inc)": st.column_config.NumberColumn("Premio USD", format="USD %.0f"),
                "Premio UYU (IVA inc)": st.column_config.NumberColumn("Premio UYU", format="$ %.0f")
            }
        )
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_venc_f.to_excel(writer, index=False)
        st.download_button(label="📥 Exportar a Excel", data=output.getvalue(), file_name='vencimientos.xlsx')

# --- PESTAÑA COTIZADOR INDIVIDUAL (Con todas las columnas) ---
with tab_cot:
    st.subheader("📝 Cotizador Seguros para Vehículos")
    
    # 1. Recuperar datos de edición (Solo si es individual, detectamos por la 'v' de vehículo)
    edit_ind = st.session_state.edit_data if st.session_state.edit_data and "v" in st.session_state.edit_data else {}
    
    # 2. Cabecera de Datos
    with st.container(border=True):
        c_doc, c_nom, c_veh, c_ase, c_con = st.columns([1.5, 2, 2, 1, 2])
        doc_in = c_doc.text_input("CI/RUT", value=edit_ind.get("doc", ""), key="ci_v_final")
        n_cot = c_nom.text_input("Nombre", value=edit_ind.get('n', '') if edit_ind else "", key="nom_v_final")
        v_cot = c_veh.text_input("Vehículo", value=edit_ind.get("v", "") if edit_ind else "", key="veh_v_final")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="ase_v_final")
        cont_cot = c_con.text_input("Contacto Asesor", value=edit_ind.get("cont", "099 635 244") if edit_ind else "099 635 244", key="cont_v_final")

    st.markdown("---")
    
    # 3. TABLA CON LAS 4 COLUMNAS QUE FALTABAN
    st.markdown("#### Seleccione las opciones de cobertura:")
    
    # Definimos el orden de las columnas para que no se pierdan
    cols_individual = ["Aseguradora", "Contado", "10 Cuotas", "Deducible"]
    
    if edit_ind and "tab" in edit_ind:
        df_p_init = pd.DataFrame(edit_ind["tab"])
    else:
        # Cargamos las aseguradoras por defecto
        df_p_init = pd.DataFrame([
            {"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0},
            {"Aseguradora": "SURA", "Contado": 0, "10 Cuotas": 0, "Deducible": 0},
            {"Aseguradora": "MAPFRE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0},
            {"Aseguradora": "SANCOR", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}
        ])
    
    # EL EDITOR: Aquí forzamos las 4 columnas
    t_edit = st.data_editor(
        df_p_init, 
        num_rows="dynamic", 
        use_container_width=True, 
        column_order=cols_individual, # <--- ESTO ASEGURA QUE SE VEAN LAS 4
        key="editor_individual_completo"
    )
    
    # 4. Textos Precargados (Beneficios y Complementarios)
    col_a, col_b = st.columns(2)
    with col_a:
        t_ben_def = "• Auxilio mecánico 24hs: Todas las aseguradoras\n• Cristales: BSE/SBI USD 200, SURA USD 100, MAPFRE ilimitado, SANCOR USD 300\n• Granizo: SANCOR sin deducible"
        b_cot = st.text_area("Beneficios:", value=edit_ind.get("ben", t_ben_def), height=200, key="ben_v_final")
    with col_b:
        t_h_def = "• Incendio Edificio: USD 100.000\n• Incendio Contenido: USD 50.000\n• Hurto Contenido: USD 5.000\nCosto Anual Apartamentos: USD 120\nCosto Anual Casas: USD 190"
        c_h = st.text_area("Hogar:", value=edit_ind.get("ch", t_h_def), height=130, key="hog_v_final")
        c_a = st.text_area("Alquiler:", value=edit_ind.get("ca", "• Auto cortesía 15 días en caso de que tu vehículo vaya al taller por un siniestro\nCosto Anual: $3.500"), height=70, key="alq_v_final")
        c_b = st.text_area("Bici Eléctrica:", value=edit_ind.get("cb", "• Hurto USD 1.000\n• Accidentes Personales: USD 5.000\n• Daños a terceros: USD 10.000\nCosto Anual: USD 120"), height=70, key="bic_v_final")

    # 5. Lógica de Guardado (Específica para Individual)
    if st.button("💾 Guardar y ver Vista Previa", use_container_width=True):
        datos_i = {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "n": n_cot, "v": v_cot, "e": e_cot, "cont": cont_cot, "doc": doc_in,
            "tab": t_edit.to_dict(orient='records'),
            "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b,
            "tipo": "Individual"
        }
        # ESTA ES LA LÍNEA CLAVE:
        st.session_state.historico.append(datos_i) 
        
        st.session_state.edit_data = datos_i
        st.success(f"✅ Cotización de {n_cot} guardada en el historial.")
        st.rerun()
        
    # 6. Botón de Vista Previa (Solo para Individual)
    if st.session_state.edit_data and "v" in st.session_state.edit_data:
        st.markdown("---")
        # Encriptamos
        datos_b64 = base64.b64encode(json.dumps(st.session_state.edit_data).encode()).decode()
        link_final = f"https://dfseguros.streamlit.app/?q={datos_b64}"
        
        st.link_button("🚀 VER VISTA PREVIA", link_final, type="primary", use_container_width=True)
        st.code(link_final)

# --- PESTAÑA FLOTAS ---
# --- PESTAÑA FLOTAS (CON CORRECCIÓN DE ENCABEZADOS Y VISTA PREVIA) ---
with tab_flota:
    st.subheader("📋 Cotizador Seguro de Flotas")
    
    # 1. Recuperar datos de edición (Detectamos si es Flota)
    edit_f = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Flota" else {}
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_asegurado = st.text_input("Asegurado", value=edit_f.get('n', ''), key="f_nom_flota_vfinal")
        # Aseguradora (Compañía)
        f_cia_elegida = st.selectbox("Aseguradora", ["BSE", "SURA", "MAPFRE", "SANCOR", "SBI", "PORTO", "ALIANZ"], key="f_cia_select_vfinal")
    with col_f2:
        # ASESOR (Nombre de la persona) - Variable independiente
        f_asesor_nombre = st.text_input("Asesor", value=edit_f.get('e_nombre', 'EDF SEGUROS'), key="f_asesor_input_vfinal")
        f_contacto = st.text_input("Contacto", value=edit_f.get('cont', '099 635 244'), key="f_cont_vfinal")

    st.markdown("---")
    
    # 2. DEFINICIÓN DE COLUMNAS DE FLOTA (Ahora con Año)
    cols_f = ["Marca", "Modelo", "Año", "Matrícula", "Cobertura", "Contado", "Deducible"]
    
    # 3. CARGA DE TABLA
    if edit_f and "tab" in edit_f:
        df_f_init = pd.DataFrame(edit_f["tab"])
        # Reindexamos para que tome la nueva columna Año si no existe en el registro viejo
        df_f_init = df_f_init.reindex(columns=cols_f).fillna("")
    else:
        # Fila inicial vacía con la columna Año
        df_f_init = pd.DataFrame([{
            "Marca": "", "Modelo": "", "Año": "", "Matrícula": "", 
            "Cobertura": "Total", "Contado": 0, "Deducible": 0
        }])

    # 4. EL EDITOR
    t_flota = st.data_editor(
        df_f_init, 
        num_rows="dynamic", 
        use_container_width=True, 
        column_order=cols_f, 
        key="editor_flotas_v_final_año"
    )

    st.markdown("### 📝 Detalles de la Propuesta")
    f_obs = st.text_area("Observaciones:", value=edit_f.get('ben', ''), height=150, key="f_obs_vfinal_fix")

    # 5. BOTÓN GUARDAR (Corregido para separar Aseguradora de Asesor)
    if st.button("🚀 GUARDAR PROPUESTA", key="btn_save_flota_vfinal", use_container_width=True):
        nueva_f = {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "n": f_asegurado, 
            "e": f_cia_elegida,     # Guarda BSE, SURA, etc.
            "e_nombre": f_asesor_nombre,  # Guarda tu nombre (ej: Roque)
            "cont": f_contacto,
            "tab": t_flota.to_dict(orient='records'), 
            "ben": f_obs, 
            "tipo": "Flota"
        }
        if "historico" not in st.session_state: st.session_state.historico = []
        st.session_state.historico.append(nueva_f)
        st.session_state.edit_data = nueva_f
        st.success(f"✅ ¡Flota de {f_asegurado} guardada!")
        st.rerun()

    # 6. RECUPERACIÓN DEL BOTÓN VISTA PREVIA (Gris Oscuro)
    # Se muestra si acabas de guardar o si cargaste una flota del historial
    if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Flota":
        st.markdown("---")
        st.markdown("### 🔗 Link de Flota para enviar")
        
        # Encriptamos los datos actuales
        datos_f_json = json.dumps(st.session_state.edit_data)
        datos_f_b64 = base64.b64encode(datos_f_json.encode()).decode()
        
    # --- BOTÓN PARA FLOTAS GRANDES (Línea 580 aprox) ---
    if st.button("🔗 GENERAR LINK", use_container_width=True):
            try:
                import uuid
                # CAMBIO CLAVE: Usamos el código largo que Supabase espera
                f_id = str(uuid.uuid4()) 
                datos_f = st.session_state.edit_data
                
                headers_sp = {
                    "apikey": SUPABASE_KEY, 
                    "Authorization": f"Bearer {SUPABASE_KEY}", 
                    "Content-Type": "application/json"
                }
                
                # Mandamos el f_id largo
                payload = {"id": f_id, "data": datos_f, "tipo": "flota"}
                
                res = requests.post(f"{SUPABASE_URL}/rest/v1/cotizaciones", headers=headers_sp, json=payload)
                
                if res.status_code in [200, 201]:
                    link_f = f"https://dfseguros.streamlit.app/?f_id={f_id}"
                    st.success("✅ ¡Link generado con éxito!")
                    st.code(link_f)
                    st.link_button("🚀 VISTA PREVIA", link_f, type="primary", use_container_width=True)
                else:
                    st.error(f"Error: {res.text}")
            except Exception as e:
                st.error(f"Error técnico: {e}")
        
# --- PESTAÑA HISTORIAL (CORREGIDA) ---
with tab_historial:
    st.subheader("📜 Historial de Cotizaciones")
    if "historico" in st.session_state and st.session_state.historico:
        # Recorremos el historial del más nuevo al más viejo
        for i, reg in enumerate(reversed(st.session_state.historico)):
            idx_real = len(st.session_state.historico) - 1 - i
            
            # Creamos una fila con columnas: Info, Editar y Borrar
            col_info, col_edit, col_del = st.columns([0.7, 0.15, 0.15])
            
            with col_info:
                fecha = reg.get('fecha', 'S/F')[:10]  # Tomamos solo la fecha
                nombre = reg.get('n', 'Cliente')
                
                # --- AQUÍ ESTÁ EL CAMBIO DEL PASO 2 ---
                tipo_raw = reg.get("tipo", "Individual") # Si no tiene tipo, asumimos Individual
                
                if tipo_raw == "Flota":
                    tipo_display = "🚚 Flota"
                else:
                    tipo_display = "🚗 Individual"
                
                # Mostramos la línea del historial
                st.write(f"**{fecha}** | {tipo_display} | **{nombre}**")
            
            with col_edit:
                if st.button("✏️ Editar", key=f"edit_{idx_real}"):
                    st.session_state.edit_data = reg
                    st.success(f"Cargado: {nombre}")
                    st.rerun()
            
            with col_del:
                if st.button("🗑️", key=f"del_{idx_real}"):
                    st.session_state.historico.pop(idx_real)
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No hay cotizaciones guardadas aún.")


# --- PESTAÑA ANÁLISIS ---
with tab_an:
    st.subheader("📊 Análisis de Cartera")
    if not df_f.empty:
        t_usd = df_f['Premio_Total_USD'].sum()
        k1, k2 = st.columns(2)
        k1.metric("Cartera Total (USD)", f"USD {t_usd:,.0f}")
        k2.metric("Total de Pólizas", f"{len(df_f)}")
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Compañía", hole=0.4), use_container_width=True)
        with c2: st.plotly_chart(px.pie(df_f, names='Ramo', values='Premio_Total_USD', title="Ramo", hole=0.4), use_container_width=True)
