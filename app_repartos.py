import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests
import time

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM - Control Maestro v4.8", layout="wide")

# --- LINK DE IMPLEMENTACIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- BARRA LATERAL (REINICIAR SIEMPRE DISPONIBLE) ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        st.session_state['hora_referencia'] = ""
        st.rerun()
    st.write("---")
    st.caption("v4.8 - Selectores Independientes")

# --- BASE DE DATOS COMPLETA DE TIENDAS Y CÓDIGOS ---
TIENDAS_CIUDAD = {
    'CALI': {
        'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA HOLGUINES': '2596540', 'CARULLA PANCE': '2594540', 
        'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'CARULLA AV COLOMBIA': '4219540',
        'CARULLA PUI': '4799540', 'ÉXITO LA FLORA': '2054540', 'CARULLA SANTA RITA': '2595540',
        'CARULLA LA MARIA': '4781540', 'SUPER INTER POPULAR': '4210', 'CAÑAVERAL PASOANCHO': 'CAN01'
    },
    'MANIZALES': {
        'CARULLA CABLE PLAZA': '2334540', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540',
        'SUPERINTER VILLA PILAR': '4303540', 'ÉXITO MANIZALES': '383', 'SUPERINTER CENTRO': '4273540',
        'SUPERINTER PLAZA': '4279540', 'SUPERINTER TORRES': '4280540', 'CARULLA SAN MARCEL': '4805'
    },
    'MEDELLÍN': {
        'ÉXITO CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'SURTIMAX CALDAS': '4534', 'ÉXITO GARDEL': '4070'
    },
    'BOGOTÁ': {
        'CARULLA CEDRITOS': '468', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX BOSA': '311', 'SURTIMAX LA ESPAÑOLA': '449'
    }
}

if 'hora_referencia' not in st.session_state: st.session_state['hora_referencia'] = ""

st.title("🛵 Control Maestro SERGEM")

# --- IDENTIFICACIÓN ---
c1, c2 = st.columns(2)
with c1: cedula = st.text_input("Cédula:", key="ced")
with c2: nombre = st.text_input("Nombre:", key="nom").upper()

if cedula and nombre:
    if st.session_state['hora_referencia'] == "":
        h_ini = st.time_input("Salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            st.rerun()
    else:
        st.success(f"✅ Mensajero: {nombre} | Inicio: {st.session_state['hora_referencia']}")
        
        # --- FILTROS ---
        f1, f2, f3 = st.columns(3)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"])
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        with f3: empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SUPERINTER-SURTIMAX", "CAÑAVERAL", "OTROS"])

        info = None
        if ciudad != "--":
            tiendas = TIENDAS_CIUDAD.get(ciudad, {})
            opciones_t = ["--"] + sorted(list(tiendas.keys()))
            
            # --- LÓGICA DE SELECTORES INDEPENDIENTES PARA PANADERÍA ---
            if producto == "PANADERÍA":
                st.subheader("🥖 Ruta Flexible de Panadería")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    orig = st.selectbox("📦 Recoge en:", opciones_t, key="pan_orig")
                with col_p2:
                    dest = st.selectbox("🏠 Entrega en:", opciones_t, key="pan_dest")
                
                if orig != "--" and dest != "--":
                    info = {"TO": orig, "CO": tiendas[orig], "TD": dest, "CD": tiendas[dest]}
            
            # --- LÓGICA DE TIENDA ÚNICA PARA POLLOS ---
            else:
                st.subheader("🍗 Entrega de Pollos")
                tienda = st.selectbox("🏪 Tienda:", opciones_t, key="pol_t")
                if tienda != "--":
                    info = {"TO": tienda, "CO": tiendas[tienda], "TD": tienda, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1)
            if st.button("ENVIAR A LA NUBE ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                duracion = int((datetime.strptime(h_llegada, "%H:%M") - datetime.strptime(st.session_state['hora_referencia'], "%H:%M")).total_seconds() / 60)
                
                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), "Cedula": cedula, "Mensajero": nombre,
                    "Empresa": empresa, "Ciudad": ciudad, "Producto": producto,
                    "Tienda_O": info["TO"], "Cod_O": info["CO"], "Cod_D": info["CD"], "Tienda_D": info["TD"],
                    "Cant": int(cant), "Inicio": st.session_state['hora_referencia'], "Llegada": h_llegada, "Minutos": duracion
                }
                
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=30)
                    st.success(f"¡Sincronizado! De {info['TO']} a {info['TD']}")
                    st.session_state['hora_referencia'] = h_llegada
                    time.sleep(1.5)
                    st.rerun()
                except:
                    st.warning("Respuesta lenta del servidor, pero el registro probablemente se envió. Verifica el Drive.")
                    st.session_state['hora_referencia'] = h_llegada
