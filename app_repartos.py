import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM - Control Maestro v4.4", layout="wide")

# --- LINK DE IMPLEMENTACIÓN ACTUALIZADO ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- OPCIÓN DE REINICIAR (SIEMPRE DISPONIBLE) ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        st.session_state['hora_referencia'] = ""
        st.rerun()
    st.write("---")
    st.caption("v4.4 - Panadería Inteligente")

# --- BASE DE DATOS DE RUTAS PANADERÍA (SEGÚN TU IMAGEN) ---
RUTAS_PAN = {
    'CALI': [
        {'R': 'CARULLA CIUDAD JARDIN', 'CR': '2732540', 'E': 'CARULLA HOLGUINES', 'CE': '2596540'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'ÉXITO UNICALI', 'CE': '2054056'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'CARULLA CIUDAD JARDIN', 'CE': '2732540'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'CARULLA HOLGUINES', 'CE': '2596540'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'ÉXITO JAMUNDI', 'CE': '2054049'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'CARULLA AV COLOMBIA', 'CE': '4219540'}
    ],
    'MANIZALES': [
        {'R': 'CARULLA CABLE PLAZA', 'CR': '2334540', 'E': 'SUPERINTER CRISTO REY', 'CE': '4301540'},
        {'R': 'CARULLA CABLE PLAZA', 'CR': '2334540', 'E': 'SUPERINTER ALTA SUIZA', 'CE': '4302540'},
        {'R': 'ÉXITO MANIZALES', 'CR': '383', 'E': 'SUPERINTER MANIZALES CENTRO', 'CE': '4273540'}
    ]
}

# Tiendas para Pollos o General
TIENDAS_GENERAL = {
    'CALI': {'CARULLA AV COLOMBIA': '4219540', 'ÉXITO JAMUNDI': '2054049', 'CARULLA PANCE': '2594540'},
    'MANIZALES': {'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805'}
}

if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = ""

st.title("🛵 Control Maestro SERGEM")

# --- IDENTIFICACIÓN ---
c1, c2 = st.columns(2)
with c1:
    cedula = st.text_input("Cédula:", key="ced")
with c2:
    nombre = st.text_input("Nombre:", key="nom").upper()

if cedula and nombre:
    if st.session_state['hora_referencia'] == "":
        st.subheader("🕒 Iniciar Jornada")
        h_ini = st.time_input("Hora de salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            st.rerun()
    else:
        st.success(f"✅ Mensajero: {nombre} | Inicio: {st.session_state['hora_referencia']}")
        
        # --- FILTROS ---
        f1, f2, f3 = st.columns(3)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES"])
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        with f3: empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SUPERINTER-SURTIMAX", "CAÑAVERAL", "OTROS"])

        info = None
        if ciudad != "--":
            if producto == "PANADERÍA":
                rutas = RUTAS_PAN.get(ciudad, [])
                opciones = [f"{r['R']} -> {r['E']}" for r in rutas]
                sel = st.selectbox("🥖 Seleccione Ruta:", ["--"] + opciones)
                if sel != "--":
                    idx = opciones.index(sel)
                    info = {"TO": rutas[idx]['R'], "CO": rutas[idx]['CR'], "TD": rutas[idx]['E'], "CD": rutas[idx]['CE']}
            else:
                tiendas = TIENDAS_GENERAL.get(ciudad, {})
                sel = st.selectbox("🍗 Tienda Entrega:", ["--"] + list(tiendas.keys()))
                if sel != "--":
                    info = {"TO": sel, "CO": tiendas[sel], "TD": sel, "CD": "N/A"}

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
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    if "Éxito" in res.text:
                        st.success(f"¡Guardado! Próximo destino desde: {h_llegada}")
                        st.session_state['hora_referencia'] = h_llegada
                        st.rerun()
                    else:
                        st.error("Error en servidor. Verifica tu internet.")
                except:
                    st.error("Error de conexión.")
