import streamlit as st
import pandas as pd
import os
import time

# ==========================================
# 1. CONFIGURACIÓN VISUAL Y CSS
# ==========================================
st.set_page_config(page_title="Gestión de Cartera - EDF", layout="wide")

st.markdown("""
    <style>
        /* 1. Zoom general al 90% */
        div[data-testid="stAppViewContainer"] {
            zoom: 0.90;
        }
        div[data-testid="stSidebar"] {
            zoom: 0.90;
        }

        /* 2. Achicar el Título Principal (H1) */
        h1 {
            font-size: 1.8rem !important; /* Más pequeño */
            padding-top: 0rem !important;
            margin-bottom: 0rem !important;
        }

        /* 3. Ajustar espacio superior para que el logo y título queden pegados arriba */
        .block-container {
            padding-top: 2rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURACIÓN DE ARCHIVOS
# ==========================================
ARCHIVO_EXCEL = "datos.xlsx"   # Asegúrate de que este archivo esté en la carpeta
CARPETA_PDFS = "pdfs"          # Carpeta para guardar pdfs

# Asegurarse que la carpeta de PDFs exista
if not os.path.exists(CARPETA_PDFS):
    os.makedirs(CARPETA_PDFS)

# Nombres exactos de tus columnas (basado en tu foto anterior)
COL_ID = "Matrícula / Dato Referencia / Sub categoría de producto"
COL_PDF = "Adjunto (póliza)"
COL_EJECUTIVO = "Ejecutivo"
COL_CORREDOR = "Corredor"

# ==========================================
# 3. FUNCIONES DE CARGA Y GUARDADO
# ==========================================
def cargar_datos():
    try:
        df = pd.read_excel(ARCHIVO_EXCEL)
        # Convertimos a string para evitar errores
        df[COL_EJECUTIVO] = df[COL_EJECUTIVO].astype(str)
        df[COL_CORREDOR] = df[COL_CORREDOR].astype(str)
        
        if COL_PDF not in df.columns:
            df[COL_PDF] = ""
        else:
            df[COL_PDF] = df[COL_PDF].fillna("").astype(str)
            
        return df
    except Exception as e:
        st.error(f"⚠️ No encontré el archivo '{ARCHIVO_EXCEL}' en la carpeta.")
        return pd.DataFrame()

def guardar_excel(df):
    df.to_excel(ARCHIVO_EXCEL, index=False)

# ==========================================
# 4. INTERFAZ PRINCIPAL
# ==========================================
def main():
    
    # --- ENCABEZADO (LOGO + TÍTULO ACHICADO) ---
    col_logo, col_titulo = st.columns([1, 6])
    
    with col_logo:
        # AQUÍ VA TU LOGO. Si tienes el archivo 'logo.png' ponlo en la carpeta
        # Si no tienes imagen, comenta esta línea. 'width=120' lo hace pequeño.
        try:
            st.image("logo.png", width=120) 
        except:
            st.write("📷 (Logo)") # Texto si no hay imagen

    with col_titulo:
        # Usamos markdown para un título más controlado y alineado verticalmente
        st.markdown("# Gestión de Cartera - Grupo EDF")

    # Separador sutil
    st.markdown("---")

    # --- CARGA DE DATOS ---
    df = cargar_datos()
    if df.empty:
        st.stop()

    # --- BOTÓN DE ALTA (OCULTO EN EXPANDER) ---
    # Aquí escondemos el botón rojo dentro del menú desplegable
    with st.expander("➕ ALTA DE NUEVO CLIENTE (Abrir Formulario)"):
        st.info("💡 Para ingresar un nuevo cliente, utilice el formulario oficial. Los datos se sincronizarán automáticamente.")
        
        # Usamos columnas para que el botón no ocupe todo el ancho (Alineado a la Izquierda)
        c_btn, c_vacia = st.columns([1, 4]) 
        with c_btn:
            # Pon aquí el link real de tu Google Form
            LINK_FORMULARIO = "https://docs.google.com/forms/d/e/TU_ID_DE_FORMULARIO/viewform"
            st.link_button("🚀 Abrir Formulario", LINK_FORMULARIO, type="primary")

    # --- FILTROS ---
    st.subheader("🔍 Buscador de Pólizas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        lista_ejec = ["Todos"] + sorted(list(set(df[COL_EJECUTIVO])))
        filtro_ejecutivo = st.selectbox("Ejecutivo", lista_ejec)

    with col2:
        lista_corr = ["Todos"] + sorted(list(set(df[COL_CORREDOR])))
        filtro_corredor = st.selectbox("Corredor", lista_corr)

    with col3:
        estado_opciones = ["Todos", "Falta PDF", "Con PDF"]
        filtro_estado = st.selectbox("Estado Documentación", estado_opciones)

    with col4:
        busqueda = st.text_input("Buscar (Matrícula, Cliente...)")

    # --- LÓGICA DE FILTRADO ---
    df_filtrado = df.copy()

    if filtro_ejecutivo != "Todos":
        df_filtrado = df_filtrado[df_filtrado[COL_EJECUTIVO] == filtro_ejecutivo]

    if filtro_corredor != "Todos":
        df_filtrado = df_filtrado[df_filtrado[COL_CORREDOR] == filtro_corredor]

    if filtro_estado == "Falta PDF":
        df_filtrado = df_filtrado[df_filtrado[COL_PDF] == ""]
    elif filtro_estado == "Con PDF":
        df_filtrado = df_filtrado[df_filtrado[COL_PDF] != ""]
    
    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        ]

    # --- MOSTRAR TABLA ---
    st.write(f"Mostrando **{len(df_filtrado)}** registros.")
    
    # Seleccionamos columnas visuales
    cols_posibles = [COL_ID, "Inicio de Vigencia", COL_EJECUTIVO, COL_CORREDOR, COL_PDF]
    cols_finales = [c for c in cols_posibles if c in df_filtrado.columns]

    st.dataframe(df_filtrado[cols_finales], use_container_width=True, hide_index=True)

    # --- SECCIÓN CARGA DE PDF ---
    st.markdown("---")
    st.subheader("📎 Vincular PDF a Póliza")

    c1, c2 = st.columns([1, 1])

    with c1:
        if COL_ID in df_filtrado.columns:
            opciones = df_filtrado[COL_ID].astype(str).tolist()
            seleccion = st.selectbox("Seleccione Matrícula para adjuntar:", opciones)
        else:
            seleccion = None

    with c2:
        archivo = st.file_uploader("Subir PDF", type=['pdf'])

    if st.button("💾 Guardar y Actualizar", type="primary"):
        if archivo and seleccion:
            # Guardamos el archivo
            nombre_archivo = f"{seleccion}_{archivo.name}"
            ruta_completa = os.path.join(CARPETA_PDFS, nombre_archivo)
            
            with open(ruta_completa, "wb") as f:
                f.write(archivo.getbuffer())
            
            # Actualizamos Excel
            indice = df[df[COL_ID].astype(str) == str(seleccion)].index
            
            if not indice.empty:
                # Escribimos 'OK' o la ruta
                df.loc[indice, COL_PDF] = "✅ PDF Cargado" # O puedes poner ruta_completa
                guardar_excel(df)
                
                st.success(f"¡Listo! PDF vinculado a {seleccion}.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Error al localizar la póliza en la base de datos.")
        else:
            st.warning("⚠️ Faltan datos (Selección o Archivo).")

if __name__ == "__main__":
    main()