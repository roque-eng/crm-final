import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64
import gspread
from google.oauth2.service_account import Credentials

URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
SHEET_ID = "1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA"
TC_USD = 40.5

def f_num(val):
    try: return f"{int(float(str(val).replace('$','').replace('USD','').replace('.','').replace(',','').strip())):,}".replace(",",".")
    except: return str(val)

def get_gspread_client():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        service_account_info = json.loads(st.secrets["connections"]["gsheets"]["service_account"])
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        return gspread.authorize(creds)
    except:
        return None

def guardar_en_sheet(hoja_nombre, fila):
    try:
        gc = get_gspread_client()
        if gc is None:
            return False
        sh = gc.open_by_key(SHEET_ID)
        ws = sh.worksheet(hoja_nombre)
        ws.append_row(fila, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.warning(f"No se pudo guardar en el Sheet: {e}")
        return False

CONTACTOS = {
    "RDF": "099236116", "JOE": "099595185", "ANDRE": "098592816",
    "AB": "098358393", "GR": "091339642", "ER": "094430277",
    "GS": "094536444", "MDF": "095074767", "EH": "099513224",
    "AP": "099661587", "RS": "092188815", "LT": "099816395",
    "EC": "099654708", "PG": "091282011"
}

NOMBRES = {
    "RDF": "Roque de Freitas", "JOE": "Joel Mokosce", "ANDRE": "Andrea Cazarian",
    "AB": "Amelia Bentancor", "GR": "Gonzalo Robaina", "ER": "Eduardo Robaina",
    "GS": "Grismer Sanchez", "MDF": "Matias de Freitas", "EH": "Erica Hugo",
    "AP": "Ana Perdomo", "RS": "Romina Sierra", "LT": "Letizia Tomasi",
    "EC": "Eugenia Cabral", "PG": "Pablo Gagliardi"
}

TASAS_AERONAVE = {
    "Privado / Otro": {
        "principales": [
            {"Cobertura": "Perdida o Dano de la Aeronave", "Tasa (%)": 1.50, "Capital (USD)": 0},
            {"Cobertura": "RC hacia Terceros (Excepto pasajeros)", "Tasa (%)": 0.50, "Capital (USD)": 0},
            {"Cobertura": "Responsabilidad Civil Legal de Carga", "Tasa (%)": 0.50, "Capital (USD)": 0},
        ],
        "accidentes": [
            {"Cobertura": "Accidente Personales Tripulantes", "Tasa (%)": 0.30, "Asientos": 1, "Capital (USD)": 0},
            {"Cobertura": "Accidente Personales Pasajeros", "Tasa (%)": 0.30, "Asientos": 1, "Capital (USD)": 0},
        ],
    },
    "Agrícola": {
        "principales": [
            {"Cobertura": "Perdida o Dano de la Aeronave", "Tasa (%)": 3.00, "Capital (USD)": 0},
            {"Cobertura": "RC hacia Terceros (Excepto pasajeros)", "Tasa (%)": 0.50, "Capital (USD)": 0},
            {"Cobertura": "Responsabilidad Civil Danos Quimicos", "Tasa (%)": 3.00, "Capital (USD)": 0},
        ],
        "accidentes": [
            {"Cobertura": "Accidente Personales Tripulantes", "Tasa (%)": 0.30, "Asientos": 1, "Capital (USD)": 0},
            {"Cobertura": "Accidente Personales Pasajeros", "Tasa (%)": 0.30, "Asientos": 1, "Capital (USD)": 0},
        ],
    },
    "Escuela e Instrucción": {
        "principales": [
            {"Cobertura": "Perdida o Dano de la Aeronave", "Tasa (%)": 2.50, "Capital (USD)": 0},
            {"Cobertura": "RC hacia Terceros (Excepto pasajeros)", "Tasa (%)": 0.50, "Capital (USD)": 0},
        ],
        "accidentes": [],
    },
}

# ==========================================
# DETECCION DEL LINK EXTERNO (CLIENTE)
# ==========================================
query_params = st.query_params

if "q" in query_params:
    try:
        datos_b64 = query_params["q"]
        datos_json = base64.b64decode(datos_b64).decode()
        propuesta_cliente = json.loads(datos_json)

        st.set_page_config(page_title="EDF SEGUROS - Propuesta", layout="wide", page_icon="🛡️")
        st.markdown("""
            <style>
            .ben-fila { background-color: #f8f9fa; padding: 10px 18px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #1E3A8A !important; font-size: 14px; color: #333; }
            .caja-azul { background-color: #ffffff; padding: 18px; border-radius: 12px; height: 100%; border: 1px solid #e0e0e0; border-top: 5px solid #1E3A8A !important; }
            </style>
        """, unsafe_allow_html=True)

        st.image("https://raw.githubusercontent.com/roque-eng/crm-final/main/de-freitas-logo-01.jpg", width=150)

        # --- VISTA AERONAVE ---
        if propuesta_cliente.get("tipo") == "Aeronave":
            mat = propuesta_cliente.get('matricula', '')
            geo = propuesta_cliente.get('alcance_geo', '')
            aseg = propuesta_cliente.get('aseguradora', '')
            aeronave = propuesta_cliente.get('aeronave', '')
            destino = propuesta_cliente.get('destino', '')

            filas_info = ""
            if aseg: filas_info += f'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Aseguradora:</b> {aseg}</p>'
            if aeronave: filas_info += f'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Aeronave:</b> {aeronave}</p>'
            if mat: filas_info += f'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Matricula:</b> {mat}</p>'
            if geo: filas_info += f'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Alcance Geografico:</b> {geo}</p>'
            if destino: filas_info += f'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Destino:</b> {destino}</p>'

            st.markdown(f"""
            <div style="font-family: sans-serif; padding-left: 5px; margin-bottom: 20px; margin-top: 20px;">
                <h2 style="margin: 0 0 12px 0; font-size: 24px; color: #111; font-weight: bold;">Asegurado: {propuesta_cliente.get('n', 'Cliente')}</h2>
                {filas_info}
            </div>
            """, unsafe_allow_html=True)

            tab_data = propuesta_cliente.get("tab", [])
            if tab_data:
                html_tabla = '<table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:15px;">'
                html_tabla += '<tr style="background:#1E3A8A;color:white;">'
                for col in ["Cobertura", "Asientos", "Capital (USD)"]:
                    html_tabla += f'<th style="padding:8px 12px;text-align:left;">{col}</th>'
                html_tabla += '</tr>'
                for i, row in enumerate(tab_data):
                    bg = "#f8f9fa" if i % 2 == 0 else "white"
                    html_tabla += f'<tr style="background:{bg};">'
                    html_tabla += f'<td style="padding:7px 12px;border-bottom:1px solid #e5e7eb;">{row.get("Cobertura","")}</td>'
                    asientos = row.get("Asientos", 0)
                    asientos_fmt = str(int(float(str(asientos)))) if asientos and str(asientos) not in ["0","0.0",""] else "—"
                    capital = row.get("Capital", 0)
                    cob_str = str(row.get("Cobertura", "")).lower()
                    try: capital_fmt = f"USD {int(float(capital)):,}".replace(",",".")
                    except: capital_fmt = str(capital)
                    if str(capital) in ["0", "0.0", ""] and "aptitud" in cob_str:
                        capital_fmt = "Incluido"
                    html_tabla += f'<td style="padding:7px 12px;border-bottom:1px solid #e5e7eb;">{asientos_fmt}</td>'
                    html_tabla += f'<td style="padding:7px 12px;border-bottom:1px solid #e5e7eb;">{capital_fmt}</td>'
                    html_tabla += '</tr>'
                html_tabla += '</table>'
                st.markdown(html_tabla, unsafe_allow_html=True)

            obs_av = propuesta_cliente.get("obs_av", "")
            if obs_av:
                st.markdown(f"""
                <div style="margin-top:15px; padding:12px 16px; background:#f8f9fa; border-radius:8px; border-left:4px solid #1E3A8A; font-size:14px; color:#333;">
                    {obs_av.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

            subtotal = propuesta_cliente.get("subtotal", 0)
            cargos = propuesta_cliente.get("cargos", 0)
            total = propuesta_cliente.get("total", 0)
            st.markdown(f"""
            <div style="margin-top:20px; padding:15px; background:#EFF6FF; border-radius:10px; border-left:5px solid #1E3A8A;">
                <p style="margin:4px 0;">Subtotal: <b>USD {subtotal:,.0f}</b></p>
                <p style="margin:4px 0;">Cargos de Emision (15%): <b>USD {cargos:,.0f}</b></p>
                <p style="margin:4px 0; font-size:17px; color:#1E3A8A;">Costo Anual Total: <b>USD {total:,.0f}</b></p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            asesor_key_av = propuesta_cliente.get('e', 'EDF')
            asesor_nombre_av = NOMBRES.get(asesor_key_av, asesor_key_av)
            st.markdown(f"<div style='display:flex; justify-content:space-between; color:gray;'><div><b>Asesor:</b> {asesor_nombre_av} | <b>Contacto:</b> {propuesta_cliente.get('cont','')}</div><div><b>Fecha:</b> {propuesta_cliente.get('fecha','')}</div></div>", unsafe_allow_html=True)
            st.stop()

        # --- VISTA FLOTA ---
        if propuesta_cliente.get("tipo") == "Flota":
            filas_info_f = ""
            if propuesta_cliente.get('e'): filas_info_f += f'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Aseguradora:</b> {propuesta_cliente.get("e","")}</p>'
            st.markdown(f"""
            <div style="font-family: sans-serif; padding-left: 5px; margin-bottom: 20px; margin-top: 20px;">
                <h2 style="margin: 0 0 12px 0; font-size: 24px; color: #111; font-weight: bold;">Asegurado: {propuesta_cliente.get('n', 'Cliente')}</h2>
                {filas_info_f}
            </div>
            """, unsafe_allow_html=True)
        else:
            # --- VISTA INDIVIDUAL ---
            st.markdown(f"""
            <div style="font-family: sans-serif; padding-left: 5px; margin-bottom: 20px; margin-top: 20px;">
                <h2 style="margin: 0 0 12px 0; font-size: 24px; color: #111; font-weight: bold;">Asegurado: {propuesta_cliente.get('n', 'Cliente')}</h2>
                {'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Vehiculo:</b> ' + propuesta_cliente.get('v','') + '</p>' if propuesta_cliente.get('v') else ''}
                {'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Matricula:</b> ' + propuesta_cliente.get('matricula','') + '</p>' if propuesta_cliente.get('matricula') else ''}
                {'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Cobertura cotizada:</b> ' + propuesta_cliente.get('cobertura_cot','') + '</p>' if propuesta_cliente.get('cobertura_cot') else ''}
                {'<p style="margin:2px 0; font-size:15px; color:#333;"><b>Zona de Circulacion principal:</b> ' + propuesta_cliente.get('zona','') + '</p>' if propuesta_cliente.get('zona') else ''}
            </div>
            """, unsafe_allow_html=True)

        df_cli = pd.DataFrame(propuesta_cliente.get("tab", []))
        if not df_cli.empty:
            cols_num = ["Contado", "Deducible"] if propuesta_cliente.get("tipo") == "Flota" else ["Contado", "10 Cuotas", "Deducible"]
            for col in cols_num:
                if col in df_cli.columns:
                    df_cli[col] = pd.to_numeric(df_cli[col], errors='coerce').fillna(0).astype(int)
            cols_mostrar = [c for c in df_cli.columns if c in ["Aseguradora","Marca","Modelo","Ano","Matricula","Cobertura","Contado","10 Cuotas","Deducible"]]
            html_tabla = '<table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:10px;">'
            html_tabla += '<tr style="background:#1E3A8A;color:white;">'
            for col in cols_mostrar:
                html_tabla += f'<th style="padding:8px 12px;text-align:left;">{col.upper()}</th>'
            html_tabla += '</tr>'
            for i, row in df_cli.iterrows():
                bg = "#f8f9fa" if i % 2 == 0 else "white"
                html_tabla += f'<tr style="background:{bg};">'
                for col in cols_mostrar:
                    val = row.get(col, "")
                    if col in ["Contado", "10 Cuotas", "Deducible"]:
                        try: val = f"$ {int(float(val)):,}".replace(",", ".")
                        except: pass
                    html_tabla += f'<td style="padding:7px 12px;border-bottom:1px solid #e5e7eb;">{val}</td>'
                html_tabla += '</tr>'
            html_tabla += '</table>'
            st.markdown(html_tabla, unsafe_allow_html=True)

        if propuesta_cliente.get("ben"):
            st.write("")
            st.markdown(f"### {'Beneficios Incluidos' if propuesta_cliente.get('tipo') != 'Flota' else 'Observaciones y Comentarios'}")
            for b in propuesta_cliente.get("ben", "").split('\n'):
                if b.strip(): st.markdown(f'<div class="ben-fila">{b.strip()}</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown("### Coberturas Complementarias")
        cx1, cx2, cx3 = st.columns(3)
        def b_html_cli(tit, ico, txt):
            if not txt: return ""
            out = f'<div class="caja-azul"><span style="font-weight:bold; color:#1E3A8A;">{ico} {tit}</span><br>'
            for l in txt.split('\n'):
                l = l.strip()
                if not l: continue
                if l.lower().startswith("costo") or l.lower().startswith("- costo") or l.lower().startswith("* costo"):
                    partes = l.lstrip("*- ").split(":", 1)
                    if len(partes) == 2:
                        out += f'<span style="display:block; margin-top:8px; padding:6px 10px; background:#EFF6FF; border-radius:6px; font-weight:bold; color:#1E3A8A;">💰 {partes[0].strip()}: <span style="color:#111;">{partes[1].strip()}</span></span>'
                    else:
                        out += f'<span style="display:block; margin-top:8px; padding:6px 10px; background:#EFF6FF; border-radius:6px; font-weight:bold; color:#1E3A8A;">💰 <span style="color:#111;">{l.lstrip("*- ")}</span></span>'
                else:
                    out += f'<span style="display:block; margin-top:3px;">{l}</span>'
            return out + '</div>'

        es_flota = propuesta_cliente.get("tipo") == "Flota"
        tit_ch = "Accidentes Personales" if es_flota else "Hogar"
        ico_ch = "🧑‍⚕️" if es_flota else "🏠"
        tit_ca = "Auto Sustituto / Alquiler" if es_flota else "Alquiler / Auto Sust."
        tit_cb = "Bici Electrica o Moto" if es_flota else "Bici"
        ico_cb = "🛵" if es_flota else "🚲"
        cx1.markdown(b_html_cli(tit_ch, ico_ch, propuesta_cliente.get("ch", "")), unsafe_allow_html=True)
        cx2.markdown(b_html_cli(tit_ca, "🚗", propuesta_cliente.get("ca", "")), unsafe_allow_html=True)
        cx3.markdown(b_html_cli(tit_cb, ico_cb, propuesta_cliente.get("cb", "")), unsafe_allow_html=True)
        st.markdown("---")
        asesor_pie = propuesta_cliente.get('e_nombre') if propuesta_cliente.get('tipo') == 'Flota' else propuesta_cliente.get('e', 'EDF')
        st.markdown(f"<div style='display:flex; justify-content:space-between; color:gray;'><div><b>Asesor:</b> {asesor_pie} | <b>Contacto:</b> {propuesta_cliente.get('cont', '')}</div><div><b>Fecha:</b> {propuesta_cliente.get('fecha','')}</div></div>", unsafe_allow_html=True)
        st.stop()
    except Exception as e:
        st.error(f"Error al cargar la propuesta externa: {e}")
        st.stop()


# ==========================================
# LOGICA DEL ASESOR (CRM)
# ==========================================
if "historico" not in st.session_state: st.session_state.historico = []
if "edit_data" not in st.session_state: st.session_state.edit_data = {}

if "historico_sheet_cargado" not in st.session_state:
    try:
        gc = get_gspread_client()
        if gc:
            sh = gc.open_by_key(SHEET_ID)
            hist = []
            for hoja, tipo in [("Cotizaciones Individuales", "Individual"), ("Cotizaciones Flotas", "Flota"), ("Cotizaciones Aeronaves", "Aeronave")]:
                try:
                    ws = sh.worksheet(hoja)
                    rows = ws.get_all_values()
                    for row in rows[1:]:
                        if row and row[0]:
                            if tipo == "Individual" and len(row) >= 13:
                                hist.append({"fecha": row[0], "n": row[1], "doc": row[2], "v": row[3], "matricula": row[4], "cobertura_cot": row[5], "zona": row[6], "e": row[7], "tipo": "Individual", "link": row[12] if len(row) > 12 else ""})
                            elif tipo == "Flota" and len(row) >= 6:
                                hist.append({"fecha": row[0], "n": row[1], "e": row[2], "e_nombre": row[3], "tipo": "Flota", "link": row[5] if len(row) > 5 else ""})
                            elif tipo == "Aeronave" and len(row) >= 12:
                                # Si existe columna JSON (col 12), reconstruimos el dict completo
                                if len(row) > 12 and row[12]:
                                    try:
                                        datos_completos = json.loads(row[12])
                                        datos_completos["link"] = row[11] if len(row) > 11 else ""
                                        hist.append(datos_completos)
                                    except:
                                        hist.append({"fecha": row[0], "n": row[1], "aseguradora": row[2], "aeronave": row[3], "matricula": row[4], "alcance_geo": row[5], "destino": row[6], "e": row[7], "total": row[10], "tipo": "Aeronave", "link": row[11] if len(row) > 11 else ""})
                                else:
                                    hist.append({"fecha": row[0], "n": row[1], "aseguradora": row[2], "aeronave": row[3], "matricula": row[4], "alcance_geo": row[5], "destino": row[6], "e": row[7], "total": row[10], "tipo": "Aeronave", "link": row[11] if len(row) > 11 else ""})
                except: pass
            st.session_state.historico = hist
    except: pass
    st.session_state.historico_sheet_cargado = True

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

st.markdown("""
<style>
.ben-fila { background-color: #f8f9fa; padding: 10px 18px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #1E3A8A !important; font-size: 14px; color: #333; }
.caja-azul { background-color: #ffffff; padding: 18px; border-radius: 12px; height: 100%; border: 1px solid #e0e0e0; border-top: 5px solid #1E3A8A !important; }
div.stButton > button { background-color: #ff4b4b !important; color: white !important; border: 2px solid #ff4b4b !important; font-weight: bold !important; border-radius: 8px !important; padding: 10px 24px !important; transition: all 0.3s ease !important; }
div.stButton > button:hover { background-color: #ff3333 !important; border-color: #ff3333 !important; color: white !important; transform: scale(1.01) !important; }
.btn-copiar-edf { background-color: #1E3A8A !important; color: white !important; border: none; padding: 10px 20px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 10px; display: inline-block; }
.btn-copiar-edf:hover { background-color: #111827 !important; }
</style>
""", unsafe_allow_html=True)

USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "GS": "GSanchez2025", "MDF": "Matiti2025", "EH": "EHugo2025", "AP": "APerdomo2025", "RS": "RSierra2025", "LT": "LTomasi2025", "EC": "ECabral2025", "PG": "PGagliardi2025"}

if 'usuario_actual' not in st.session_state: st.session_state['usuario_actual'] = "RDF"

if 'logueado' not in st.session_state or not st.session_state['logueado']:
    col_logo, col_form = st.columns([1, 1.6])
    with col_logo:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.image("https://raw.githubusercontent.com/roque-eng/crm-final/main/de-freitas-logo-01.jpg", use_container_width=True)
    with col_form:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("EDF SEGUROS")
        st.markdown("##### Sistema de Gestión y Cotización")
        u_sel = st.selectbox("Seleccione su Usuario:", list(USUARIOS.keys()))
        p_in = st.text_input("Contrasena:", type="password")
        if st.button("Ingresar", type="primary"):
            if USUARIOS.get(u_sel) == p_in:
                st.session_state['logueado'] = True
                st.session_state['usuario_actual'] = u_sel
                st.rerun()
            else: st.error("Contrasena incorrecta.")
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(spreadsheet=URL_HOJA, ttl=0)
df_raw.columns = df_raw.columns.str.strip()

col_map = {c.lower(): c for c in df_raw.columns}
c_asegurado = col_map.get("asegurado", col_map.get("cliente", "Asegurado"))
c_documento = col_map.get("documento", col_map.get("ci", col_map.get("rut", "Documento")))
c_aseguradora = col_map.get("aseguradora", col_map.get("compania", "Aseguradora"))
c_ramo = col_map.get("ramo", "Ramo")
c_p_usd = col_map.get("premio usd (iva inc)", "Premio USD (IVA inc)")
c_p_uyu = col_map.get("premio uyu (iva inc)", "Premio UYU (IVA inc)")
c_adjunto = col_map.get("adjunto (poliza)", col_map.get("adjunto (poliza)", "Adjunto (poliza)"))

df_raw['Premio_Total_USD'] = (pd.to_numeric(df_raw.get(c_p_usd, 0), errors='coerce').fillna(0) + (pd.to_numeric(df_raw.get(c_p_uyu, 0), errors='coerce').fillna(0) / TC_USD)).round(0)
df_raw['Fin de Vigencia'] = pd.to_datetime(df_raw.get('Fin de Vigencia', date.today()), dayfirst=True, errors='coerce').dt.date

with st.sidebar:
    st.title(f"👤 {NOMBRES.get(st.session_state.usuario_actual, st.session_state.usuario_actual)}")
    def get_list(col): return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
    f_ej = st.selectbox("Ejecutivo", get_list('Ejecutivo'))
    f_as = st.selectbox("Aseguradora", get_list(c_aseguradora))
    f_ra = st.selectbox("Ramo", get_list(c_ramo))
    f_co = st.selectbox("Corredor", get_list('Corredor'))
    f_ag = st.selectbox("Agente", get_list('Agente'))
    if st.button("Cerrar Sesion"):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos" and 'Ejecutivo' in df_f.columns: df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f[c_aseguradora] == f_as]
if f_ra != "Todos": df_f = df_f[df_f[c_ramo] == f_ra]
if f_co != "Todos" and 'Corredor' in df_f.columns: df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos" and 'Agente' in df_f.columns: df_f = df_f[df_f['Agente'] == f_ag]

tab_car, tab_ven, tab_cot, tab_flota, tab_aeronave, tab_historial, tab_an = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 VEHICULOS", "🚛 FLOTAS", "✈️ AERONAVES", "📜 HISTORIAL", "📊 ANALISIS"])

# --- CARTERA ---
with tab_car:
    busq = st.text_input("🔍 Buscar cliente o matricula en cartera...")
    df_c = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f
    if not df_c.empty:
        df_resumen = df_c.copy()
        col_cliente_real = next((col for col in df_resumen.columns if "asegurado" in str(col).lower() or "client" in str(col).lower()), None)
        if col_cliente_real: df_resumen = df_resumen.rename(columns={col_cliente_real: "Asegurado"})
        df_resumen = df_resumen.rename(columns={c_adjunto: "Poliza", c_documento: "Documento", c_aseguradora: "Aseguradora", c_ramo: "Ramo", 'Fin de Vigencia': "Vencimiento", c_p_usd: "Premio USD", c_p_uyu: "Premio UYU", 'Premio_Total_USD': "Premio Total (USD)"})
        columnas_visibles = ["Poliza", "Asegurado", "Documento", "Aseguradora", "Ramo", "Vencimiento", "Premio USD", "Premio UYU", "Premio Total (USD)"]
        cols_validas = [c for c in columnas_visibles if c in df_resumen.columns]
        df_resumen = df_resumen[cols_validas]
        st.markdown("##### 📋 Resumen de Contratos Activos")
        st.markdown("<small style='color:gray;'>💡 Hace un clic en el extremo izquierdo de cualquier fila para ver el detalle abajo</small>", unsafe_allow_html=True)
        st.dataframe(df_resumen, use_container_width=True, hide_index=False, on_select="rerun", selection_mode="single-row", key="grid_cartera_unica",
            column_config={"Poliza": st.column_config.LinkColumn("Poliza", display_text="📎 Ver PDF"), "Vencimiento": st.column_config.DateColumn("Vencimiento", format="DD/MM/YYYY"), "Premio USD": st.column_config.NumberColumn("Premio USD", format="USD %,d"), "Premio UYU": st.column_config.NumberColumn("Premio UYU", format="$ %,d"), "Premio Total (USD)": st.column_config.NumberColumn("Premio Total (USD)", format="USD %,d")})
        selection = st.session_state.get("grid_cartera_unica", {}).get("selection", {})
        filas_seleccionadas = selection.get("rows", [])
        if filas_seleccionadas:
            fila_completa = df_c.iloc[filas_seleccionadas[0]]
            st.write("")
            with st.container(border=True):
                st.markdown(f"### Detalle de la Poliza: {fila_completa.get(c_asegurado, 'Cliente')}")
                cx1, cx2, cx3 = st.columns(3)
                with cx1:
                    st.markdown("**Datos del Cliente:**")
                    st.write(f"• **Documento:** {fila_completa.get(c_documento, 'N/D')}")
                    st.write(f"• **Celular:** {fila_completa.get('Celular', 'N/D')}")
                    st.write(f"• **Mail:** {fila_completa.get('Mail', 'N/D')}")
                with cx2:
                    st.markdown("**Detalles del Bien:**")
                    st.write(f"• **Ramo:** {fila_completa.get(c_ramo, 'N/D')}")
                    st.write(f"• **Matricula:** {fila_completa.get('Matricula', 'N/D')}")
                    st.write(f"• **Detalle:** {fila_completa.get('Detalle', 'N/D')}")
                with cx3:
                    st.markdown("**Gestion e Intermediacion:**")
                    st.write(f"• **Fin de Vigencia:** {fila_completa.get('Fin de Vigencia', 'N/D')}")
                    st.write(f"• **Ejecutivo:** {fila_completa.get('Ejecutivo', 'N/D')}")
                    st.write(f"• **Corredor/Agente:** {fila_completa.get('Corredor', 'N/D')} / {fila_completa.get('Agente', 'N/D')}")
    else:
        st.info("No se encontraron registros en la cartera.")

# --- VENCIMIENTOS ---
with tab_ven:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        c1, c2 = st.columns(2)
        f_ini = c1.date_input("Desde:", date.today().replace(day=1))
        f_fin = c2.date_input("Hasta:", date.today() + timedelta(days=90))
        df_venc_f = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')
        if not df_venc_f.empty:
            df_venc_resumen = df_venc_f.copy()
            col_cliente_real_v = next((col for col in df_venc_resumen.columns if "asegurado" in str(col).lower() or "client" in str(col).lower()), None)
            if col_cliente_real_v: df_venc_resumen = df_venc_resumen.rename(columns={col_cliente_real_v: "Asegurado"})
            df_venc_resumen = df_venc_resumen.rename(columns={c_adjunto: "Poliza", c_documento: "Documento", c_aseguradora: "Aseguradora", c_ramo: "Ramo", 'Fin de Vigencia': "Vencimiento", c_p_usd: "Premio USD", c_p_uyu: "Premio UYU", 'Premio_Total_USD': "Premio Total (USD)"})
            columnas_visibles_v = ["Poliza", "Asegurado", "Documento", "Aseguradora", "Ramo", "Vencimiento", "Premio USD", "Premio UYU", "Premio Total (USD)"]
            cols_validas_v = [c for c in columnas_visibles_v if c in df_venc_resumen.columns]
            df_venc_resumen = df_venc_resumen[cols_validas_v]
            st.markdown("<small style='color:gray;'>💡 Hace un clic en el extremo izquierdo de cualquier fila para ver el detalle abajo</small>", unsafe_allow_html=True)
            st.dataframe(df_venc_resumen, use_container_width=True, hide_index=False, on_select="rerun", selection_mode="single-row", key="grid_venc_unico",
                column_config={"Poliza": st.column_config.LinkColumn("Poliza", display_text="📎 Ver PDF"), "Vencimiento": st.column_config.DateColumn("Vencimiento", format="DD/MM/YYYY"), "Premio USD": st.column_config.NumberColumn("Premio USD", format="USD %,d"), "Premio UYU": st.column_config.NumberColumn("Premio UYU", format="$ %,d"), "Premio Total (USD)": st.column_config.NumberColumn("Premio Total (USD)", format="USD %,d")})
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_venc_f.to_excel(writer, index=False, sheet_name='Vencimientos')
            st.download_button(label="📥 Exportar Vencimientos Completos a Excel", data=output.getvalue(), file_name="Vencimientos.xlsx")
            selection_v = st.session_state.get("grid_venc_unico", {}).get("selection", {})
            filas_seleccionadas_v = selection_v.get("rows", [])
            if filas_seleccionadas_v:
                fila_completa_v = df_venc_f.iloc[filas_seleccionadas_v[0]]
                def limpiar(val):
                    v = str(val).strip()
                    return '' if v in ['nan', 'None', 'N/D', 'none'] else v
                nombre_completo = limpiar(fila_completa_v.get(c_asegurado, ''))
                if not nombre_completo:
                    for col in fila_completa_v.index:
                        if 'asegurado' in str(col).lower() or 'nombre' in str(col).lower():
                            val = limpiar(str(fila_completa_v.get(col, '')))
                            if val:
                                nombre_completo = val
                                break
                nombre_corto = nombre_completo.split()[0].capitalize() if nombre_completo else 'Cliente'
                c_mail_v = col_map.get("direccion de correo electronico", col_map.get("mail", col_map.get("email", "")))
                premio_uyu_v = limpiar(str(fila_completa_v.get(c_p_uyu, '')))
                premio_usd_v = limpiar(str(fila_completa_v.get(c_p_usd, '')))
                aseguradora_actual = limpiar(fila_completa_v.get(c_aseguradora, '')) or 'su aseguradora'
                ramo_v = limpiar(fila_completa_v.get(c_ramo, '')) or 'bien asegurado'
                c_detalle_v = col_map.get("detalle", "")
                detalle_ren = limpiar(fila_completa_v.get(c_detalle_v, '')) if c_detalle_v else ''
                ramo_completo = f"{ramo_v} ({detalle_ren})" if detalle_ren else ramo_v
                vencimiento_v = fila_completa_v.get('Fin de Vigencia', '')
                fecha_fmt = vencimiento_v.strftime('%d/%m/%Y') if hasattr(vencimiento_v, 'strftime') else str(vencimiento_v)
                nombre_asesor_v = NOMBRES.get(st.session_state.usuario_actual, st.session_state.usuario_actual)
                if premio_uyu_v and str(premio_uyu_v) not in ['0']:
                    premio_txt = f"UYU {f_num(premio_uyu_v)}"
                elif premio_usd_v and str(premio_usd_v) not in ['0']:
                    premio_txt = f"USD {f_num(premio_usd_v)}"
                else:
                    premio_txt = "a coordinar"
                texto_wp = f"""Hola {nombre_corto}!
Te escribo porque esta venciendo la poliza de tu {ramo_completo} el proximo *{fecha_fmt}*.
Este anio estabas pagando en *{aseguradora_actual}: {premio_txt}*.
Para la renovacion tenemos los siguientes comparativos:

- BSE:
- SBI:
- MAPFRE:
- SANCOR:
- SURA:
- PORTO:
- BERKLEY:

Auto Sustituto (por 15 dias) en caso de chocar y que tu vehiculo vaya al taller y necesites uno, debemos agregar $3.300 a cualquier aseguradora.

Quedo a las ordenes,
Saludos!
{nombre_asesor_v}"""
                st.write("")
                with st.container(border=True):
                    st.markdown(f"### Detalle de la Poliza (Vencimiento): {fila_completa_v.get(c_asegurado, 'Cliente')}")
                    cv1, cv2 = st.columns(2)
                    with cv1:
                        st.markdown("**Datos del Cliente:**")
                        st.write(f"• **Documento:** {fila_completa_v.get(c_documento, 'N/D')}")
                        st.write(f"• **Cell:** {fila_completa_v.get('Celular', 'N/D')}")
                        st.write(f"• **Mail:** {fila_completa_v.get(c_mail_v, 'N/D') if c_mail_v else 'N/D'}")
                    with cv2:
                        st.markdown("**Detalles del Bien:**")
                        st.write(f"• **Ramo:** {fila_completa_v.get(c_ramo, 'N/D')}")
                        c_npoliza_v = col_map.get("n de poliza", col_map.get("numero de poliza", ""))
                        st.write(f"• **N de Poliza:** {fila_completa_v.get(c_npoliza_v, 'N/D') if c_npoliza_v else 'N/D'}")
                        detalle_col_v2 = next((col for col in fila_completa_v.index if str(col).lower() == 'detalle'), None)
                        st.write(f"• **Detalle:** {fila_completa_v.get(detalle_col_v2, 'N/D') if detalle_col_v2 else 'N/D'}")
                st.markdown('<style>details summary { background-color: #1E3A8A22 !important; border-radius: 6px; padding: 8px 12px; color: #1E3A8A; font-weight: bold; }</style>', unsafe_allow_html=True)
                with st.expander("💬 Texto renovacion (predeterminado)"):
                    st.code(texto_wp, language=None)
        else:
            st.info("No hay vencimientos en el rango seleccionado.")

# PLANTILLAS
txt_ben_veh = "• Auxilio mecanico e ilimitado\n• Cobertura Mercosur\n• Cristales: USD 300 SANCOR, USD 200 BSE O SBI, USD 100 SURA, demas cobran deducible\n• Granizo: SANCOR incluido sin deducible, demas aplican deducible."
txt_hog_veh = "• Incendio Edificio USD 100.000\n• Incendio Contenido 50.000\n• Hurto Contenido 5.000\n• Costo anual Casas: USD 180\n• Costo anual Aptos: USD 120"
txt_alq_veh = "• Auto sustituto por hasta 15 dias.\n• Costo anual: UYU 3.000 por vehiculo."
txt_bic_veh = "• Cobertura Hurto bicicleta hasta USD 1.000.\n• Costo anual: USD 120"
txt_obs_flota = "Vigencia:\nForma de Pago: redes de cobranza o tarjeta de credito en 10 cuotas sin recargo.\nBeneficios\n  - Auxilio mecanico ilimitado.\n  - Cristales: SANCOR USD 300, BSE y SBI USD 200, SURA USD 100.\n  - Granizo: SANCOR lo cubre, demas cobran deducible."
txt_acc_flota = "• Seguro de Vida Accidentes choferes: USD 25.000.\n• Costo anual: UYU 1.900 por chofer."
txt_alq_flota = "• Auto sustituto por hasta 15 dias.\n• Costo anual: UYU 3.000 por vehiculo."
txt_bic_flota = "• Bici electrica o moto hasta USD 1.000.\n• Costo anual: UYU 5.000"

# --- VEHICULOS INDIVIDUAL ---
with tab_cot:
    st.subheader("📝 Cotizador Seguros Individuales")
    edit_ind = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Individual" else {}
    if edit_ind:
        st.session_state["ci_v_final"] = edit_ind.get("doc", "")
        st.session_state["nom_v_final"] = edit_ind.get("n", "")
        st.session_state["veh_v_final"] = edit_ind.get("v", "")
        st.session_state["mat_v_final"] = edit_ind.get("matricula", "")
        st.session_state["cob_v_final"] = edit_ind.get("cobertura_cot", "")
        st.session_state["zona_v_final"] = edit_ind.get("zona", "")
    with st.container(border=True):
        c_doc, c_nom, c_veh, c_mat = st.columns([1.5, 2, 2, 1.5])
        doc_in = c_doc.text_input("CI/RUT", key="ci_v_final")
        n_cot = c_nom.text_input("Nombre", key="nom_v_final")
        v_cot = c_veh.text_input("Vehiculo (marca/modelo)", key="veh_v_final")
        mat_cot = c_mat.text_input("Matricula", key="mat_v_final")
        c_cob, c_zona, c_ase, c_con = st.columns([2, 2, 1, 2])
        cob_cot = c_cob.text_input("Cobertura cotizada", key="cob_v_final")
        zona_cot = c_zona.text_input("Zona de Circulacion principal", key="zona_v_final")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="ase_v_final")
        if not edit_ind:
            st.session_state["cont_v_final"] = CONTACTOS.get(e_cot, "")
        cont_cot = c_con.text_input("Contacto Asesor", key="cont_v_final")

    cols_individual = ["Aseguradora", "Contado", "10 Cuotas", "Deducible"]
    if edit_ind and "tab" in edit_ind:
        df_p_init = pd.DataFrame(edit_ind["tab"])
    else:
        df_p_init = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "SURA", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "MAPFRE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "SANCOR", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}])
    t_edit = st.data_editor(df_p_init, num_rows="dynamic", use_container_width=True, column_order=cols_individual, key="editor_individual_completo",
        column_config={"Contado": st.column_config.NumberColumn("Contado", format="$ %,d"), "10 Cuotas": st.column_config.NumberColumn("10 Cuotas", format="$ %,d"), "Deducible": st.column_config.NumberColumn("Deducible", format="$ %,d")})
    col_a, col_b = st.columns(2)
    with col_a:
        b_cot = st.text_area("Beneficios:", value=edit_ind.get("ben", txt_ben_veh), height=150, key="ben_v_final")
    with col_b:
        st.markdown("**Coberturas Complementarias**")
        c_h = st.text_area("Hogar:", value=edit_ind.get("ch", txt_hog_veh), height=80, key="ind_hog_v_final")
        c_a = st.text_area("Auto Sustituto / Alquiler:", value=edit_ind.get("ca", txt_alq_veh), height=50, key="ind_alq_v_final")
        c_b = st.text_area("Bici Electrica:", value=edit_ind.get("cb", txt_bic_veh), height=50, key="ind_bic_v_final")
    if st.button("💾 Guardar propuesta y Generar Link", type="primary", use_container_width=True, key="save_ind_btn"):
        datos_i = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": n_cot, "v": v_cot, "matricula": mat_cot, "cobertura_cot": cob_cot, "zona": zona_cot, "e": e_cot, "cont": cont_cot, "doc": doc_in, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b, "tipo": "Individual"}
        st.session_state.historico.append(datos_i)
        st.session_state.edit_data = datos_i
        datos_b64 = base64.b64encode(json.dumps(datos_i).encode()).decode()
        link_cliente = f"https://dfseguros.streamlit.app/?q={datos_b64}"
        primera_aseg = t_edit.iloc[0] if not t_edit.empty else {}
        guardar_en_sheet("Cotizaciones Individuales", [datos_i["fecha"], n_cot, doc_in, v_cot, mat_cot, cob_cot, zona_cot, e_cot, str(primera_aseg.get("Aseguradora", "")), str(primera_aseg.get("Contado", "")), str(primera_aseg.get("10 Cuotas", "")), str(primera_aseg.get("Deducible", "")), link_cliente])
        st.success("Propuesta guardada!")
        st.text_input("🔗 Enlace para mandar al cliente:", value=link_cliente)
        st.components.v1.html(f'<button class="btn-copiar-edf" onclick="navigator.clipboard.writeText(\'{link_cliente}\').then(() => {{ this.innerText = \'📋 Link Copiado!\'; }}).catch(err => {{ alert(\'Error\'); }})">📋 Copiar Link de Vehiculo</button>', height=60)

# --- FLOTAS ---
with tab_flota:
    st.subheader("🚛 Cotizador Seguro de Flotas")
    edit_f = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Flota" else {}
    if edit_f:
        st.session_state["f_nom_fl"] = edit_f.get("n", "")
        st.session_state["f_cia_fl"] = edit_f.get("e", "")
        st.session_state["f_as_fl"] = edit_f.get("e_nombre", "")
        st.session_state["f_co_fl"] = edit_f.get("cont", "")
    with st.container(border=True):
        f_c1, f_c2, f_c3, f_c4 = st.columns([2, 2, 1, 2])
        f_asegurado = f_c1.text_input("Asegurado", key="f_nom_fl")
        f_cia_elegida = f_c2.text_input("Aseguradora", key="f_cia_fl")
        f_asesor_nombre = f_c3.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="f_as_fl")
        if not edit_f:
            st.session_state["f_co_fl"] = CONTACTOS.get(f_asesor_nombre, "")
        f_contacto = f_c4.text_input("Contacto", key="f_co_fl")
    cols_f = ["Marca", "Modelo", "Ano", "Matricula", "Cobertura", "Contado", "Deducible"]
    if edit_f and "tab" in edit_f:
        df_f_init = pd.DataFrame(edit_f["tab"])
    else:
        df_f_init = pd.DataFrame([{"Marca": "", "Modelo": "", "Ano": "", "Matricula": "", "Cobertura": "Todo Riesgo", "Contado": 0, "Deducible": 0}])
    t_flota = st.data_editor(df_f_init, num_rows="dynamic", use_container_width=True, column_order=cols_f, key="editor_flotas",
        column_config={"Contado": st.column_config.NumberColumn("Contado", format="$ %,d"), "Deducible": st.column_config.NumberColumn("Deducible", format="$ %,d")})
    col_f_a, col_f_b = st.columns(2)
    with col_f_a:
        f_obs = st.text_area("Observaciones / Comentarios:", value=edit_f.get('ben', txt_obs_flota), height=320, key="f_obs_fl")
    with col_f_b:
        st.markdown("**Coberturas Complementarias para la Flota**")
        f_ch = st.text_area("Accidentes Personales:", value=edit_f.get("ch", txt_acc_flota), height=80, key="flota_hog_v_final")
        f_ca = st.text_area("Auto Sustituto / Alquiler:", value=edit_f.get("ca", txt_alq_flota), height=50, key="flota_alq_v_final")
        f_cb = st.text_area("Bici Electrica o Moto:", value=edit_f.get("cb", txt_bic_flota), height=50, key="flota_bic_v_final")
    if st.button("💾 Guardar propuesta de Flota y Generar Link", key="btn_save_fl", use_container_width=True):
        nueva_f = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": f_asegurado, "e": f_cia_elegida, "e_nombre": f_asesor_nombre, "cont": f_contacto, "tab": t_flota.to_dict(orient='records'), "ben": f_obs, "ch": f_ch, "ca": f_ca, "cb": f_cb, "tipo": "Flota"}
        st.session_state.historico.append(nueva_f)
        st.session_state.edit_data = nueva_f
        datos_b64 = base64.b64encode(json.dumps(nueva_f).encode()).decode()
        link_flota = f"https://dfseguros.streamlit.app/?q={datos_b64}"
        vehiculos_txt = " | ".join([f"{r.get('Marca','')} {r.get('Modelo','')} {r.get('Matricula','')}" for _, r in t_flota.iterrows() if r.get('Marca','')])
        guardar_en_sheet("Cotizaciones Flotas", [nueva_f["fecha"], f_asegurado, f_cia_elegida, f_asesor_nombre, vehiculos_txt, link_flota])
        st.success("Propuesta de Flota guardada!")
        st.text_input("🔗 Enlace para mandar al cliente:", value=link_flota)
        st.components.v1.html(f'<button class="btn-copiar-edf" onclick="navigator.clipboard.writeText(\'{link_flota}\').then(() => {{ this.innerText = \'📋 Link Copiado!\'; }}).catch(err => {{ alert(\'Error\'); }})">📋 Copiar Link de Flota</button>', height=60)

# --- AERONAVES ---
with tab_aeronave:
    st.subheader("✈️ Cotizador Seguros de Aeronaves")
    edit_av = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Aeronave" else {}
    # Solo cargamos los valores al session_state UNA vez (cuando se acaba de elegir editar),
    # igual que Individual/Flotas. Usamos un flag para no pisar lo que el usuario escribe.
    edit_av_id = id(st.session_state.edit_data) if edit_av else None
    if edit_av and st.session_state.get("_av_edit_loaded_id") != edit_av_id:
        st.session_state["av_asegurado"] = edit_av.get("n", "")
        st.session_state["av_aseguradora"] = edit_av.get("aseguradora", "")
        st.session_state["av_aeronave"] = edit_av.get("aeronave", "")
        st.session_state["av_matricula"] = edit_av.get("matricula", "")
        st.session_state["av_alcance_geo"] = edit_av.get("alcance_geo", "")
        st.session_state["av_contacto"] = edit_av.get("cont", "")
        st.session_state["_av_edit_loaded_id"] = edit_av_id
    with st.container(border=True):
        av_r1c1, av_r1c2, av_r1c3 = st.columns(3)
        av_asegurado = av_r1c1.text_input("Asegurado", key="av_asegurado")
        av_aseguradora = av_r1c2.text_input("Aseguradora", value=edit_av.get("aseguradora", "SBI Seguros"), key="av_aseguradora")
        av_aeronave = av_r1c3.text_input("Aeronave (Marca y Modelo)", key="av_aeronave")
        av_r2c1, av_r2c2, av_r2c3, av_r2c4 = st.columns(4)
        av_matricula = av_r2c1.text_input("Matricula", key="av_matricula")
        av_alcance_geo = av_r2c2.text_input("Alcance Geografico", key="av_alcance_geo")

        av_asesor = av_r2c3.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="av_asesor_sel",
                                       index=sorted(list(USUARIOS.keys())).index(st.session_state.usuario_actual) if st.session_state.usuario_actual in sorted(list(USUARIOS.keys())) else 0)
        if not edit_av:
            st.session_state["av_contacto"] = CONTACTOS.get(av_asesor, "")
        av_contacto = av_r2c4.text_input("Contacto (cel / mail)", key="av_contacto")

    destinos = ["Privado / Otro", "Agrícola", "Escuela e Instrucción"]
    av_destino_idx = destinos.index(edit_av.get("destino", "Privado / Otro")) if edit_av.get("destino") in destinos else 0
    av_destino = st.selectbox("Destino / Uso", destinos, index=av_destino_idx, key="av_destino")

    st.markdown("---")
    st.markdown("**Coberturas y Tasas** *(las tasas no se muestran al cliente)*")
    tasas_dest = TASAS_AERONAVE[av_destino]

    if edit_av and "tab_principales" in edit_av:
        df_princ_init = pd.DataFrame(edit_av["tab_principales"])
    else:
        df_princ_init = pd.DataFrame(tasas_dest["principales"])

    t_princ = st.data_editor(df_princ_init, num_rows="dynamic", use_container_width=True, key="editor_av_principales",
        column_order=["Cobertura", "Tasa (%)", "Capital (USD)"],
        column_config={"Cobertura": st.column_config.TextColumn("Cobertura"), "Tasa (%)": st.column_config.NumberColumn("Tasa (%)", format="%.2f%%", min_value=0.0, step=0.01), "Capital (USD)": st.column_config.NumberColumn("Capital (USD)", format="$ %,d")})

    t_acc = pd.DataFrame()
    if tasas_dest["accidentes"]:
        st.markdown("<small style='color:gray;'>Coberturas de Accidentes Personales</small>", unsafe_allow_html=True)
        if edit_av and "tab_accidentes" in edit_av:
            df_acc_init = pd.DataFrame(edit_av["tab_accidentes"])
        else:
            df_acc_init = pd.DataFrame(tasas_dest["accidentes"])
        t_acc = st.data_editor(df_acc_init, num_rows="dynamic", use_container_width=True, key="editor_av_accidentes",
            column_order=["Cobertura", "Tasa (%)", "Asientos", "Capital (USD)"],
            column_config={"Cobertura": st.column_config.TextColumn("Cobertura"), "Tasa (%)": st.column_config.NumberColumn("Tasa (%)", format="%.2f%%", min_value=0.0, step=0.01), "Asientos": st.column_config.NumberColumn("Asientos", format="%d", min_value=0), "Capital (USD)": st.column_config.NumberColumn("Capital (USD)", format="$ %,d")})

    aptitud_default = edit_av.get("aptitud_aterrizaje", True) if edit_av else True
    aptitud_incluida = st.checkbox("Aptitud de aterrizaje en pistas no autorizadas: Incluido", value=aptitud_default, key="av_aptitud")

    filas_calc = []
    subtotal = 0.0
    for _, row in t_princ.iterrows():
        cob = str(row.get("Cobertura", ""))
        tasa = float(row.get("Tasa (%)", 0) or 0)
        capital = float(row.get("Capital (USD)", 0) or 0)
        costo = round(capital * tasa / 100, 2)
        subtotal += costo
        filas_calc.append({"Cobertura": cob, "Tasa (%)": tasa, "Asientos": 0, "Capital": capital, "Costo": costo})
    if not t_acc.empty:
        for _, row in t_acc.iterrows():
            cob = str(row.get("Cobertura", ""))
            tasa = float(row.get("Tasa (%)", 0) or 0)
            capital = float(row.get("Capital (USD)", 0) or 0)
            asientos = int(row.get("Asientos", 0) or 0)
            costo = round(capital * tasa / 100, 2)
            subtotal += costo
            filas_calc.append({"Cobertura": cob, "Tasa (%)": tasa, "Asientos": asientos, "Capital": capital, "Costo": costo})
    if aptitud_incluida:
        filas_calc.append({"Cobertura": "Aptitud de aterrizaje en pistas no autorizadas", "Tasa (%)": 0, "Asientos": 0, "Capital": 0, "Costo": 0})

    obs_av_default = edit_av.get("obs_av", "") if edit_av else ""
    obs_av = st.text_area("Observaciones (aparece entre la tabla y el precio en la vista del cliente):", value=obs_av_default, height=80, key="av_obs")

    cargos_emision = round(subtotal * 0.15, 2)
    total_anual = round(subtotal + cargos_emision, 2)
    st.markdown("")
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Subtotal", f"USD {subtotal:,.0f}")
    col_res2.metric("Cargos de Emision (15%)", f"USD {cargos_emision:,.0f}")
    col_res3.metric("Costo Anual Total", f"USD {total_anual:,.0f}")

    if st.button("💾 Guardar cotizacion y Generar Link", type="primary", use_container_width=True, key="save_av_btn"):
        datos_av = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": av_asegurado, "aseguradora": av_aseguradora, "aeronave": av_aeronave, "matricula": av_matricula, "alcance_geo": av_alcance_geo, "destino": av_destino, "e": av_asesor, "cont": av_contacto, "tab": filas_calc, "tab_principales": t_princ.to_dict(orient='records'), "tab_accidentes": t_acc.to_dict(orient='records') if not t_acc.empty else [], "aptitud_aterrizaje": aptitud_incluida, "obs_av": obs_av, "subtotal": subtotal, "cargos": cargos_emision, "total": total_anual, "tipo": "Aeronave"}
        st.session_state.historico.append(datos_av)
        st.session_state.edit_data = datos_av
        st.session_state["_av_edit_loaded_id"] = None  # reset flag para proxima edicion
        datos_b64 = base64.b64encode(json.dumps(datos_av).encode()).decode()
        link_av = f"https://dfseguros.streamlit.app/?q={datos_b64}"
        guardar_en_sheet("Cotizaciones Aeronaves", [datos_av["fecha"], av_asegurado, av_aseguradora, av_aeronave, av_matricula, av_alcance_geo, av_destino, av_asesor, subtotal, cargos_emision, total_anual, link_av, json.dumps(datos_av)])
        st.success("Cotizacion de Aeronave guardada!")
        st.text_input("🔗 Enlace para mandar al cliente:", value=link_av)
        st.components.v1.html(f'<button class="btn-copiar-edf" onclick="navigator.clipboard.writeText(\'{link_av}\').then(() => {{ this.innerText = \'📋 Link Copiado!\'; }}).catch(err => {{ alert(\'Error\'); }})">📋 Copiar Link Aeronave</button>', height=60)

# --- HISTORIAL ---
with tab_historial:
    st.subheader("📜 Historial de Propuestas Guardadas")

    # CSS para íconos compactos en el historial
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) div.stButton > button,
    div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(3) div.stButton > button {
        padding: 2px 10px !important;
        min-height: 0px !important;
        height: 30px !important;
        font-size: 16px !important;
        line-height: 1 !important;
        background: transparent !important;
        border: 1px solid #ddd !important;
        color: #333 !important;
        border-radius: 6px !important;
        transform: none !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) div.stButton > button:hover,
    div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(3) div.stButton > button:hover {
        background: #f5f5f5 !important;
        border-color: #999 !important;
        transform: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.historico:
        hf1, hf2, hf3 = st.columns([2, 1, 1])
        busq_hist_nom = hf1.text_input("🔍 Buscar por asegurado:", key="busq_hist_nom")
        busq_hist_mat = hf2.text_input("🔍 Buscar por matricula:", key="busq_hist_mat")
        tipos_disponibles = ["Todos"] + sorted(list(set(r.get("tipo", "") for r in st.session_state.historico)))
        filtro_tipo = hf3.selectbox("Filtrar por tipo:", tipos_disponibles, key="filtro_tipo_hist")
        historico_filtrado = st.session_state.historico
        if busq_hist_nom:
            historico_filtrado = [r for r in historico_filtrado if busq_hist_nom.lower() in r.get("n", "").lower()]
        if busq_hist_mat:
            historico_filtrado = [r for r in historico_filtrado if busq_hist_mat.lower() in r.get("matricula", "").lower()]
        if filtro_tipo != "Todos":
            historico_filtrado = [r for r in historico_filtrado if r.get("tipo") == filtro_tipo]
        for i, reg in enumerate(reversed(historico_filtrado)):
            idx_real = st.session_state.historico.index(reg)
            col_info, col_edit, col_del = st.columns([0.78, 0.11, 0.11])
            with col_info:
                if reg.get("tipo") == "Flota": icon = "🚚"
                elif reg.get("tipo") == "Aeronave": icon = "✈️"
                else: icon = "🚗"
                mat_hist = f" | {reg.get('matricula')}" if reg.get('matricula') else ""
                st.write(f"📅 **{reg.get('fecha', '')[:10]}** | {icon} {reg.get('tipo')} | **{reg.get('n', 'Cliente')}**{mat_hist}")
            with col_edit:
                if st.button("✏️", key=f"edit_f_{i}_{idx_real}", help="Cargar / Editar"):
                    st.session_state.edit_data = reg
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_f_{i}_{idx_real}", help="Eliminar"):
                    st.session_state.historico.pop(idx_real)
                    st.rerun()
    else:
        st.info("No hay propuestas en el historial todavia.")

# --- ANALISIS ---
with tab_an:
    st.subheader("📊 Analisis de Cartera")
    if not df_f.empty:
        t_usd = df_f['Premio_Total_USD'].sum()
        k1, k2 = st.columns(2)
        k1.metric("Cartera Total (USD)", f"USD {t_usd:,.0f}")
        k2.metric("Total de Polizas", f"{len(df_f)}")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df_f, names=c_aseguradora, values='Premio_Total_USD', title="Compania", hole=0.4), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(df_f, names=c_ramo, values='Premio_Total_USD', title="Ramo", hole=0.4), use_container_width=True)
