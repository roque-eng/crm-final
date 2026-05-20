import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
from datetime import date, datetime, timedelta
import io
import json
import base64

# ==========================================
# ⚙️ CONFIGURACIÓN GLOBAL Y ENLACES
# ==========================================
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xyzaQncW_4XcjV5hcrc41YGFUst5068tYglGTAQZ2AA/edit#gid=860430337"
TC_USD = 40.5

# FUNCIÓN COMODÍN PARA LIMPIAR Y FORMATEAR NÚMEROS EN LA VISTA
def f_num(val):
    try: return f"{int(float(str(val).replace('$', '').replace('USD', '').replace('.', '').replace(',', '').strip())):,}".replace(",", ".")
    except: return str(val)

# ==========================================
# ⚙️ DETECCIÓN DEL LINK EXTERNO (CLIENTE)
# ==========================================
query_params = st.query_params

# Si en la URL viene el parámetro "?q=", significa que entró un CLIENTE desde el link externo
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
            <p style="margin: 0; font-size: 16px; color: #555; text-align: left !important;"><b>{"Aseguradora" if propuesta_cliente.get("tipo") == "Flota" else "Vehículo"}:</b> {propuesta_cliente.get('v' if propuesta_cliente.get('tipo') != 'Flota' else 'e', 'Detalle')}</p>
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
                "Matrícula": st.column_config.TextColumn("MATRÍCULA"),
                "Cobertura": st.column_config.TextColumn("COBERTURA"),
                "Contado": st.column_config.NumberColumn("CONTADO", format="$ %,d"),
                "Deducible": st.column_config.NumberColumn("DEDUCIBLE", format="$ %,d")
            }
            if propuesta_cliente.get("tipo") != "Flota":
                conf_columnas["10 Cuotas"] = st.column_config.NumberColumn("10 CUOTAS", format="$ %,d")

            st.dataframe(df_cli, use_container_width=True, hide_index=True, column_config=conf_columnas)
            
        if propuesta_cliente.get("ben"):
            st.write("")
            st.markdown(f"### {'✅ Beneficios Incluidos' if propuesta_cliente.get('tipo') != 'Flota' else '📋 Observaciones y Comentarios'}")
            for b in propuesta_cliente.get("ben", "").split('\n'):
                if b.strip(): st.markdown(f'<div class="ben-fila">{b.strip()}</div>', unsafe_allow_html=True)
                
        st.write("")
        st.markdown("### ⚠️ Coberturas Complementarias")
        cx1, cx2, cx3 = st.columns(3)
        def b_html_cli(tit, ico, txt):
            if not txt: return ""
            out = f'<div class="caja-azul"><span style="font-weight:bold; color:#1E3A8A;">{ico} {tit}</span><br>'
            for l in txt.split('\n'): out += f'<span style="display:block; margin-top:3px;">{l.strip()}</span>'
            return out + '</div>'
            
        cx1.markdown(b_html_cli("Hogar", "🏠", propuesta_cliente.get("ch", "")), unsafe_allow_html=True)
        cx2.markdown(b_html_cli("Alquiler / Auto Sust.", "🚗", propuesta_cliente.get("ca", "")), unsafe_allow_html=True)
        cx3.markdown(b_html_cli("Bici", "🚲", propuesta_cliente.get("cb", "")), unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown(f"<div style='display:flex; justify-content:space-between; color:gray;'><div><b>Asesor:</b> {propuesta_cliente.get('e_nombre' if propuesta_cliente.get('tipo') == 'Flota' else 'e','EDF')} | <b>Contacto:</b> {propuesta_cliente.get('cont', '')}</div><div><b>Fecha:</b> {propuesta_cliente.get('fecha','')}</div></div>", unsafe_allow_html=True)
        
        st.stop()
    except Exception as e:
        st.error("Error al cargar la propuesta externa.")
        st.stop()


# ==========================================
# 🏢 LÓGICA DEL INTERFAZ DEL ASESOR (CRM CONTRASEÑA)
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
if 'usuario_actual' not in st.session_state: st.session_state['usuario_actual'] = "RDF"

if 'logueado' not in st.session_state or not st.session_state['logueado']:
    st.title("🛡️ EDF SEGUROS")
    u_sel = st.selectbox("Seleccione su Usuario:", list(USUARIOS.keys()))
    p_in = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar", type="primary"):
        if USUARIOS.get(u_sel) == p_in:
            st.session_state['logueado'] = True
            st.session_state['usuario_actual'] = u_sel
            st.rerun()
        else: st.error("Contraseña incorrecta.")
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(spreadsheet=URL_HOJA, ttl=0)
df_raw.columns = df_raw.columns.str.strip()

# Mapeo dinámico e inteligente de columnas para evitar KeyErrors si cambian las mayúsculas en Sheets
col_map = {c.lower(): c for c in df_raw.columns}
c_asegurado = col_map.get("asegurado", col_map.get("cliente", "Asegurado"))
c_documento = col_map.get("documento", col_map.get("ci", col_map.get("rut", "Documento")))
c_aseguradora = col_map.get("aseguradora", col_map.get("compañia", "Aseguradora"))
c_ramo = col_map.get("ramo", "Ramo")
c_p_usd = col_map.get("premio usd (iva inc)", "Premio USD (IVA inc)")
c_p_uyu = col_map.get("premio uyu (iva inc)", "Premio UYU (IVA inc)")
c_adjunto = col_map.get("adjunto (póliza)", col_map.get("adjunto (poliza)", "Adjunto (póliza)"))

df_raw['Premio_Total_USD'] = (pd.to_numeric(df_raw.get(c_p_usd, 0), errors='coerce').fillna(0) + (pd.to_numeric(df_raw.get(c_p_uyu, 0), errors='coerce').fillna(0) / TC_USD)).round(0)
df_raw['Fin de Vigencia'] = pd.to_datetime(df_raw.get('Fin de Vigencia', date.today()), dayfirst=True, errors='coerce').dt.date

with st.sidebar:
    st.title(f"👤 {USUARIOS.get(st.session_state.usuario_actual, 'Asesor')}")
    def get_list(col): return ["Todos"] + sorted(df_raw[col].dropna().unique().tolist()) if col in df_raw.columns else ["Todos"]
    f_ej = st.selectbox("Ejecutivo", get_list('Ejecutivo'))
    f_as = st.selectbox("Aseguradora", get_list(c_aseguradora))
    f_ra = st.selectbox("Ramo", get_list(c_ramo))
    f_co = st.selectbox("Corredor", get_list('Corredor'))
    f_ag = st.selectbox("Agente", get_list('Agente'))
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

df_f = df_raw.copy()
if f_ej != "Todos" and 'Ejecutivo' in df_f.columns: df_f = df_f[df_f['Ejecutivo'] == f_ej]
if f_as != "Todos": df_f = df_f[df_f[c_aseguradora] == f_as]
if f_ra != "Todos": df_f = df_f[df_f[c_ramo] == f_ra]
if f_co != "Todos" and 'Corredor' in df_f.columns: df_f = df_f[df_f['Corredor'] == f_co]
if f_ag != "Todos" and 'Agente' in df_f.columns: df_f = df_f[df_f['Agente'] == f_ag]

tab_car, tab_ven, tab_cot, tab_flota, tab_historial, tab_an = st.tabs(["👥 CARTERA", "🔄 VENCIMIENTOS", "📝 VEHÍCULOS", "🚛 FLOTAS", "📜 HISTORIAL", "📊 ANÁLISIS"])

# --- PESTAÑA CARTERA ---
with tab_car:
    busq = st.text_input("🔍 Buscar cliente o matrícula en cartera...")
    df_c = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busq, case=False)).any(axis=1)] if busq else df_f
    
    if not df_c.empty:
        # 1. Copia limpia de los datos
        df_resumen = df_c.copy()
        
        # 2. DETECTOR EXACTO: Buscamos la columna por su nombre real o variantes comunes
        col_cliente_real = next((col for col in df_resumen.columns if "asegurado" in str(col).lower() or "client" in str(col).lower()), None)
        if col_cliente_real:
            df_resumen = df_resumen.rename(columns={col_cliente_real: "Asegurado"})
        
        # 3. Renombramos el resto de las columnas críticas
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
        
        # 4. Forzamos el orden visual estricto en la pantalla
        columnas_visibles = ["📄 Póliza", "Asegurado", "Documento", "Aseguradora", "Ramo", "Vencimiento", "Premio USD", "Premio UYU", "Premio Total (USD)"]
        cols_validas = [c for c in columnas_visibles if c in df_resumen.columns]
        df_resumen = df_resumen[cols_validas]
        
        st.markdown("##### 📋 Resumen de Contratos Activos")
        st.markdown("<small style='color:gray;'>💡 Hacé un clic en el extremo izquierdo de cualquier fila para ver el detalle abajo</small>", unsafe_allow_html=True)
        
        # 5. Renderizado de la tabla
        tabla_cartera_interactiva = st.dataframe(
            df_resumen, use_container_width=True, hide_index=False,
            on_select="rerun", selection_mode="single-row", key="grid_cartera_unica",
            column_config={
                "📄 Póliza": st.column_config.LinkColumn("📄 Póliza", display_text="📎 Ver PDF"),
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
                st.markdown(f"### 🛡️ Detalle de la Póliza: {fila_completa.get(c_asegurado, 'Cliente')}")
                cx1, cx2, cx3 = st.columns(3)
                with cx1:
                    st.markdown("**👤 Datos del Cliente:**")
                    st.write(f"• **Documento:** {fila_completa.get(c_documento, 'N/D')}")
                    st.write(f"• **Celular:** {fila_completa.get('Celular', col_map.get('celular', 'N/D'))}")
                    st.write(f"• **Mail:** {fila_completa.get('Mail', col_map.get('mail', 'N/D'))}")
                with cx2:
                    st.markdown("**🚗 Detalles del Bien:**")
                    st.write(f"• **Ramo:** {fila_completa.get(c_ramo, 'N/D')}")
                    st.write(f"• **Matrícula:** {fila_completa.get('Matricula', col_map.get('matrícula', 'N/D'))}")
                    st.write(f"• **Marca/Modelo:** {fila_completa.get('Marca/Modelo', col_map.get('marca/modelo', 'N/D'))}")
                with cx3:
                    st.markdown("**📅 Gestión e Intermediación:**")
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
            
            # DETECTOR EXACTO para Vencimientos
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
            
            st.markdown("<small style='color:gray;'>💡 Hacé un clic en el extremo izquierdo de cualquier fila para ver el detalle abajo</small>", unsafe_allow_html=True)
            
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
            st.download_button(label="📥 Exportar Vencimientos Completos a Excel", data=output.getvalue(), file_name=f"Vencimientos.xlsx")
            
            selection_v = st.session_state.get("grid_venc_unico", {}).get("selection", {})
            filas_seleccionadas_v = selection_v.get("rows", [])
            
            if filas_seleccionadas_v:
                indice_fila_v = filas_seleccionadas_v[0]
                fila_completa_v = df_venc_f.iloc[indice_fila_v]
                
                st.write("")
                with st.container(border=True):
                    st.markdown(f"### 🛡️ Detalle de la Póliza (Vencimiento): {fila_completa_v.get(c_asegurado, 'Cliente')}")
                    cv1, cv2, cv3 = st.columns(3)
                    with cv1:
                        st.markdown("**👤 Datos del Cliente:**")
                        st.write(f"• **Documento:** {fila_completa_v.get(c_documento, 'N/D')}")
                        st.write(f"• **Cell:** {fila_completa_v.get('Celular', col_map.get('celular', 'N/D'))}")
                        st.write(f"• **Mail:** {fila_completa_v.get('Mail', col_map.get('mail', 'N/D'))}")
                    with cv2:
                        st.markdown("**🚗 Detalles del Bien:**")
                        st.write(f"• **Ramo:** {fila_completa_v.get(c_ramo, 'N/D')}")
                        st.write(f"• **Matrícula:** {fila_completa_v.get('Matricula', col_map.get('matrícula', 'N/D'))}")
                        st.write(f"• **Marca/Modelo:** {fila_completa_v.get('Marca/Modelo', col_map.get('marca/modelo', 'N/D'))}")
                    with cv3:
                        st.markdown("**📅 Gestión de Vigencia:**")
                        st.write(f"• **Fin de Vigencia:** {fila_completa_v.get('Fin de Vigencia', 'N/D')}")
                        st.write(f"• **Ejecutivo:** {fila_completa_v.get('Ejecutivo', 'N/D')}")
                        st.write(f"• **Corredor/Agente:** {fila_completa_v.get('Corredor', 'N/D')} / {fila_completa_v.get('Agente', 'N/D')}")
        else:
            st.info("No hay vencimientos en el rango seleccionado.")

# ==========================================
# 📋 PLANTILLAS DE TEXTOS PRECARGADOS (SEPARADOS)
# ==========================================

# --- PLANTILLAS EXCLUSIVAS PARA VEHÍCULOS ---
txt_ben_veh = "• Auxilio mecánico e ilimitado\n• Cobertura Mercosur\n• Cristales, cerraduras y espejos sin límite de eventos ni deducible\n• Gestión de siniestros"
txt_hog_veh = "• Incendio Edificio e Incendio Contenido 40.000\n• Hurto Contenido 10.000\n• Costo ANUAL: 95 IVA INC"
txt_alq_veh = "• Auto sustituto por hasta 15 días en caso de que tu vehículo sufra un siniestro total o parcial.\n• Costo: UYU 3.000 (IVA incluido) por vehículo."
txt_bic_veh = "• Cobertura por Hurto y/o Rapiña de la bicicleta dentro y fuera del hogar hasta USD 1.000 y Daños a Terceros que puedas provocar hasta USD 10.000\n• Costo ANUAL: 120 IVA INC"

# --- PLANTILLAS EXCLUSIVAS PARA FLOTAS ---
txt_obs_flota = """
• **Vigencia:** 
• **Forma de Pago:** redes de cobranza o tarjeta de crédito en 10 cuotas sin recargo.
• **Condiciones Especiales de Contratación:**
  - Auxilio mecánico ilimitado para toda la flota (Uruguay y países limítrofes) menos camiones y motos (camiones: todos los que digan "camión" en la libreta de propiedad).
  - Cobertura de cristales, cerraduras: SANCOR USD 300, BSE Y SBI USD 200, SURA USD 100, demás compañías aplican deducible y después pagan.
  - Cobertura de Granizo: SANCOR lo cubre, demás compañías cobran deducible y después pagan.

txt_acc_flota = "• Seguro de Vida a causa de Accidentes (para los choferes): USD 25.000 de cobertura.\n• Costo Anual USD 50 (IVA incluido) por chofer."
txt_alq_flota = "• Auto sustituto por hasta 15 días en caso de que tu vehículo sufra un siniestro total o parcial.\n• Costo: UYU 3.000 (IVA incluido) por vehículo."
txt_bic_flota = "• Si algún empleado de su empresa quiere asegurar la bici eléctrica o moto. Valor hasta USD 1.000.\n• Cobertura: Daños a Terceros + Hurto + Incendio\n• Costo Anual: UYU 6.000"


# ==========================================
# 🎨 ESTILOS CSS (BOTONES ROJOS DE ALTA VISIBILIDAD)
# ==========================================
st.markdown("""
    <style>
    /* Forzamos el color rojo en los botones principales de generación de link */
    div.stButton > button {
        background-color: #ff4b4b !important;
        color: white !important;
        border: 2px solid #ff4b4b !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background-color: #ff3333 !important;
        border-color: #ff3333 !important;
        color: white !important;
        transform: scale(1.01);
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 📝 PESTAÑA VEHÍCULOS (INDIVIDUAL)
# ==========================================
with tab_cot:
    st.subheader("📝 Cotizador Seguros Individuales")
    edit_ind = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Individual" else {}
    
    with st.container(border=True):
        c_doc, c_nom, c_veh, c_ase, c_con = st.columns([1.5, 2, 2, 1, 2])
        doc_in = c_doc.text_input("CI/RUT", value=edit_ind.get("doc", ""), key="ci_v_final")
        n_cot = c_nom.text_input("Nombre", value=edit_ind.get('n', ''), key="nom_v_final")
        v_cot = c_veh.text_input("Vehículo", value=edit_ind.get("v", ""), key="veh_v_final")
        e_cot = c_ase.selectbox("Asesor", sorted(list(USUARIOS.keys())), key="ase_v_final")
        cont_cot = c_con.text_input("Contacto Asesor", value=edit_ind.get("cont", "099 635 244"), key="cont_v_final")

    cols_individual = ["Aseguradora", "Contado", "10 Cuotas", "Deducible"]
    if edit_ind and "tab" in edit_ind: df_p_init = pd.DataFrame(edit_ind["tab"])
    else: df_p_init = pd.DataFrame([{"Aseguradora": "BSE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "SURA", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "MAPFRE", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}, {"Aseguradora": "SANCOR", "Contado": 0, "10 Cuotas": 0, "Deducible": 0}])
    
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
        c_b = st.text_area("Bici Eléctrica:", value=edit_ind.get("cb", txt_bic_veh), height=50, key="ind_bic_v_final")

    if st.button("💾 Guardar propuesta y Generar Link", type="primary", use_container_width=True, key="save_ind_btn"):
        datos_i = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": n_cot, "v": v_cot, "e": e_cot, "cont": cont_cot, "doc": doc_in, "tab": t_edit.to_dict(orient='records'), "ben": b_cot, "ch": c_h, "ca": c_a, "cb": c_b, "tipo": "Individual"}
        st.session_state.historico.append(datos_i)
        st.session_state.edit_data = datos_i
        
        datos_b64 = base64.b64encode(json.dumps(datos_i).encode()).decode()
        link_cliente = f"https://dfseguros.streamlit.app/?q={datos_b64}"
        st.success("✅ ¡Propuesta guardada con éxito en el Historial!")
        st.text_input("🔗 Copiá este Link y enviáselo al cliente por WhatsApp:", value=link_cliente, read_only=True)
        st.copy_to_clipboard(link_cliente, before_text="📋 Copiar Link de Vehículo", after_text="✨ ¡Link de Vehículo Copiado!")


# ==========================================
# 🚛 PESTAÑA FLOTAS (CORPORATIVO)
# ==========================================
with tab_flota:
    st.subheader("🚛 Cotizador Seguro de Flotas")
    edit_f = st.session_state.edit_data if st.session_state.edit_data and st.session_state.edit_data.get("tipo") == "Flota" else {}
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_asegurado = st.text_input("Asegurado", value=edit_f.get('n', ''), key="f_nom_fl")
        f_cia_elegida = st.text_input("Compañía Aseguradora", value=edit_f.get('e', 'SBI'), key="f_cia_fl")
    with col_f2:
        f_asesor_nombre = st.text_input("Asesor", value=edit_f.get('e_nombre', 'EDF SEGUROS'), key="f_as_fl")
        f_contacto = st.text_input("Contacto", value=edit_f.get('cont', '099 635 244'), key="f_co_fl")

    cols_f = ["Marca", "Modelo", "Año", "Matrícula", "Cobertura", "Contado", "Deducible"]
    if edit_f and "tab" in edit_f: df_f_init = pd.DataFrame(edit_f["tab"])
    else: df_f_init = pd.DataFrame([{"Marca": "", "Modelo": "", "Año": "", "Matrícula": "", "Cobertura": "Todo Riesgo", "Contado": 0, "Deducible": 0}])
    
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
        f_cb = st.text_area("Bici Eléctrica o Moto (Movilidad):", value=edit_f.get("cb", txt_bic_flota), height=50, key="flota_bic_v_final")

    if st.button("💾 Guardar propuesta de Flota y Generar Link", key="btn_save_fl", use_container_width=True):
        nueva_f = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "n": f_asegurado, "e": f_cia_elegida, "e_nombre": f_asesor_nombre, "cont": f_contacto, "tab": t_flota.to_dict(orient='records'), "ben": f_obs, "ch": f_ch, "ca": f_ca, "cb": f_cb, "tipo": "Flota"}
        st.session_state.historico.append(nueva_f)
        st.session_state.edit_data = nueva_f
        
        datos_b64 = base64.b64encode(json.dumps(nueva_f).encode()).decode()
        link_flota = f"https://dfseguros.streamlit.app/?q={datos_b64}"
        st.success("✅ ¡Propuesta de Flota guardada con éxito!")
        st.text_input("🔗 Enlace para mandar al cliente de Flotas:", value=link_flota, read_only=True)
        st.copy_to_clipboard(link_flota, before_text="📋 Copiar Link de Flota", after_text="✨ ¡Link de Flota Copiado!")


# ==========================================
# 📜 PESTAÑA HISTORIAL
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
        st.info("No hay propuestas en el historial temporal todavía.")


# ==========================================
# 📊 PESTAÑA ANÁLISIS
# ==========================================
with tab_an:
    st.subheader("📊 Análisis de Cartera")
    if not df_f.empty:
        t_usd = df_f['Premio_Total_USD'].sum()
        k1, k2 = st.columns(2)
        k1.metric("Cartera Total (USD)", f"USD {t_usd:,.0f}")
        k2.metric("Total de Pólizas", f"{len(df_f)}")
        c1, c2 = st.columns(2)
        with c1: 
            st.plotly_chart(px.pie(df_f, names=c_aseguradora, values='Premio_Total_USD', title="Compañía", hole=0.4), use_container_width=True)
        with c2: 
            st.plotly_chart(px.pie(df_f, names=c_ramo, values='Premio_Total_USD', title="Ramo", hole=0.4), use_container_width=True)
