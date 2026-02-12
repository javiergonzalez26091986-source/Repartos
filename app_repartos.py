import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# 1. Configuración de Zona Horaria Colombia
col_tz = pytz.timezone('America/Bogota')

st.set_page_config(page_title="SERGEM - Control Maestro v3.2", layout="wide")

# --- URL DEFINITIVA (Asegúrate de que sea la de tu última implementación de 13 columnas) ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbxBtAsWq2jhnVrqwhGIVXQ8Ue-aKybwZGp5WwvqIa4p5-Bdi7CROvos1dzy1su8_1Lh/exec"
DB_FILE = "registro_diario.csv"

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR JORNADA"):
        if os.path.exists(DB_FILE): 
            os.remove(DB_FILE)
        st.session_state['hora_referencia'] = ""
        st.rerun()
    st.write("---")
    st.caption("SERGEM App v3.2 | Full Ciudades | Cédula")

# --- BASE DE DATOS DE RUTAS Y TIENDAS ---
DATA_POLLOS = {
    'CALI': {'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 'SUPER INTER VILLA COLOMBIA': '4215', 'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 'CARULLA LA MARIA': '4781', 'ÉXITO CRA OCTAVA (L)': '650'},
    'MEDELLÍN': {'ÉXITO EXPRESS CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'ÉXITO GARDEL': '4070', 'SURTIMAX CALDAS': '4534', 'SURTIMAX PILARICA': '4557'},
    'BOGOTÁ': {'CARULLA EXPRESS CEDRITOS': '468', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX BRASIL BOSA': '311', 'SURTIMAX LA ESPAÑOLA': '449', 'SURTIMAX SAN ANTONIO': '450'},
    'MANIZALES': {'ÉXITO MANIZALES Centro': '383', 'CARULLA CABLE PLAZA': '2334', 'CARULLA SAN MARCEL': '4805'}
}

RUTAS_PAN = {
    'CALI': [
        {'R': 'CARULLA CIUDAD JARDIN', 'RC': '2732540', 'E': 'CARULLA HOLGUINES', 'EC': '2596540'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'ÉXITO UNICALI', 'EC': '2054056'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'CARULLA CIUDAD JARDIN', 'EC': '2732540'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'CARULLA HOLGUINES', 'EC': '2596540'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'ÉXITO JAMUNDI', 'EC': '2054049'},
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'CARULLA AV COLOMBIA', 'EC': '4219540'}
    ],
    'MANIZALES': [
        {'R': 'CARULLA CABLE PLAZA', 'RC': '2334540', 'E': 'SUPERINTER CRISTO REY', 'EC': '4301540'},
        {'R': 'CARULLA CABLE PLAZA', 'RC': '2334540', 'E': 'SUPERINTER ALTA SUIZA', 'EC': '4302540'},
        {'R': 'ÉXITO MANIZALES', 'RC': '383', 'E': 'SUPERINTER MANIZALES CENTRO', 'EC': '4273540'},
        {'R': 'CARULLA SAN MARCEL', 'RC': '4805', 'E': 'CARULLA SAN MARCEL', 'EC': '4805'}
    ]
}

if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = ""

st.title("🛵 Control Maestro SERGEM")

# --- SECCIÓN 1: IDENTIFICACIÓN ---
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
        st.info(f"👤 **Mensajero:** {nombre} | **CC:** {cedula} | **Inicio:** {st.session_state['hora_referencia']}")
        
        # --- SECCIÓN 2: DATOS DEL REPARTO ---
        c1, c2 = st.columns(2)
        with c1:
            ciudad_sel = st.selectbox("📍 Seleccione Ciudad:", ["--", "CALI", "MEDELLÍN", "BOGOTÁ", "MANIZALES"])
        with c2:
            prod_sel = st.radio("📦 Seleccione Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)

        info_reg = None
        if ciudad_sel != "--":
            if prod_sel == "PANADERÍA":
                rutas_disponibles = RUTAS_PAN.get(ciudad_sel, [])
                opciones = [f"{r['R']} -> {r['E']}" for r in rutas_disponibles]
                sel_ruta = st.selectbox("🛣️ Seleccione Ruta:", ["--"] + opciones)
                if sel_ruta != "--":
                    idx = opciones.index(sel_ruta)
                    r = rutas_disponibles[idx]
                    info_reg = {"T_O": r['R'], "C1": r['RC'], "T_D": r['E'], "C2": r['EC']}
            
            elif prod_sel == "POLLOS":
                tiendas = DATA_POLLOS.get(ciudad_sel, {})
                sel_tienda = st.selectbox("🏪 Seleccione Tienda:", ["--"] + list(tiendas.keys()))
                if sel_tienda != "--":
                    info_reg = {"T_O": sel_tienda, "C1": tiendas[sel_tienda], "T_D": sel_tienda, "C2": "N/A"}

        if info_reg:
            cant = st.number_input("Cantidad:", min_value=1, step=1)
            
            # --- SECCIÓN 3: ENVÍO ---
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
                    "Tienda": info_reg["T_O"],    # Columna E
                    "Cod_Rec": str(info_reg["C1"]), # Columna F
                    "Cod_Ent": str(info_reg["C2"]), # Columna G
                    "Destino": info_reg["T_D"],    # Columna H
                    "Cant": int(cant),
                    "Inicio": st.session_state['hora_referencia'],
                    "Llegada": h_llegada,
                    "Minutos": duracion
                }
                
                with st.spinner('Sincronizando...'):
                    try:
                        res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                        if res.status_code == 200 and "Éxito" in res.text:
                            st.success(f"¡Sincronizado! Entrega registrada en {info_reg['T_D']}")
                            st.session_state['hora_referencia'] = h_llegada
                            # Guardado local
                            pd.DataFrame([payload]).to_csv(DB_FILE, mode='a', index=False, header=not os.path.exists(DB_FILE))
                            st.rerun()
                        else:
                            st.error(f"Error en el servidor: {res.text}")
                    except:
                        st.error("Error de conexión: Los datos no se enviaron. Revisa tu internet.")

    # --- SECCIÓN 4: HISTORIAL LOCAL ---
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if not df.empty:
                st.markdown("---")
                st.subheader("📋 Respaldo local (Últimos 5)")
                st.dataframe(df.tail(5), use_container_width=True)
        except:
            pass
