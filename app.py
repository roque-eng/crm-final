import streamlit as st
import pandas as pd
import psycopg2
import os
import time
from datetime import date

# 1. Configuración de página (CON EL NUEVO TÍTULO)
st.set_page_config(page_title="Gestión de Cartera - Grupo EDF", layout="wide", page_icon="🛡️")

# ==========================================
# 🔐 GESTIÓN DE USUARIOS
# ==========================================
USUARIOS = {
    "RDF": "claveRockuda.4428",
    "AB": "claveABentancor2025",
    "GR": "claveGRobaina2025"
}

def verificar_login(usuario, contrasena):
    if usuario in USUARIOS and USUARIOS[usuario] == contrasena:
        return True
    return False

# Inicializar estado
if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False
if 'usuario_actual' not in st.session_state:
    st.session_state['usuario_actual'] = ""

# --- PANTALLA DE LOGIN ---
if not st.session_state['logueado']:
    col_login_logo, col_login_text = st.columns([1, 4])
    with col_login_text:
        st.markdown("<h1 style='text-align: left;'>☁️ CRM Grupo EDF</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.info("Ingrese sus credenciales para continuar")
        with st.form("login_form"):
            user = st.text_input("Usuario")
            passwd = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit:
                if verificar_login(user, passwd):
                    st.session_state['logueado'] = True
                    st.session_state['usuario_actual'] = user
                    st.success("✅ Acceso correcto")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

# ==========================================
# ⚙️ SISTEMA INTERNO
# ==========================================

# --- BARRA SUPERIOR (DISEÑO MEJORADO) ---
# Columnas ajustadas para dar espacio al logo
col_logo, col_titulo, col_user = st.columns([1.5, 6.5, 2])

with col_logo:
    # Espaciado para bajar el logo y centrarlo visualmente
    st.write("") 
    st.write("") 
    try:
        # Logo más grande (220px)
        st.image("logo.png", width=220) 
    except:
        st.write("🛡️")

with col_titulo:
    # Título con HTML para controlar márgenes y alineación
    st.markdown("""
        <h1 style='text-align: left; margin-top: 15px; margin-bottom: 0px; padding-bottom: 0px;'>
            Gestión de Cartera - Grupo EDF
        </h1>
    """, unsafe_allow_html=True)

with col_user:
    st.write("") # Espaciador para alinear el usuario
    st.write(f"👤 **{st.session_state['usuario_actual']}**")
    if st.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

# --- VARIABLE PARA EL FORMULARIO DE GOOGLE ---
URL_GOOGLE_FORM = "https://docs