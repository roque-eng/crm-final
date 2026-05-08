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
    st.markdown("""
        <style>
            .main .block-container { max-width: 100% !important; padding-top: 2rem; }
            .titulo-cot { color: #000; font-size: 42px !important; font-weight: 800; margin-bottom: 0px; }
            .linea { border-bottom: 3px solid #000; margin-bottom: 30px; }
            .tabla-container { width: 100%; margin: 25px 0; }
            table { width: 100% !important; border-collapse: collapse; margin: 0 auto; }
            thead tr th { background-color: rgba(0, 102, 204, 0.1) !important; color: #000; padding: 18px; font-size: 20px; text-align: center !important; }
            thead tr th:first-child { text-align: left !important; padding-left: 20px; }
            tbody td { padding: 16px; font-size: 18px; text-align: center; border-bottom: 1px solid #eee; }
            tbody td:first-child { text-align: left !important; font-weight: bold; padding-left: 20px; width: 30%; }
            .caja-azul { background-color: rgba(0, 102, 204, 0.05); padding: 20px; border-radius: 12px; height: 100%; border: 1px solid rgba(0, 102, 204, 0.1); }
            .sub-tit { font-size: 22px !important; font-weight: bold; color: #000; margin-bottom: 10px; display: block; }
            .costo-res { color: #0066cc; font-weight: bold; display: block; margin-top: 10px; font-size: 18px; }
            .ben-fila { background-color: #f8f9fa; padding: 12px 20px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #28a745; width: 100%; font-size: 16px; color: #333; }
        </style>
        <div class="titulo-cot">🛡️ EDF SEGUROS - Propuesta</div>
        <div class="linea"></div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.markdown(f"### 👤 Asegurado: {p.get('n', 'N/A')}")
    if "v" in p: c2.markdown(f"### 🚗 Vehículo: {p.get('v', 'N/A')}")

    # --- TABLA SIN NaN ---
    df_p = pd.DataFrame(p["tab"]).fillna("")
    for col in df_p.columns:
        if col not in ["Aseguradora", "Vehículo"]:
            df_p[col] = df_p[col].apply(lambda x: f"$ {int(float(x)):,}".replace(',', '.') if str(x).replace('.','').replace(',','').isdigit() and x != "" else x)
    
    st.markdown('<div class="tabla-container">', unsafe_allow_html=True)
    st.write(df_p.to_html(index=False, escape=False), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ... (El resto de beneficios y coberturas complementarias que ya tenés) ...
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
tab_car, tab_ven, tab_cot, tab_flota, tab_hist, tab_an = st.tabs([
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
    st.subheader("📝 Cotizador Individual")
    edit = st.session_state.edit_data
    if st.session_state.es_edicion:
        st.warning(f"⚠️ Editando cotización de: {edit['n']}. Se guardará como V.2")
        if st.button("❌ CANCELAR EDICIÓN"):
            st.session_state.edit_data = None
            st.session_state.es_edicion = False
            st.rerun()

    with st.container(border=True):
        c_doc, c_nom, c_veh, c_ase, c_con = st.columns([1.5, 2, 2, 1, 2])
        doc_in = c_doc.text_input("CI/RUT", value=edit["doc"] if edit and "doc" in edit else "")
        nom_sug = edit["n"] if edit else ""
        if st.session_state.es_edicion and "V.2" not in nom_sug: nom_sug = f"{nom_sug} V.2"
        n_cot = c_nom.text_input("Nombre", value=nom_sug)
        v_cot = c_veh.text_input("Vehículo", value=edit.get("v", "") if edit else "")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), index=0)
        cont_cot = c_con.text_input("Nombre y Contacto Asesor", value=edit["cont"] if edit else "")

    df_p_init = pd.DataFrame(edit["tab"]) if edit else pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}])
    t_edit = st.data_editor(df_p_init, num_rows="dynamic", use_container_width=True, column_config={
        "Contado": st.column_config.NumberColumn(format="$ %.0f"),
        "10 Cuotas": st.column_config.NumberColumn(format="$ %.0f"),
        "Deducible": st.column_config.NumberColumn(format="$ %.0f")
    })
    
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
    
if st.button("🚀 GUARDAR Y GENERAR PROPUESTA DE FLOTA", use_container_width=True):
        nombre_cod = base64.b64encode(f_nom.encode()).decode()
        l_f = f"https://dfseguros.streamlit.app/?flota={nombre_cod}"
        
        db_f = {
            "tipo": "flota", 
            "asegurado": f_nom, 
            "vehiculo_o_flota": "Flota", 
            "asesor": f_ase, 
            "datos_json": datos_f, 
            "link_cotizacion": l_f 
        }
        
        if guardar_en_db(db_f):
            st.success("✅ Flota guardada correctamente.")
            st.link_button("👁️ VER VISTA PREVIA FLOTA", l_f, use_container_width=True)
            
# --- PESTAÑA FLOTAS ---
with tab_flota:
    st.subheader("🚛 Cotizador de Flotas Pro")
    with st.container(border=True):
        f1, f2, f3, f4, f5, f6 = st.columns([2, 1.2, 1.2, 1.2, 1, 2])
        f_nom = f1.text_input("Asegurado Flota")
        f_as1 = f2.text_input("Cía 1", value="SURA"); f_as2 = f3.text_input("Cía 2", value="BSE"); f_as3 = f4.text_input("Cía 3", value="SBI")
        f_ase = f5.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="f_ase_sel")
        f_cont = f6.text_input("Contacto", key="f_con_sel")
    
    df_f_init = pd.DataFrame([{"Vehículo": "Unidad 1", f"Precio {f_as1}": 0, f"Ded {f_as1}": 0, f"Precio {f_as2}": 0, f"Ded {f_as2}": 0, f"Precio {f_as3}": 0, f"Ded {f_as3}": 0}])
    t_flota = st.data_editor(df_f_init, num_rows="dynamic", use_container_width=True, column_config={
        f"Precio {f_as1}": st.column_config.NumberColumn(format="$ %.0f"), f"Ded {f_as1}": st.column_config.NumberColumn(format="$ %.0f"),
        f"Precio {f_as2}": st.column_config.NumberColumn(format="$ %.0f"), f"Ded {f_as2}": st.column_config.NumberColumn(format="$ %.0f"),
        f"Precio {f_as3}": st.column_config.NumberColumn(format="$ %.0f"), f"Ded {f_as3}": st.column_config.NumberColumn(format="$ %.0f")
    })
    datos_f = {"n": f_nom, "e": f_ase, "cont": f_cont, "tab": t_flota.to_dict(orient='records'), "ben": "Auxilio mecánico incluido."}
    l_f = f"https://dfseguros.streamlit.app/?f={base64.b64encode(json.dumps(datos_f).encode()).decode()}"
# ... (Dentro de la pestaña de flotas, después de definir datos_f)

# --- PESTAÑA HISTORIAL (CON EDICIÓN) ---
with tab_hist:
    st.subheader("📜 Gestión de Historial")
    c_bus, c_ref, c_del_all = st.columns([3, 1, 2])
    bus_h = c_bus.text_input("🔍 Buscar por cliente...", key="bus_hist")
    if c_ref.button("🔄 ACTUALIZAR"): st.rerun()
    if c_del_all.button("🔥 BORRAR TODO EL HISTORIAL", type="primary"):
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        res = requests.delete(f"{SUPABASE_URL}/rest/v1/cotizaciones?id=not.is.null", headers=headers)
        if res.status_code in [200, 204]: st.success("Vaciado."); st.rerun()

    df_h = leer_historial()
    if not df_h.empty:
        df_h['Fecha'] = pd.to_datetime(df_h['created_at']).dt.strftime('%d/%m/%Y %H:%M')
        if bus_h: df_h = df_h[df_h['asegurado'].str.contains(bus_h, case=False, na=False)]
        for index, row in df_h.iterrows():
            with st.container(border=True):
                h1, h2, h3 = st.columns([4, 1, 1])
                h1.write(f"📅 {row['Fecha']} | 👤 **{row['asegurado']}**")
                h2.link_button("📂 VER", row['link_cotizacion'], use_container_width=True)
                if h3.button("📝 EDITAR", key=f"btn_ed_{row['id']}", use_container_width=True):
                    st.session_state.edit_data = row['datos_json']
                    st.session_state.es_edicion = True
                    st.success("Cargado. Ve a COTIZADOR.")
                    st.rerun()

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
