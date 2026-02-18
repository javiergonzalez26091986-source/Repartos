import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import requests
import time
from urllib.parse import quote

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="Control de entregas SERGEM", layout="wide")

# --- BLOQUE DE SEGURIDAD Y ESTÉTICA (TU DISEÑO ORIGINAL) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    div[data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    
    /* Estilo para el botón de recuperación en el sidebar */
    .link-recuperacion {
        background-color: #f0f2f6;
        border: 2px solid #ff4b4b;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        display: block;
        text-decoration: none;
        color: #ff4b4b;
        font-weight: bold;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbzLjiRvoIRnFkjLmHoMVTv-V_zb6xiX3tbakP9b8YWlILKpIn44r8q5-ojqG32NApMz/exec"

# --- MOTOR DE PERSISTENCIA POR URL ---
params = st.query_params
if 'cedula' not in st.session_state: st.session_state.cedula = params.get("ced", "")
if 'nombre' not in st.session_state: st.session_state.nombre = params.get("nom", "")
if 'hora_ref' not in st.session_state: st.session_state.hora_ref = params.get("hor", "")

# --- INTERFAZ ---
st.title("🛵 Control de entregas SERGEM")

with st.sidebar:
    if st.button("🏁 FINALIZAR DÍA", type="primary"):
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()
    
    # --- BOTÓN DINÁMICO DE RESTAURACIÓN ---
    if st.session_state.cedula and st.session_state.hora_ref:
        st.markdown("---")
        st.write("🔄 **¿Se cerró el navegador?**")
        nom_encoded = quote(st.session_state.nombre)
        # IMPORTANTE: Reemplaza con tu URL real de Streamlit
        url_app = "https://repartos-sergem.streamlit.app/" 
        link_recuperacion = f"{url_app}?ced={st.session_state.cedula}&nom={nom_encoded}&hor={st.session_state.hora_ref}"
        
        st.markdown(f"""
            <a href="{link_recuperacion}" target="_self" class="link-recuperacion">
                🚀 TOCAR AQUÍ PARA ASEGURAR SESIÓN
            </a>
            <p style='font-size: 0.8em; color: gray; text-align: center; margin-top: 5px;'>
            Toca para fijar los datos o deja presionado para copiar y guardar en WhatsApp.
            </p>
        """, unsafe_allow_html=True)

# 2. Identificación
c1, c2 = st.columns(2)
ced_input = c1.text_input("Cédula:", value=st.session_state.cedula)
nom_input = c2.text_input("Nombre:", value=st.session_state.nombre).upper()

# Si el usuario escribe manualmente, actualizamos la URL
if ced_input != st.session_state.cedula or nom_input != st.session_state.nombre:
    st.session_state.cedula = ced_input
    st.session_state.nombre = nom_input
    st.query_params.update({"ced": ced_input, "nom": nom_input, "hor": st.session_state.hora_ref})

if st.session_state.cedula and st.session_state.nombre:
    
    # Lógica de Inicio de Jornada
    if not st.session_state.hora_ref or st.session_state.hora_ref in ["", "None"]:
        st.subheader("🚀 Iniciar Jornada")
        if st.button("▶️ CAPTURAR HORA DE SALIDA", use_container_width=True):
            nueva_hora = datetime.now(col_tz).strftime("%H:%M")
            st.session_state.hora_ref = nueva_hora
            st.query_params.update({"ced": st.session_state.cedula, "nom": st.session_state.nombre, "hor": nueva_hora})
            st.rerun()
    else:
        st.success(f"✅ **Mensajero:** {st.session_state.nombre} | **Hora Base:** {st.session_state.hora_ref}")
        
        # --- BASES DE DATOS (RESTAURADAS COMPLETAS) ---
        LISTA_CANAVERAL = ['20 DE JULIO', 'BRISAS DE LOS ALAMOS', 'BUGA', 'CAVASA (VIA CANDELARIA)', 'CENTENARIO (AV 4N)', 'COOTRAEMCALI', 'DOSQUEBRADAS (PEREIRA)', 'EL INGENIO', 'EL LIMONAR (CRA 70)', 'GUADALUPE (CALI)', 'JAMUNDÍ (COUNTRY MALL)', 'LOS PINOS', 'PALMIRA', 'PANCE', 'PASOANCHO (CALI)', 'PRADOS DEL NORTE (LA 34)', 'ROLDANILLO', 'SANTA HELENA', 'TULUA', 'VILLAGORGONA', 'VILLANUEVA']
        
        TIENDAS_POLLOS = {
            'CALI': {'Super Inter Popular': '4210', 'Super Inter Guayacanes': '4206', 'Super Inter Unico Salomia': '4218', 'Super Inter Villa Colombia': '4215', 'Super Inter El Sembrador': '4216', 'Super Inter Siloe': '4223', 'Super Inter San Fernando': '4232', 'Super Inter Buenos Aires': '4262', 'Super Inter Valdemoro': '4233', 'Carulla la Maria': '4781', 'Super Inter Express Av. Sexta': '4212', 'Super Inter Pasarela': '4214', 'Super Inter Primavera': '4271', 'Super Inter Independencia': '4261', 'Carulla Pasoancho': '4799', 'éxito Cra Octava (L)': '650'},
            'MEDELLIN': {'éxito express Ciudad del Rio': '197', 'Carulla Sao Paulo': '341', 'Carulla express Villa Grande': '452', 'Surtimax Centro de la Moda': '516', 'Surtimax Trianon': '745', 'Surtimax San Javier Metro': '758', 'éxito Indiana Mall': '4042', 'éxito San Javier': '4067', 'éxito Gardel': '4070', 'Surtimax Camino Verde': '4381', 'Surtimax Caldas': '4534', 'Surtimax Pilarica': '4557', 'Carulla express Padre Marianito': '4664', 'Carulla express EDS la Sierra': '4665', 'Carulla express Parque Poblado': '4669', 'Carulla express la América': '4776', 'Carulla express Nutibara': '4777', 'Carulla express Laureles': '4778', 'Carulla express Divina Eucaristia': '4829', 'Carulla express Loma Escobero': '4878'},
            'BOGOTA': {'éxito express Embajada': '110', 'éxito express Colseguros (CAF)': '301', 'Surtimax Brasil Bosa': '311', 'Surtimax Casa Blanca (CAF)': '434', 'Surtimax la Española': '449', 'Surtimax San Antonio': '450', 'éxito express Bima': '459', 'Surtimax Barrancas': '467', 'Carulla express Cedritos': '468', 'Surtimax Nueva Roma': '470', 'Surtimax Tibabuyes': '473', 'Surtimax Trinitaria': '474', 'Surtimax la Gloria': '481', 'Surtimax San Fernando': '511', 'Carulla calle 147': '549', 'éxito Plaza Bolivar': '558', 'Surtimax Tocancipá': '573', 'Surtimax San Mateo': '575', 'Surtimax Cajicá': '576', 'Surtimax Sopó': '577', 'Surtimax Compartir Soacha': '579', 'Surtimax Santa Rita': '623', 'éxito express Cra 15 con 100': '657', 'Surtimax la Calera': '703', 'Surtimax Yanguas': '709', 'Surtimax el Socorro': '768', 'Surtimax el Recreo Bosa': '781', 'Carulla la Calera': '886', 'éxito Primavera calle 80': '4068', 'éxito Parque Fontibon': '4069', 'éxito Pradilla': '4071', 'éxito Ciudadel': '4082', 'éxito express Cra 24 83-22': '4187', 'Surtimax Chapinero': '4523', 'Surtimax Lijaca': '4524', 'Surtimax Quiroga': '4527', 'Surtimax Suba Bilbao': '4533', 'Surtimax Santa Isabel': '4539', 'Carulla BACATA': '4813', 'Carulla SMARTMARKET': '4814', 'Carulla LA PRADERA DE POTOSÍ': '4818', 'Carulla EXPRESS C109 C14': '4822', 'Carulla EXPRESS SIBERIA': '4825', 'Carulla EXPRESS CALLE 90': '4828', 'Carulla EXPRESS PONTEVEDRA': '4836', 'Carulla EXPRESS CARRERA 7': '4839', 'Carulla EXPRESS SALITRE': '4875', 'Carulla EXPRESS CORFERIAS': '4876'}
        }
        
        TIENDAS_PANADERIA = {
            'CALI': {'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES': '4219540', 'CARULLA PUNTO VERDE': '4799540', 'CARULLA AV COLOMBIA': '4219540', 'CARULLA SAN FERNANDO': '2595540', 'CARULLA LA MARIA': '4781540', 'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO LA FLORA': '2054540'},
            'MANIZALES': {'CARULLA CABLE PLAZA': '2334540', 'ÉXITO MANIZALES': '383', 'CARULLA SAN MARCEL': '4805', 'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER SAN SEBASTIAN': '4303540', 'SUPERINTER MANIZALES CENTRO': '4273540', 'SUPERINTER CHIPRE': '4279540', 'SUPERINTER VILLA PILAR': '4280540'}
        }

        # 3. Selectores de Ciudad, Producto y Empresa
        f1, f2 = st.columns(2)
        with f1: 
            ciudad = st.selectbox("📍 Ciudad:", ["--", "CALI", "MANIZALES", "MEDELLIN", "BOGOTA"], key="s_ciu")
        
        opciones_producto = ["POLLOS", "PANADERIA"]
        if ciudad == "MANIZALES": opciones_producto = ["PANADERIA"]
        elif ciudad in ["MEDELLIN", "BOGOTA"]: opciones_producto = ["POLLOS"]
        
        with f2: 
            producto = st.radio("📦 Producto:", opciones_producto, horizontal=True, key="s_prod")
        
        opciones_empresa = ["--", "EXITO-CARULLA-SURTIMAX-SUPERINTER"]
        if ciudad == "CALI": opciones_empresa.append("CAÑAVERAL")
        empresa = st.selectbox("🏢 Empresa:", opciones_empresa, key="s_emp")

        # 4. Lógica de Tiendas Origen/Destino
        info = None
        if ciudad != "--" and empresa != "--":
            if empresa == "CAÑAVERAL":
                c1c, c2c = st.columns(2)
                with c1c: co = st.selectbox("📦 Origen:", ["--"] + sorted(LISTA_CANAVERAL), key="co")
                with c2c: cd = st.selectbox("🏠 Destino:", ["--"] + sorted(LISTA_CANAVERAL), key="cd")
                if co != "--" and cd != "--": info = {"TO": co, "CO": "CAN", "TD": cd, "CD": "CAN"}
            
            elif empresa == "EXITO-CARULLA-SURTIMAX-SUPERINTER":
                if producto == "PANADERIA":
                    dic = TIENDAS_PANADERIA.get(ciudad, {})
                    if dic:
                        p1, p2 = st.columns(2)
                        with p1: t_o = st.selectbox("📦 Recoge en:", ["--"] + sorted(list(dic.keys())), key="to")
                        with p2: t_d = st.selectbox("🏠 Entrega en:", ["--"] + sorted(list(dic.keys())), key="td")
                        if t_o != "--" and t_d != "--": info = {"TO": t_o, "CO": dic[t_o], "TD": t_d, "CD": dic[t_d]}
                else:
                    dic = TIENDAS_POLLOS.get(ciudad, {})
                    if dic:
                        t_sel = st.selectbox("🏪 Tienda Destino:", ["--"] + sorted(list(dic.keys())), key="ct")
                        if t_sel != "--": info = {"TO": "BASE", "CO": "BASE", "TD": t_sel, "CD": dic[t_sel]}

        # 5. Botón de Envío
        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1, key="ccant")
            if st.button("ENVIAR REGISTRO ✅", use_container_width=True, type="primary"):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                # Cálculo de minutos
                t_ini = datetime.strptime(st.session_state.hora_ref, "%H:%M")
                t_fin = datetime.strptime(h_llegada, "%H:%M")
                minutos = int((t_fin - t_ini).total_seconds() / 60)
                if minutos < 0: minutos += 1440

                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"), 
                    "Cedula": st.session_state.cedula, 
                    "Mensajero": st.session_state.nombre,
                    "Empresa": empresa, "Ciudad": ciudad, "Producto": producto,
                    "Tienda_O": info["TO"], "Cod_O": info["CO"], 
                    "Tienda_D": info["TD"], "Cod_D": info["CD"],
                    "Cant": int(cant), 
                    "Inicio": st.session_state.hora_ref, 
                    "Llegada": h_llegada, 
                    "Minutos": minutos
                }
                
                try: 
                    requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                except: 
                    st.error("Error de conexión al Drive. Intenta de nuevo.")

                # ACTUALIZACIÓN DE HORA BASE PARA EL PRÓXIMO VIAJE
                st.session_state.hora_ref = h_llegada
                st.query_params.update({"ced": st.session_state.cedula, "nom": st.session_state.nombre, "hor": h_llegada})
                
                # Limpiar solo los selectores de carga
                for k in ['s_ciu', 's_emp', 'co', 'cd', 'ct', 'to', 'td', 'ccant']:
                    if k in st.session_state: del st.session_state[k]
                
                st.success(f"Registro Procesado. Nueva hora base: {h_llegada}")
                time.sleep(1.5)
                st.rerun()
