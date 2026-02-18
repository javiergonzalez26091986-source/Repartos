import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
from streamlit_javascript import st_javascript

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="Control de entregas SERGEM", layout="wide")

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- FUNCIONES DE MEMORIA EN EL NAVEGADOR (Local Storage) ---
def set_local(key, value):
    st_javascript(f"localStorage.setItem('{key}', '{value}');")

def get_local(key):
    return st_javascript(f"localStorage.getItem('{key}');")

def clear_local():
    st_javascript("localStorage.clear();")

# --- INICIALIZACIÓN DE ESTADO ---
# Intentamos recuperar de la memoria del celular si se refresca la página
if 'cedula' not in st.session_state:
    st.session_state.cedula = ""
if 'nombre' not in st.session_state:
    st.session_state.nombre = ""
if 'hora_referencia' not in st.session_state:
    st.session_state.hora_referencia = ""

# --- RECUPERACIÓN AUTOMÁTICA AL REFRESCAR ---
# Esta parte lee lo que el celular guardó antes de refrescar
local_ced = get_local("sergem_ced")
local_nom = get_local("sergem_nom")
local_hora = get_local("sergem_hora")

if local_ced and not st.session_state.cedula:
    st.session_state.cedula = local_ced
    st.session_state.nombre = local_nom
    st.session_state.hora_referencia = local_hora if local_hora != "None" else ""

# --- INTERFAZ (Estética Original) ---
st.title("🛵 Control de entregas SERGEM")

with st.sidebar:
    if st.button("🏁 FINALIZAR DÍA", type="primary"):
        clear_local()
        st.session_state.clear()
        st.rerun()

c1, c2 = st.columns(2)
# Los campos donde se digita la cédula y nombre
cedula = c1.text_input("Cédula:", value=st.session_state.cedula)
nombre = c2.text_input("Nombre:", value=st.session_state.nombre).upper()

# Si se digitan datos nuevos, guardarlos en la memoria del celular inmediatamente
if cedula != st.session_state.cedula or nombre != st.session_state.nombre:
    st.session_state.cedula = cedula
    st.session_state.nombre = nombre
    set_local("sergem_ced", cedula)
    set_local("sergem_nom", nombre)

if st.session_state.cedula and st.session_state.nombre:
    # Lógica del Botón de Inicio
    if st.session_state.hora_referencia == "":
        st.subheader("🚀 Iniciar Jornada")
        if st.button("▶️ CAPTURAR HORA DE SALIDA", use_container_width=True):
            hora_str = datetime.now(col_tz).strftime("%H:%M")
            st.session_state.hora_referencia = hora_str
            set_local("sergem_hora", hora_str)
            st.rerun()
    
    else:
        st.info(f"✅ **Hora de Inicio para esta entrega:** {st.session_state.hora_referencia}")
        
        # --- BASES DE DATOS (Misma estructura) ---
        LISTA_CANAVERAL = ['20 DE JULIO', 'BRISAS DE LOS ALAMOS', 'BUGA', 'CAVASA (VIA CANDELARIA)', 'CENTENARIO (AV 4N)', 'COOTRAEMCALI', 'DOSQUEBRADAS (PEREIRA)', 'EL INGENIO', 'EL LIMONAR (CRA 70)', 'GUADALUPE (CALI)', 'JAMUNDÍ (COUNTRY MALL)', 'LOS PINOS', 'PALMIRA', 'PANCE', 'PASOANCHO (CALI)', 'PRADOS DEL NORTE (LA 34)', 'ROLDANILLO', 'SANTA HELENA', 'TULUA', 'VILLAGORGONA', 'VILLANUEVA']
        TIENDAS_PANADERIA = {'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES': '4219540', 'CARULLA PUNTO VERDE': '4799540', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA SAN FERNANDO': '2595540', 'CARULLA LA MARIA': '4781540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO LA FLORA': '2054540'}, 'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER SAN SEBASTIAN': '4303540', 'SUPERINTER MANIZALES CENTRO': '4273540', 'SUPERINTER CHIPRE': '4279540', 'SUPERINTER VILLA PILAR': '4280540'}}
        TIENDAS_POLLOS = {'CALI': {'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 'SUPER INTER VILLA COLOMBIA': '4215', 'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 'SUPER INTER SAN FERNANDO': '4232', 'SUPER INTER BUENOS AIRES': '4262', 'SUPER INTER VALDEMORO': '4233', 'CARULLA LA MARIA': '4781', 'SUPER INTER EXPRESS AV. SEXTA': '4212', 'SUPER INTER PASARELA': '4214', 'SUPER INTER PRIMAVERA': '4271', 'SUPER INTER INDEPENDENCIA': '4261', 'CARULLA PASOANCHO': '4799', 'ÉXITO CRA OCTAVA (L)': '650'}}

        f1, f2 = st.columns(2)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"], key="sel_ciu")
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True, key="rad_prod")
        
        opciones_empresa = ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER", "OTROS"]
        if ciudad in ["CALI", "MANIZALES"]: opciones_empresa.insert(2, "CAÑAVERAL")
        empresa = st.selectbox("🏢 Empresa:", opciones_empresa, key="sel_emp")

        # Lógica de asignación de tiendas (simplificada para asegurar funcionamiento)
        info = None
        if ciudad != "--" and empresa != "--":
            if empresa == "CAÑAVERAL":
                c_o = st.selectbox("📦 Origen:", ["--"] + sorted(LISTA_CANAVERAL), key="c_o")
                c_d = st.selectbox("🏠 Destino:", ["--"] + sorted(LISTA_CANAVERAL), key="c_d")
                if c_o != "--" and c_d != "--": info = {"TO": c_o, "CO": "CAN", "TD": c_d, "CD": "CAN"}
            elif empresa == "EXITO-CARULLA-SURTIMAX-SUPERINTER":
                dic = TIENDAS_PANADERIA.get(ciudad, {}) if producto == "PANADERÍA" else TIENDAS_POLLOS.get(ciudad, {})
                t_sel = st.selectbox("🏪 Tienda:", ["--"] + sorted(list(dic.keys())), key="t_sel")
                if t_sel != "--": info = {"TO": "BASE", "CO": "BASE", "TD": t_sel, "CD": dic[t_sel]}
            else:
                ext = st.text_input("Nombre Externo:", key="txt_ext").upper()
                if ext: info = {"TO": "OTRO", "CO": "N/A", "TD": ext, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1, key="cant_val")
            if st.button("ENVIAR REGISTRO ✅", use_container_width=True, type="primary"):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                # Cálculo de minutos
                t_ini = datetime.strptime(st.session_state.hora_referencia, "%H:%M")
                t_fin = datetime.strptime(h_llegada, "%H:%M")
                minutos = int((t_fin - t_ini).total_seconds() / 60)
                if minutos < 0: minutos += 1440

                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), "Cedula": cedula, "Mensajero": nombre,
                    "Empresa": empresa, "Ciudad": ciudad, "Producto": producto,
                    "Tienda_O": info["TO"], "Cod_O": info["CO"], "Cod_D": info["CD"], "Tienda_D": info["TD"],
                    "Cant": int(cant), "Inicio": st.session_state.hora_referencia, "Llegada": h_llegada, "Minutos": minutos
                }
                
                try:
                    requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=10)
                    st.success("¡Enviado!")
                    # Actualizar hora para siguiente viaje y guardar en memoria del celular
                    st.session_state.hora_referencia = h_llegada
                    set_local("sergem_hora", h_llegada)
                    
                    # Limpiar selectores
                    for k in ['sel_ciu', 'sel_emp', 'c_o', 'c_d', 't_sel', 'txt_ext', 'cant_val']:
                        if k in st.session_state: del st.session_state[k]
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("Error de conexión al Drive")
