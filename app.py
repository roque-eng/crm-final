import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64
import urllib.parse

# ==========================================
# CONFIGURACION GLOBAL Y ENLACES
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5

def f_num(val):
    try: return f"{int(float(str(val).replace('$', '').replace('USD', '').replace('.', '').replace(',', '').strip())):,}".replace(",", ".")
    except: return str(val)

def limpiar(val):
    v = str(val).strip()
    return '' if v in ['nan', 'None', 'N/D', 'none'] else v

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
            .tabla-edf { width:100%; border-collapse: collapse; margin-top: 15px; font-family: sans-serif; background-color: white; }
            .izq-negrita { text-align: left !important; font-weight: bold; }
            .ben-fila { background-color: #f8f9fa; padding: 10px 18px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #1E3A8A !important; font-size: 14px; color: #333; }
            .caja-azul { background-color: #ffffff; padding: 18px; border-radius: 12px; height: 100%; border: 1px solid #e0e0e0; border-top: 5px solid #1E3A8A !important; }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-family: sans-serif; text-align: left !important; padding-left: 5px; margin-bottom: 15px; margin-top: 20px;">
            <h2 style="margin: 0 0 6px 0; font-size: 22px; color: #111; text-align: left !important;">Asegurado: {propuesta_cliente.get('n', 'Cliente')}</h2>
            <p style="margin: 0; font-size: 16px; color: #555; text-align: left !important;"><b>{"Aseguradora" if propuesta_cliente.get("tipo") == "Flota" else "Vehiculo"}:</b> {propuesta_cliente.get('v' if propuesta_cliente.get('tipo') != 'Flota' else 'e', 'Detalle')}</p>
        </div>
        """, unsafe_allow_html=True)

        df_cli = pd.DataFrame(propuesta_cliente.get("tab", []))
        if not df_cli.empty:
            cols_num = ["Contado", "Deducible"] if propuesta_cliente.get("tipo") == "Flota" else ["Contado", "10 Cuotas", "Deducible"]
            for col in cols_num:
                if col in df_cli.columns:
                    df_cli[col] = pd.to_numeric(df_cli[col], errors='coerce').fillna(0).astype(int)

            conf_columnas = {
                "Aseguradora": st.column_config.TextColumn("ASEGURADORA"),
                "Marca": st.column_config.TextColumn("MARCA"),
                "Modelo": st.column_config.TextColumn("MODELO"),
                "Año": st.column_config.TextColumn("AÑO"),
                "Matricula": st.column_config.TextColumn("MATRICULA"),
                "Cobertura": st.column_config.TextColumn("COBERTURA"),
                "Contado": st.column_config.NumberColumn("CONTADO", format="$ %,d"),
                "Deducible": st.column_config.NumberColumn("DEDUCIBLE", format="$ %,d")
            }
            if propuesta_cliente.get("tipo") != "Flota":
                conf_columnas["10 Cuotas"] = st.column_config.NumberColumn("10 CUOTAS", format="$ %,d")

            # Tabla HTML pura (se imprime correctamente)
            cols_mostrar = [c for c in df_cli.columns if c in ["Aseguradora","Marca","Modelo","Año","Matricula","Cobertura","Contado","10 Cuotas","Deducible"]]
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
                if l.lower().startswith("costo") or l.lower().startswith("- costo") or l.lower().startswith("costo"):
                    partes = l.lstrip("- ").split(":", 1)
                    if len(partes) == 2:
                        out += f'<span style="display:block; margin-top:8px; padding:6px 10px; background:#EFF6FF; border-radius:6px; font-weight:bold; color:#1E3A8A;">💰 {partes[0].strip()}: <span style="color:#111;">{partes[1].strip()}</span></span>'
                    else:
                        out += f'<span style="display:block; margin-top:8px; padding:6px 10px; background:#EFF6FF; border-radius:6px; font-weight:bold; color:#1E3A8A;">💰 <span style="color:#111;">{l.lstrip("- ")}</span></span>'
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
        st.markdown(f"<div style='display:flex; justify-content:space-between; color:gray;'><div><b>Asesor:</b> {propuesta_cliente.get('e_nombre' if propuesta_cliente.get('tipo') == 'Flota' else 'e','EDF')} | <b>Contacto:</b> {propuesta_cliente.get('cont', '')}</div><div><b>Fecha:</b> {propuesta_cliente.get('fecha','')}</div></div>", unsafe_allow_html=True)

        st.stop()
    except Exception as e:
        st.error("Error al cargar la propuesta externa.")
        st.stop()


# ==========================================
# LOGICA DEL INTERFAZ DEL ASESOR (CRM)
# ==========================================
if "historico" not in st.session_state: st.session_state.historico = []
if "edit_data" not in st.session_state: st.session_state.edit_data = {}

st.set_page_config(page_title="EDF SEGUROS", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .ben-fila { background-color: #f8f9fa; padding: 10px 18px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #1E3A8A !important; font-size: 14px; color: #333; }
    .caja-azul { background-color: #ffffff; padding: 18px; border-radius: 12px; height: 100%; border: 1px solid #e0e0e0; border-top: 5px solid #1E3A8A !important; }
    </style>
""", unsafe_allow_html=True)

USUARIOS = {"RDF": "Rockuda.4428", "JOE": "Joe2025", "ANDRE": "Andre2025", "AB": "ABentancor2025", "GR": "GRobaina2025", "ER": "ERobaina.2025", "GS": "GSanchez2025", "MDF": "Matiti2025", "EH": "EHugo2025", "AP": "APerdomo2025", "RS": "RSierra2025", "LT": "LTomasi2025", "EC": "ECabral2025", "PG": "PGagliardi2025"}

CONTACTOS = {
    "RDF": "099236116",
    "JOE": "099595185",
    "ANDRE": "098592816",
    "AB": "098358393",
    "GR": "091339642",
    "ER": "094430277",
    "GS": "094536444",
    "MDF": "095074767",
    "EH": "099513224",
    "AP": "099661587",
    "RS": "092188815",
    "LT": "099816395",
    "EC": "099654708",
    "PG": "091282011"
}

NOMBRES = {
    "RDF": "Roque de Freitas",
    "JOE": "Joel Mokosce",
    "ANDRE": "Andrea Cazarian",
    "AB": "Amelia Bentancor",
    "GR": "Gonzalo Robaina",
    "ER": "Eduardo Robaina",
    "GS": "Grismer Sanchez",
    "MDF": "Matias de Freitas",
    "EH": "Erica Hugo",
    "AP": "Ana Perdomo",
    "RS": "Romina Sierra",
    "LT": "Letizia Tomasi",
    "EC": "Eugenia Cabral",
    "PG": "Pablo Gagliardi"
}

if 'usuario_actual' not in st.session_state: st.session_state['usuario_actual'] = "RDF"

if 'logueado' not in st.session_state or not st.session_state['logueado']:
    st.title("🛡️ EDF SEGUROS")
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
c_asegurado = col_map.get("asegurado (nombre/razon social)", col_map.get("asegurado", col_map.get("cliente", "Asegurado")))
c_documento = col_map.get("documento", col_map.get("ci", col_map.get("rut", "Documento")))
c_aseguradora = col_map.get("aseguradora", col_map.get("compañia", "Aseguradora"))
c_ramo = col_map.get("ramo", "Ramo")
c_p_usd = col_map.get("premio usd (iva inc)", "Premio USD (IVA inc)")
c_p_uyu = col_map.get("premio uyu (iva inc)", "Premio UYU (IVA inc)")
c_adjunto = col_map.get("adjunto (póliza)", col_map.get("adjunto (poliza)", "Adjunto (póliza)"))
c_mail = col_map.get("direccion de correo electronico", col_map.get("mail", col_map.get("email", "Mail")))
c_detalle = col_map.get("detalle", "")

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

tab_car, tab_ven, tab_cot, tab_flota, tab_historial, tab_an = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 VEHICULOS", "🚛 FLOTAS", "📜 HISTORIAL", "📊 ANALISIS"])

# --- PESTAÑA CARTERA ---
with tab_car:
    busq = st.text_input("🔍 Buscar cliente o matricula en cartera...")
    df_c = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f

    if not df_c.empty:
        df_resumen = df_c.copy()
        col_cliente_real = next((col for col in df_resumen.columns if "asegurado" in str(col).lower() or "client" in str(col).lower()), None)
        if col_cliente_real:
            df_resumen = df_resumen.rename(columns={col_cliente_real: "Asegurado"})
        df_resumen = df_resumen.rename(columns={
            c_adjunto: "📄 Póliza",
            c_documento: "Documento",
            c_aseguradora: "Aseguradora",
            c_ramo: "Ramo",
            'Fin de Vigencia': "Vencimiento",
            c_p_usd: "Premio USD",
            c_p_uyu: "Premio UYU",
            'Premio_Total_USD': "Premio Total (USD)"
        })
        columnas_visibles = ["📄 Póliza", "Asegurado", "Documento", "Aseguradora", "Ramo", "Vencimiento", "Premio USD", "Premio UYU", "Premio Total (USD)"]
        cols_validas = [c for c in columnas_visibles if c in df_resumen.columns]
        df_resumen = df_resumen[cols_validas]

        st.markdown("##### 📋 Resumen de Contratos Activos")
        st.markdown("<small style='color:gray;'>💡 Hace un clic en el extremo izquierdo de cualquier fila para ver el detalle abajo</small>", unsafe_allow_html=True)

        tabla_cartera_interactiva = st.dataframe(
            df_resumen, use_container_width=True, hide_index=False,
            on_select="rerun", selection_mode="single-row", key="grid_cartera_unica",
            column_config={
                "📄 Póliza": st.column_config.LinkColumn("📄 Póliza", display_text="📎 Ver PDF", validate="^https://"),
                "Vencimiento": st.column_config.DateColumn("Vencimiento", format="DD/MM/YYYY"),
                "Premio USD": st.column_config.NumberColumn("Premio USD", format="USD %,d"),
                "Premio UYU": st.column_config.NumberColumn("Premio UYU", format="$ %,d"),
                "Premio Total (USD)": st.column_config.NumberColumn("Premio Total (USD)", format="USD %,d")
            }
        )

        selection = st.session_state.get("grid_cartera_unica", {}).get("selection", {})
        filas_seleccionadas = selection.get("rows", [])

        if filas_seleccionadas:
            indice_fila = filas_seleccionadas[0]
            fila_completa = df_c.iloc[indice_fila]
            st.write("")
            with st.container(border=True):
                st.markdown(f"### 🛡️ Detalle de la Poliza: {fila_completa.get(c_asegurado, 'Cliente')}")
                cx1, cx2, cx3 = st.columns(3)
                with cx1:
                    st.markdown("**👤 Datos del Cliente:**")
                    st.write(f"• **Documento:** {fila_completa.get(c_documento, 'N/D')}")
                    st.write(f"• **Celular:** {fila_completa.get('Celular', col_map.get('celular', 'N/D'))}")
                    st.write(f"• **Mail:** {fila_completa.get(c_mail, 'N/D')}")
                with cx2:
                    st.markdown("**🚗 Detalles del Bien:**")
                    st.write(f"• **Ramo:** {fila_completa.get(c_ramo, 'N/D')}")
                    st.write(f"• **Matricula:** {fila_completa.get('Matricula', col_map.get('matricula', 'N/D'))}")
                    st.write(f"• **Marca/Modelo:** {fila_completa.get('Marca/Modelo', col_map.get('marca/modelo', 'N/D'))}")
                with cx3:
                    st.markdown("**📅 Gestion e Intermediacion:**")
                    st.write(f"• **Fin de Vigencia:** {fila_completa.get('Fin de Vigencia', 'N/D')}")
                    st.write(f"• **Ejecutivo:** {fila_completa.get('Ejecutivo', 'N/D')}")
                    st.write(f"• **Corredor/Agente:** {fila_completa.get('Corredor', 'N/D')} / {fila_completa.get('Agente', 'N/D')}")
    else:
        st.info("No se encontraron registros en la cartera.")

# --- PESTAÑA VENCIMIENTOS ---
with tab_ven:
    st.subheader("🔄 Control de Vencimientos")
    if not df_f.empty:
        df_v = df_f.dropna(subset=['Fin de Vigencia'])
        c1, c2 = st.columns(2)
        f_ini, f_fin = c1.date_input("Desde:", date.today().replace(day=1)), c2.date_input("Hasta:", date.today() + timedelta(days=90))
        df_venc_f = df_v[(df_v['Fin de Vigencia'] >= f_ini) & (df_v['Fin de Vigencia'] <= f_fin)].sort_values('Fin de Vigencia')

        if not df_venc_f.empty:
            df_venc_resumen = df_venc_f.copy()
            col_cliente_real_v = next((col for col in df_venc_resumen.columns if "asegurado" in str(col).lower() or "client" in str(col).lower()), None)
            if col_cliente_real_v:
                df_venc_resumen = df_venc_resumen.rename(columns={col_cliente_real_v: "Asegurado"})
            df_venc_resumen = df_venc_resumen.rename(columns={
                c_adjunto: "📄 Póliza",
                c_documento: "Documento",
                c_aseguradora: "Aseguradora",
                c_ramo: "Ramo",
                'Fin de Vigencia': "Vencimiento",
                c_p_usd: "Premio USD",
                c_p_uyu: "Premio UYU",
                'Premio_Total_USD': "Premio Total (USD)"
            })
            columnas_visibles_v = ["📄 Póliza", "Asegurado", "Documento", "Aseguradora", "Ramo", "Vencimiento", "Premio USD", "Premio UYU", "Premio Total (USD)"]
            cols_validas_v = [c for c in columnas_visibles_v if c in df_venc_resumen.columns]
            df_venc_resumen = df_venc_resumen[cols_validas_v]

            st.markdown("<small style='color:gray;'>💡 Hace un clic en el extremo izquierdo de cualquier fila para ver el detalle abajo</small>", unsafe_allow_html=True)

            tabla_venc_interactiva = st.dataframe(
                df_venc_resumen, use_container_width=True, hide_index=False,
                on_select="rerun", selection_mode="single-row", key="grid_venc_unico",
                column_config={
                    "📄 Póliza": st.column_config.LinkColumn("📄 Póliza", display_text="📎 Ver PDF"),
                    "Vencimiento": st.column_config.DateColumn("Vencimiento", format="DD/MM/YYYY"),
                    "Premio USD": st.column_config.NumberColumn("Premio USD", format="USD %,d"),
                    "Premio UYU": st.column_config.NumberColumn("Premio UYU", format="$ %,d"),
                    "Premio Total (USD)": st.column_config.NumberColumn("Premio Total (USD)", format="USD %,d")
                }
            )

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_venc_f.to_excel(writer, index=False, sheet_name='Vencimientos')
            st.markdown("")
            st.download_button(label="📥 Exportar Vencimientos Completos a Excel", data=output.getvalue(), file_name="Vencimientos.xlsx")

            selection_v = st.session_state.get("grid_venc_unico", {}).get("selection", {})
            filas_seleccionadas_v = selection_v.get("rows", [])

            if filas_seleccionadas_v:
                indice_fila_v = filas_seleccionadas_v[0]
                fila_completa_v = df_venc_f.iloc[indice_fila_v]

                st.write("")
                with st.container(border=True):
                    st.markdown(f"### 🛡️ Detalle de la Poliza (Vencimiento): {fila_completa_v.get(c_asegurado, 'Cliente')}")
                    cv1, cv2 = st.columns(2)
                    with cv1:
                        st.markdown("**👤 Datos del Cliente:**")
                        st.write(f"• **Documento:** {fila_completa_v.get(c_documento, 'N/D')}")
                        c_npoliza = col_map.get("n° de póliza", col_map.get("n de poliza", col_map.get("numero de poliza", "")))
                        npoliza_val = limpiar(fila_completa_v.get(c_npoliza, '')) if c_npoliza else 'N/D'
                        st.write(f"• **N° de Póliza:** {npoliza_val or 'N/D'}")
                        st.write(f"• **Mail:** {fila_completa_v.get(c_mail, 'N/D')}")
                    with cv2:
                        st.markdown("**📋 Detalles del Bien:**")
                        st.write(f"• **Ramo:** {fila_completa_v.get(c_ramo, 'N/D')}")
                        st.write(f"• **Matricula:** {fila_completa_v.get('Matricula', col_map.get('matricula', 'N/D'))}")
                        detalle_col2 = next((col for col in fila_completa_v.index if str(col).lower() == 'detalle'), None)
                        detalle_val = limpiar(fila_completa_v.get(detalle_col2, '')) if detalle_col2 else 'N/D'
                        st.write(f"• **Detalle:** {detalle_val or 'N/D'}")

                    # Texto de renovacion
                    nombre_completo = limpiar(fila_completa_v.get(c_asegurado, ''))
                    if not nombre_completo:
                        for col in fila_completa_v.index:
                            if 'asegurado' in str(col).lower() or 'nombre' in str(col).lower():
                                val = limpiar(str(fila_completa_v.get(col, '')))
                                if val:
                                    nombre_completo = val
                                    break
                    nombre_corto = nombre_completo.split()[0].capitalize() if nombre_completo else 'Cliente'
                    mail_cliente = limpiar(fila_completa_v.get(c_mail, ''))
                    premio_uyu = limpiar(str(fila_completa_v.get(c_p_uyu, '')))
                    premio_usd = limpiar(str(fila_completa_v.get(c_p_usd, '')))
                    aseguradora_actual = limpiar(fila_completa_v.get(c_aseguradora, '')) or 'su aseguradora'
                    ramo = limpiar(fila_completa_v.get(c_ramo, '')) or 'bien asegurado'
                    detalle = limpiar(fila_completa_v.get(c_detalle, '')) if c_detalle else ''
                    ramo_completo = f"{ramo} ({detalle})" if detalle else ramo
                    vencimiento = fila_completa_v.get('Fin de Vigencia', '')
                    fecha_fmt = vencimiento.strftime('%d/%m/%Y') if hasattr(vencimiento, 'strftime') else str(vencimiento)
                    nombre_asesor = NOMBRES.get(st.session_state.usuario_actual, st.session_state.usuario_actual)
                    contacto_asesor = CONTACTOS.get(st.session_state.usuario_actual, '')
                    if premio_uyu and str(premio_uyu) not in ['0']:
                        premio_txt = f"UYU {f_num(premio_uyu)}"
                    elif premio_usd and str(premio_usd) not in ['0']:
                        premio_txt = f"USD {f_num(premio_usd)}"
                    else:
                        premio_txt = "a coordinar"

                    with st.expander("💬 Texto renovacion (predeterminado)"):
                        texto_wp = f"""Hola {nombre_corto}!

Te escribo porque esta venciendo la poliza de tu {ramo_completo} el proximo *{fecha_fmt}*.

Este año estabas pagando en *{aseguradora_actual}: {premio_txt}*. El costo de renovación (próxima vigencia) sería: *PRECIO NUEVO*

También sacamos algunos comparativos:

- BSE:
- SBI:
- MAPFRE:
- SURA:

Si queres agregar Auto Sustituto (por 15 dias) en caso de chocar y que tu vehiculo vaya al taller y necesites uno, debemos agregar $3.300 a cualquier aseguradora.

Saludos!
{nombre_asesor}"""
                        st.code(texto_wp, language=None)
        else:
            st.info("No hay vencimientos en el rango seleccionado.")

# ==========================================
# PLANTILLAS DE TEXTOS PRECARGADOS
# ==========================================
txt_ben_veh = "• Auxilio mecanico e ilimitado\n• Cobertura Mercosur\n• Cristales: USD 300 SANCOR, USD 200 BSE O SBI, USD 100 SURA, demas cobran deducible\n• Granizo: SANCOR incluido sin deducible, demas aplican deducible."
txt_hog_veh = "• Incendio Edificio USD 100.000\n• Incendio Contenido 50.000\n• Hurto Contenido 5.000\n• Costo anual Casas: USD 180\n• Costo anual Aptos: USD 120"
txt_alq_veh = "• Auto sustituto por hasta 15 dias en caso de que tu vehiculo sufra un siniestro total o parcial.\n• Costo anual: UYU 3.000 por vehiculo."
txt_bic_veh = "• Cobertura por Hurto y/o Rapina de la bicicleta dentro y fuera del hogar hasta USD 1.000 y Danos a Terceros que puedas provocar hasta USD 10.000.\n• Costo anual: USD 120"

txt_obs_flota = """
Vigencia:
Forma de Pago: redes de cobranza o tarjeta de credito en 10 cuotas sin recargo.
Beneficios
  - Auxilio mecanico ilimitado para toda la flota (Uruguay y paises limitrofes) menos camiones y motos.
  - Cobertura de cristales, cerraduras: SANCOR USD 300, BSE y SBI USD 200, SURA USD 100, demas companias aplican deducible y despues pagan.
  - Cobertura de Granizo: SANCOR lo cubre, demas companias cobran deducible y despues pagan."""

txt_acc_flota = "• Seguro de Vida a causa de Accidentes (para los choferes): USD 25.000 de cobertura.\n• Costo anual: UYU 1.900 por chofer."
txt_alq_flota = "• Auto sustituto por hasta 15 dias en caso de que tu vehiculo sufra un siniestro total o parcial.\n• Costo anual: UYU 3.000 por vehiculo."
txt_bic_flota = "• Si algun empleado de su empresa quiere asegurar la bici electrica o moto. Valor hasta USD 1.000.\n• Cobertura: Danos a Terceros + Hurto + Incendio\n• Costo anual: UYU 5.000"

# ==========================================
# ESTILOS CSS
# ==========================================
st.markdown("""
<style>
div.stButton > button[kind="primary"] {
    background-color: #ff4b4b !important;
    color: white !important;
    border: 2px solid #ff4b4b !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #ff3333 !important;
    border-color: #ff3333 !important;
    color: white !important;
    transform: scale(1.01) !important;
}
div.stButton > button[kind="secondary"] {
    background-color: white !important;
    color: #374151 !important;
    border: 1px solid #d1d5db !important;
    font-weight: normal !important;
    padding: 3px 10px !important;
    font-size: 13px !important;
    border-radius: 6px !important;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: #f3f4f6 !important;
    border-color: #9ca3af !important;
    transform: none !important;
}
.btn-copiar-edf {
    background-color: #1E3A8A !important;
    color: white !important;
    border: none;
    padding: 10px 20px;
    font-weight: bold;
    border-radius: 8px;
    cursor: pointer;
    margin-top: 10px;
    display: inline-block;
}
.btn-copiar-edf:hover {
    background-color: #111827 !important;
}
@media print {
    header, footer, [data-testid="stSidebar"],
    [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], .stDeployButton {
        display: none !important;
    }
    [data-testid="stAppViewContainer"] { padding: 0 !important; margin: 0 !important; }
    [data-testid="stMainBlockContainer"] { max-width: 100% !important; padding: 10px !important; }
    body, p, span, div { font-size: 11px !important; line-height: 1.3 !important; }
    h2 { font-size: 15px !important; }
    h3 { font-size: 13px !important; }
    * { box-shadow: none !important; overflow: visible !important; }
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# PESTANA VEHICULOS (INDIVIDUAL)
# ==========================================
with tab_cot:
    st.subheader("📝 Cotizador Seguros Individuales")
    edit_ind = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Individual" else {}

    if edit_ind:
        st.session_state["ci_v_final"] = edit_ind.get("doc", "")
        st.session_state["nom_v_final"] = edit_ind.get("n", "")
        st.session_state["veh_v_final"] = edit_ind.get("v", "")
        st.session_state["cont_v_final"] = edit_ind.get("cont", "099 635 244")

    with st.container(border=True):
        c_doc, c_nom, c_veh, c_ase, c_con = st.columns([1.5, 2, 2, 1, 2])
        doc_in = c_doc.text_input("CI/RUT", key="ci_v_final")
        n_cot = c_nom.text_input("Nombre", key="nom_v_final")
        v_cot = c_veh.text_input("Vehiculo", key="veh_v_final")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="ase_v_final")
        if not edit_ind:
            st.session_state["cont_v_final"] = CONTACTOS.get(e_cot, "")
        cont_cot = c_con.text_input("Contacto Asesor", key="cont_v_final")

    cols_individual = ["Aseguradora", "Contado", "10 Cuotas", "Deducible"]
    if edit_ind and "tab" in edit_ind:
        df_p_init = pd.DataFrame(edit_ind["tab"])
    else:
        df_p_init = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "SURA", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "MAPFRE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "SANCOR", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}])

    t_edit = st.data_editor(
        df_p_init, num_rows="dynamic", use_container_width=True, column_order=cols_individual, key="editor_individual_completo",
        column_config={
            "Contado": st.column_config.NumberColumn("Contado", format="$ %,d"),
            "10 Cuotas": st.column_config.NumberColumn("10 Cuotas", format="$ %,d"),
            "Deducible": st.column_config.NumberColumn("Deducible", format="$ %,d")
        }
    )

    col_a, col_b = st.columns(2)
    with col_a:
        b_cot = st.text_area("Beneficios:", value=edit_ind.get("ben", txt_ben_veh), height=150, key="ben_v_final")
    with col_b:
        st.markdown("**Coberturas Complementarias**")
        c_h = st.text_area("Hogar:", value=edit_ind.get("ch", txt_hog_veh), height=80, key="ind_hog_v_final")
        c_a = st.text_area("Auto Sustituto / Alquiler:", value=edit_ind.get("ca", txt_alq_veh), height=50, key="ind_alq_v_final")
        c_b = st.text_area("Bici Electrica:", value=edit_ind.get("cb", txt_bic_veh), height=50, key="ind_bic_v_final")

    if st.button("💾 Guardar propuesta y Generar Link", type="primary", use_container_width=True, key="save_ind_btn"):
        datos_i = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": n_cot, "v": v_cot, "e": e_cot, "cont": cont_cot, "doc": doc_in, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b, "tipo": "Individual"}
        st.session_state.historico.append(datos_i)
        st.session_state.edit_data = datos_i
        datos_b64 = base64.b64encode(json.dumps(datos_i).encode()).decode()
        link_cliente = f"https://dfseguros.streamlit.app/?q={datos_b64}"
        st.success("✅ Propuesta guardada con exito en el Historial!")
        st.text_input("🔗 Enlace para mandar al cliente por WhatsApp:", value=link_cliente)
        componente_copiar_html = f"""
        <button class="btn-copiar-edf" onclick="navigator.clipboard.writeText('{link_cliente}').then(() => {{ this.innerText = '📋 Link Copiado!'; }}).catch(err => {{ alert('Error al copiar'); }})">📋 Copiar Link de Vehiculo</button>
        """
        st.components.v1.html(componente_copiar_html, height=60)


# ==========================================
# PESTANA FLOTAS (CORPORATIVO)
# ==========================================
with tab_flota:
    st.subheader("🚛 Cotizador Seguro de Flotas")
    edit_f = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Flota" else {}

    if edit_f:
        st.session_state["f_nom_fl"] = edit_f.get("n", "")
        st.session_state["f_cia_fl"] = edit_f.get("e", "SBI")
        st.session_state["f_as_fl"] = edit_f.get("e_nombre", "EDF SEGUROS")
        st.session_state["f_co_fl"] = edit_f.get("cont", "099 635 244")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_asegurado = st.text_input("Asegurado", key="f_nom_fl")
        f_cia_elegida = st.text_input("Compania Aseguradora", key="f_cia_fl")
    with col_f2:
        f_asesor_nombre = st.text_input("Asesor", key="f_as_fl")
        if not edit_f:
            st.session_state["f_co_fl"] = CONTACTOS.get(st.session_state.get("f_as_fl", ""), "")
        f_contacto = st.text_input("Contacto", key="f_co_fl")

    cols_f = ["Marca", "Modelo", "Año", "Matricula", "Cobertura", "Contado", "Deducible"]
    if edit_f and "tab" in edit_f:
        df_f_init = pd.DataFrame(edit_f["tab"])
    else:
        df_f_init = pd.DataFrame([{"Marca": "", "Modelo": "", "Año": "", "Matricula": "", "Cobertura": "Todo Riesgo", "Contado": 0, "Deducible": 0}])

    t_flota = st.data_editor(
        df_f_init, num_rows="dynamic", use_container_width=True, column_order=cols_f, key="editor_flotas",
        column_config={
            "Contado": st.column_config.NumberColumn("Contado", format="$ %,d"),
            "Deducible": st.column_config.NumberColumn("Deducible", format="$ %,d")
        }
    )

    col_f_a, col_f_b = st.columns(2)
    with col_f_a:
        f_obs = st.text_area("Observaciones / Comentarios:", value=edit_f.get('ben', txt_obs_flota), height=320, key="f_obs_fl")
    with col_f_b:
        st.markdown("**Coberturas Complementarias para la Flota**")
        f_ch = st.text_area("Accidentes Personales:", value=edit_f.get("ch", txt_acc_flota), height=80, key="flota_hog_v_final")
        f_ca = st.text_area("Auto Sustituto / Alquiler:", value=edit_f.get("ca", txt_alq_flota), height=50, key="flota_alq_v_final")
        f_cb = st.text_area("Bici Electrica o Moto (Movilidad):", value=edit_f.get("cb", txt_bic_flota), height=50, key="flota_bic_v_final")

    if st.button("💾 Guardar propuesta de Flota y Generar Link", key="btn_save_fl", use_container_width=True):
        nueva_f = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": f_asegurado, "e": f_cia_elegida, "e_nombre": f_asesor_nombre, "cont": f_contacto, "tab": t_flota.to_dict(orient='records'), "ben": f_obs, "ch": f_ch, "ca": f_ca, "cb": f_cb, "tipo": "Flota"}
        st.session_state.historico.append(nueva_f)
        st.session_state.edit_data = nueva_f
        datos_b64 = base64.b64encode(json.dumps(nueva_f).encode()).decode()
        link_flota = f"https://dfseguros.streamlit.app/?q={datos_b64}"
        st.success("✅ Propuesta de Flota guardada con exito!")
        st.text_input("🔗 Enlace para mandar al cliente de Flotas:", value=link_flota)
        componente_copiar_flota_html = f"""
        <button class="btn-copiar-edf" onclick="navigator.clipboard.writeText('{link_flota}').then(() => {{ this.innerText = '📋 Link Copiado!'; }}).catch(err => {{ alert('Error al copiar'); }})">📋 Copiar Link de Flota</button>
        """
        st.components.v1.html(componente_copiar_flota_html, height=60)


# ==========================================
# PESTANA HISTORIAL
# ==========================================
with tab_historial:
    st.subheader("📜 Historial de Propuestas Guardadas")
    if st.session_state.historico:
        for i, reg in enumerate(reversed(st.session_state.historico)):
            idx_real = len(st.session_state.historico) - 1 - i
            col_info, col_edit, col_del = st.columns([0.7, 0.15, 0.15])
            with col_info:
                icon = "🚚" if reg.get("tipo") == "Flota" else "🚗"
                st.write(f"📅 **{reg.get('fecha', '')[:10]}** | {icon} {reg.get('tipo')} | **{reg.get('n', 'Cliente')}**")
            with col_edit:
                if st.button("✏️ Cargar/Editar", key=f"edit_{idx_real}"):
                    st.session_state.edit_data = reg
                    st.success("Cargada.")
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_{idx_real}"):
                    st.session_state.historico.pop(idx_real)
                    st.rerun()
    else:
        st.info("No hay propuestas en el historial temporal todavia.")


# ==========================================
# PESTANA ANALISIS
# ==========================================
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
