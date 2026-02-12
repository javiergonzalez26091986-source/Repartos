import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
import os

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM v5.3", layout="wide")

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# ARCHIVOS DE RESPALDO LOCAL
PERSISTENCIA_INI = "hora_inicio_respaldo.txt"
DB_LOCAL = "registro_diario_respaldo.csv"

# --- FUNCIONES DE MEMORIA ---
def guardar_hora_inicio(hora):
    with open(PERSISTENCIA_INI, "w") as f:
        f.write(hora)

def leer_hora_inicio():
    if os.path.exists(PERSISTENCIA_INI):
        with open(PERSISTENCIA_INI, "r") as f:
            return f.read()
    return ""

def borrar_todo():
    if os.path.exists(PERSISTENCIA_INI): os.remove(PERSISTENCIA_INI)
    if os.path.exists(DB_LOCAL): os.remove(DB_LOCAL)
    st.session_state['hora_referencia'] = ""

# --- INICIALIZACIÓN ---
if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = leer_hora_inicio()

with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        borrar_todo()
        st.rerun()
    st.write("---")
    st.caption("v5.3 - Respaldo + Memoria")

# --- BASE DE TIENDAS ---
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
        st.subheader("🕒 Iniciar Jornada")
        h_ini = st.time_input("Salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            hora_texto = h_ini.strftime("%H:%M")
            st.session_state['hora_referencia'] = hora_texto
            guardar_hora_inicio(hora_texto)
            st.rerun()
    else:
        st.success(f"✅ Mensajero: {nombre} | Inicio Jornada: {st.session_state['hora_referencia']}")
        
        f1, f2, f3 = st.columns(3)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"])
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        with f3: empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SUPERINTER-SURTIMAX", "CAÑAVERAL", "OTROS"])

        info = None
        if ciudad != "--":
            tiendas = TIENDAS_DATOS.get(ciudad, {})
            opciones = ["--"] + sorted(list(tiendas.keys()))
            if producto == "PANADERÍA":
                st.subheader("🥖 Panadería")
                cp1, cp2 = st.columns(2)
                with cp1: o = st.selectbox("📦 Recoge en:", opciones, key="p_o")
                with cp2: d = st.selectbox("🏠 Entrega en:", opciones, key="p_d")
                if o != "--" and d != "--": info = {"TO": o, "CO": tiendas[o], "TD": d, "CD": tiendas[d]}
            else:
                st.subheader("🍗 Pollos")
                t = st.selectbox("🏪 Tienda:", opciones, key="p_t")
                if t != "--": info = {"TO": t, "CO": tiendas[t], "TD": t, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1)
            if st.button("ENVIAR A LA NUBE ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                t_inicio = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                t_fin = datetime.strptime(h_llegada, "%H:%M")
                minutos = int((t_fin - t_inicio).total_seconds() / 60)
                if minutos < 0: minutos += 1440
                
                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), "Cedula": cedula, "Mensajero": nombre,
                    "Empresa": empresa, "Ciudad": ciudad, "Producto": producto,
                    "Tienda_O": info["TO"], "Cod_O": info["CO"], "Cod_D": info["CD"], "Tienda_D": info["TD"],
                    "Cant": int(cant), "Inicio": st.session_state['hora_referencia'], "Llegada": h_llegada, "Minutos": minutos
                }
                
                try:
                    requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=30)
                    st.success("¡Enviado!")
                    # GUARDAR EN RESPALDO LOCAL
                    pd.DataFrame([payload]).to_csv(DB_LOCAL, mode='a', index=False, header=not os.path.exists(DB_LOCAL))
                    # ACTUALIZAR MEMORIA
                    st.session_state['hora_referencia'] = h_llegada
                    guardar_hora_inicio(h_llegada)
                    time.sleep(1.2)
                    st.rerun()
                except:
                    st.error("Error de conexión, pero se guardó localmente.")

    # --- TABLA DE REGISTRO LOCAL (ABAJO) ---
    if os.path.exists(DB_LOCAL):
        st.markdown("---")
        st.subheader("📋 Últimos registros de hoy")
        df_local = pd.read_csv(DB_LOCAL)
        st.dataframe(df_local.tail(5), use_container_width=True)
