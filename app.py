import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64
import urllib.request
import urllib.parse

# ==========================================
# ⚙️ CONFIGURACIÓN Y ESTILOS
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5 

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

def fmt_curr(val):
    try: return f"$ {int(float(val)):,}".replace(",", ".")
    except: return val

st.markdown("""
    <style>
    @media print {
        .stButton, [data-testid="stSidebar"], .stDownloadButton, footer, header { display: none !important; }
        .main .block-container { padding: 0 !important; margin: 0 !important; }
    }
    .titulo-bordo { color: #800020; font-size: 22px; font-weight: bold; border-bottom: 3px solid #800020; padding-bottom: 8px; margin-bottom: 20px; text-transform: uppercase; }
    .quote-card { background-color: #fdfdfd; padding: 20px; border-radius: 10px; border: 1px solid #eee; white-space: pre-wrap; font-family: sans-serif; font-size: 14px; line-height: 1.6; }
    [data-testid="stTable"] td { text-align: right !important; }
    [data-testid="stTable"] td:first-child { text-align: left !important; }
    .stDownloadButton button { background-color: #1D6F42 !important; color: white !important; border-radius: 8px !important; width: auto !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🕵️ LÓGICA DE VISTA DE CLIENTE
# ==========================================
query_params = st.query_params
if "q" in query_params or "f" in query_params:
    p_tipo = "f" if "f" in query_params else "q"
    try:
        data_raw = base64.b64decode(query_params[p_tipo]).decode()
        q_data = json.loads(data_raw)
        st.markdown(f"<div class='titulo-bordo'>🛡️ EDF SEGUROS - {'PROPUESTA FLOTA' if p_tipo=='f' else 'COTIZACIÓN VEHÍCULO'}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Asegurado:** {q_data['n']}")
            if p_tipo == "q": 
                st.markdown(f"**Vehículo:** {q_data.get('v', 'S/D')}")
                if q_data.get('cob'): st.markdown(f"**Cobertura:** {q_data['cob']}")
        with c2:
            st.markdown(f"**Fecha:** {date.today().strftime('%d/%m/%Y')}")
            st.markdown(f"**Asesor:** {q_data['e']}")
        
        df_view = pd.DataFrame(q_data['tab'])
        for col in df_view.columns:
            if any(p in col.lower() for p in ["precio", "contado", "cuotas", "deducible"]):
                df_view[col] = df_view[col].apply(fmt_curr)
        st.table(df_view) 
        
        st.write("### ✅ Beneficios Incluidos")
        st.markdown(f"<div class='quote-card'>{q_data['ben']}</div>", unsafe_allow_html=True)
        
        if p_tipo == "q" and q_data.get('ch'):
            st.write("### 🏠 Coberturas Complementarias")
            col_comp = st.columns(3)
            with col_comp[0]: st.info("**Hogar**"); st.caption(q_data['ch'])
            with col_comp[1]: st.info("**Alquiler**"); st.caption(q_data['ca'])
            with col_comp[2]: st.info("**Bici**"); st.caption(q_data['cb'])

        st.markdown("---")
        if st.button("🖨️ Imprimir / Guardar PDF", use_container_width=True):
            st.components.v1.html("<script>window.parent.print();</script>", height=0)
        st.stop() 
    except:
        st.error("Error al cargar la cotización."); st.stop()

# ==========================================
# 🔐 SEGURIDAD
# ==========================================
USUARIOS = {
    "RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", 
    "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025",
    "GS": "GSanchez2025", "MDF": "Matiti2025", "EH": "EHugo2025",
    "AP": "APerdomo2025", "RS": "RSierra2025", "LT": "LTomasi2025",
    "EC": "ECabral2025", "PG": "PGagliardi2025"
}

if 'logueado' not in st.session_state: st.session_state['logueado'] = False
if not st.session_state['logueado']:
    st.markdown("<h1 style='text-align: center;'>🛡️ EDF SEGUROS</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state['logueado'] = True; st.session_state['usuario_actual'] = u; st.rerun()
                else: st.error("❌ Credenciales incorrectas")
    st.stop()
    conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        df = conn.read(spreadsheet=URL_HOJA, ttl=0)
        df.columns = df.columns.str.strip()
        df = df.dropna(how='all') 
        df['Premio_Total_USD'] = (pd.to_numeric(df.get('Premio USD (IVA inc)', 0), errors='coerce').fillna(0) + (pd.to_numeric(df.get('Premio UYU (IVA inc)', 0), errors='coerce').fillna(0) / TC_USD)).round(0)
        df['Fin de Vigencia'] = pd.to_datetime(df['Fin de Vigencia'], dayfirst=True, errors='coerce').dt.date
        return df
    except: return pd.DataFrame()

df_raw = cargar_datos()

conf_cols = {}
if "Adjunto (póliza)" in df_raw.columns:
    conf_cols["Adjunto (póliza)"] = st.column_config.LinkColumn("Póliza", display_text="📂")
if "Premio_Total_USD" in df_raw.columns:
    conf_cols["Premio_Total_USD"] = st.column_config.NumberColumn("Total USD", format="U$S %d")

with st.sidebar:
    st.title(f"👤 {st.session_state['usuario_actual']}")
    st.divider()
    def get_list(col): return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
    f_ej = st.selectbox("Ejecutivo", get_list('Ejecutivo'))
    f_as = st.selectbox("Aseguradora", get_list('Aseguradora'))
    f_ra = st.selectbox("Ramo", get_list('Ramo'))
    f_co = st.selectbox("Corredor", get_list('Corredor')) # Restaurado
    f_ag = st.selectbox("Agente", get_list('Agente'))     # Restaurado
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['logueado'] = False; st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos": df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f['Aseguradora'] == f_as]
if f_ra != "Todos": df_f = df_f[df_f['Ramo'] == f_ra]
if f_co != "Todos": df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos": df_f = df_f[df_f['Agente'] == f_ag]

tab1, tab2, tab3, tab_flota, tab4 = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 COTIZADOR", "🚛 FLOTAS", "📊 ANÁLISIS"])

with tab1:
    busq = st.text_input("🔍 Buscar cliente o matrícula...")
    df_c = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f
    st.write(f"Mostrando {len(df_c)} registros")
    st.dataframe(df_c, use_container_width=True, hide_index=True, column_config=conf_cols)

with tab2:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty and "Fin de Vigencia" in df_f.columns:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Desde:", date.today().replace(day=1))
        f_fin = c_f2.date_input("Hasta:", date.today() + timedelta(days=90))
        df_venc_final = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')
        st.dataframe(df_venc_final, use_container_width=True, hide_index=True, column_config=conf_cols)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_venc_final.to_excel(writer, index=False)
        st.download_button(label="📥 EXCEL", data=output.getvalue(), file_name='vencimientos.xlsx')

with tab3:
    st.subheader("📝 Generador Individual")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        n_cot = c1.text_input("Asegurado")
        v_cot = c2.text_input("Vehículo")
        cob_cot = c2.text_input("Cobertura", value="TODO RIESGO")
        e_cot = c3.selectbox("Asesor", sorted(list(USUARIOS.keys())), index=0)
    
    t_edit = st.data_editor(pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}]), num_rows="dynamic", use_container_width=True)
    
    st.write("### ✅ Detalles de Cobertura")
    col_a, col_b = st.columns(2)
    with col_a:
        txt_ben = "• Auxilio mecánico 24hs:\nTodas las aseguradoras\n\n• Ayuda económica para cristales:\nSBI: USD 200\nBSE: USD 200\nSURA: USD 100\nSANCOR: USD 300\nMAPFRE: Ilimitado\n\n• Ayuda económica para granizo:\nPORTO: Sin deducible"
        b_cot = st.text_area("Beneficios Incluidos:", value=txt_ben, height=300)
    with col_b:
        # Textos actualizados con negritas y nuevos valores
        txt_h = "• Incendio Edificio: USD 100.000\n• Incendio Contenido: USD 50.000\n• Hurto Contenido: USD 5.000\n• Remoción de Escombros: USD 5.000\n**Costo Anual para Apartamentos: USD 120**\n**Costo Anual para Casas: USD 190**\n**Costo Anual para Casas de construcción alternativas: USD 175**"
        txt_a = "• Auto cortesía 15 días en caso de que tu vehículo tenga un siniestro y vaya a un taller\n**Costo Anual: UYU 3.500**"
        txt_b = "• Hurto hasta USD 1.000\n• Responsabilidad Civil (daños a terceros): USD 10.000\n**Costo Anual: USD 110**"
        c_h = st.text_area("Hogar:", value=txt_h, height=180)
        c_a = st.text_area("Alquiler:", value=txt_a, height=100)
        c_b = st.text_area("Bici:", value=txt_b, height=100)
    
    if st.button("Generar Link Individual"):
        datos = {"n": n_cot, "v": v_cot, "cob": cob_cot, "e": e_cot, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b}
        b64 = base64.b64encode(json.dumps(datos).encode()).decode()
        st.code(f"https://dfseguros.streamlit.app/?q={b64}", language=None)

with tab_flota:
    st.subheader("🚛 Cotizador de Flotas")
    with st.container(border=True):
        c1, fc2, c3 = st.columns(3)
        f_nom = c1.text_input("Asegurado Flota")
        f_as1 = fc2.text_input("Aseguradora 1", value="SURA")
        f_as2 = fc2.text_input("Aseguradora 2", value="BSE")
        f_ase = c3.selectbox("Asesor Flota", sorted(list(USUARIOS.keys())), key="ase_flota")
    df_flota_init = pd.DataFrame([{"Vehículo": "Unidad 1", "Cobertura": "Todo Riesgo", f"Precio {f_as1}": 0, f"Ded. {f_as1}": 0, f"Precio {f_as2}": 0, f"Ded. {f_as2}": 0}])
    t_flota = st.data_editor(df_flota_init, num_rows="dynamic", use_container_width=True)
    f_ben = st.text_area("Beneficios Flota:", value=txt_ben, height=200, key="ben_flota")
    if st.button("Generar Link Flota"):
        datos_f = {"n": f_nom, "e": f_ase, "tab": t_flota.to_dict(orient='records'), "ben": f_ben}
        b64_f = base64.b64encode(json.dumps(datos_f).encode()).decode()
        st.code(f"https://dfseguros.streamlit.app/?f={b64_f}", language=None)

with tab4:
    if not df_f.empty:
        c_g1, c_g2 = st.columns(2)
        with c_g1: st.plotly_chart(px.pie(df_f, names='Aseguradora', values='Premio_Total_USD', title="Cartera por Cía", hole=0.4), use_container_width=True)
        with c_g2:
            if 'Ramo' in df_f.columns:
                r_counts = df_f['Ramo'].value_counts().reset_index()
                r_counts.columns = ['Ramo', 'Cantidad']
                st.plotly_chart(px.bar(r_counts, x='Ramo', y='Cantidad', title="Pólizas por Ramo", color='Ramo'), use_container_width=True)
