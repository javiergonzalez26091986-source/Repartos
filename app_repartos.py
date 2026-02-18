import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM", layout="wide")

# Ocultar menús de Streamlit
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

# --- LÓGICA DE PERSISTENCIA (Sincronización con URL) ---
params = st.query_params

if "ced" in params and 'cedula' not in st.session_state:
    st.session_state.cedula = params["ced"]
if "nom" in params and 'nombre' not in st.session_state:
    st.session_state.nombre = params["nom"]
if "hor" in params and 'hora_ref' not in st.session_state:
    st.session_state.hora_ref = params["hor"]

if 'cedula' not in st.session_state: st.session_state.cedula = ""
if 'nombre' not in st.session_state: st.session_state.nombre = ""
if 'hora_ref' not in st.session_state: st.session_state.hora_ref = ""

def guardar_en_url():
    st.query_params.update({
        "ced": st.session_state.cedula,
        "nom": st.session_state.nombre,
        "hor": st.session_state.hora_ref
    })

# --- INTERFAZ ---
st.title("🛵 Control de entregas SERGEM")

with st.sidebar:
    if st.button("🏁 FINALIZAR DÍA", type="primary"):
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()

# Identificación
c1, c2 = st.columns(2)
ced_input = c1.text_input("Cédula:", value=st.session_state.cedula)
nom_input = c2.text_input("Nombre:", value=st.session_state.nombre).upper()

if ced_input != st.session_state.cedula or nom_input != st.session_state.nombre:
    st.session_state.cedula = ced_input
    st.session_state.nombre = nom_input
    guardar_en_url()

if st.session_state.cedula and st.session_state.nombre:
    
    # Lógica de Hora de Inicio
    if not st.session_state.hora_ref:
        st.subheader("🚀 Iniciar Jornada")
        if st.button("▶️ CAPTURAR HORA DE SALIDA", use_container_width=True):
            st.session_state.hora_ref = datetime.now(col_tz).strftime("%H:%M")
            guardar_en_url()
            st.rerun()
    else:
        st.success(f"✅ **Mensajero:** {st.session_state.nombre} | **Hora de Salida:** {st.session_state.hora_ref}")
        
        # --- FORMULARIO DE ENTREGAS (Sin modificaciones) ---
        st.divider()
        col1, col2 = st.columns(2)
        
        ciudad = col1.selectbox("Ciudad:", ["CALI", "JAMUNDI", "YUMBO", "PALMIRA"])
        producto = col2.selectbox("Producto:", ["PAQUETE", "DOCUMENTO", "VALORADO", "OTROS"])
        cantidad = st.number_input("Cantidad entregada:", min_value=1, step=1)
        observaciones = st.text_area("Observaciones (opcional):")

        if st.button("📤 REGISTRAR ENTREGA", use_container_width=True):
            hora_entrega = datetime.now(col_tz).strftime("%H:%M")
            
            datos = {
                "fecha": datetime.now(col_tz).strftime("%Y-%m-%d"),
                "cedula": st.session_state.cedula,
                "nombre": st.session_state.nombre,
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
                    st.success(f"¡Registro guardado! (Hora entrega: {hora_entrega})")
                else:
                    st.error("Error al enviar a Google Sheets.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
