import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64
import requests

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

st.markdown("""
    <style>
    @media print { .stButton, [data-testid="stSidebar"], .stDownloadButton, footer, header { display: none !important; } }
    .titulo-bordo { color: #800020; font-size: 22px; font-weight: bold; border-bottom: 3px solid #800020; padding-bottom: 8px; margin-bottom: 20px; text-transform: uppercase; }
    .quote-card { background-color: #fdfdfd; padding: 20px; border-radius: 10px; border: 1px solid #eee; white-space: pre-wrap; font-family: sans-serif; font-size: 14px; line-height: 1.6; }
    [data-testid="stTable"] td { text-align: right !important; }
    </style>
    """, unsafe_allow_html=True)

query_params = st.query_params
# Esta parte suele ir arriba del todo en tu código principal
# ==========================================
# 📱 VISTA DE LA PROPUESTA PARA EL CLIENTE
# ==========================================
# --- DETECCIÓN DE PROPUESTA (Individual o Flota) ---
p = None
if "flota" in st.query_params:
    try:
        nombre_cliente = base64.b64decode(st.query_params["flota"]).decode()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        url_busqueda = f"{SUPABASE_URL}/rest/v1/cotizaciones?asegurado=eq.{nombre_cliente}&tipo=eq.flota&order=created_at.desc&limit=1"
        res = requests.get(url_busqueda, headers=headers)
        if res.status_code == 200 and len(res.json()) > 0:
            p = res.json()[0]["datos_json"]
    except: st.error("Error al cargar datos de flota.")
elif "q" in st.query_params or "f" in st.query_params:
    try:
        val = st.query_params.get("q") or st.query_params.get("f")
        p = json.loads(base64.b64decode(val).decode())
    except: st.error("Error al cargar cotización.")

# Si hay una propuesta, se muestra la vista limpia
if p:
# --- ALREDEDOR DE LA FILA 85 ---
# --- VISTA DEL CLIENTE: ESTILO REFINADO ---
    st.markdown("""
        <style>
            .main .block-container { max-width: 100% !important; padding-top: 2rem; }
            
            /* Título en Gris Muy Oscuro */
            .titulo-cot { color: #2C2C2C; font-size: 42px !important; font-weight: 800; margin-bottom: 0px; }
            
            /* Línea en Bordó institucional */
            .linea { border-bottom: 4px solid #800020; margin-bottom: 30px; }
            
            .tabla-container { width: 100%; margin: 25px 0; }
            table { width: 100% !important; border-collapse: collapse; margin: 0 auto; }
            
            /* Encabezados con toque bordó */
            thead tr th { background-color: rgba(128, 0, 32, 0.05) !important; color: #800020; padding: 18px; font-size: 20px; text-align: center !important; }
            thead tr th:first-child { text-align: left !important; padding-left: 20px; }
            
            tbody td { padding: 16px; font-size: 18px; text-align: center; border-bottom: 1px solid #eee; }
            tbody td:first-child { text-align: left !important; font-weight: bold; padding-left: 20px; width: 30%; }
            
            /* Cajones de Coberturas */
            .caja-azul { 
                background-color: #ffffff; 
                padding: 20px; border-radius: 12px; height: 100%; 
                border: 1px solid #e0e0e0; 
                border-top: 5px solid #800020; /* Detalle superior en bordó */
                box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
            }
            .sub-tit { font-size: 22px !important; font-weight: bold; color: #2C2C2C; margin-bottom: 10px; display: block; }
            
            /* Costos resaltados en Gris Oscuro */
            .costo-res { color: #2C2C2C; font-weight: bold; display: block; margin-top: 10px; font-size: 19px; background: #f4f4f4; padding: 5px 10px; border-radius: 5px; }
            
            .ben-fila { 
                background-color: #f8f9fa; padding: 12px 20px; border-radius: 8px; 
                margin-bottom: 10px; border-left: 6px solid #800020; width: 100%; 
                font-size: 16px; color: #333; 
            }
        </style>
        <div class="titulo-cot">🛡️ EDF SEGUROS - Propuesta</div>
        <div class="linea"></div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.markdown(f"### 👤 Asegurado: {p.get('n', 'N/A')}")
    if "v" in p: c2.markdown(f"### 🚗 Vehículo: {p.get('v', 'N/A')}")

    df_p = pd.DataFrame(p["tab"]).fillna("")
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
        st.download_button(label="📥 EXCEL VENCIMIENTOS", data=output.getvalue(), file_name='vencimientos.xlsx')

# --- PESTAÑA COTIZADOR INDIVIDUAL (CON EDICIÓN V.2) ---
with tab_cot:
    st.subheader("📝 Cotizador Seguros para Vehículos")
    edit = st.session_state.edit_data
    if st.session_state.es_edicion:
        # Solo mostramos el aviso si 'edit' existe y tiene contenido
        if isinstance(edit, dict) and edit:
            nom_cliente_edit = edit.get('n') or edit.get('asegurado', 'Cliente')
            st.warning(f"⚠️ Editando cotización de: {nom_cliente_edit}. Se guardará como V.2")

    with st.container(border=True):
        c_doc, c_nom, c_veh, c_ase, c_con = st.columns([1.5, 2, 2, 1, 2])
        doc_in = c_doc.text_input("CI/RUT", value=edit["doc"] if edit and "doc" in edit else "")
        # Reemplazo de seguridad para que no explote si no hay datos
        nom_sug = edit.get('n') or edit.get('asegurado', '') if edit else ""
        if st.session_state.es_edicion and "V.2" not in nom_sug: nom_sug = f"{nom_sug} V.2"
        n_cot = c_nom.text_input("Nombre", value=nom_sug)
        v_cot = c_veh.text_input("Vehículo", value=edit.get("v", "") if edit else "")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), index=0)
        cont_cot = c_con.text_input("Nombre y Contacto Asesor", value=edit["cont"] if edit else "")

    df_p_init = pd.DataFrame(edit["tab"]) if edit else pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}])
    
    t_edit = st.data_editor(
        df_p_init, 
        num_rows="dynamic", 
        use_container_width=True,
        # ESTA LÍNEA FIJA EL ORDEN DE IZQUIERDA A DERECHA
        column_order=("Aseguradora", "Contado", "10 Cuotas", "Deducible"),
        column_config={
            "Aseguradora": st.column_config.TextColumn("Aseguradora", width="medium"),
            "Contado": st.column_config.NumberColumn("Contado", format="$ %.0f"),
            "10 Cuotas": st.column_config.NumberColumn("10 Cuotas", format="$ %.0f"),
            "Deducible": st.column_config.NumberColumn("Deducible", format="$ %.0f")
        }
    )
    
    col_a, col_b = st.columns(2)
    with col_a:
        t_ben = "• Auxilio mecánico 24hs: Todas las aseguradoras\n• Cristales: BSE/SBI USD 200, SURA USD 100, MAPFRE ilimitado, SANCOR USD 300\n• Granizo: SANCOR sin deducible"
        b_cot = st.text_area("Beneficios:", value=edit["ben"] if edit else t_ben, height=200)
    with col_b:
        t_h = "• Incendio Edificio: USD 100.000\n• Incendio Contenido: USD 50.000\n• Hurto Contenido: USD 5.000\n• Remoción de Escombros: USD 5.000\nCosto Anual Apartamentos: USD 120\nCosto Anual Casas: USD 190"
        c_h = st.text_area("Hogar:", value=edit.get("ch", t_h) if edit else t_h, height=130)
        c_a = st.text_area("Alquiler:", value=edit.get("ca", "• Auto cortesía 15 días...") if edit else "• Auto cortesía 15 días...", height=70)
        c_b = st.text_area("Bici:", value=edit.get("cb", "• Hurto USD 1.000...") if edit else "• Hurto USD 1.000...", height=70)
    datos_i = {"n": n_cot, "v": v_cot, "e": e_cot, "cont": cont_cot, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b, "doc": doc_in}
    l_i = f"https://dfseguros.streamlit.app/?q={base64.b64encode(json.dumps(datos_i).encode()).decode()}"

# --- PESTAÑA FLOTAS ---
with tab_flota:
    st.subheader("📋 Cotizador Seguro de Flotas")
    
    # 1. Cabecera de Datos
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        nom_f = (edit.get('asegurado') or edit.get('n', '')) if (edit and isinstance(edit, dict)) else ""
        f_asegurado = st.text_input("Asegurado", value=nom_f, key="f_nom_v3")
        f_aseguradora = st.selectbox("Aseguradora", ["BSE", "SURA", "MAPFRE", "SANCOR", "SBI", "PORTO", "BERKLEY", "BARBUS"], key="f_cia_v3")
    
    with col_f2:
        f_asesor = st.text_input("Asesor", value=edit.get('asesor', 'EDF SEGUROS') if (edit and isinstance(edit, dict)) else "EDF SEGUROS", key="f_ase_v3")
        cont_f = edit.get('cont') or "099 635 244" if (edit and isinstance(edit, dict)) else "099 635 244"
        f_contacto = st.text_input("Contacto", value=cont_f, key="f_cont_v3")

    st.markdown("---")

    # 2. Definición de Columnas (Crucial para que no de NameError)
    cols_f = ["Marca", "Modelo", "Matrícula", "Cobertura", "Contado", "Deducible"]
    
    # 3. Lógica de la Tabla
    if edit and isinstance(edit, dict) and "tab" in edit:
        df_f_init = pd.DataFrame(edit["tab"])
        for c in cols_f:
            if c not in df_f_init.columns: df_f_init[c] = ""
    else:
        df_f_init = pd.DataFrame([{"Marca": "", "Modelo": "", "Matrícula": "", "Cobertura": "Total Riesgo", "Contado": 0, "Deducible": 0}])

    # 4. El Editor de Tabla
    t_flota = st.data_editor(
        df_f_init[cols_f], 
        num_rows="dynamic",
        use_container_width=True,
        key="editor_final_v10"
    )

    # 5. Observaciones Finales
    st.markdown("### 📝 Detalles de la Propuesta")
    obs_val = edit.get('ben', '') if (edit and isinstance(edit, dict)) else ""
    st.text_area("Observaciones:", value=obs_val, height=150, key="f_obs_v3")

    # 6. BOTÓN DE GUARDAR Y GENERAR
    if st.button("💾 Guardar y Generar Link de Flota", use_container_width=True):
        # Creamos el diccionario con toda la info de la cabecera y la tabla
        nueva_flota = {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "asegurado": f_asegurado,
            "n": f_asegurado, # Para que sea compatible con el historial
            "aseguradora": f_aseguradora,
            "asesor": f_asesor,
            "cont": f_contacto,
            "tab": t_flota.to_dict('records'), # Guarda los vehículos de la tabla
            "ben": obs_val, # Guarda las observaciones
            "tipo": "Flota"
        }
        
        # Lo metemos en el historial
        if "historico" not in st.session_state:
            st.session_state.historico = []
        
        st.session_state.historico.append(nueva_flota)
        
        # Guardamos en 'edit_data' para que la vista previa sepa qué mostrar
        st.session_state.edit_data = nueva_flota
        
        st.success("✅ ¡Flota guardada en el historial!")
        st.rerun() # Refrescamos para que aparezca en el historial al toque

    # 7. BOTÓN DE VISTA PREVIA (Solo aparece si hay algo guardado)
    if st.session_state.get('edit_data') and "tab" in st.session_state.edit_data:
        st.markdown("---")
        # Aquí ponés el link a tu web de cliente (propuesta.streamlit.app o la que uses)
        url_cliente = "https://tu-app-de-propuestas.streamlit.app/" 
        st.link_button("🔗 Ver Vista Previa para el Cliente", url_cliente, use_container_width=True, type="primary")
        
# --- PESTAÑA HISTORIAL ---
with tab_historial:
    st.subheader("📋 Gestión de Historial")
    
    # 1. Botones de acción general
    c_ref, c_del = st.columns([1, 1])
    with c_ref:
        if st.button("🔄 Actualizar Historial", use_container_width=True):
            st.rerun()
    with c_del:
        if st.button("🔥 BORRAR TODO", type="primary", use_container_width=True):
            st.session_state.historico = []
            st.rerun()

    st.divider()

    # 2. Lista con borrado individual
    if "historico" in st.session_state and st.session_state.historico:
        # Mostramos de la más nueva a la más vieja
        for i, registro in enumerate(reversed(st.session_state.historico)):
            idx_real = len(st.session_state.historico) - 1 - i
            
            col_info, col_btn = st.columns([0.85, 0.15])
            
            with col_info:
                f = registro.get('fecha', 'S/F')[:10]
                n = registro.get('n') or registro.get('asegurado', 'Cliente')
                t = "🚚 Flota" if "tab" in registro else "🚗 Indiv."
                st.write(f"**{f}** | {t} | **{n}**")
            
            with col_btn:
                # El botón de borrar individual
                if st.button("❌", key=f"btn_del_{idx_real}"):
                    st.session_state.historico.pop(idx_real)
                    st.rerun()
            st.divider()
    else:
        st.info("No hay registros en el historial.")

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
