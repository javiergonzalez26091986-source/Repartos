import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time

# 1. Configuración de Zona Horaria
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="Control SERGEM", layout="wide")

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- LÓGICA DE PERSISTENCIA POR URL (Inmune a refrescos) ---
def actualizar_url():
    st.query_params.update({
        "ced": st.session_state.cedula,
        "nom": st.session_state.nombre,
        "hor": st.session_state.hora_ref
    })

# Recuperar datos de la URL si existen (esto ocurre al refrescar)
params = st.query_params
if "ced" in params and 'cedula' not in st.session_state:
    st.session_state.cedula = params["ced"]
    st.session_state.nombre = params["nom"]
    st.session_state.hora_ref = params["hor"]

# Inicializar sesión si está vacío
if 'cedula' not in st.session_state: st.session_state.cedula = ""
if 'nombre' not in st.session_state: st.session_state.nombre = ""
if 'hora_ref' not in st.session_state: st.session_state.hora_ref = ""

# --- INTERFAZ ---
st.title("🛵 Control de entregas SERGEM")

with st.sidebar:
    if st.button("🏁 FINALIZAR DÍA", type="primary"):
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()

# --- BLOQUE DE IDENTIFICACIÓN ---
c1, c2 = st.columns(2)
ced_input = c1.text_input("Cédula:", value=st.session_state.cedula)
nom_input = c2.text_input("Nombre:", value=st.session_state.nombre).upper()

# Si el usuario escribe, guardamos en URL para que no se pierda
if ced_input != st.session_state.cedula or nom_input != st.session_state.nombre:
    st.session_state.cedula = ced_input
    st.session_state.nombre = nom_input
    actualizar_url()

if st.session_state.cedula and st.session_state.nombre:
    
    # 1. CAPTURA DE HORA INICIAL
    if st.session_state.hora_ref == "" or st.session_state.hora_ref == "None":
        st.subheader("🚀 Iniciar Jornada")
        if st.button("▶️ CAPTURAR HORA DE SALIDA", use_container_width=True):
            h_act = datetime.now(col_tz).strftime("%H:%M")
            st.session_state.hora_ref = h_act
            actualizar_url()
            st.rerun()
    
    # 2. FORMULARIO DE ENTREGAS
    else:
        st.info(f"✅ **Hora de Inicio para esta entrega:** {st.session_state.hora_ref}")
        
        # BASES DE DATOS
        LISTA_CANAVERAL = ['20 DE JULIO', 'BRISAS DE LOS ALAMOS', 'BUGA', 'CAVASA (VIA CANDELARIA)', 'CENTENARIO (AV 4N)', 'COOTRAEMCALI', 'DOSQUEBRADAS (PEREIRA)', 'EL INGENIO', 'EL LIMONAR (CRA 70)', 'GUADALUPE (CALI)', 'JAMUNDÍ (COUNTRY MALL)', 'LOS PINOS', 'PALMIRA', 'PANCE', 'PASOANCHO (CALI)', 'PRADOS DEL NORTE (LA 34)', 'ROLDANILLO', 'SANTA HELENA', 'TULUA', 'VILLAGORGONA', 'VILLANUEVA']
        TIENDAS_PANADERIA = {'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES': '4219540', 'CARULLA PUNTO VERDE': '4799540', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA SAN FERNANDO': '2595540', 'CARULLA LA MARIA': '4781540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO LA FLORA': '2054540'}, 'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER SAN SEBASTIAN': '4303540', 'SUPERINTER MANIZALES CENTRO': '4273540', 'SUPERINTER CHIPRE': '4279540', 'SUPERINTER VILLA PILAR': '4280540'}}
        TIENDAS_POLLOS = {'CALI': {'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 'SUPER INTER VILLA COLOMBIA': '4215', 'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 'SUPER INTER SAN FERNANDO': '4232', 'SUPER INTER BUENOS AIRES': '4262', 'SUPER INTER VALDEMORO': '4233', 'CARULLA LA MARIA': '4781', 'SUPER INTER EXPRESS AV. SEXTA': '4212', 'SUPER INTER PASARELA': '4214', 'SUPER INTER PRIMAVERA': '4271', 'SUPER INTER INDEPENDENCIA': '4261', 'CARULLA PASOANCHO': '4799', 'ÉXITO CRA OCTAVA (L)': '650'}}

        f1, f2 = st.columns(2)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"], key="s_ciu")
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True, key="s_prod")
        
        empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER", "CAÑAVERAL", "OTROS"], key="s_emp")

        info = None
        if ciudad != "--" and empresa != "--":
            if empresa == "CAÑAVERAL":
                o = st.selectbox("📦 Origen:", ["--"] + sorted(LISTA_CANAVERAL), key="co")
                d = st.selectbox("🏠 Destino:", ["--"] + sorted(LISTA_CANAVERAL), key="cd")
                if o != "--" and d != "--": info = {"TO": o, "CO": "CAN", "TD": d, "CD": "CAN"}
            elif empresa == "EXITO-CARULLA-SURTIMAX-SUPERINTER":
                dic = TIENDAS_PANADERIA.get(ciudad, {}) if producto == "PANADERÍA" else TIENDAS_POLLOS.get(ciudad, {})
                t = st.selectbox("🏪 Tienda:", ["--"] + sorted(list(dic.keys())), key="ct")
                if t != "--": info = {"TO": "BASE", "CO": "BASE", "TD": t, "CD": dic[t]}
            else:
                ext = st.text_input("Nombre Externo:", key="ce").upper()
                if ext: info = {"TO": "OTRO", "CO": "N/A", "TD": ext, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1, key="ccant")
            if st.button("ENVIAR REGISTRO ✅", use_container_width=True, type="primary"):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                # Calcular minutos desde la hora_ref actual
                t_ini = datetime.strptime(st.session_state.hora_ref, "%H:%M")
                t_fin = datetime.strptime(h_llegada, "%H:%M")
                minutos = int((t_fin - t_ini).total_seconds() / 60)
                if minutos < 0: minutos += 1440

                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), "Cedula": st.session_state.cedula, "Mensajero": st.session_state.nombre,
                    "Empresa": empresa, "Ciudad": ciudad, "Producto": producto,
                    "Tienda_O": info["TO"], "Cod_O": info["CO"], "Cod_D": info["CD"], "Tienda_D": info["TD"],
                    "Cant": int(cant), "Inicio": st.session_state.hora_ref, "Llegada": h_llegada, "Minutos": minutos
                }
                
                try:
                    requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=10)
                    st.success(f"¡Registro enviado! Nueva hora de inicio: {h_llegada}")
                    
                    # AQUÍ ESTÁ EL TRUCO: Actualizamos la hora de referencia con la de llegada
                    st.session_state.hora_ref = h_llegada
                    actualizar_url() # Guardamos en la URL para el próximo viaje
                    
                    # Limpiar selectores de tienda pero NO la cédula/hora
                    for k in ['s_ciu', 's_emp', 'co', 'cd', 'ct', 'ce', 'ccant']:
                        if k in st.session_state: del st.session_state[k]
                    
                    time.sleep(1.5)
                    st.rerun()
                except:
                    st.error("Error al enviar. Verifique su conexión.")
