import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# Configuración de Zona Horaria Colombia
col_tz = pytz.timezone('America/Bogota')

st.set_page_config(page_title="SERGEM - Control Maestro Nube", layout="wide")

# --- CONFIGURACIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbz7247cJGrI1TYEse0OjdsUlnqruEGoPRrZTmSki8gtL29bqtH6l7y6FISnS0sjoQI/exec"
DB_FILE = "registro_diario.csv"

# --- DATOS DE RUTAS ---
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
        {'R': 'CARULLA PANCE', 'RC': '2594540', 'E': 'CARULLA AV COLOMBIA', 'EC': '4219540'},
        {'R': 'CARULLA CIUDAD JARDIN', 'RC': '2732540', 'E': 'CARULLA PUNTO VERDE', 'EC': '4799540'},
        {'R': 'CARULLA CIUDAD JARDIN', 'RC': '2732540', 'E': 'CARULLA AV COLOMBIA', 'EC': '4219540'},
        {'R': 'CARULLA CIUDAD JARDIN', 'RC': '2732540', 'E': 'ÉXITO LA FLORA', 'EC': '2054540'},
        {'R': 'CARULLA HOLGUINES', 'RC': '2596540', 'E': 'CARULLA PUNTO VERDE', 'EC': '4799540'},
        {'R': 'CARULLA SAN FERNANDO', 'RC': '2595540', 'E': 'CARULLA AV COLOMBIA', 'EC': '4219540'}
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

with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR JORNADA"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state['hora_referencia'] = ""
        st.rerun()

nombre = st.text_input("Nombre del Mensajero:").upper()

if nombre:
    if st.session_state['hora_referencia'] == "":
        st.subheader("🕒 Iniciar Jornada")
        h_ini = st.time_input("Hora de salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            st.rerun()
    else:
        st.info(f"⏱️ Tiempo cronometrado desde: **{st.session_state['hora_referencia']}**")
        
        col1, col2 = st.columns(2)
        with col1:
            ciudad_sel = st.selectbox("📍 1. Seleccione Ciudad:", ["--", "CALI", "MEDELLÍN", "BOGOTÁ", "MANIZALES"])
        with col2:
            producto_sel = st.radio("📦 2. Seleccione Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)

        info_reg = None

        if ciudad_sel != "--":
            if producto_sel == "PANADERÍA":
                if ciudad_sel in RUTAS_PAN:
                    rutas = RUTAS_PAN[ciudad_sel]
                    opciones = [f"Rec: {r['R']} -> Ent: {r['E']}" for r in rutas]
                    sel_ruta = st.selectbox("🛣️ 3. Seleccione Ruta:", ["--"] + opciones)
                    if sel_ruta != "--":
                        idx = opciones.index(sel_ruta)
                        r = rutas[idx]
                        # Tienda mostrará la ruta completa: Origen a Destino
                        info_reg = {"Tienda": f"{r['R']} -> {r['E']}", "C1": r['RC'], "C2": r['EC']}
            
            elif producto_sel == "POLLOS":
                tiendas = DATA_POLLOS.get(ciudad_sel, {})
                if tiendas:
                    sel_tienda = st.selectbox("🏪 3. Seleccione Tienda:", ["--"] + list(tiendas.keys()))
                    if sel_tienda != "--":
                        # Tienda mostrará el nombre seleccionado directamente
                        info_reg = {"Tienda": sel_tienda, "C1": tiendas[sel_tienda], "C2": "N/A"}

        if info_reg:
            cant = st.number_input("Cantidad:", min_value=1, step=1)
            if st.button("ENVIAR A LA NUBE ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                hora_llegada = ahora.strftime("%H:%M")
                
                t1 = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                t2 = datetime.strptime(hora_llegada, "%H:%M")
                duracion = int((t2 - t1).total_seconds() / 60)
                
                datos = {
                    "Fecha": ahora.strftime("%d/%m/%Y"),
                    "Mensajero": nombre,
                    "Ciudad": ciudad_sel,
                    "Producto": producto_sel,
                    "Tienda": info_reg["Tienda"],  # <--- Aquí ya enviamos el nombre claro
                    "Cod_Rec": str(info_reg["C1"]),
                    "Cod_Ent": str(info_reg["C2"]),
                    "Cant": int(cant),
                    "Inicio": st.session_state['hora_referencia'],
                    "Llegada": hora_llegada,
                    "Minutos": int(duracion)
                }
                
                with st.spinner('Sincronizando con Google Sheets...'):
                    try:
                        response = requests.post(URL_GOOGLE_SCRIPT, json=datos, timeout=15)
                        if response.status_code == 200:
                            st.success("¡Datos enviados a la nube!")
                            st.session_state['hora_referencia'] = hora_llegada
                            pd.DataFrame([datos]).to_csv(DB_FILE, mode='a', index=False, header=not os.path.exists(DB_FILE))
                            st.rerun()
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

    # Bloque de respaldo local con protección contra archivos vacíos
    if os.path.exists(DB_FILE):
        st.markdown("---")
        st.subheader("📋 Respaldo local")
        try:
            df_historial = pd.read_csv(DB_FILE)
            if not df_historial.empty:
                st.dataframe(df_historial.tail(5), use_container_width=True)
        except:
            pass
