import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
import os

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM v6.3 - AntiDuplicados", layout="wide")

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

PERSISTENCIA_INI = "hora_inicio_respaldo.txt"
DB_LOCAL = "registro_diario_respaldo.csv"

# --- FUNCIONES DE MEMORIA ---
def guardar_memoria(hora):
    with open(PERSISTENCIA_INI, "w") as f: f.write(hora)

def leer_memoria():
    if os.path.exists(PERSISTENCIA_INI):
        with open(PERSISTENCIA_INI, "r") as f: return f.read()
    return ""

def finalizar_operacion():
    if os.path.exists(PERSISTENCIA_INI): os.remove(PERSISTENCIA_INI)
    if os.path.exists(DB_LOCAL): os.remove(DB_LOCAL)
    # Limpiamos todos los campos al finalizar
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = leer_memoria()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Menú")
    if st.button("🏁 FINALIZAR ENTREGAS DEL DÍA", use_container_width=True, type="primary"):
        finalizar_operacion()

# --- BASES DE DATOS (IGUAL A V6.2) ---
TIENDAS_PANADERIA = {
    'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES (TRADE CENTER)': '4219540', 'CARULLA PUNTO VERDE': '4799540', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA SAN FERNANDO': '2595540', 'CARULLA LA MARIA': '4781540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO LA FLORA': '2054540', 'CARULLA HOLGUINES (ENTREGA)': '2596540'},
    'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER SAN SEBASTIAN': '4303540', 'SUPERINTER MANIZALES CENTRO': '4273540', 'SUPERINTER CHIPRE': '4279540', 'SUPERINTER VILLA PILAR': '4280540'}
}
TIENDAS_POLLOS = {
    'CALI': {'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 'SUPER INTER VILLA COLOMBIA': '4215', 'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 'SUPER INTER SAN FERNANDO': '4232', 'SUPER INTER BUENOS AIRES': '4262', 'SUPER INTER VALDEMORO': '4233', 'CARULLA LA MARIA': '4781', 'SUPER INTER EXPRESS AV. SEXTA': '4212', 'SUPER INTER PASARELA': '4214', 'SUPER INTER PRIMAVERA': '4271', 'SUPER INTER INDEPENDENCIA': '4261', 'CARULLA PASOANCHO': '4799', 'ÉXITO CRA OCTAVA (L)': '650'},
    'MEDELLÍN': {'ÉXITO EXPRESS CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'CARULLA EXPRESS VILLA GRANDE': '452', 'SURTIMAX CENTRO DE LA MODA': '516', 'SURTIMAX TRIANON': '745', 'SURTIMAX SAN JAVIER METRO': '758', 'ÉXITO INDIANA MALL': '4042', 'ÉXITO SAN JAVIER': '4067', 'ÉXITO GARDEL': '4070', 'SURTIMAX CAMINO VERDE': '4381', 'SURTIMAX CALDAS': '4534', 'SURTIMAX PILARICA': '4557', 'CARULLA EXPRESS PADRE MARIANITO': '4664', 'CARULLA EXPRESS EDS LA SIERRA': '4665', 'CARULLA EXPRESS PARQUE POBLADO': '4669', 'CARULLA EXPRESS LA AMÉRICA': '4776', 'CARULLA EXPRESS NUTIBARA': '4777', 'CARULLA EXPRESS LAURELES': '4778', 'CARULLA EXPRESS DIVINA EUCARISTIA': '4829', 'CARULLA EXPRESS LOMA ESCOBERO': '4878'},
    'BOGOTÁ': {'ÉXITO EXPRESS EMBAJADA': '110', 'ÉXITO EXPRESS COLSEGUROS (CAF)': '301', 'SURTIMAX BRASIL BOSA': '311', 'SURTIMAX CASA BLANCA (CAF)': '434', 'SURTIMAX LA ESPAÑOLA': '449', 'SURTIMAX SAN ANTONIO': '450', 'ÉXITO EXPRESS BIMA': '459', 'SURTIMAX BARRANCAS': '467', 'CARULLA EXPRESS CEDRITOS': '468', 'SURTIMAX NUEVA ROMA': '470', 'SURTIMAX TIBABUYES': '473', 'SURTIMAX TRINITARIA': '474', 'SURTIMAX LA GLORIA': '481', 'SURTIMAX SAN FERNANDO': '511', 'CARULLA CALLE 147': '549', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX TOCANCIPÁ': '573', 'SURTIMAX SAN Mateo': '575', 'SURTIMAX CAJICÁ': '576', 'SURTIMAX SOPÓ': '577', 'SURTIMAX COMPARTIR SOACHA': '579', 'SURTIMAX SANTA RITA': '623', 'ÉXITO EXPRESS CRA 15 CON 100': '657', 'SURTIMAX LA CALERA': '703', 'SURTIMAX YANGUAS': '709', 'SURTIMAX EL SOCORRO': '768', 'SURTIMAX EL RECREO BOSA': '781', 'CARULLA LA CALERA': '886', 'ÉXITO PRIMAVERA CALLE 80': '4068', 'ÉXITO PARQUE FONTIBON': '4069', 'ÉXITO PRADILLA': '4071', 'ÉXITO CIUDADELA': '4082', 'ÉXITO EXPRESS CRA 24 83-22': '4187', 'SURTIMAX CHAPINERO': '4523', 'SURTIMAX LIJACA': '4524', 'SURTIMAX QUIROGA': '4527', 'SURTIMAX SUBA BILBAO': '4533', 'SURTIMAX SANTA ISABEL': '4539', 'CARULLA BACATA': '4813', 'CARULLA SMARTMARKET': '4814', 'CARULLA LA PRADERA DE POTOSÍ': '4818', 'CARULLA EXPRESS C109 C14': '4822', 'CARULLA EXPRESS SIBERIA': '4825', 'CARULLA EXPRESS CALLE 90': '4828', 'CARULLA EXPRESS PONTEVEDRA': '4836', 'CARULLA EXPRESS CARRERA 7': '4839', 'CARULLA EXPRESS SALITRE': '4875', 'CARULLA EXPRESS CORFERIAS': '4876'}
}
CANAVERAL_CALI = ['VILLAGORGONA', 'VILLANUEVA', 'COOTRAEMCALI']

st.title("🛵 Control Maestro SERGEM")

# Formulario de entrada
with st.form("form_registro", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1: cedula = st.text_input("Cédula:")
    with c2: nombre = st.text_input("Nombre:").upper()
    
    # Solo mostramos el resto si ya hay identificación
    if cedula and nombre:
        if st.session_state['hora_referencia'] == "":
            st.warning("⚠️ Primero marca tu Salida de Base abajo.")
        else:
            st.info(f"📍 Tiempos calculados desde: {st.session_state['hora_referencia']}")
            f1, f2, f3 = st.columns(3)
            with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"])
            with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
            with f3: empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SUPERINTER-SURTIMAX", "CAÑAVERAL", "OTROS"])

            info = None
            if ciudad != "--":
                if ciudad == "CALI" and empresa == "CAÑAVERAL":
                    col1, col2 = st.columns(2)
                    with col1: o = st.selectbox("📦 Recoge en:", ["--"] + CANAVERAL_CALI)
                    with col2: d = st.selectbox("🏠 Entrega en:", ["--"] + CANAVERAL_CALI)
                    if o != "--" and d != "--": info = {"TO": o, "CO": "CAN", "TD": d, "CD": "CAN"}
                elif producto == "PANADERÍA" and (ciudad in ["CALI", "MANIZALES"]):
                    tiendas_p = TIENDAS_PANADERIA.get(ciudad, {})
                    opciones_p = ["--"] + sorted(list(tiendas_p.keys()))
                    col1, col2 = st.columns(2)
                    with col1: o = st.selectbox("📦 Recoge en:", opciones_p)
                    with col2: d = st.selectbox("🏠 Entrega en:", opciones_p)
                    if o != "--" and d != "--": info = {"TO": o, "CO": tiendas_p[o], "TD": d, "CD": tiendas_p[d]}
                else:
                    tiendas_gen = TIENDAS_POLLOS.get(ciudad, {}) if producto == "POLLOS" else TIENDAS_PANADERIA.get(ciudad, {})
                    op_gen = ["--"] + sorted(list(tiendas_gen.keys()))
                    if producto == "PANADERÍA":
                        col1, col2 = st.columns(2)
                        with col1: o = st.selectbox("📦 Recoge en:", op_gen)
                        with col2: d = st.selectbox("🏠 Entrega en:", op_gen)
                        if o != "--" and d != "--": info = {"TO": o, "CO": tiendas_gen[o], "TD": d, "CD": tiendas_gen[d]}
                    else:
                        t = st.selectbox("🏪 Tienda de Entrega:", op_gen)
                        if t != "--": info = {"TO": t, "CO": tiendas_gen[t], "TD": t, "CD": "N/A"}

            cant = st.number_input("Cantidad:", min_value=1, step=1)
            enviar = st.form_submit_button("ENVIAR REGISTRO ✅", use_container_width=True)

            if enviar and info:
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
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
                
                pd.DataFrame([payload]).to_csv(DB_LOCAL, mode='a', index=False, header=not os.path.exists(DB_LOCAL))
                try:
                    requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=25)
                    st.success("¡Enviado!")
                except:
                    st.warning("Guardado localmente.")
                
                st.session_state['hora_referencia'] = h_llegada
                guardar_memoria(h_llegada)
                time.sleep(1)
                st.rerun()

# Botón de Inicio de Jornada separado para que no se borre con el formulario
if st.session_state['hora_referencia'] == "":
    with st.expander("🕒 MARCAR SALIDA DE BASE", expanded=True):
        h_ini = st.time_input("Hora de salida:", datetime.now(col_tz))
        if st.button("INICIAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            guardar_memoria(st.session_state['hora_referencia'])
            st.rerun()

if os.path.exists(DB_LOCAL):
    st.markdown("---")
    st.subheader("📋 Resumen de Hoy")
    st.dataframe(pd.read_csv(DB_LOCAL).tail(10), use_container_width=True)
