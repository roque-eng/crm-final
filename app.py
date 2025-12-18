import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Cartera - EDF", layout="wide")

# ==========================================
# 1. CONFIGURACIÓN EXACTA DE TUS COLUMNAS
# ==========================================
# IMPORTANTE: Copia el nombre EXACTO de la celda J1 de tu Excel aquí abajo
COLUMNA_ID_POLIZA = "Matrícula / Dato Referencia / Sub categoría de producto" 
# (Si el nombre en tu excel es más largo, pégalo tal cual arriba entre las comillas)

COLUMNA_PDF = "Adjunto (póliza)"
COLUMNA_EJECUTIVO = "Ejecutivo"
COLUMNA_ASEGURADORA = "Aseguradora" # (Asegúrate que esta columna exista, si no, avísame)
NOMBRE_HOJA_CALCULO = "Clientes DEF Seguros"
NOMBRE_PESTANA = "Respuestas de formulario 2"

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def conectar_google_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Recuerda tener tu archivo 'credentials.json' en la misma carpeta
    credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    gc = gspread.authorize(credentials)
    return gc

# --- CARGA DE DATOS ---
def cargar_datos(gc):
    try:
        sh = gc.open(NOMBRE_HOJA_CALCULO)
        worksheet = sh.worksheet(NOMBRE_PESTANA)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df, worksheet
    except Exception as e:
        st.error(f"Error cargando el Excel. Verifica el nombre: {e}")
        return pd.DataFrame(), None

# --- FUNCIÓN SIMULADA DE SUBIDA ---
def subir_archivo_a_drive(archivo_bytes, nombre_archivo):
    # AQUÍ VA TU LÓGICA REAL DE DRIVE. 
    # Por ahora devolvemos un link simulado para probar que guarda en el Excel.
    time.sleep(1)
    return f"https://drive.google.com/open?id=ARCHIVO_SUBIDO_{nombre_archivo}"

# ==========================================
#              INTERFAZ PRINCIPAL
# ==========================================

def main():
    st.title("📂 Gestión de Cartera - Grupo EDF")
    
    gc = conectar_google_sheets()
    df, worksheet = cargar_datos(gc)

    if df.empty:
        st.stop()

    # --- SECCIÓN A: FILTROS ---
    st.markdown("### 🔍 Buscador y Filtros")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Filtro Ejecutivo
        if COLUMNA_EJECUTIVO in df.columns:
            lista = ["Todos"] + sorted(list(set(df[COLUMNA_EJECUTIVO].astype(str))))
            filtro_ejecutivo = st.selectbox("Ejecutivo", lista)
        else:
            st.warning(f"No encuentro la columna '{COLUMNA_EJECUTIVO}'")
            filtro_ejecutivo = "Todos"

    with col2:
        # Filtro Estado (PDF)
        estado_opciones = ["Todos", "Falta PDF", "Con PDF"]
        filtro_estado = st.selectbox("Estado Documentación", estado_opciones)

    with col3:
         # Buscador de texto
        busqueda = st.text_input("Buscar (Matrícula, Cliente...)")

    # --- LÓGICA DE FILTRADO ---
    df_filtrado = df.copy()

    if filtro_ejecutivo != "Todos":
        df_filtrado = df_filtrado[df_filtrado[COLUMNA_EJECUTIVO] == filtro_ejecutivo]

    # Filtrar por PDF vacio o lleno
    if COLUMNA_PDF in df.columns:
        if filtro_estado == "Falta PDF":
            # Filtra celdas vacías
            df_filtrado = df_filtrado[df_filtrado[COLUMNA_PDF].eq("")]
        elif filtro_estado == "Con PDF":
            # Filtra celdas con texto
            df_filtrado = df_filtrado[df_filtrado[COLUMNA_PDF].ne("")]
    
    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        ]

    # --- SECCIÓN B: TABLA DE RESULTADOS ---
    st.divider()
    st.info(f"Mostrando {len(df_filtrado)} registros.")
    
    # Mostramos columnas clave (Ajusta 'Cliente' si tu columna se llama diferente, ej: 'Nombre Completo')
    cols_a_mostrar = [COLUMNA_ID_POLIZA, COLUMNA_EJECUTIVO, "Inicio de Vigencia", COLUMNA_PDF]
    
    # Intentamos mostrar solo las columnas que existen
    cols_validas = [c for c in cols_a_mostrar if c in df_filtrado.columns]
    
    st.dataframe(
        df_filtrado[cols_validas], 
        use_container_width=True, 
        hide_index=True
    )

    # --- SECCIÓN C: GESTIÓN DE CARGA ---
    st.divider()
    st.subheader("📎 Vincular PDF a una Póliza")

    c_upload1, c_upload2 = st.columns([1, 1])

    with c_upload1:
        # Usamos la columna "Matrícula..." para identificar la póliza en el dropdown
        if COLUMNA_ID_POLIZA in df_filtrado.columns:
            # Creamos una lista de las matrículas filtradas
            opciones_polizas = df_filtrado[COLUMNA_ID_POLIZA].astype(str).tolist()
            seleccion_usuario = st.selectbox("Seleccione Matrícula / Póliza:", opciones_polizas)
        else:
            st.error(f"Revisa la variable COLUMNA_ID_POLIZA al inicio del código.")
            seleccion_usuario = None
    
    with c_upload2:
        archivo_subido = st.file_uploader("Subir PDF", type=['pdf'])

    # --- BOTÓN DE GUARDADO ---
    if st.button("💾 Guardar y Actualizar Sheet", type="primary"):
        if archivo_subido is not None and seleccion_usuario:
            
            with st.spinner("Actualizando Google Sheets..."):
                try:
                    # 1. Subir archivo (simulado)
                    link_generado = subir_archivo_a_drive(archivo_subido, archivo_subido.name)
                    
                    # 2. Buscar la fila en Sheets usando FIND
                    # Buscamos la matrícula exacta en la hoja
                    celda_encontrada = worksheet.find(seleccion_usuario)
                    
                    if celda_encontrada:
                        fila = celda_encontrada.row
                        
                        # 3. Buscar la columna 'Adjunto (póliza)' dinámicamente
                        try:
                            # Busca en la fila 1 (encabezados) en qué número de columna está "Adjunto (póliza)"
                            col_pdf_obj = worksheet.find(COLUMNA_PDF)
                            col_pdf_index = col_pdf_obj.col
                            
                            # 4. Escribir el Link
                            worksheet.update_cell(fila, col_pdf_index, link_generado)
                            
                            st.success(f"✅ ¡Listo! Póliza '{seleccion_usuario}' actualizada con el PDF.")
                            time.sleep(1.5)
                            st.rerun()
                            
                        except gspread.exceptions.CellNotFound:
                            st.error(f"No encontré la columna '{COLUMNA_PDF}' en los encabezados del Excel.")
                    else:
                        st.error(f"No encontré la matrícula '{seleccion_usuario}' en la hoja.")

                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Selecciona una póliza y sube un archivo.")

if __name__ == "__main__":
    main()