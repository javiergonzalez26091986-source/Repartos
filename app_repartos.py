import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM v4.9", layout="wide")

# --- VERIFICA QUE ESTA URL SEA LA DE TU ÚLTIMA IMPLEMENTACIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        st.session_state['hora_referencia'] = ""
        st.rerun()

# --- TIENDAS ---
TIENDAS_CIUDAD = {
    'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA HOLGUINES': '2596540', 'CARULLA PANCE': '2594540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA PUI': '4799540', 'SUPER INTER POPULAR': '4210', 'CAÑAVERAL PASOANCHO': 'CAN01'},
    'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805'},
    'MEDELLÍN': {'ÉXITO CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'SURTIMAX CALDAS': '4534'},
    'BOGOTÁ': {'CARULLA CEDRITOS': '468', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX BOSA': '311'}
}

if 'hora_referencia' not in st.session_state: st.session_state['hora_referencia'] = ""

st.title("🛵 Control Maestro SERGEM")

cedula = st.text_input("Cédula:")
nombre = st.text_input("Nombre:").upper()

if cedula and nombre:
    if st.session_state['hora_referencia'] == "":
        h_ini = st.time_input("Salida:", datetime.now(col_tz))
        if st.button("COMENZAR"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            st.rerun()
    else:
        st.success(f"✅ {nombre} | {st.session_state['hora_referencia']}")
        f1, f2, f3 = st.columns(3)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"])
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        with f3: empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA", "CAÑAVERAL", "OTROS"])

        info = None
        if ciudad != "--":
            tiendas = TIENDAS_CIUDAD.get(ciudad, {})
            opciones_t = ["--"] + sorted(list(tiendas.keys()))
            if producto == "PANADERÍA":
                col_p1, col_p2 = st.columns(2)
                with col_p1: o = st.selectbox("📦 Recoge en:", opciones_t)
                with col_p2: d = st.selectbox("🏠 Entrega en:", opciones_t)
                if o != "--" and d != "--": info = {"TO": o, "CO": tiendas[o], "TD": d, "CD": tiendas[d]}
            else:
                t = st.selectbox("🏪 Tienda:", opciones_t)
                if t != "--": info = {"TO": t, "CO": tiendas[t], "TD": t, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad:", min_value=1)
            if st.button("ENVIAR ✅", use_container_width=True):
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
                    # Usamos 'headers' para forzar a Google a aceptar el JSON
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                    if res.status_code == 200:
                        st.success("¡LOGRADO! Info en el Drive.")
                        st.session_state['hora_referencia'] = h_llegada
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Error {res.status_code}: El Drive rechazó la info.")
                except Exception as e:
                    st.error("La App no pudo conectar con el Drive. Revisa el link de implementación.")
