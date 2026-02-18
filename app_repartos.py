import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
from urllib.parse import quote

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="Control de entregas SERGEM", layout="wide")

# --- BLOQUE DE SEGURIDAD Y ESTÉTICA (INTACTO) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    div[data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    /* Estilo para el botón de recuperación */
    .link-recuperacion {
        background-color: #f0f2f6;
        border: 1px solid #ff4b4b;
        border-radius: 5px;
        padding: 10px;
        text-align: center;
        display: block;
        text-decoration: none;
        color: #ff4b4b;
        font-weight: bold;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- PERSISTENCIA POR URL ---
params = st.query_params
if 'cedula' not in st.session_state: st.session_state.cedula = params.get("ced", "")
if 'nombre' not in st.session_state: st.session_state.nombre = params.get("nom", "")
if 'hora_ref' not in st.session_state: st.session_state.hora_ref = params.get("hor", "")

# --- INTERFAZ ---
st.title("🛵 Control de entregas SERGEM")

with st.sidebar:
    if st.button("🏁 FINALIZAR DÍA", type="primary"):
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()
    
    # --- LINK DINÁMICO DE RESTAURACIÓN ---
    if st.session_state.cedula and st.session_state.hora_ref:
        st.markdown("---")
        st.write("🔄 **¿Se cerró la App?**")
        nom_encoded = quote(st.session_state.nombre)
        # Cambia 'repartos-sergem.streamlit.app' por tu URL real si es distinta
        link_recuperacion = f"https://repartos-sergem.streamlit.app/?ced={st.session_state.cedula}&nom={nom_encoded}&hor={st.session_state.hora_ref}"
        
        st.markdown(f"""
            <a href="{link_recuperacion}" class="link-recuperacion">
                🚀 TOCAR AQUÍ PARA RE-ASEGURAR SESIÓN
            </a>
            <p style='font-size: 0.8em; color: gray; text-align: center;'>
            (Presiona para restaurar o deja presionado para copiar y guardar en WhatsApp)
            </p>
        """, unsafe_allow_html=True)

# Identificación (Lógica intacta)
c1, c2 = st.columns(2)
ced_input = c1.text_input("Cédula:", value=st.session_state.cedula)
nom_input = c2.text_input("Nombre:", value=st.session_state.nombre).upper()

if ced_input != st.session_state.cedula or nom_input != st.session_state.nombre:
    st.session_state.cedula = ced_input
    st.session_state.nombre = nom_input
    st.query_params.update({"ced": ced_input, "nom": nom_input, "hor": st.session_state.hora_ref})

if st.session_state.cedula and st.session_state.nombre:
    
    if not st.session_state.hora_ref or st.session_state.hora_ref in ["", "None"]:
        st.subheader("🚀 Iniciar Jornada")
        if st.button("▶️ CAPTURAR HORA DE SALIDA", use_container_width=True):
            nueva_hora = datetime.now(col_tz).strftime("%H:%M")
            st.session_state.hora_ref = nueva_hora
            st.query_params.update({"ced": st.session_state.cedula, "nom": st.session_state.nombre, "hor": nueva_hora})
            st.rerun()
    else:
        st.success(f"✅ **Mensajero:** {st.session_state.nombre} | **Hora Base:** {st.session_state.hora_ref}")
        
        # --- AQUÍ SIGUE TODA TU LÓGICA DE TIENDAS Y ENVÍO (MANTENIDA 100%) ---
