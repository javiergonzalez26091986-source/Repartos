import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
import os

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="Control de entregas SERGEM", layout="wide")

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- FUNCIONES DE PERSISTENCIA INDIVIDUAL ---
def obtener_archivo_usuario(cedula):
    return f"user_{cedula}.txt"

def obtener_archivo_hora(cedula):
    return f"hora_{cedula}.txt"

def guardar_datos_locales(cedula, nombre, hora):
    with open(obtener_archivo_usuario(cedula), "w") as f:
        f.write(nombre)
    with open(obtener_archivo_hora(cedula), "w") as f:
        f.write(hora)

def borrar_datos_locales(cedula):
    archivos = [obtener_archivo_usuario(cedula), obtener_archivo_hora(cedula)]
    for arc in archivos:
        if os.path.exists(arc): os.remove(arc)

# --- INICIALIZACIÓN ---
if 'cedula_activa' not in st.session_state:
    st.session_state['cedula_activa'] = ""
if 'nombre_activo' not in st.session_state:
    st.session_state['nombre_activo'] = ""
if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = ""

st.title("🛵 Control de entregas SERGEM")

# --- SIDEBAR PARA FINALIZAR ---
with st.sidebar:
    if st.session_state['cedula_activa']:
        if st.button("🏁 FINALIZAR DÍA", type="primary"):
            borrar_datos_locales(st.session_state['cedula_activa'])
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

# --- LOGICA DE ACCESO (PERSISTENCIA REAL) ---
if not st.session_state['cedula_activa']:
    st.subheader("👤 Identificación")
    ced = st.text_input("Cédula:", key="input_cedula")
    if ced:
        # Intentar recuperar datos si existen archivos para esta cédula
        arch_u = obtener_archivo_usuario(ced)
        arch_h = obtener_archivo_hora(ced)
        
        if os.path.exists(arch_u):
            with open(arch_u, "r") as f: nom_recuperado = f.read()
            with open(arch_h, "r") as f: hora_recuperada = f.read()
            
            st.session_state['cedula_activa'] = ced
            st.session_state['nombre_activo'] = nom_recuperado
            st.session_state['hora_referencia'] = hora_recuperada
            st.rerun()
        else:
            nom = st.text_input("Nombre completo:").upper()
            if st.button("INICIAR JORNADA"):
                if nom:
                    st.session_state['cedula_activa'] = ced
                    st.session_state['nombre_activo'] = nom
                    st.session_state['hora_referencia'] = "" # Empezará pidiendo hora de salida
                    st.rerun()
else:
    # SESIÓN ACTIVA
    cedula = st.session_state['cedula_activa']
    nombre = st.session_state['nombre_activo']
    st.write(f"👤 **Mensajero:** {nombre} ({cedula})")

    # 1. CAPTURA DE HORA DE INICIO (Solo la primera vez del día)
    if st.session_state['hora_referencia'] == "":
        st.subheader("🚀 Salida de Base")
        if st.button("▶️ REGISTRAR HORA DE SALIDA", use_container_width=True):
            hora_actual = datetime.now(col_tz).strftime("%H:%M")
            st.session_state['hora_referencia'] = hora_actual
            guardar_datos_locales(cedula, nombre, hora_actual)
            st.rerun()
    
    # 2. FORMULARIO DE ENTREGAS
    else:
        st.info(f"✅ **Hora de Inicio para esta entrega:** {st.session_state['hora_referencia']}")
        
        # BASES DE DATOS (Se mantienen igual)
        LISTA_CANAVERAL = ['20 DE JULIO', 'BRISAS DE LOS ALAMOS', 'BUGA', 'CAVASA (VIA CANDELARIA)', 'CENTENARIO (AV 4N)', 'COOTRAEMCALI', 'DOSQUEBRADAS (PEREIRA)', 'EL INGENIO', 'EL LIMONAR (CRA 70)', 'GUADALUPE (CALI)', 'JAMUNDÍ (COUNTRY MALL)', 'LOS PINOS', 'PALMIRA', 'PANCE', 'PASOANCHO (CALI)', 'PRADOS DEL NORTE (LA 34)', 'ROLDANILLO', 'SANTA HELENA', 'TULUA', 'VILLAGORGONA', 'VILLANUEVA']
        TIENDAS_PANADERIA = {'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES': '4219540', 'CARULLA PUNTO VERDE': '4799540', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA SAN FERNANDO': '2595540', 'CARULLA LA MARIA': '4781540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO LA FLORA': '2054540'}, 'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER SAN SEBASTIAN': '4303540', 'SUPERINTER MANIZALES CENTRO': '4273540', 'SUPERINTER CHIPRE': '4279540', 'SUPERINTER VILLA PILAR': '4280540'}}
        TIENDAS_POLLOS = {'CALI': {'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 'SUPER INTER VILLA COLOMBIA': '4215', 'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 'SUPER INTER SAN FERNANDO': '4232', 'SUPER INTER BUENOS AIRES': '4262', 'SUPER INTER VALDEMORO': '4233', 'CARULLA LA MARIA': '4781', 'SUPER INTER EXPRESS AV. SEXTA': '4212', 'SUPER INTER PASARELA': '4214', 'SUPER INTER PRIMAVERA': '4271', 'SUPER INTER INDEPENDENCIA': '4261', 'CARULLA PASOANCHO': '4799', 'ÉXITO CRA OCTAVA (L)': '650'}, 'MEDELLÍN': {'ÉXITO EXPRESS CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'CARULLA EXPRESS VILLA GRANDE': '452', 'SURTIMAX CENTRO DE LA MODA': '516', 'SURTIMAX TRIANON': '745', 'SURTIMAX SAN JAVIER METRO': '758', 'ÉXITO INDIANA MALL': '4042', 'ÉXITO SAN JAVIER': '4067', 'ÉXITO GARDEL': '4070', 'SURTIMAX CAMINO VERDE': '4381', 'SURTIMAX CALDAS': '4534', 'SURTIMAX PILARICA': '4557', 'CARULLA EXPRESS PADRE MARIANITO': '4664', 'CARULLA EXPRESS EDS LA SIERRA': '4665', 'CARULLA EXPRESS PARQUE POBLADO': '4669', 'CARULLA EXPRESS LA AMÉRICA': '4776', 'CARULLA EXPRESS NUTIBARA': '4777', 'CARULLA EXPRESS LAURELES': '4778', 'CARULLA EXPRESS DIVINA EUCARISTIA': '4829', 'CARULLA EXPRESS LOMA ESCOBERO': '4878'}, 'BOGOTÁ': {'ÉXITO EXPRESS EMBAJADA': '110', 'ÉXITO EXPRESS COLSEGUROS (CAF)': '301', 'SURTIMAX BRASIL BOSA': '311', 'SURTIMAX CASA BLANCA (CAF)': '434', 'SURTIMAX LA ESPAÑOLA': '449', 'SURTIMAX SAN ANTONIO': '450', 'ÉXITO EXPRESS BIMA': '459', 'SURTIMAX BARRANCAS': '467', 'CARULLA EXPRESS CEDRITOS': '468', 'SURTIMAX NUEVA ROMA': '470', 'SURTIMAX TIBABUYES': '473', 'SURTIMAX TRINITARIA': '474', 'SURTIMAX LA GLORIA': '481', 'SURTIMAX SAN FERNANDO': '511', 'CARULLA CALLE 147': '549', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX TOCANCIPÁ': '573', 'SURTIMAX SAN MATEO': '575', 'SURTIMAX CAJICÁ': '576', 'SURTIMAX SOPÓ': '577', 'SURTIMAX COMPARTIR SOACHA': '579', 'SURTIMAX SANTA RITA': '623', 'ÉXITO EXPRESS CRA 15 CON 100': '657', 'SURTIMAX LA CALERA': '703', 'SURTIMAX YANGUAS': '709', 'SURTIMAX EL SOCORRO': '768', 'SURTIMAX EL RECREO BOSA': '781', 'CARULLA LA CALERA': '886', 'ÉXITO PRIMAVERA CALLE 80': '4068', 'ÉXITO PARQUE FONTIBON': '4069', 'ÉXITO PRADILLA': '4071', 'ÉXITO CIUDADEL': '4082', 'ÉXITO EXPRESS CRA 24 83-22': '4187', 'SURTIMAX CHAPINERO': '4523', 'SURTIMAX LIJACA': '4524', 'SURTIMAX QUIROGA': '4527', 'SURTIMAX SUBA BILBAO': '4533', 'SURTIMAX SANTA ISABEL': '4539', 'CARULLA BACATA': '4813', 'CARULLA SMARTMARKET': '4814', 'CARULLA LA PRADERA DE POTOSÍ': '4818', 'CARULLA EXPRESS C109 C14': '4822', 'CARULLA EXPRESS SIBERIA': '4825', 'CARULLA EXPRESS CALLE 90': '4828', 'CARULLA EXPRESS PONTEVEDRA': '4836', 'CARULLA EXPRESS CARRERA 7': '4839', 'CARULLA EXPRESS SALITRE': '4875', 'CARULLA EXPRESS CORFERIAS': '4876'}}

        f1, f2 = st.columns(2)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"], key="sel_ciu")
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True, key="rad_prod")
        opciones_empresa = ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER", "OTROS"]
        if ciudad in ["CALI", "MANIZALES"]: opciones_empresa.insert(2, "CAÑAVERAL")
        empresa = st.selectbox("🏢 Empresa:", opciones_empresa, key="sel_emp")

        info = None
        if ciudad != "--" and empresa != "--":
            if empresa == "CAÑAVERAL":
                col1, col2 = st.columns(2)
                with col1: o = st.selectbox("📦 Origen:", ["--"] + sorted(LISTA_CANAVERAL), key="c_o")
                with col2: d = st.selectbox("🏠 Destino:", ["--"] + sorted(LISTA_CANAVERAL), key="c_d")
                if o != "--" and d != "--": info = {"TO": o, "CO": "CAN", "TD": d, "CD": "CAN"}
            elif empresa == "EXITO-CARULLA-SURTIMAX-SUPERINTER":
                dic = TIENDAS_PANADERIA.get(ciudad, {}) if producto == "PANADERÍA" else TIENDAS_POLLOS.get(ciudad, {})
                ops = ["--"] + sorted(list(dic.keys()))
                if producto == "PANADERÍA":
                    col1, col2 = st.columns(2)
                    with col1: o = st.selectbox("📦 Recoge en:", ops, key="p_o_v")
                    with col2: d = st.selectbox("🏠 Entrega en:", ops, key="p_d_v")
                    if o != "--" and d != "--": info = {"TO": o, "CO": dic[o], "TD": d, "CD": dic[d]}
                else:
                    t = st.selectbox("🏪 Tienda de Entrega:", ops, key="pol_gen")
                    if t != "--": info = {"TO": "BASE", "CO": "BASE", "TD": t, "CD": dic.get(t, "N/A")}
            else:
                t_otros = st.text_input("Escriba la tienda/empresa externa:", key="txt_ext").upper()
                if t_otros: info = {"TO": "OTRO", "CO": "N/A", "TD": t_otros, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1, key="cant_val")
            if st.button("ENVIAR REGISTRO ✅", use_container_width=True, type="primary"):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                # Calcular minutos
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
                
                try:
                    requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    st.success("¡Registro Exitoso!")
                    # ACTUALIZAR HORA PARA EL SIGUIENTE VIAJE
                    st.session_state['hora_referencia'] = h_llegada
                    guardar_datos_locales(cedula, nombre, h_llegada)
                    
                    # Limpiar selección
                    for k in ['sel_ciu', 'sel_emp', 'c_o', 'c_d', 'p_o_v', 'p_d_v', 'pol_gen', 'cant_val', 'txt_ext']:
                        if k in st.session_state: del st.session_state[k]
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("Error de conexión. Intente de nuevo.")
