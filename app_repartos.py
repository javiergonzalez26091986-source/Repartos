import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# 1. Configuración de Zona Horaria Colombia
col_tz = pytz.timezone('America/Bogota')

st.set_page_config(page_title="SERGEM - Control Maestro v3", layout="wide")

# --- URL DEFINITIVA DE TU ÚLTIMA IMPLEMENTACIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbxBtAsWq2jhnVrqwhGIVXQ8Ue-aKybwZGp5WwvqIa4p5-Bdi7CROvos1dzy1su8_1Lh/exec"
DB_FILE = "registro_diario.csv"

# --- SIDEBAR: Recuperamos el botón de Reiniciar ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR JORNADA"):
        if os.path.exists(DB_FILE): 
            os.remove(DB_FILE)
        st.session_state['hora_referencia'] = ""
        st.success("Jornada reiniciada")
        st.rerun()
    st.write("---")
    st.caption("SERGEM App v3.0 | Cédula habilitada")

# --- BASE DE DATOS DE RUTAS ---
DATA_POLLOS = {
    'CALI': {'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 'SUPER INTER VILLA COLOMBIA': '4215', 'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 'CARULLA LA MARIA': '4781', 'ÉXITO CRA OCTAVA (L)': '650'},
    'MEDELLÍN': {'ÉXITO EXPRESS CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'ÉXITO GARDEL': '4070', 'SURTIMAX CALDAS': '4534', 'SURTIMAX PILARICA': '4557'},
    'BOGOTÁ': {'CARULLA EXPRESS CEDRITOS': '468', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX BRASIL BOSA': '311', 'SURTIMAX LA ESPAÑOLA': '449', 'SURTIMAX SAN ANTONIO': '450'}
}

RUTAS_PAN = {
    'CALI': [
        {'R': 'CARULLA CIUDAD JARDIN', 'RC': '2732540', 'E': 'CARULLA HOLGUINES', 'EC': '2596540'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'ÉXITO UNICALI', 'EC': '2054056'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'CARULLA CIUDAD JARDIN', 'EC': '2732540'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'CARULLA HOLGUINES', 'EC': '2596540'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'ÉXITO JAMUNDI', 'EC': '2054049'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'CARULLA AV COLOMBIA', 'EC': '4219540'}
    ]
}

if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = ""

st.title("🛵 Control Maestro SERGEM")

# --- IDENTIFICACIÓN DEL PERSONAL ---
col_id1, col_id2 = st.columns(2)
with col_id1:
    cedula = st.text_input("Número de Cédula:")
with col_id2:
    nombre = st.text_input("Nombre Completo:").upper()

if cedula and nombre:
    if st.session_state['hora_referencia'] == "":
        st.subheader("🕒 Iniciar Jornada")
        h_ini = st.time_input("Hora de salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            st.rerun()
    else:
        st.info(f"⏱️ Registro activo: **{nombre}** (CC: {cedula}) | Inicio: **{st.session_state['hora_referencia']}**")
        
        c1, c2 = st.columns(2)
        with c1:
            ciudad_sel = st.selectbox("📍 Ciudad:", ["--", "CALI", "MEDELLÍN", "BOGOTÁ"])
        with c2:
            prod_sel = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)

        info = None
        if ciudad_sel != "--":
            if prod_sel == "PANADERÍA":
                rutas = [f"{r['R']} -> {r['E']}" for r in RUTAS_PAN.get(ciudad_sel, [])]
                sel = st.selectbox("🛣️ Ruta de Panadería:", ["--"] + rutas)
                if sel != "--":
                    r = RUTAS_PAN[ciudad_sel][rutas.index(sel)]
                    info = {"O": r['R'], "C1": r['RC'], "D": r['E'], "C2": r['EC']}
            elif prod_sel == "POLLOS":
                tiendas = DATA_POLLOS.get(ciudad_sel, {})
                sel = st.selectbox("🏪 Tienda de Pollos:", ["--"] + list(tiendas.keys()))
                if sel != "--":
                    info = {"O": sel, "C1": tiendas[sel], "D": sel, "C2": "N/A"}

        if info:
            cant = st.number_input("Cantidad entregada:", min_value=1, step=1)
            if st.button("ENVIAR A LA NUBE ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                # Cálculo de minutos transcurridos
                t1 = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                t2 = datetime.strptime(h_llegada, "%H:%M")
                duracion = int((t2 - t1).total_seconds() / 60)
                
                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"),
                    "Cedula": cedula,
                    "Mensajero": nombre,
                    "Ciudad": ciudad_sel,
                    "Producto": prod_sel,
                    "Tienda": info["O"],
                    "Cod_Rec": str(info["C1"]),
                    "Cod_Ent": str(info["C2"]),
                    "Destino": info["D"],
                    "Cant": int(cant),
                    "Inicio": st.session_state['hora_referencia'],
                    "Llegada": h_llegada,
                    "Minutos": duracion
                }
                
                with st.spinner('Sincronizando con el Excel de Doña Yesenia...'):
                    try:
                        res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                        if "Éxito" in res.text:
                            st.success(f"¡Sincronizado! Entrega registrada en {info['D']}")
                            st.session_state['hora_referencia'] = h_llegada
                            # Respaldo local
                            pd.DataFrame([payload]).to_csv(DB_FILE, mode='a', index=False, header=not os.path.exists(DB_FILE))
                            st.rerun()
                    except:
                        st.error("Error de conexión. Verifique internet.")

    # Mostrar historial local si existe
    if os.path.exists(DB_FILE):
        try:
            df_hist = pd.read_csv(DB_FILE)
            if not df_hist.empty:
                st.markdown("---")
                st.subheader("📋 Últimos registros guardados")
                st.dataframe(df_hist.tail(5), use_container_width=True)
        except: pass
