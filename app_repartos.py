import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests
import time

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM - Control Maestro v4.6", layout="wide")

# --- LINK DE IMPLEMENTACIÓN (EL QUE GENERASTE ÚLTIMO) ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        st.session_state['hora_referencia'] = ""
        st.rerun()
    st.write("---")
    st.caption("v4.6 - Estabilidad Reforzada")

# --- BASE DE DATOS DE RUTAS PANADERÍA ---
RUTAS_PAN_ESPECIFICAS = {
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

# --- LISTADO GENERAL POR CIUDAD ---
TIENDAS_CIUDAD = {
    'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'CARULLA AV COLOMBIA': '4219540'},
    'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805'},
    'MEDELLÍN': {'ÉXITO CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'SURTIMAX CALDAS': '4534'},
    'BOGOTÁ': {'CARULLA CEDRITOS': '468', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX BOSA': '311'}
}

if 'hora_referencia' not in st.session_state: st.session_state['hora_referencia'] = ""

st.title("🛵 Control Maestro SERGEM")

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
        f1, f2, f3 = st.columns(3)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"])
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        with f3: empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SUPERINTER-SURTIMAX", "CAÑAVERAL", "OTROS"])

        info = None
        if ciudad != "--":
            if producto == "PANADERÍA" and ciudad in RUTAS_PAN_ESPECIFICAS:
                rutas = RUTAS_PAN_ESPECIFICAS[ciudad]
                opciones = [f"{r['R']} -> {r['E']}" for r in rutas]
                sel = st.selectbox("Seleccione Trayecto:", ["--"] + opciones)
                if sel != "--":
                    idx = opciones.index(sel)
                    info = {"TO": rutas[idx]['R'], "CO": rutas[idx]['CR'], "TD": rutas[idx]['E'], "CD": rutas[idx]['CE']}
            else:
                tiendas = TIENDAS_CIUDAD.get(ciudad, {})
                op_t = ["--"] + sorted(list(tiendas.keys()))
                if producto == "PANADERÍA":
                    col1, col2 = st.columns(2)
                    with col1: o = st.selectbox("Recoge en:", op_t, key="pan_o")
                    with col2: d = st.selectbox("Entrega en:", op_t, key="pan_d")
                    if o != "--" and d != "--": info = {"TO": o, "CO": tiendas[o], "TD": d, "CD": tiendas[d]}
                else:
                    t = st.selectbox("Tienda Entrega:", op_t)
                    if t != "--": info = {"TO": t, "CO": tiendas[t], "TD": t, "CD": "N/A"}

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
                
                # REINTENTO AUTOMÁTICO PARA EVITAR "ERROR DE RED"
                for i in range(2):
                    try:
                        res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=20)
                        if "Éxito" in res.text:
                            st.success("¡Guardado correctamente!")
                            st.session_state['hora_referencia'] = h_llegada
                            time.sleep(1)
                            st.rerun()
                            break
                    except:
                        if i == 0: time.sleep(2)
                        else: st.error("Error persistente de conexión. Revisa el ID de Google.")
