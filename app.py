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
    st.session_state['usuario_actual'] = "Invitado"

# ==========================================
# ⚙️ CONFIGURACIÓN Y CONEXIONES
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

# Credenciales de Supabase
SUPABASE_URL = "https://flizerdhoxxoekaczihm.supabase.co"
SUPABASE_KEY = "sb_publishable_lkSd6DNhiwifC-qCMkYNdQ_U97XIxog" 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estilos CSS - Solo Vista Cliente en Azul Profesional
st.markdown("""
    <style>
    @media print { .stButton, [data-testid="stSidebar"], .stDownloadButton, footer, header { display: none !important; } }
    
    .tabla-edf { width:100%; border-collapse: collapse; margin-top: 20px; font-family: sans-serif; }
    .tabla-edf th { background-color: #f0f7ff !important; color: #1E3A8A !important; padding: 12px; border: 1px solid #ddd; text-align: center; font-size: 15px; }
    .tabla-edf td { padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 14px; }
    .der { text-align: right !important; font-weight: bold; }

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
    
    .caja-azul { 
        background-color: #ffffff;
        padding: 20px; 
        border-radius: 12px; 
        height: 100%; 
        border: 1px solid #e0e0e0; 
        border-top: 5px solid #1E3A8A !important; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
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
    </style>
    """, unsafe_allow_html=True)

# --- RECEPCIÓN DE DATOS DEL LINK ---
query_params = st.query_params
p = None

if "f_id" in query_params:
    f_id = query_params["f_id"]
    headers_sp = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    url_get = f"{SUPABASE_URL}/rest/v1/cotizaciones?id=eq.{f_id}&select=data"
    try:
        response = requests.get(url_get, headers=headers_sp).json()
        if response: p = response[0]["data"]
    except: pass

if not p:
    if "f" in query_params:
        p = json.loads(base64.b64decode(query_params["f"]).decode())
    elif "q" in query_params:
        p = json.loads(base64.b64decode(query_params["q"]).decode())

# ==========================================
# 🛡️ INTERFAZ DE VISTA DEL CLIENTE (REPARADA)
# ==========================================
if p:
    # --- 1. ENCABEZADO UNIFICADO ---
    d = p.get('data', p) 
    
    # Mapeo de nombres para Individual y Flotas
    cliente_v = d.get('n') or d.get('cliente') or d.get('nombre_cliente') or "Asegurado"
    aseguradora_v = d.get('e') or d.get('aseguradora') or d.get('compania') or "Compañía"
    vehiculo_v = d.get('v') or "Vehículo / Propuesta Comercial"
    fecha_val = d.get('fecha') or p.get('fecha', datetime.now().strftime("%d/%m/%Y"))
    
    col_l, col_i = st.columns([1, 2])
    with col_l:
        st.image("https://rpyiditlookfcrgeterf.supabase.co/storage/v1/object/public/logos/EDF%20Logotipo%20PNG.png", width=180)
    with col_i:
        st.markdown(f"## Asegurado: {cliente_v}")
        st.markdown(f"### 📋 {vehiculo_v} | 🏦 Aseguradora: **{aseguradora_v}**")

    # --- 2. TABLA DE VEHÍCULOS / COBERTURAS ---
    vehiculos = d.get('tab') or d.get('vehiculos') or []
    
    if vehiculos:
        # Detectamos si viene en formato Flota (con clave Marca) o Individual (con clave Aseguradora)
        es_flota_data = any('Marca' in k or 'marca' in k for k in vehiculos[0].keys()) if isinstance(vehiculos, list) and len(vehiculos) > 0 else False
        
        t_html = """
        <table class="tabla-edf" style="width:100%; border-collapse: collapse; margin-top: 20px; font-family: sans-serif;">
            <thead>
                <tr style="background-color: #f0f7ff; color: #1E3A8A;">
        """
        if es_flota_data:
            t_html += """
                    <th style="padding: 12px; border: 1px solid #ddd;">MARCA</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">MODELO</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">AÑO</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">MATRICULA</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">COBERTURA</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">CONTADO</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">DEDUCIBLE</th>
            """
        else:
            t_html += """
                    <th style="padding: 12px; border: 1px solid #ddd;">ASEGURADORA</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">CONTADO</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">10 CUOTAS</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">DEDUCIBLE</th>
            """
            
        t_html += """
                </tr>
            </thead>
            <tbody>
        """
        
        for v in vehiculos:
            def f_num(n):
                try: 
                    # Limpiamos símbolos previos para que la conversión matemática sea limpia y quite el .0
                    n_clean = str(n).replace('$', '').replace('USD', '').replace('.', '').replace(',', '').strip()
                    return f"{int(float(n_clean)):,}".replace(",", ".")
                except: 
                    return str(n)

            if es_flota_data:
                marca = v.get('Marca') or v.get('marca') or ""
                modelo = v.get('Modelo') or v.get('modelo') or ""
                anio = v.get('Año') or v.get('anio') or ""
                mat = v.get('Matrícula') or v.get('matricula') or "-"
                cob = v.get('Cobertura') or v.get('cobertura') or ""
                contado = f"USD {f_num(v.get('Contado') or v.get('cuota') or v.get('precio') or 0)}"
                deduc = f_num(v.get('Deducible') or v.get('deducible') or 0)
                
                t_html += f"""
                    <tr style="text-align: center; border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; border: 1px solid #ddd;">{marca}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{modelo}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{anio}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{mat}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cob}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #1E3A8A;">{contado}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{deduc}</td>
                    </tr>
                """
            else:
                aseg = v.get('Aseguradora') or v.get('aseguradora') or ""
                cont = f"USD {f_num(v.get('Contado') or v.get('cuota') or 0)}"
                cuot = f"USD {f_num(v.get('10 Cuotas') or v.get('cuota_10') or 0)}"
                dedu = f_num(v.get('Deducible') or v.get('deducible') or 0)
                
                t_html += f"""
                    <tr style="text-align: center; border-bottom: 1px solid #eee;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><b>{aseg}</b></td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold; color: #1E3A8A;">{cont}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{cuot}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{dedu}</td>
                    </tr>
                """
                
        t_html += "</tbody></table>"
        st.markdown(t_html, unsafe_allow_html=True)
    else:
        st.error("⚠️ No se encontraron registros de cobertura en esta propuesta.")

    # --- 3. SECCIÓN DE BENEFICIOS Y COBERTURAS ADICIONALES ---
    if d.get("ben"):
        st.write("")
        st.markdown("### ✅ Beneficios Incluidos")
        for b in d.get("ben", "").split('\n'):
            if b.strip():
                st.markdown(f'<div class="ben-fila">{b.strip()}</div>', unsafe_allow_html=True)

    if d.get("ch") or d.get("ca") or d.get("cb"):
        st.write("")
        st.markdown("### ⚠️ Coberturas Complementarias")
        col1, col2, col3 = st.columns(3)

        def bloque_html(titulo, icono, texto):
            if not texto: return ""
            html_out = f'<div class="caja-azul"><span class="sub-tit" style="font-weight:bold; color:#1E3A8A;">{icono} {titulo}</span><br>'
            lineas = texto.split('\n')
            for linea in lineas:
                linea = linea.strip()
                if not linea: continue
                if "$" in linea or "Costo" in linea:
                    l_limpia = linea.replace("•", "").strip()
                    html_out += f'<span class="costo-res">💰 {l_limpia}</span>'
                else:
                    html_out += f'<span style="display:block; margin-top:3px;">{linea}</span>'
            html_out += '</div>'
            return html_out

        col1.markdown(bloque_html("Hogar", "🏠", d.get("ch", "")), unsafe_allow_html=True)
        col2.markdown(bloque_html("Alquiler", "🚗", d.get("ca", "")), unsafe_allow_html=True)
        col3.markdown(bloque_html("Bici", "🚲", d.get("cb", "")), unsafe_allow_html=True)

    # --- 4. PIE DE PÁGINA Y CORTE ---
    st.markdown("---")
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; color: gray; font-size: 13px;">
            <div><b>EDF SEGUROS</b> | Contacto: {contacto_v}</div>
            <div><b>Fecha de Cotización:</b> {fecha_val}</div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(spreadsheet=URL_HOJA, ttl=0)
df_raw.columns = df_raw.columns.str.strip()
df_raw['Premio_Total_USD'] = (pd.to_numeric(df_raw.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0) + (pd.to_numeric(df_raw.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0) / TC_USD)).round(0)
df_raw['Fin de Vigencia'] = pd.to_datetime(df_raw['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date

with st.sidebar:
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

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]

# Pestañas del CRM sin la pestaña "Flotas" conflictiva
tab_car, tab_ven, tab_cot, tab_historial, tab_an = st.tabs([
    "👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR INDIVIDUAL", "📜 HISTORIAL", "📊 ANÁLISIS"
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

# --- PESTAÑA COTIZADOR INDIVIDUAL ---
with tab_cot:
    st.subheader("📝 Cotizador Seguros para Vehículos")
    edit_ind = st.session_state.edit_data if st.session_state.edit_data else {}
    
    with st.container(border=True):
        c_doc, c_nom, c_veh, c_ase, c_con = st.columns([1.5, 2, 2, 1, 2])
        doc_in = c_doc.text_input("CI/RUT", value=edit_ind.get("doc", ""), key="ci_v_final")
        n_cot = c_nom.text_input("Nombre", value=edit_ind.get('n', ''), key="nom_v_final")
        v_cot = c_veh.text_input("Vehículo", value=edit_ind.get("v", ""), key="veh_v_final")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="ase_v_final")
        cont_cot = c_con.text_input("Contacto Asesor", value=edit_ind.get("cont", "099 635 244"), key="cont_v_final")

    st.markdown("---")
    st.markdown("#### Seleccione las opciones de cobertura:")
    cols_individual = ["Aseguradora", "Contado", "10 Cuotas", "Deducible"]
    
    if edit_ind and "tab" in edit_ind:
        df_p_init = pd.DataFrame(edit_ind["tab"])
    else:
        df_p_init = pd.DataFrame([
            {"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0},
            {"Aseguradora": "SURA", "Contado": 0, "10 Cuotas": 0, "Deducible": 0},
            {"Aseguradora": "MAPFRE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0},
            {"Aseguradora": "SANCOR", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}
        ])
    
    t_edit = st.data_editor(df_p_init, num_rows="dynamic", use_container_width=True, column_order=cols_individual, key="editor_individual_completo")
    
    col_a, col_b = st.columns(2)
    with col_a:
        t_ben_def = "• Auxilio mecánico 24hs: Todas las aseguradoras\n• Cristales: BSE/SBI USD 200, SURA USD 100, MAPFRE ilimitado, SANCOR USD 300\n• Granizo: SANCOR sin deducible"
        b_cot = st.text_area("Beneficios:", value=edit_ind.get("ben", t_ben_def), height=200, key="ben_v_final")
    with col_b:
        t_h_def = "• Incendio Edificio: USD 100.000\n• Incendio Contenido: USD 50.000\n• Hurto Contenido: USD 5.000\nCosto Anual Apartamentos: USD 120\nCosto Anual Casas: USD 190"
        c_h = st.text_area("Hogar:", value=edit_ind.get("ch", t_h_def), height=130, key="hog_v_final")
        c_a = st.text_area("Alquiler:", value=edit_ind.get("ca", "• Auto cortesía 15 días en caso de que tu vehículo vaya al taller por un siniestro\nCosto Anual: $3.500"), height=70, key="alq_v_final")
        c_b = st.text_area("Bici Eléctrica:", value=edit_ind.get("cb", "• Hurto USD 1.000\n• Accidentes Personales: USD 5.000\n• Daños a terceros: USD 10.000\nCosto Anual: USD 120"), height=70, key="bic_v_final")

    if st.button("💾 Guardar en Historial y Generar Link", type="primary", use_container_width=True):
        datos_i = {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "n": n_cot, "v": v_cot, "e": e_cot, "cont": cont_cot, "doc": doc_in,
            "tab": t_edit.to_dict(orient='records'),
            "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b
        }
        st.session_state.historico.append(datos_i) 
        st.session_state.edit_data = datos_i
        
        # Generación de URL codificada
        datos_b64 = base64.b64encode(json.dumps(datos_i).encode()).decode()
        link_final = f"https://dfseguros.streamlit.app/?q={datos_b64}"
        
        st.success(f"✅ Cotización de {n_cot} guardada con éxito.")
        st.text_input("🔗 Copiá este Link Seguro para enviar al cliente:", value=link_final)
        st.rerun()

# --- PESTAÑA HISTORIAL ---
with tab_historial:
    st.subheader("📜 Historial de Cotizaciones")
    if "historico" in st.session_state and st.session_state.historico:
        for i, reg in enumerate(reversed(st.session_state.historico)):
            idx_real = len(st.session_state.historico) - 1 - i
            col_info, col_edit, col_del = st.columns([0.7, 0.15, 0.15])
            
            with col_info:
                fecha = reg.get('fecha', 'S/F')[:10]
                nombre = reg.get('n', 'Cliente')
                vehiculo = reg.get('v', 'Vehículo')
                st.write(f"📅 **{fecha}** | 🚗 Individual | **{nombre}** ({vehiculo})")
            
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
        with c1: 
            st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Compañía", hole=0.4), use_container_width=True)
        with c2: 
            st.plotly_chart(px.pie(df_f, names='Ramo', values='Premio_Total_USD', title="Ramo", hole=0.4), use_container_width=True)
