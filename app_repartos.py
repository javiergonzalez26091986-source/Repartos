import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM", layout="wide")

# Ocultar menús (Tu bloque de CSS original)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    div[data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
    </style>
    """, unsafe_allow_html=True)

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- LO ÚNICO NUEVO PARA LA MEMORIA ---
if 'hora_ref' not in st.session_state:
    st.session_state.hora_ref = st.query_params.get("hor", "")

# --- TU LÓGICA ORIGINAL DE INTERFAZ ---
st.title("🛵 Control de entregas SERGEM")

with st.sidebar:
    if st.button("🏁 FINALIZAR DÍA", type="primary"):
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()

c1, c2 = st.columns(2)
cedula = c1.text_input("Cédula:")
nombre = c2.text_input("Nombre:").upper()

if cedula and nombre:
    # Si no hay hora, mostramos el botón de capturar
    if not st.session_state.hora_ref:
        if st.button("▶️ CAPTURAR HORA DE SALIDA", use_container_width=True):
            st.session_state.hora_ref = datetime.now(col_tz).strftime("%H:%M")
            # Guardamos en la URL para que no se borre
            st.query_params["hor"] = st.session_state.hora_ref
            st.rerun()
    else:
        # Si ya hay hora, mostramos el mensaje verde que ya tenías
        st.success(f"✅ **Mensajero:** {nombre} | **Hora de Salida:** {st.session_state.hora_ref}")
        
        st.divider()
        col1, col2 = st.columns(2)
        
        # Tus selectbox y inputs originales
        ciudad = col1.selectbox("Ciudad:", ["CALI", "JAMUNDI", "YUMBO", "PALMIRA"])
        producto = col2.selectbox("Producto:", ["PAQUETE", "DOCUMENTO", "VALORADO", "OTROS"])
        cantidad = st.number_input("Cantidad entregada:", min_value=1, step=1)
        observaciones = st.text_area("Observaciones (opcional):")

        if st.button("📤 REGISTRAR ENTREGA", use_container_width=True):
            hora_entrega = datetime.now(col_tz).strftime("%H:%M")
            
            # Tus datos para Google Sheets originales
            datos = {
                "fecha": datetime.now(col_tz).strftime("%Y-%m-%d"),
                "cedula": cedula,
                "nombre": nombre,
                "hora_salida": st.session_state.hora_ref,
                "ciudad": ciudad,
                "producto": producto,
                "cantidad": cantidad,
                "hora_entrega": hora_entrega,
                "observaciones": observaciones
            }

            try:
                response = requests.post(URL_GOOGLE_SCRIPT, json=datos)
                if response.status_code == 200:
                    st.balloons()
                    st.success(f"¡Registro guardado! (Hora: {hora_entrega})")
                else:
                    st.error("Error al enviar.")
            except Exception as e:
                st.error(f"Error: {e}")
