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
PERSISTENCIA_INI = "hora_inicio_respaldo.txt"
PERSISTENCIA_USER = "user_respaldo.txt" 
DB_LOCAL = "registro_diario_respaldo.csv"

# --- FUNCIONES DE CONTROL ---
def guardar_memoria(hora):
    with open(PERSISTENCIA_INI, "w") as f: 
        f.write(hora)

def leer_memoria():
    if os.path.exists(PERSISTENCIA_INI):
        with open(PERSISTENCIA_INI, "r") as f: 
            return f.read().strip()
    return ""

def guardar_usuario(cedula, nombre):
    with open(PERSISTENCIA_USER, "w") as f:
        f.write(f"{cedula}|{nombre}")

def leer_usuario():
    if os.path.exists(PERSISTENCIA_USER):
        with open(PERSISTENCIA_USER, "r") as f:
            datos = f.read().split("|")
            if len(datos) == 2: return datos[0], datos[1]
    return "", ""

def finalizar_operacion():
    archivos = [PERSISTENCIA_INI, PERSISTENCIA_USER, DB_LOCAL]
    for arc in archivos:
        if os.path.exists(arc): os.remove(arc)
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("Operación finalizada. Limpiando datos...")
    time.sleep(1.5)
    st.rerun()

# --- INICIALIZACIÓN DE ESTADO ---
if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = leer_memoria()

saved_ced, saved_nom = leer_usuario()

# --- INTERFAZ ---
st.title("🛵 Control de entregas SERGEM")

with st.sidebar:
    if st.button("🏁 FINALIZAR DÍA", type="primary"):
        finalizar_operacion()

c1, c2 = st.columns(2)
cedula = c1.text_input("Cédula:", value=saved_ced, key="ced")
nombre = c2.text_input("Nombre:", value=saved_nom, key="nom").upper()

if cedula and nombre and (cedula != saved_ced or nombre != saved_nom):
    guardar_usuario(cedula, nombre)

if cedula and nombre:
    # SI NO HAY HORA REGISTRADA (INICIO DE JORNADA)
    if st.session_state['hora_referencia'] == "":
        st.subheader("🚀 Iniciar Jornada")
        h_ini = st.time_input("Salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR OPERACIÓN"):
            hora_str = h_ini.strftime("%H:%M")
            st.session_state['hora_referencia'] = hora_str
            guardar_memoria(hora_str)
            st.rerun()
    
    # JORNADA EN CURSO
    else:
        st.info(f"✅ **Hora de Inicio para esta entrega:** {st.session_state['hora_referencia']}")
        
        # --- BASES DE DATOS ---
        LISTA_CANAVERAL = ['20 DE JULIO', 'BRISAS DE LOS ALAMOS', 'BUGA', 'CAVASA (VIA CANDELARIA)', 'CENTENARIO (AV 4N)', 'COOTRAEMCALI', 'DOSQUEBRADAS (PEREIRA)', 'EL INGENIO', 'EL LIMONAR (CRA 70)', 'GUADALUPE (CALI)', 'JAMUNDÍ (COUNTRY MALL)', 'LOS PINOS', 'PALMIRA', 'PANCE', 'PASOANCHO (CALI)', 'PRADOS DEL NORTE (LA 34)', 'ROLDANILLO', 'SANTA HELENA', 'TULUA', 'VILLAGORGONA', 'VILLANUEVA']
        
        TIENDAS_PANADERIA = {
            'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES': '4219540', 'CARULLA PUNTO VERDE': '4799540', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA SAN FERNANDO': '2595540', 'CARULLA LA MARIA': '4781540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO LA FLORA': '2054540'},
            'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER SAN SEBASTIAN': '4303540', 'SUPERINTER MANIZALES CENTRO': '4273540', 'SUPERINTER CHIPRE': '4279540', 'SUPERINTER VILLA PILAR': '4280540'}
        }
        
        TIENDAS_POLLOS = {
            'CALI': {'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 'SUPER INTER VILLA COLOMBIA': '4215', 'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 'SUPER INTER SAN FERNANDO': '4232', 'SUPER INTER BUENOS AIRES': '4262', 'SUPER INTER VALDEMORO': '4233', 'CARULLA LA MARIA': '4781', 'SUPER INTER EXPRESS AV. SEXTA': '4212', 'SUPER INTER PASARELA': '4214', 'SUPER INTER PRIMAVERA': '4271', 'SUPER INTER INDEPENDENCIA': '4261', 'CARULLA PASOANCHO': '4799', 'ÉXITO CRA OCTAVA (L)': '650'},
            'MEDELLÍN': {'ÉXITO EXPRESS CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'CARULLA EXPRESS VILLA GRANDE': '452', 'SURTIMAX CENTRO DE LA MODA': '516', 'SURTIMAX TRIANON': '745', 'SURTIMAX SAN JAVIER METRO': '758', 'ÉXITO INDIANA MALL': '4042', 'ÉXITO SAN JAVIER': '4067', 'ÉXITO GARDEL': '4070', 'SURTIMAX CAMINO VERDE': '4381', 'SURTIMAX CALDAS': '4534', 'SURTIMAX PILARICA': '4557', 'CARULLA EXPRESS PADRE MARIANITO': '4664', 'CARULLA EXPRESS EDS LA SIERRA': '4665', 'CARULLA EXPRESS PARQUE POBLADO': '4669', 'CARULLA EXPRESS LA AMÉRICA': '4776', 'CARULLA EXPRESS NUTIBARA': '4777', 'CARULLA EXPRESS LAURELES': '4778', 'CARULLA EXPRESS DIVINA EUCARISTIA': '4829', 'CARULLA EXPRESS LOMA ESCOBERO': '4878'},
            'BOGOTÁ': {'ÉXITO EXPRESS EMBAJADA': '110', 'ÉXITO EXPRESS COLSEGUROS (CAF)': '301', 'SURTIMAX BRASIL BOSA': '311', 'SURTIMAX CASA BLANCA (CAF)': '434', 'SURTIMAX LA ESPAÑOLA': '449', 'SURTIMAX SAN ANTONIO': '450', 'ÉXITO EXPRESS BIMA': '459', 'SURTIMAX BARRANCAS': '467', 'CARULLA EXPRESS CEDRITOS': '468', 'SURTIMAX NUEVA ROMA': '470', 'SURTIMAX TIBABUYES': '473', 'SURTIMAX TRINITARIA': '474', 'SURTIMAX LA GLORIA': '481', 'SURTIMAX SAN FERNANDO': '511', 'CARULLA CALLE 147': '549', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX TOCANCIPÁ': '573', 'SURTIMAX SAN MATEO': '575', 'SURTIMAX CAJICÁ': '576', 'SURTIMAX SOPÓ': '577', 'SURTIMAX COMPARTIR SOACHA': '579', 'SURTIMAX SANTA RITA': '623', 'ÉXITO EXPRESS CRA 15 CON 100': '657', 'SURTIMAX LA CALERA': '703', 'SURTIMAX YANGUAS': '709', 'SURTIMAX EL SOCORRO': '768', 'SURTIMAX EL RECREO BOSA': '781', 'CARULLA LA CALERA': '886', 'ÉXITO PRIMAVERA CALLE 80': '4068', 'ÉXITO PARQUE FONTIBON': '4069', 'ÉXITO PRADILLA': '4071', 'ÉXITO CIUDADEL': '4082', 'ÉXITO EXPRESS CRA 24 83-22': '4187', 'SURTIMAX CHAPINERO': '4523', 'SURTIMAX LIJACA': '4524', 'SURTIMAX QUIROGA': '4527', 'SURTIMAX SUBA BILBAO': '4533', 'SURTIMAX SANTA ISABEL': '4539', 'CARULLA BACATA': '4813', 'CARULLA SMARTMARKET': '4814', 'CARULLA LA PRADERA DE POTOSÍ': '4818', 'CARULLA EXPRESS C109 C14': '4822', 'CARULLA EXPRESS SIBERIA': '4825', 'CARULLA EXPRESS CALLE 90': '4828', 'CARULLA EXPRESS PONTEVEDRA': '4836', 'CARULLA EXPRESS CARRERA 7': '4839', 'CARULLA EXPRESS SALITRE': '4875', 'CARULLA EXPRESS CORFERIAS': '4876'}
        }

        f1, f2 = st.columns(2)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"], key="sel_ciu")
        with f2: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True, key="rad_prod")
        
        opciones_empresa = ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER", "OTROS"]
        if ciudad in ["CALI", "MANIZALES"]: opciones_empresa.insert(2, "CAÑAVERAL")
        empresa = st.selectbox("🏢 Empresa:", opciones_empresa, key="sel_emp")

        info = None
        # LÓGICA DE SELECCIÓN SEGÚN EMPRESA
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

        # --- BOTÓN UNIFICADO ENVIAR REGISTRO ---
        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1, key="cant_val")
            if st.button("ENVIAR REGISTRO ✅", use_container_width=True, type="primary"):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                # Cálculo de tiempo (Minutos)
                try:
                    t_ini = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                    t_fin = datetime.strptime(h_llegada, "%H:%M")
                    minutos = int((t_fin - t_ini).total_seconds() / 60)
                    if minutos < 0: minutos += 1440
                except:
                    minutos = 0

                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), 
                    "Cedula": cedula, 
                    "Mensajero": nombre,
                    "Empresa": empresa, 
                    "Ciudad": ciudad, 
                    "Producto": producto,
                    "Tienda_O": info["TO"], 
                    "Cod_O": info["CO"], 
                    "Cod_D": info["CD"], 
                    "Tienda_D": info["TD"],
                    "Cant": int(cant), 
                    "Inicio": st.session_state['hora_referencia'], 
                    "Llegada": h_llegada, 
                    "Minutos": minutos
                }
                
                # 1. Guardar Local
                pd.DataFrame([payload]).to_csv(DB_LOCAL, mode='a', index=False, header=not os.path.exists(DB_LOCAL))
                
                # 2. Enviar a Google
                try:
                    requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    st.success("¡Enviado a Drive y actualizado!")
                except:
                    st.warning("Guardado local (Sin internet).")
                
                # 3. EL CAMBIO CLAVE: Actualizar hora de inicio para el siguiente viaje
                st.session_state['hora_referencia'] = h_llegada
                guardar_memoria(h_llegada)
                
                # Limpiar campos de selección
                for k in ['c_o', 'c_d', 'p_o_v', 'p_d_v', 'pol_gen', 'cant_val', 'txt_ext']:
                    if k in st.session_state: del st.session_state[k]
                
                time.sleep(1)
                st.rerun()

# Mostrar últimos registros locales
if os.path.exists(DB_LOCAL):
    st.markdown("---")
    st.subheader("📋 Últimos registros de hoy")
    try:
        df_rev = pd.read_csv(DB_LOCAL)
        st.dataframe(df_rev.tail(5), use_container_width=True)
    except:
        pass
