import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
from streamlit_javascript import st_javascript

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="Control SERGEM", layout="wide")

# --- BLOQUE DE SEGURIDAD Y ESTILOS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    div[data-testid="stToolbar"] { visibility: hidden !important; }
    
    /* Botón ENVIAR REGISTRO -> VERDE */
    div.stButton > button:first-child[kind="primary"] {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
        color: white !important;
    }

    /* Botón FINALIZAR (Arriba) -> ROJO */
    .stColumn div.stButton > button[kind="primary"] {
        background-color: #dc3545 !important;
        border-color: #dc3545 !important;
    }
    </style>
    """, unsafe_allow_html=True)

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- LÓGICA DE PERSISTENCIA ---
js_get_data = """
(async () => {
    return {
        ced: localStorage.getItem('sergem_ced'),
        nom: localStorage.getItem('sergem_nom'),
        hor: localStorage.getItem('sergem_hor')
    };
})()
"""
local_data = st_javascript(js_get_data)
params = st.query_params

if "ced" in params: st.session_state.cedula = params["ced"]
elif local_data and local_data.get('ced'): st.session_state.cedula = local_data['ced']
if "nom" in params: st.session_state.nombre = params["nom"]
elif local_data and local_data.get('nom'): st.session_state.nombre = local_data['nom']
if "hor" in params: st.session_state.hora_ref = params["hor"]
elif local_data and local_data.get('hor'): st.session_state.hora_ref = local_data['hor']

if 'cedula' not in st.session_state: st.session_state.cedula = ""
if 'nombre' not in st.session_state: st.session_state.nombre = ""
if 'hora_ref' not in st.session_state: st.session_state.hora_ref = ""

def actualizar_url_y_disco():
    st.query_params.update({"ced": st.session_state.cedula, "nom": st.session_state.nombre, "hor": st.session_state.hora_ref})
    st_javascript(f"localStorage.setItem('sergem_ced', '{st.session_state.cedula}');")
    st_javascript(f"localStorage.setItem('sergem_nom', '{st.session_state.nombre}');")
    st_javascript(f"localStorage.setItem('sergem_hor', '{st.session_state.hora_ref}');")

# --- CABECERA CON BOTÓN DE CIERRE ---
head_l, head_r = st.columns([3, 1])
with head_l:
    st.title("🛵 SERGEM")
with head_r:
    st.write(" ") # Espaciador
    if st.button("🏁 FINALIZAR", type="primary", key="btn_top_final"):
        st.session_state.confirmar_cierre = True

# --- LÓGICA DE CONFIRMACIÓN (MODAL SIMULADO) ---
if st.session_state.get('confirmar_cierre'):
    st.error("⚠️ **¿SALIR DE LA APP?**")
    c1, c2 = st.columns(2)
    if c1.button("❌ NO, VOLVER", use_container_width=True):
        st.session_state.confirmar_cierre = False
        st.rerun()
    if c2.button("🚨 SÍ, CERRAR", use_container_width=True, type="primary"):
        st_javascript("localStorage.clear();")
        st.query_params.clear()
        st.session_state.clear()
        st_javascript("window.location.href = 'https://www.google.com';")
        st.stop()

# --- CUERPO DE LA APP ---
c1, c2 = st.columns(2)
ced_input = c1.text_input("Cédula:", value=st.session_state.cedula)
nom_input = c2.text_input("Nombre:", value=st.session_state.nombre).upper()

if ced_input != st.session_state.cedula or nom_input != st.session_state.nombre:
    st.session_state.cedula = ced_input
    st.session_state.nombre = nom_input
    actualizar_url_y_disco()

if st.session_state.cedula and st.session_state.nombre:
    if not st.session_state.hora_ref or st.session_state.hora_ref in ["", "None"]:
        if st.button("▶️ CAPTURAR HORA DE SALIDA", use_container_width=True):
            st.session_state.hora_ref = datetime.now(col_tz).strftime("%H:%M")
            actualizar_url_y_disco()
            st.rerun()
    else:
        st.success(f"✅ {st.session_state.nombre} | Base: {st.session_state.hora_ref}")
        
        # Selectores de Ciudad, Producto y Empresa
        f1, f2 = st.columns(2)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLIN", "BOGOTA"], key="s_ciu")
        with f2: 
            opciones_producto = ["POLLOS", "PANADERIA"]
            if ciudad == "MANIZALES": opciones_producto = ["PANADERIA"]
            elif ciudad in ["MEDELLIN", "BOGOTA"]: opciones_producto = ["POLLOS"]
            producto = st.radio("📦 Producto:", opciones_producto, horizontal=True, key="s_prod")
        
        empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER", "CAÑAVERAL"] if ciudad == "CALI" else ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER"], key="s_emp")

        # Lógica de tiendas (Se mantiene igual a tu versión anterior)
        # ... [Aquí va el diccionario de tiendas que ya tienes] ...
        # [Por brevedad no repito todo el diccionario, pero úsalo igual]

        # Ejemplo de botón de envío (VERDE)
        if st.button("ENVIAR REGISTRO ✅", use_container_width=True, type="primary"):
            # Lógica de envío...
            pass
