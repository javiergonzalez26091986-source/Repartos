import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM - Control Maestro v4.3", layout="wide")

# --- NUEVOS LINKS DE IMPLEMENTACIÓN ACTUALIZADOS ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- BASE DE DATOS DE TIENDAS ---
TIENDAS_DATOS = {
    'CALI': {
        'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA HOLGUINES': '2596540', 
        'CARULLA PANCE': '2594540', 'ÉXITO UNICALI': '2054056', 
        'ÉXITO JAMUNDI': '2054049', 'CARULLA AV COLOMBIA': '4219540',
        'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206',
        'CAÑAVERAL PASOANCHO': 'CAN01', 'CAÑAVERAL SUR': 'CAN02'
    },
    'MANIZALES': {
        'CARULLA CABLE PLAZA': '2334540', 'SUPERINTER CRISTO REY': '4301540',
        'SUPERINTER ALTA SUIZA': '4302540', 'ÉXITO MANIZALES': '383',
        'SUPERINTER MANIZALES CENTRO': '4273540', 'CARULLA SAN MARCEL': '4805'
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
c_id1, c_id2 = st.columns(2)
with c_id1:
    cedula = st.text_input("Cédula:")
with c_id2:
    nombre = st.text_input("Nombre:").upper()

if cedula and nombre:
    if st.session_state['hora_referencia'] == "":
        st.subheader("🕒 Iniciar Jornada")
        h_ini = st.time_input("Hora de salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            st.rerun()
    else:
        st.success(f"✅ Mensajero: **{nombre}** | Inicio: **{st.session_state['hora_referencia']}**")
        
        # --- FILTROS ---
        f1, f2, f3 = st.columns(3)
        with f1:
            ciudad_sel = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"])
        with f2:
            prod_sel = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        with f3:
            empresa_sel = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SUPERINTER-SURTIMAX", "CAÑAVERAL", "OTROS"])

        info = None
        if ciudad_sel != "--":
            tiendas_ciudad = TIENDAS_DATOS.get(ciudad_sel, {})
            opciones = ["--"] + sorted(list(tiendas_ciudad.keys()))
            
            if prod_sel == "PANADERÍA":
                st.subheader("🥖 Ruta de Panadería")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    orig = st.selectbox("📦 Recoge en:", opciones, key="p_orig")
                with col_p2:
                    dest = st.selectbox("🏠 Entrega en:", opciones, key="p_dest")
                
                if orig != "--" and dest != "--":
                    info = {"TO": orig, "CO": tiendas_ciudad[orig], "TD": dest, "CD": tiendas_ciudad[dest]}
            else:
                st.subheader("🍗 Entrega de Pollos")
                tienda = st.selectbox("🏪 Tienda:", opciones, key="p_pollos")
                if tienda != "--":
                    info = {"TO": tienda, "CO": tiendas_ciudad[tienda], "TD": tienda, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad:", min_value=1)
            msg_status = st.empty()
            
            if st.button("ENVIAR A LA NUBE ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                # Cálculo de minutos
                t1 = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                t2 = datetime.strptime(h_llegada, "%H:%M")
                duracion = int((t2 - t1).total_seconds() / 60)
                
                # Payload alineado a 14 columnas para Google Sheets
                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), 
                    "Cedula": cedula, 
                    "Mensajero": nombre,
                    "Empresa": empresa_sel, 
                    "Ciudad": ciudad_sel, 
                    "Producto": prod_sel,
                    "Tienda_O": info["TO"], 
                    "Cod_O": info["CO"], 
                    "Cod_D": info["CD"], 
                    "Tienda_D": info["TD"],
                    "Cant": int(cant), 
                    "Inicio": st.session_state['hora_referencia'], 
                    "Llegada": h_llegada, 
                    "Minutos": duracion
                }
                
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    if "Éxito" in res.text:
                        msg_status.success(f"¡Sincronizado! De {info['TO']} a {info['TD']}")
                        st.session_state['hora_referencia'] = h_llegada
                        st.rerun()
                    else:
                        msg_status.error(f"Error en servidor: {res.text}")
                except:
                    msg_status.error("Falla de conexión. Intente de nuevo.")
