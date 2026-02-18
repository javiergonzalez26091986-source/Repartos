import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
import os

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="Control SERGEM", layout="wide")

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- FUNCIONES DE PERSISTENCIA ---
def get_file_path(cedula, tipo):
    # Crea carpetas o nombres de archivos únicos por cédula
    return f"{tipo}_{cedula}.txt"

def guardar_progreso(cedula, nombre, hora):
    with open(get_file_path(cedula, "nom"), "w") as f: f.write(nombre)
    with open(get_file_path(cedula, "hor"), "w") as f: f.write(hora)

def borrar_progreso(cedula):
    for t in ["nom", "hor"]:
        path = get_file_path(cedula, t)
        if os.path.exists(path): os.remove(path)

# --- INTERFAZ ---
st.title("🛵 Control de entregas SERGEM")

# Paso 1: Identificación (Siempre visible si no hay sesión)
if 'cedula' not in st.session_state:
    st.session_state.cedula = ""

if st.session_state.cedula == "":
    ced_input = st.text_input("Ingrese su Cédula para continuar:")
    if ced_input:
        # Verificar si ya existe un archivo para esta cédula (Persistencia Real)
        path_nom = get_file_path(ced_input, "nom")
        if os.path.exists(path_nom):
            with open(path_nom, "r") as f: st.session_state.nombre = f.read()
            with open(get_file_path(ced_input, "hor"), "r") as f: st.session_state.hora_ref = f.read()
            st.session_state.cedula = ced_input
            st.rerun()
        else:
            nom_input = st.text_input("Nombre Completo:").upper()
            if st.button("INICIAR DÍA"):
                if nom_input:
                    st.session_state.cedula = ced_input
                    st.session_state.nombre = nom_input
                    st.session_state.hora_ref = ""
                    guardar_progreso(ced_input, nom_input, "")
                    st.rerun()
else:
    # SESIÓN ACTIVA
    ced = st.session_state.cedula
    nom = st.session_state.nombre
    
    with st.sidebar:
        st.write(f"👤 {nom}")
        if st.button("🏁 FINALIZAR DÍA"):
            borrar_progreso(ced)
            st.session_state.clear()
            st.rerun()

    # Lógica de Tiempos
    if st.session_state.hora_ref == "":
        st.subheader("🚀 Salida de Base")
        if st.button("▶️ CAPTURAR HORA DE SALIDA", use_container_width=True):
            h_act = datetime.now(col_tz).strftime("%H:%M")
            st.session_state.hora_ref = h_act
            guardar_progreso(ced, nom, h_act)
            st.rerun()
    else:
        st.info(f"✅ **Hora de referencia:** {st.session_state.hora_ref}")
        
        # --- EL FORMULARIO ---
        LISTA_CANAVERAL = ['20 DE JULIO', 'BRISAS DE LOS ALAMOS', 'BUGA', 'CAVASA (VIA CANDELARIA)', 'CENTENARIO (AV 4N)', 'COOTRAEMCALI', 'DOSQUEBRADAS (PEREIRA)', 'EL INGENIO', 'EL LIMONAR (CRA 70)', 'GUADALUPE (CALI)', 'JAMUNDÍ (COUNTRY MALL)', 'LOS PINOS', 'PALMIRA', 'PANCE', 'PASOANCHO (CALI)', 'PRADOS DEL NORTE (LA 34)', 'ROLDANILLO', 'SANTA HELENA', 'TULUA', 'VILLAGORGONA', 'VILLANUEVA']
        TIENDAS_PANADERIA = {'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES': '4219540', 'CARULLA PUNTO VERDE': '4799540', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA SAN FERNANDO': '2595540', 'CARULLA LA MARIA': '4781540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO LA FLORA': '2054540'}, 'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER SAN SEBASTIAN': '4303540', 'SUPERINTER MANIZALES CENTRO': '4273540', 'SUPERINTER CHIPRE': '4279540', 'SUPERINTER VILLA PILAR': '4280540'}}
        TIENDAS_POLLOS = {'CALI': {'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 'SUPER INTER VILLA COLOMBIA': '4215', 'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 'SUPER INTER SAN FERNANDO': '4232', 'SUPER INTER BUENOS AIRES': '4262', 'SUPER INTER VALDEMORO': '4233', 'CARULLA LA MARIA': '4781', 'SUPER INTER EXPRESS AV. SEXTA': '4212', 'SUPER INTER PASARELA': '4214', 'SUPER INTER PRIMAVERA': '4271', 'SUPER INTER INDEPENDENCIA': '4261', 'CARULLA PASOANCHO': '4799', 'ÉXITO CRA OCTAVA (L)': '650'}, 'MEDELLÍN': {'ÉXITO EXPRESS CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'CARULLA EXPRESS VILLA GRANDE': '452', 'SURTIMAX CENTRO DE LA MODA': '516', 'SURTIMAX TRIANON': '745', 'SURTIMAX SAN JAVIER METRO': '758', 'ÉXITO INDIANA MALL': '4042', 'ÉXITO SAN JAVIER': '4067', 'ÉXITO GARDEL': '4070', 'SURTIMAX CAMINO VERDE': '4381', 'SURTIMAX CALDAS': '4534', 'SURTIMAX PILARICA': '4557', 'CARULLA EXPRESS PADRE MARIANITO': '4664', 'CARULLA EXPRESS EDS LA SIERRA': '4665', 'CARULLA EXPRESS PARQUE POBLADO': '4669', 'CARULLA EXPRESS LA AMÉRICA': '4776', 'CARULLA EXPRESS NUTIBARA': '4777', 'CARULLA EXPRESS LAURELES': '4778', 'CARULLA EXPRESS DIVINA EUCARISTIA': '4829', 'CARULLA EXPRESS LOMA ESCOBERO': '4878'}, 'BOGOTÁ': {'ÉXITO EXPRESS EMBAJADA': '110', 'ÉXITO EXPRESS COLSEGUROS (CAF)': '301', 'SURTIMAX BRASIL BOSA': '311', 'SURTIMAX CASA BLANCA (CAF)': '434', 'SURTIMAX LA ESPAÑOLA': '449', 'SURTIMAX SAN ANTONIO': '450', 'ÉXITO EXPRESS BIMA': '459', 'SURTIMAX BARRANCAS': '467', 'CARULLA EXPRESS CEDRITOS': '468', 'SURTIMAX NUEVA ROMA': '470', 'SURTIMAX TIBABUYES': '473', 'SURTIMAX TRINITARIA': '474', 'SURTIMAX LA GLORIA': '481', 'SURTIMAX SAN FERNANDO': '511', 'CARULLA CALLE 147': '549', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX TOCANCIPÁ': '573', 'SURTIMAX SAN MATEO': '575', 'SURTIMAX CAJICÁ': '576', 'SURTIMAX SOPÓ': '577', 'SURTIMAX COMPARTIR SOACHA': '579', 'SURTIMAX SANTA RITA': '623', 'ÉXITO EXPRESS CRA 15 CON 100': '657', 'SURTIMAX LA CALERA': '703', 'SURTIMAX YANGUAS': '709', 'SURTIMAX EL SOCORRO': '768', 'SURTIMAX EL RECREO BOSA': '781', 'CARULLA LA CALERA': '886', 'ÉXITO PRIMAVERA CALLE 80': '4068', 'ÉXITO PARQUE FONTIBON': '4069', 'ÉXITO PRADILLA': '4071', 'ÉXITO CIUDADEL': '4082', 'ÉXITO EXPRESS CRA 24 83-22': '4187', 'SURTIMAX CHAPINERO': '4523', 'SURTIMAX LIJACA': '4524', 'SURTIMAX QUIROGA': '4527', 'SURTIMAX SUBA BILBAO': '4533', 'SURTIMAX SANTA ISABEL': '4539', 'CARULLA BACATA': '4813', 'CARULLA SMARTMARKET': '4814', 'CARULLA LA PRADERA DE POTOSÍ': '4818', 'CARULLA EXPRESS C109 C14': '4822', 'CARULLA EXPRESS SIBERIA': '4825', 'CARULLA EXPRESS CALLE 90': '4828', 'CARULLA EXPRESS PONTEVEDRA': '4836', 'CARULLA EXPRESS CARRERA 7': '4839', 'CARULLA EXPRESS SALITRE': '4875', 'CARULLA EXPRESS CORFERIAS': '4876'}}

        col_c, col_p = st.columns(2)
        with col_c: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLÍN", "BOGOTÁ"], key="s_ciu")
        with col_p: producto = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        
        empresa = st.selectbox("🏢 Empresa:", ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER", "CAÑAVERAL", "OTROS"], key="s_emp")

        info = None
        if ciudad != "--" and empresa != "--":
            # (Aquí va la misma lógica de selección de tiendas de antes...)
            # Por brevedad, asumo que ya la tienes, si no, el código la integra.
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
                h_llega = ahora.strftime("%H:%M")
                
                # Calcular minutos
                t_ini = datetime.strptime(st.session_state.hora_ref, "%H:%M")
                t_fin = datetime.strptime(h_llega, "%H:%M")
                minutos = int((t_fin - t_ini).total_seconds() / 60)
                if minutos < 0: minutos += 1440

                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), "Cedula": ced, "Mensajero": nom,
                    "Empresa": empresa, "Ciudad": ciudad, "Producto": producto,
                    "Tienda_O": info["TO"], "Cod_O": info["CO"], "Cod_D": info["CD"], "Tienda_D": info["TD"],
                    "Cant": int(cant), "Inicio": st.session_state.hora_ref, "Llegada": h_llega, "Minutos": minutos
                }
                
                try:
                    requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=10)
                    st.success("¡Enviado!")
                    # ACTUALIZAR Y GUARDAR PARA EL SIGUIENTE VIAJE
                    st.session_state.hora_ref = h_llega
                    guardar_progreso(ced, nom, h_llega)
                    # Limpiar UI
                    for k in ['s_ciu', 's_emp', 'co', 'cd', 'ct', 'ce', 'ccant']:
                        if k in st.session_state: del st.session_state[k]
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("Error de conexión.")
