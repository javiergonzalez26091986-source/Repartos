import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM - Control Maestro v4.5", layout="wide")

# --- LINK DE IMPLEMENTACIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- BARRA LATERAL (OPCIÓN REINICIAR SIEMPRE PRESENTE) ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        st.session_state['hora_referencia'] = ""
        st.rerun()
    st.write("---")
    st.caption("v4.5 - Todas las Ciudades + Rutas Panadería")

# --- BASE DE DATOS DE RUTAS PANADERÍA (SEGÚN TU IMAGEN) ---
RUTAS_PAN_ESPECIFICAS = {
    'CALI': [
        {'R': 'CARULLA CIUDAD JARDIN', 'CR': '2732540', 'E': 'CARULLA HOLGUINES', 'CE': '2596540'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'ÉXITO UNICALI', 'CE': '2054056'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'CARULLA CIUDAD JARDIN', 'CE': '2732540'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'CARULLA HOLGUINES', 'CE': '2596540'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'ÉXITO JAMUNDI', 'CE': '2054049'},
        {'R': 'CARULLA PANCE', 'CR': '2594540', 'E': 'CARULLA AV COLOMBIA', 'CE': '4219540'},
        {'R': 'CARULLA CIUDAD JARDIN', 'CR': '2732540', 'E': 'CARULLA PANCE', 'CE': '4799540'},
        {'R': 'CARULLA CIUDAD JARDIN', 'CR': '2732540', 'E': 'CARULLA AV COLOMBIA', 'CE': '4219540'}
    ],
    'MANIZALES': [
        {'R': 'CARULLA CABLE PLAZA', 'CR': '2334540', 'E': 'SUPERINTER CRISTO REY', 'CE': '4301540'},
        {'R': 'CARULLA CABLE PLAZA', 'CR': '2334540', 'E': 'SUPERINTER ALTA SUIZA', 'CE': '4302540'},
        {'R': 'ÉXITO MANIZALES', 'CR': '383', 'E': 'SUPERINTER MANIZALES CENTRO', 'CE': '4273540'}
    ]
}

# --- LISTADO GENERAL DE TIENDAS POR CIUDAD ---
TIENDAS_CIUDAD = {
    'CALI': {
        'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA HOLGUINES': '2596540', 'CARULLA PANCE': '2594540', 
        'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'CARULLA AV COLOMBIA': '4219540',
        'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'CAÑAVERAL PASOANCHO': 'CAN01'
    },
    'MANIZALES': {
        'CARULLA CABLE PLAZA': '2334540', 'SUPERINTER CRISTO REY': '4301540', 'ÉXITO MANIZALES': '383',
        'CARULLA SAN MARCEL': '4805', 'SUPERINTER ALTA SUIZA': '4302540'
    },
    'MEDELLÍN': {
        'ÉXITO EXPRESS CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 
        'ÉXITO GARDEL': '4070', 'SURTIMAX CALDAS': '4534'
    },
    'BOGOTÁ': {
        'CARULLA EXPRESS CEDRITOS': '468', 'ÉXITO PLAZA BOLIVAR': '558', 
        'SURTIMAX BRASIL BOSA': '311', 'SURTIMAX LA ESPAÑOLA': '449'
    }
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
        h_ini = st.time_input("Hora de salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            st.rerun()
    else:
        st.success(f"✅ Mensajero: {nombre} | Inicio: {st.session_state['hora_referencia']}")
        
        # --- FILTROS PRINCIPALES ---
        f1, f2, f3 = st.columns(3)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"])
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        with f3: empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SUPERINTER-SURTIMAX", "CAÑAVERAL", "OTROS"])

        info = None
        if ciudad != "--":
            # LÓGICA PANADERÍA ESPECÍFICA (CALI/MANIZALES)
            if producto == "PANADERÍA" and ciudad in RUTAS_PAN_ESPECIFICAS:
                st.subheader("🥖 Ruta de Panadería Predefinida")
                rutas = RUTAS_PAN_ESPECIFICAS[ciudad]
                opciones = [f"{r['R']} -> {r['E']}" for r in rutas]
                sel = st.selectbox("Seleccione Trayecto:", ["--"] + opciones)
                if sel != "--":
                    idx = opciones.index(sel)
                    info = {"TO": rutas[idx]['R'], "CO": rutas[idx]['CR'], "TD": rutas[idx]['E'], "CD": rutas[idx]['CE']}
            
            # LÓGICA GENERAL (POLLOS O PANADERÍA EN OTRAS CIUDADES)
            else:
                st.subheader(f"🏠 Registro en {ciudad}")
                tiendas = TIENDAS_CIUDAD.get(ciudad, {})
                opciones_t = ["--"] + sorted(list(tiendas.keys()))
                
                if producto == "PANADERÍA":
                    col_p1, col_p2 = st.columns(2)
                    with col_p1: orig = st.selectbox("📦 Recoge en:", opciones_t, key="pan_o")
                    with col_p2: dest = st.selectbox("🏠 Entrega en:", opciones_t, key="pan_d")
                    if orig != "--" and dest != "--":
                        info = {"TO": orig, "CO": tiendas[orig], "TD": dest, "CD": tiendas[dest]}
                else:
                    tienda = st.selectbox("🏪 Tienda de Entrega:", opciones_t)
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
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    if "Éxito" in res.text:
                        st.success(f"¡Sincronizado! Entrega registrada.")
                        st.session_state['hora_referencia'] = h_llegada
                        st.rerun()
                    else: st.error("Error en servidor. Verifica conexión.")
                except: st.error("Error de red.")
