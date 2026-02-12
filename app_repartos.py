import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
import os

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM v5.4", layout="wide")

# --- ¡IMPORTANTE! VERIFICA ESTE LINK ---
# Si generaste uno nuevo en Apps Script, pégalo aquí.
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

PERSISTENCIA_INI = "hora_inicio_respaldo.txt"
DB_LOCAL = "registro_diario_respaldo.csv"

def guardar_hora_inicio(hora):
    with open(PERSISTENCIA_INI, "w") as f: f.write(hora)

def leer_hora_inicio():
    if os.path.exists(PERSISTENCIA_INI):
        with open(PERSISTENCIA_INI, "r") as f: return f.read()
    return ""

def borrar_todo():
    if os.path.exists(PERSISTENCIA_INI): os.remove(PERSISTENCIA_INI)
    if os.path.exists(DB_LOCAL): os.remove(DB_LOCAL)
    st.session_state['hora_referencia'] = ""

if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = leer_hora_inicio()

with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        borrar_todo()
        st.rerun()
    st.caption("v5.4 - Conexión Optimizada")

# --- TIENDAS (Mantenemos todas las ciudades y códigos) ---
TIENDAS_DATOS = {
    'CALI': {
        'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA HOLGUINES': '2596540', 'CARULLA PANCE': '2594540', 
        'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'CARULLA AV COLOMBIA': '4219540',
        'CARULLA PUI': '4799540', 'ÉXITO LA FLORA': '2054540', 'CARULLA SANTA RITA': '2595540',
        'SUPER INTER POPULAR': '4210', 'CAÑAVERAL PASOANCHO': 'CAN01'
    },
    'MANIZALES': {
        'CARULLA CABLE PLAZA': '2334540', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540',
        'ÉXITO MANIZALES': '383', 'SUPERINTER CENTRO': '4273540', 'CARULLA SAN MARCEL': '4805'
    },
    'MEDELLÍN': {'ÉXITO CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'SURTIMAX CALDAS': '4534'},
    'BOGOTÁ': {'CARULLA CEDRITOS': '468', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX BOSA': '311'}
}

st.title("🛵 Control Maestro SERGEM")

c1, c2 = st.columns(2)
with c1: cedula = st.text_input("Cédula:", key="ced")
with c2: nombre = st.text_input("Nombre:", key="nom").upper()

if cedula and nombre:
    if st.session_state['hora_referencia'] == "":
        h_ini = st.time_input("Salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            guardar_hora_inicio(st.session_state['hora_referencia'])
            st.rerun()
    else:
        st.success(f"✅ {nombre} | Inicio: {st.session_state['hora_referencia']}")
        f1, f2, f3 = st.columns(3)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"])
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        with f3: empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SUPERINTER-SURTIMAX", "CAÑAVERAL", "OTROS"])

        info = None
        if ciudad != "--":
            tiendas = TIENDAS_DATOS.get(ciudad, {})
            opciones = ["--"] + sorted(list(tiendas.keys()))
            if producto == "PANADERÍA":
                col_p1, col_p2 = st.columns(2)
                with col_p1: o = st.selectbox("📦 Recoge en:", opciones, key="p_o")
                with col_p2: d = st.selectbox("🏠 Entrega en:", opciones, key="p_d")
                if o != "--" and d != "--": info = {"TO": o, "CO": tiendas[o], "TD": d, "CD": tiendas[d]}
            else:
                t = st.selectbox("🏪 Tienda:", opciones, key="p_t")
                if t != "--": info = {"TO": t, "CO": tiendas[t], "TD": t, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1)
            if st.button("ENVIAR A LA NUBE ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                t_ini = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                t_fin = datetime.strptime(h_llegada, "%H:%M")
                minutos = int((t_fin - t_ini).total_seconds() / 60)
                if minutos < 0: minutos += 1440
                
                # Payload con nombres de columnas exactos al Excel
                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), "Cedula": cedula, "Mensajero": nombre,
                    "Empresa": empresa, "Ciudad": ciudad, "Producto": producto,
                    "Tienda_O": info["TO"], "Cod_O": info["CO"], "Cod_D": info["CD"], "Tienda_D": info["TD"],
                    "Cant": int(cant), "Inicio": st.session_state['hora_referencia'], "Llegada": h_llegada, "Minutos": minutos
                }
                
                # GUARDAR SIEMPRE EN RESPALDO LOCAL PRIMERO
                pd.DataFrame([payload]).to_csv(DB_LOCAL, mode='a', index=False, header=not os.path.exists(DB_LOCAL))
                
                try:
                    # Intento de envío con timeout largo
                    response = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=35)
                    if response.status_code == 200:
                        st.success("¡Sincronizado con Google Sheets!")
                    else:
                        st.warning("Guardado localmente. El Drive no respondió (Error servidor).")
                    
                    st.session_state['hora_referencia'] = h_llegada
                    guardar_hora_inicio(h_llegada)
                    time.sleep(1.5)
                    st.rerun()
                except:
                    st.error("Error de red. El registro quedó guardado en el teléfono.")
                    st.session_state['hora_referencia'] = h_llegada
                    guardar_hora_inicio(h_llegada)

    if os.path.exists(DB_LOCAL):
        st.markdown("---")
        st.subheader("📋 Respaldo de Entregas Realizadas")
        df_l = pd.read_csv(DB_LOCAL)
        st.dataframe(df_l.tail(10), use_container_width=True)
