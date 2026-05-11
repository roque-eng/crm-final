import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64
import requests

# 1. Definició Global d'Usuaris
USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "GS": "GSanchez2025", "MDF": "Matiti2025", "EH": "EHugo2025", "AP": "APerdomo2025", "RS": "RSierra2025", "LT": "LTomasi2025", "EC": "ECabral2025", "PG": "PGagliardi2025"}

if 'usuario_actual' not in st.session_state:
    st.session_state['usuario_actual'] = "Invitado"

# Configuració de la Fulla i TC
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

# Estils CSS (Recuperats exactament del 8 de maig)
st.markdown("""
    <style>
    @media print { .stButton, [data-testid="stSidebar"], .stDownloadButton, footer, header { display: none !important; } }
    .titulo-bordo { color: #800020; font-size: 22px; font-weight: bold; border-bottom: 3px solid #800020; padding-bottom: 8px; margin-bottom: 20px; text-transform: uppercase; }
    .ben-fila { background-color: #f8f9fa; padding: 12px 20px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #800020; width: 100%; font-size: 16px; color: #333; }
    .caja-azul { background-color: #ffffff; padding: 20px; border-radius: 12px; height: 100%; border: 1px solid #e0e0e0; border-top: 5px solid #800020; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .costo-res { color: #2C2C2C; font-weight: bold; display: block; margin-top: 10px; font-size: 19px; background: #f4f4f4; padding: 5px 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- LÒGICA DE LA VISTA DEL CLIENT (Quan obren el link) ---
p = None
query_params = st.query_params
if "q" in query_params or "f" in query_params:
    try:
        val = query_params.get("q") or query_params.get("f")
        p = json.loads(base64.b64decode(val).decode())
    except:
        st.error("Error al carregar la proposta. El link pot estar incomplet.")

if p:
    st.markdown('<div style="color: #2C2C2C; font-size: 42px; font-weight: 800;">🛡️ EDF SEGUROS - Propuesta</div>', unsafe_allow_html=True)
    st.markdown('<div style="border-bottom: 4px solid #800020; margin-bottom: 30px;"></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.markdown(f"### 👤 Asegurado: {p.get('n', 'N/A')}")
    if "v" in p: 
        c2.markdown(f"### 🚗 Vehículo: {p.get('v', 'N/A')}")

    # Taula de preus per al client
    df_p = pd.DataFrame(p["tab"]).fillna("")
    # Formateig de moneda
    for col in ["Contado", "10 Cuotas", "Deducible"]:
        if col in df_p.columns:
            df_p[col] = pd.to_numeric(df_p[col], errors='coerce').fillna(0).apply(lambda x: f"$ {int(x):,}".replace(",", "."))
    
    st.write(df_p.to_html(index=False, escape=False), unsafe_allow_html=True)
    
    # Beneficis en la vista del client
    if p.get("ben"):
        st.markdown("### ✅ Beneficios Incluidos")
        for b in p["ben"].split('\n'):
            if b.strip():
                st.markdown(f'<div class="ben-fila">{b.strip()}</div>', unsafe_allow_html=True)

    # Cobertures complementàries en la vista del client
    if any(k in p for k in ["ch", "ca", "cb"]):
        st.markdown("### ⚠️ Coberturas Complementarias")
        col1, col2, col3 = st.columns(3)
        def bloque_res(tit, ico, txt):
            if not txt: return ""
            res = f'<div class="caja-azul"><b>{ico} {tit}</b><br>'
            for l in txt.split('\n'):
                if "$" in l or "Costo" in l: res += f'<span class="costo-res">💰 {l.strip()}</span>'
                else: res += f'<span>{l.strip()}</span><br>'
            return res + '</div>'
        
        if p.get("ch"): col1.markdown(bloque_res("Hogar", "🏠", p.get("ch")), unsafe_allow_html=True)
        if p.get("ca"): col2.markdown(bloque_res("Alquiler", "🚗", p.get("ca")), unsafe_allow_html=True)
        if p.get("cb"): col3.markdown(bloque_res("Bici", "🚲", p.get("cb")), unsafe_allow_html=True)
    st.stop() # Atura aquí si és vista de client
# --- CÀRREGA DE DADES GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_raw = conn.read(spreadsheet=URL_HOJA, ttl=0)
    # Neteja de columnes
    df_raw.columns = df_raw.columns.str.strip()
    
    # Càlcul de carteres (Mateixa lògica que el 8 de maig)
    df_raw['Premio_Total_USD'] = (
        pd.to_numeric(df_raw.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0) + 
        (pd.to_numeric(df_raw.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0) / TC_USD)
    ).round(0)
    
    # Format de dates
    df_raw['Fin de Vigencia'] = pd.to_datetime(df_raw['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    df_raw = pd.DataFrame(columns=['Ejecutivo', 'Aseguradora', 'Asegurado', 'Fin de Vigencia', 'Premio_Total_USD'])

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://images.squarespace-cdn.com/content/v1/5f06169c97b819266133d97d/1594247547565-9W9W9W9W9W9W9W9W9W9W/logo.png", width=200) # Opcional: El teu logo
    st.title("🛡️ EDF SEGUROS")
    
    nombre_asesor = USUARIOS.get(st.session_state.get('usuario_actual', 'RDF'), "Asesor")
    st.write(f"Sessió de: **{nombre_asesor}**")
    
    st.markdown("---")
    st.subheader("Filtres de Cartera")
    
    lista_ej = ["Todos"] + sorted(df_raw['Ejecutivo'].dropna().unique().tolist())
    f_ej = st.selectbox("Seleccionar Ejecutivo", lista_ej)
    
    lista_as = ["Todos"] + sorted(df_raw['Aseguradora'].dropna().unique().tolist())
    f_as = st.selectbox("Seleccionar Aseguradora", lista_as)
    
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

# Aplicar Filtres
df_f = df_raw.copy()
if f_ej != "Todos":
    df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos":
    df_f = df_f[df_f['Aseguradora'] == f_as]

# --- DEFINICIÓ DE PESTANYES ---
# Aquí posem exactament els noms que hem fet servir per no trencar el "with"
tab_car, tab_ven, tab_cot, tab_flota, tab_historial, tab_an = st.tabs([
    "👥 CARTERA", 
    "🔄 VENCIMIENTOS", 
    "📝 COTIZADOR", 
    "🚛 FLOTAS", 
    "📜 HISTORIAL", 
    "📊 ANÁLISIS"
])

# --- CONTINGUT PESTANYA CARTERA ---
with tab_car:
    st.subheader("👥 Cartera Total de Clients")
    busq = st.text_input("🔍 Buscar per nom o matrícula...")
    
    if busq:
        df_mostrar = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)]
    else:
        df_mostrar = df_f
        
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

# --- CONTINGUT PESTANYA VENCIMIENTOS ---
with tab_ven:
    st.subheader("🔄 Control de Propers Venciments")
    c1, c2 = st.columns(2)
    f_ini = c1.date_input("Inici del període", date.today().replace(day=1))
    f_fin = c2.date_input("Fi del període", date.today() + timedelta(days=90))
    
    df_venc = df_f[(df_f['Fin de Vigencia'] >= f_ini) & (df_f['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')
    st.dataframe(df_venc, use_container_width=True, hide_index=True)
    # --- CONTENIDO PESTAÑA COTIZADOR INDIVIDUAL ---
with tab_cot:
    st.subheader("📝 Cotizador de Seguros Individuales")
    
    # Verificamos si hay datos cargados desde el historial para editar
    edit = st.session_state.get('edit_data') if st.session_state.get('edit_data') and "v" in st.session_state.get('edit_data') else {}
    
    # 1. Cabecera de Datos del Cliente
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
        doc_in = c1.text_input("CI/RUT", value=edit.get("doc", ""), key="ind_doc")
        n_cot = c2.text_input("Nombre Asegurado", value=edit.get("n", ""), key="ind_nom")
        v_cot = c3.text_input("Vehículo (Marca/Modelo/Año)", value=edit.get("v", ""), key="ind_veh")
        cont_cot = c4.text_input("Contacto Asesor", value=edit.get("cont", "099 635 244"), key="ind_cont")

    st.markdown("---")
    
    # 2. TABLA DE COTIZACIÓN (4 columnas: Aseguradora, Contado, 10 Cuotas, Deducible)
    cols_i = ["Aseguradora", "Contado", "10 Cuotas", "Deducible"]
    
    # Si estamos editando, cargamos la tabla vieja. Si no, una nueva con las filas sugeridas.
    if edit and "tab" in edit:
        df_p_init = pd.DataFrame(edit["tab"])
    else:
        df_p_init = pd.DataFrame([
            {"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0},
            {"Aseguradora": "SURA", "Contado": 0, "10 Cuotas": 0, "Deducible": 0},
            {"Aseguradora": "MAPFRE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0},
            {"Aseguradora": "SANCOR", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}
        ])
    
    # Editor de la tabla
    t_edit = st.data_editor(df_p_init[cols_i], num_rows="dynamic", use_container_width=True, key="editor_individual_vfinal")
    
    st.markdown("---")
    
    # 3. TEXTOS PRECARGADOS (Rescatados del 8 de mayo)
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Beneficios precargados originales
        txt_ben_def = (
            "• Auxilio mecánico 24hs: BSE (Ilimitado), SURA (Ilimitado), MAPFRE (Ilimitado)\n"
            "• Cristales, Cerraduras y Parabrisas: Sin Deducible en todas las compañías\n"
            "• Responsabilidad Civil: USD 500.000\n"
            "• Asistencia en Viaje: Cobertura total en Mercosur y Chile"
        )
        b_cot = st.text_area("✅ Beneficios Incluidos:", value=edit.get("ben", txt_ben_def), height=250, key="ind_ben")
    
    with col_b:
        # Coberturas complementarias originales
        txt_hog_def = "• Incendio Edificio: USD 100.000\n• Incendio Contenido: USD 50.000\n• Hurto Contenido: USD 5.000\nCosto Anual: USD 150"
        txt_alq_def = "• Auto de cortesía por 15 días en caso de siniestro.\nCosto: USD 45 por vigencia."
        txt_bic_def = "• Hurto de bicicleta: USD 1.000\n• Responsabilidad Civil: USD 5.000\nCosto: USD 60 anual."
        
        c_h = st.text_area("🏠 Seguro de Hogar:", value=edit.get("ch", txt_hog_def), height=100, key="ind_ch")
        c_a = st.text_area("🚗 Auto Alquiler:", value=edit.get("ca", txt_alq_def), height=80, key="ind_ca")
        c_b = st.text_area("🚲 Seguro de Bici:", value=edit.get("cb", txt_bic_def), height=80, key="ind_cb")

    # Botón para Guardar Individual (La lógica de guardado viene en el siguiente bloque para no saturar)
    st.info("Configurá los datos y dale a Guardar en el siguiente paso.")
    # 4. BOTÓN GUARDAR Y GENERAR (Pestaña Individual)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Guardar Cotización y Generar Link", use_container_width=True):
        # Armamos el paquete de datos con todo lo que escribiste arriba
        datos_individual = {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "n": n_cot,       # Nombre
            "v": v_cot,       # Vehículo
            "doc": doc_in,     # Documento
            "cont": cont_cot,  # Contacto Asesor
            "tab": t_edit.to_dict(orient='records'), # La tabla de 4 columnas
            "ben": b_cot,      # Beneficios (texto precargado)
            "ch": c_h,         # Hogar
            "ca": c_a,         # Alquiler
            "cb": c_b,         # Bici
            "tipo": "Individual"
        }
        
        # Lo metemos en la base de datos temporal (Historial)
        if "historico" not in st.session_state:
            st.session_state.historico = []
        
        st.session_state.historico.append(datos_individual)
        
        # Seteamos 'edit_data' para que el botón de abajo sepa qué link crear
        st.session_state.edit_data = datos_individual
        
        st.success(f"✅ ¡Cotización de {n_cot} guardada con éxito!")
        st.rerun()

    # 5. BOTÓN DE VISTA PREVIA (Solo aparece si acabás de guardar o editar)
    # Verificamos que haya un vehículo 'v' para saber que es una cotización individual
    if st.session_state.get('edit_data') and "v" in st.session_state.edit_data:
        st.markdown("---")
        st.markdown("### 🔗 Link para el Cliente")
        
        # Encriptamos los datos para el link
        datos_json = json.dumps(st.session_state.edit_data)
        datos_b64 = base64.b64encode(datos_json.encode()).decode()
        
        # CAMBIÁ ESTA URL por la dirección real de tu App de Streamlit
        url_base = "https://dfseguros.streamlit.app/" 
        link_final = f"{url_base}?q={datos_b64}"
        
        st.info("Copiá el link de abajo o hacé clic para ver cómo lo verá el cliente:")
        st.link_button("🚀 VER VISTA PREVIA INDIVIDUAL", link_final, type="primary", use_container_width=True)
        st.code(link_final) # Te deja el link a mano para copiar y pegar

# --- AQUÍ TERMINA EL CONTENIDO DE LA PESTAÑA INDIVIDUAL ---
# 4. BOTÓN GUARDAR Y GENERAR (Pestaña Individual)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Guardar Cotización y Generar Link", use_container_width=True):
        # Armamos el paquete de datos con todo lo que escribiste arriba
        datos_individual = {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "n": n_cot,       # Nombre
            "v": v_cot,       # Vehículo
            "doc": doc_in,     # Documento
            "cont": cont_cot,  # Contacto Asesor
            "tab": t_edit.to_dict(orient='records'), # La tabla de 4 columnas
            "ben": b_cot,      # Beneficios (texto precargado)
            "ch": c_h,         # Hogar
            "ca": c_a,         # Alquiler
            "cb": c_b,         # Bici
            "tipo": "Individual"
        }
        
        # Lo metemos en la base de datos temporal (Historial)
        if "historico" not in st.session_state:
            st.session_state.historico = []
        
        st.session_state.historico.append(datos_individual)
        
        # Seteamos 'edit_data' para que el botón de abajo sepa qué link crear
        st.session_state.edit_data = datos_individual
        
        st.success(f"✅ ¡Cotización de {n_cot} guardada con éxito!")
        st.rerun()

    # 5. BOTÓN DE VISTA PREVIA (Solo aparece si acabás de guardar o editar)
    # Verificamos que haya un vehículo 'v' para saber que es una cotización individual
    if st.session_state.get('edit_data') and "v" in st.session_state.edit_data:
        st.markdown("---")
        st.markdown("### 🔗 Link para el Cliente")
        
        # Encriptamos los datos para el link
        datos_json = json.dumps(st.session_state.edit_data)
        datos_b64 = base64.b64encode(datos_json.encode()).decode()
        
        # CAMBIÁ ESTA URL por la dirección real de tu App de Streamlit
        url_base = "https://dfseguros.streamlit.app/" 
        link_final = f"{url_base}?q={datos_b64}"
        
        st.info("Copiá el link de abajo o hacé clic para ver cómo lo verá el cliente:")
        st.link_button("🚀 VER VISTA PREVIA INDIVIDUAL", link_final, type="primary", use_container_width=True)
        st.code(link_final) # Te deja el link a mano para copiar y pegar

# --- AQUÍ TERMINA EL CONTENIDO DE LA PESTAÑA INDIVIDUAL ---
# --- CONTENIDO PESTAÑA HISTORIAL ---
with tab_historial:
    st.subheader("📜 Historial de Gestión")
    
    # Botón para limpiar todo si es necesario
    if st.button("🔥 BORRAR TODO EL HISTORIAL", type="secondary", use_container_width=True):
        st.session_state.historico = []
        st.rerun()
    
    st.divider()

    # Verificamos si hay registros
    if "historico" in st.session_state and st.session_state.historico:
        # Recorremos al revés para ver lo más nuevo primero
        for i, reg in enumerate(reversed(st.session_state.historico)):
            idx_real = len(st.session_state.historico) - 1 - i
            
            # Formato de fila: Info | Editar | Borrar
            col_info, col_edit, col_del = st.columns([0.7, 0.15, 0.15])
            
            with col_info:
                fecha = reg.get('fecha', 'S/F')[:10]
                nombre = reg.get('n') or reg.get('asegurado', 'Cliente')
                # Detectamos tipo por contenido para poner el emoji correcto
                es_flota = "tab" in reg and any("Marca" in item for item in reg["tab"] if isinstance(item, dict))
                tipo_ico = "🚛 Flota" if es_flota else "🚗 Indiv."
                st.write(f"**{fecha}** | {tipo_ico} | **{nombre}**")
            
            with col_edit:
                # BOTÓN EDITAR: Carga los datos en st.session_state.edit_data
                if st.button("✏️", key=f"btn_ed_{idx_real}", help="Cargar para editar"):
                    st.session_state.edit_data = reg
                    st.success("✅ Cargado. ¡Revisá la pestaña correspondiente!")
                    st.rerun()
            
            with col_del:
                # BOTÓN BORRAR: Elimina solo este registro
                if st.button("❌", key=f"btn_del_{idx_real}", help="Eliminar registro"):
                    st.session_state.historico.pop(idx_real)
                    st.rerun()
            
            st.divider()
    else:
        st.info("El historial está vacío. Guardá una cotización para verla aquí.")

# --- CONTENIDO PESTAÑA ANÁLISIS ---
with tab_an:
    st.subheader("📊 Análisis de Cartera Actual")
    
    if not df_f.empty:
        total_usd = df_f['Premio_Total_USD'].sum()
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Cartera Total Estimada", f"USD {total_usd:,.0f}")
            # Gráfico de Torta por Aseguradora
            fig_pie = px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', 
                             title="Distribución por Aseguradora", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            # Gráfico de Barras por Ejecutivo
            fig_bar = px.bar(df_f.groupby('Ejecutivo')['Premio_Total_USD'].sum().reset_index(), 
                             x='Ejecutivo', y='Premio_Total_USD', 
                             title="Cartera por Ejecutivo", color='Ejecutivo')
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No hay datos cargados para analizar. Verificá la conexión con Google Sheets.")

# --- FIN DEL CÓDIGO ---
