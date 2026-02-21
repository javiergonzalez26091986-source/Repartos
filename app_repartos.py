import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="Control de entregas SERGEM", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    div[data-testid="stToolbar"] { visibility: hidden !important; }
    
    div.stButton > button:first-child[kind="primary"] {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
        color: white !important;
    }
    .stColumn div.stButton > button[kind="primary"] {
        background-color: #dc3545 !important;
        border-color: #dc3545 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- PERSISTENCIA Y CONTADOR DE REINICIO ---
params = st.query_params
if "ced" in params: st.session_state.cedula = params["ced"]
if "nom" in params: st.session_state.nombre = params["nom"]
if "hor" in params: st.session_state.hora_ref = params["hor"]

if 'cedula' not in st.session_state: st.session_state.cedula = ""
if 'nombre' not in st.session_state: st.session_state.nombre = ""
if 'hora_ref' not in st.session_state: st.session_state.hora_ref = ""
if 'historial_datos' not in st.session_state: st.session_state.historial_datos = []
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

def actualizar_url():
    st.query_params.update({
        "ced": st.session_state.cedula,
        "nom": st.session_state.nombre,
        "hor": st.session_state.hora_ref
    })

# --- CABECERA ---
head_l, head_r = st.columns([3, 1])
with head_l:
    st.title("🛵 Control de entregas SERGEM")
with head_r:
    st.write("##") 
    if st.button("🏁 FINALIZAR ENTREGAS", type="primary", use_container_width=True):
        st.session_state.confirmar_cierre = True

if st.session_state.get('confirmar_cierre'):
    st.error("⚠️ **¿ESTÁ SEGURO DE FINALIZAR EL DÍA?**")
    cc1, cc2 = st.columns(2)
    if cc1.button("❌ NO, VOLVER", use_container_width=True):
        st.session_state.confirmar_cierre = False
        st.rerun()
    if cc2.button("🚨 SÍ, CERRAR", use_container_width=True, type="primary"):
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()

# --- INTERFAZ IDENTIFICACIÓN ---
c1, c2 = st.columns(2)
ced_input = c1.text_input("Cédula:", value=st.session_state.cedula)
nom_input = c2.text_input("Nombre:", value=st.session_state.nombre).upper()

if ced_input != st.session_state.cedula or nom_input != st.session_state.nombre:
    st.session_state.cedula = ced_input
    st.session_state.nombre = nom_input
    actualizar_url()

if st.session_state.cedula and st.session_state.nombre:
    if not st.session_state.hora_ref or st.session_state.hora_ref in ["", "None"]:
        st.subheader("🚀 Iniciar Jornada")
        if st.button("▶️ INICIAR ENTREGAS", use_container_width=True):
            st.session_state.hora_ref = datetime.now(col_tz).strftime("%H:%M")
            actualizar_url()
            st.rerun()
    else:
        st.success(f"✅ **Mensajero:** {st.session_state.nombre} | **Hora Base:** {st.session_state.hora_ref}")
        
        # --- BASES DE DATOS ---
        LISTA_CANAVERAL = ['20 DE JULIO', 'BRISAS DE LOS ALAMOS', 'BUGA', 'CAVASA (VIA CANDELARIA)', 'CENTENARIO (AV 4N)', 'COOTRAEMCALI', 'DOSQUEBRADAS (PEREIRA)', 'EL INGENIO', 'EL LIMONAR (CRA 70)', 'GUADALUPE (CALI)', 'JAMUNDÍ (COUNTRY MALL)', 'LOS PINOS', 'PALMIRA', 'PANCE', 'PASOANCHO (CALI)', 'PRADOS DEL NORTE (LA 34)', 'ROLDANILLO', 'SANTA HELENA', 'TULUA', 'VILLAGORGONA', 'VILLANUEVA']
        TIENDAS_POLLOS = {'CALI': {'Super Inter Popular': '4210', 'Super Inter Guayacanes': '4206', 'Super Inter Unico Salomia': '4218', 'Super Inter Villa Colombia': '4215', 'Super Inter El Sembrador': '4216', 'Super Inter Siloe': '4223', 'Super Inter San Fernando': '4232', 'Super Inter Buenos Aires': '4262', 'Super Inter Valdemoro': '4233', 'Carulla la Maria': '4781', 'Super Inter Express Av. Sexta': '4212', 'Super Inter Pasarela': '4214', 'Super Inter Primavera': '4271', 'Super Inter Independencia': '4261', 'Carulla Pasoancho': '4799', 'Carulla Guadalupe': '4090', 'éxito Cra Octava (L)': '650'}, 'MEDELLIN': {'éxito express Ciudad del Rio': '197', 'Carulla Sao Paulo': '341', 'Carulla express Villa Grande': '452', 'Surtimax Centro de la Moda': '516', 'Surtimax Trianon': '745', 'Surtimax San Javier Metro': '758', 'éxito Indiana Mall': '4042', 'éxito San Javier': '4067', 'éxito Gardel': '4070', 'Surtimax Camino Verde': '4381', 'Surtimax Caldas': '4534', 'Surtimax Pilarica': '4557', 'Carulla express Padre Marianito': '4664', 'Carulla express EDS la Sierra': '4665', 'Carulla express Parque Poblado': '4669', 'Carulla express la América': '4776', 'Carulla express Nutibara': '4777', 'Carulla express Laureles': '4778', 'Carulla express Divina Eucaristia': '4829', 'Carulla express Loma Escobero': '4878'}, 'BOGOTA': {'Éxito express Embajada': '110', 'Éxito express Colseguros (CAF)': '301', 'Surtimax Brasil Bosa': '311', 'Surtimax Casa Blanca (CAF)': '434', 'Surtimax la Española': '449', 'Surtimax San Antonio': '450', 'Éxito express Bima': '459', 'Surtimax Barrancas': '467', 'Carulla express Cedritos': '468', 'Surtimax Nueva Roma': '470', 'Surtimax Tibabuyes': '473', 'Surtimax Trinitaria': '474', 'Surtimax la Gloria': '481', 'Surtimax San Fernando': '511', 'Carulla calle 147': '549', 'éxito Plaza Bolivar': '558', 'Surtimax Tocancipá': '573', 'Surtimax San Mateo': '575', 'Surtimax Cajicá': '576', 'Surtimax Sopó': '577', 'Surtimax Compartir Soacha': '579', 'Surtimax Santa Rita': '623', 'éxito express Cra 15 con 100': '657', 'Surtimax la Calera': '703', 'Surtimax Yanguas': '709', 'Surtimax el Socorro': '768', 'Surtimax el Recreo Bosa': '781', 'Carulla la Calera': '886', 'éxito Primavera calle 80': '4068', 'éxito Parque Fontibon': '4069', 'éxito Pradilla': '4071', 'éxito Ciudadel': '4082', 'Éxito express Polo': '4187', 'Surtimax Chapinero': '4523', 'Surtimax Lijaca': '4524', 'Surtimax Quiroga': '4527', 'Surtimax Suba Bilbao': '4533', 'Surtimax Santa Isabel': '4539', 'Carulla BACATA': '4813', 'Carulla SMARTMARKET': '4814', 'Carulla LA PRADERA DE POTOSÍ': '4818', 'Carulla EXPRESS C109 C14': '4822', 'Carulla EXPRESS SIBERIA': '4825', 'Carulla EXPRESS CALLE 90': '4828', 'Carulla EXPRESS PONTEVEDRA': '4836', 'Carulla EXPRESS CARRERA 7': '4839', 'Carulla EXPRESS SALITRE': '4875', 'Carulla EXPRESS CORFERIAS': '4876'}}
        TIENDAS_PANADERIA = {'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES': '4219540', 'CARULLA PUNTO VERDE': '4799540', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA SAN FERNANDO': '2595540', 'CARULLA LA MARIA': '4781540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO LA FLORA': '2054540'}, 'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER SAN SEBASTIAN': '4303540', 'SUPERINTER MANIZALES CENTRO': '4273540', 'SUPERINTER CHIPRE': '4279540', 'SUPERINTER VILLA PILAR': '4280540'}}

        # Selectores con llave dinámica para forzar reinicio total
        r = st.session_state.reset_counter
        f1, f2 = st.columns(2)
        with f1: ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLIN", "BOGOTA"], key=f"s_ciu_{r}")
        with f2: 
            ops_prod = ["PANADERIA"] if ciudad == "MANIZALES" else (["POLLOS"] if ciudad in ["MEDELLIN", "BOGOTA"] else ["POLLOS", "PANADERIA"])
            producto = st.radio("📦 Producto:", ops_prod, horizontal=True, key=f"s_prod_{r}")
        
        opciones_empresa = ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER", "CAÑAVERAL"] if ciudad == "CALI" else ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER"]
        empresa = st.selectbox("🏢 Empresa:", opciones_empresa, key=f"s_emp_{r}")

        info = None
        if ciudad != "--" and empresa != "--":
            if empresa == "CAÑAVERAL":
                c1c, c2c = st.columns(2)
                with c1c: co = st.selectbox("📦 Origen:", ["--"] + sorted(LISTA_CANAVERAL), key=f"co_{r}")
                with c2c: cd = st.selectbox("🏠 Destino:", ["--"] + sorted(LISTA_CANAVERAL), key=f"cd_{r}")
                if co != "--" and cd != "--": info = {"TO": co, "CO": "CAN", "TD": cd, "CD": "CAN"}
            else:
                dic = TIENDAS_PANADERIA.get(ciudad, {}) if producto == "PANADERIA" else TIENDAS_POLLOS.get(ciudad, {})
                if producto == "PANADERIA":
                    p1, p2 = st.columns(2)
                    t_o = p1.selectbox("📦 Recoge en:", ["--"] + sorted(list(dic.keys())), key=f"to_{r}")
                    t_d = p2.selectbox("🏠 Entrega en:", ["--"] + sorted(list(dic.keys())), key=f"td_{r}")
                    if t_o != "--" and t_d != "--": info = {"TO": t_o, "CO": dic[t_o], "TD": t_d, "CD": dic[t_d]}
                else:
                    t_sel = st.selectbox("🏪 Tienda Destino:", ["--"] + sorted(list(dic.keys())), key=f"ct_{r}")
                    if t_sel != "--": info = {"TO": "BASE", "CO": "BASE", "TD": t_sel, "CD": dic[t_sel]}

        if info:
            if producto == "POLLOS":
                col_e, col_m = st.columns(2)
                ent = col_e.number_input("Pollos Enteros:", min_value=0, step=1, value=0, key=f"ent_{r}")
                med = col_m.number_input("Medios Pollos:", min_value=0, step=1, value=0, key=f"med_{r}")
                cant_final = float(ent) + (float(med) * 0.5)
            else:
                cant_final = st.number_input("Cantidad:", min_value=1, step=1, key=f"ccant_{r}")

            if st.button("ENVIAR REGISTRO ✅", use_container_width=True, type="primary"):
                if cant_final <= 0:
                    st.warning("La cantidad debe ser mayor a 0")
                else:
                    ahora = datetime.now(col_tz)
                    fecha_str = ahora.strftime("%d/%m/%Y")
                    h_llegada = ahora.strftime("%H:%M")
                    t_ini = datetime.strptime(st.session_state.hora_ref, "%H:%M")
                    t_fin = datetime.strptime(h_llegada, "%H:%M")
                    minutos = int((t_fin - t_ini).total_seconds() / 60)
                    if minutos < 0: minutos += 1440
                    
                    payload = {
                        "Fecha": fecha_str, "Cedula": st.session_state.cedula, "Mensajero": st.session_state.nombre, 
                        "Empresa": empresa, "Ciudad": ciudad, "Producto": producto, "Tienda_O": info["TO"], 
                        "Cod_O": info["CO"], "Cod_D": info["CD"], "Tienda_D": info["TD"], "Cant": cant_final, 
                        "Inicio": st.session_state.hora_ref, "Llegada": h_llegada, "Minutos": minutos
                    }
                    
                    st.session_state.historial_datos.insert(0, {
                        "Fecha": fecha_str, "Hora": h_llegada, "Producto": producto, 
                        "Recoge": info["TO"], "Entrega": info["TD"], "Cant": cant_final, "Minutos": minutos
                    })
                    
                    try: requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    except: pass 
                    
                    st.session_state.hora_ref = h_llegada
                    actualizar_url()
                    
                    # INCREMENTO DEL CONTADOR: Esto obliga a todos los selectores a resetearse a "--"
                    st.session_state.reset_counter += 1
                    
                    st.success(f"Enviado. Nueva hora base: {h_llegada}")
                    time.sleep(1.2)
                    st.rerun()

    # --- TABLA DE HISTORIAL ---
    if st.session_state.historial_datos:
        st.markdown("---")
        st.subheader("📋 Mis entregas de hoy")
        df_hist = pd.DataFrame(st.session_state.historial_datos)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

