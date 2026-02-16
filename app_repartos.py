import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
import os

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM v6.3.0 - Predictiva", layout="wide")

# URL DE TU IMPLEMENTACIÓN (Asegúrate de que sea esta la vigente)
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

PERSISTENCIA_INI = "hora_inicio_respaldo.txt"
DB_LOCAL = "registro_diario_respaldo.csv"

# --- FUNCIONES DE MEMORIA Y LIMPIEZA ---
def guardar_memoria(hora):
    with open(PERSISTENCIA_INI, "w") as f: f.write(hora)

def leer_memoria():
    if os.path.exists(PERSISTENCIA_INI):
        with open(PERSISTENCIA_INI, "r") as f: return f.read()
    return ""

def finalizar_operacion():
    if os.path.exists(PERSISTENCIA_INI): os.remove(PERSISTENCIA_INI)
    if os.path.exists(DB_LOCAL): os.remove(DB_LOCAL)
    for key in st.session_state.keys():
        del st.session_state[key]
    st.success("Operación cerrada. ¡Buen descanso!")
    time.sleep(2)
    st.rerun()

def limpiar_entrega():
    # Solo limpiamos selecciones, mantenemos cédula y nombre
    for clave in ['sel_ciu', 'sel_emp', 'rad_prod', 'c_o', 'c_d', 'p_o_v', 'p_d_v', 'p_o_gen', 'p_d_gen', 'pol_gen', 'cant_val']:
        if clave in st.session_state: del st.session_state[clave]

if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = leer_memoria()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Menú")
    if st.button("🏁 FINALIZAR DÍA", use_container_width=True, type="primary"):
        finalizar_operacion()

# --- BASE DE DATOS AMPLIADA (CAÑAVERAL Y OTROS) ---
CIUDADES = ["CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ", "JAMUNDÍ", "PALMIRA", "BUGA", "TULUA"]

LISTA_CANAVERAL = [
    'CENTENARIO (AV 4N)', 'SANTA HELENA', 'PRADOS DEL NORTE (LA 34)', 'EL INGENIO', 
    'EL LIMONAR (CRA 70)', 'PANCE', 'BRISAS DE LOS ALAMOS', '20 DE JULIO', 
    'LOS PINOS', 'CAVASA', 'JAMUNDÍ (COUNTRY MALL)', 'PALMIRA', 'BUGA', 'TULUA', 
    'VILLAGORGONA', 'VILLANUEVA', 'COOTRAEMCALI', 'ROLDANILLO'
]

TIENDAS_PANADERIA = {
    'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES (TRADE CENTER)': '4219540', 'CARULLA PUNTO VERDE': '4799540', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA SAN FERNANDO': '2595540', 'CARULLA LA MARIA': '4781540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO LA FLORA': '2054540', 'CARULLA HOLGUINES (ENTREGA)': '2596540'},
    'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER SAN SEBASTIAN': '4303540', 'SUPERINTER MANIZALES CENTRO': '4273540', 'SUPERINTER CHIPRE': '4279540', 'SUPERINTER VILLA PILAR': '4280540'}
}

# --- INTERFAZ ---
st.title("🛵 Control Maestro SERGEM v6.3.0")

# Campos de usuario con memoria
c1, c2 = st.columns(2)
with c1: cedula = st.text_input("Cédula:", key="ced")
with c2: nombre = st.text_input("Nombre:", key="nom").upper()

if cedula and nombre:
    if st.session_state['hora_referencia'] == "":
        st.subheader("🕒 Inicio de Jornada")
        h_ini = st.time_input("Salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR OPERACIÓN"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            guardar_memoria(st.session_state['hora_referencia'])
            st.rerun()
    else:
        st.info(f"✅ Mensajero: {nombre} | Ref. Tiempo: {st.session_state['hora_referencia']}")
        
        # --- BLOQUE DE SELECCIÓN PREDICTIVA ---
        f1, f2, f3 = st.columns(3)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--"] + CIUDADES, key="sel_ciu")
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True, key="rad_prod")
        with f3: empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SUPERINTER", "CAÑAVERAL", "OTROS"], key="sel_emp")

        info = None
        if ciudad != "--":
            # Caso Cañaveral Predictivo
            if empresa == "CAÑAVERAL":
                col1, col2 = st.columns(2)
                with col1: o = st.selectbox("📦 Recoge en:", ["--"] + sorted(LISTA_CANAVERAL), key="c_o")
                with col2: d = st.selectbox("🏠 Entrega en:", ["--"] + sorted(LISTA_CANAVERAL), key="c_d")
                if o != "--" and d != "--": info = {"TO": o, "CO": "CAN", "TD": d, "CD": "CAN"}
            
            # Caso Panadería Predictivo
            elif producto == "PANADERÍA":
                tiendas_p = TIENDAS_PANADERIA.get(ciudad, {})
                opciones_p = ["--"] + sorted(list(tiendas_p.keys()))
                col1, col2 = st.columns(2)
                with col1: o = st.selectbox("📦 Recoge en (Predictivo):", opciones_p, key="p_o_v")
                with col2: d = st.selectbox("🏠 Entrega en (Predictivo):", opciones_p, key="p_d_v")
                if o != "--" and d != "--": info = {"TO": o, "CO": tiendas_p.get(o, "N/A"), "TD": d, "CD": tiendas_p.get(d, "N/A")}

            # Caso Pollos
            else:
                # Aquí podrías cargar una lista de pollos similar a las anteriores
                t = st.selectbox("🏪 Tienda de Entrega:", ["--"] + sorted(LISTA_CANAVERAL), key="pol_gen") # Ejemplo usando lista general
                if t != "--": info = {"TO": "BASE", "CO": "BASE", "TD": t, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad (Canastillas/Productos):", min_value=1, step=1, key="cant_val")
            if st.button("ENVIAR REGISTRO ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                # Cálculo automático de minutos
                t_ini = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                t_fin = datetime.strptime(h_llegada, "%H:%M")
                minutos = int((t_fin - t_ini).total_seconds() / 60)
                if minutos < 0: minutos += 1440
                
                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), "Cedula": cedula, "Mensajero": nombre,
                    "Empresa": empresa, "Ciudad": ciudad, "Producto": producto,
                    "Tienda_O": info["TO"], "Cod_O": info["CO"], "Cod_D": info["CD"], "Tienda_D": info["TD"],
                    "Cant": int(cant), "Inicio": st.session_state['hora_referencia'], "Llegada": h_llegada, "Minutos": minutos
                }
                
                # Guardado Local de Respaldo
                pd.DataFrame([payload]).to_csv(DB_LOCAL, mode='a', index=False, header=not os.path.exists(DB_LOCAL))
                
                # Envío a Drive
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=20)
                    if res.status_code == 200: st.success("¡Enviado a Drive con éxito!")
                    else: st.warning("Error de respuesta. Guardado en memoria local.")
                except:
                    st.warning("Sin conexión. Registro guardado localmente.")
                
                # Actualización de tiempos para el siguiente viaje
                st.session_state['hora_referencia'] = h_llegada
                guardar_memoria(h_llegada)
                limpiar_entrega()
                time.sleep(1.5)
                st.rerun()

# Tabla de historial diario
if os.path.exists(DB_LOCAL):
    st.markdown("---")
    st.subheader("📋 Resumen de tus Entregas de Hoy")
    st.dataframe(pd.read_csv(DB_LOCAL).tail(10), use_container_width=True)
