import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM - Control Maestro", layout="wide")

# --- URL DE TU IMPLEMENTACIÓN (Asegúrate de que sea la correcta) ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbxBtAsWq2jhnVrqwhGIVXQ8Ue-aKybwZGp5WwvqIa4p5-Bdi7CROvos1dzy1su8_1Lh/exec"
DB_FILE = "registro_diario.csv"

# --- BASE DE DATOS DE TIENDAS POR EMPRESA ---
# He añadido las nuevas categorías solicitadas
EMPRESAS_TIENDAS = {
    'Exito-Carulla-Superinter-Surtimax': {
        'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'CARULLA CIUDAD JARDIN': '2732540',
        'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES': '2596540', 'SUPER INTER POPULAR': '4210',
        'SUPER INTER VILLA COLOMBIA': '4215', 'SURTIMAX CALDAS': '4534'
    },
    'Cañaveral': {
        'CAÑAVERAL PASOANCHO': 'C001', 'CAÑAVERAL SUR': 'C002', 'CAÑAVERAL NORTE': 'C003'
    },
    'OTROS': {
        'CENTRO LOGÍSTICO': 'LOG01', 'BASE PRINCIPAL': 'BASE01'
    }
}

if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = ""

st.title("🛵 Control Maestro SERGEM")

cedula = st.text_input("Número de Cédula:")
nombre = st.text_input("Nombre del Mensajero:").upper()

if cedula and nombre:
    if st.session_state['hora_referencia'] == "":
        st.subheader("🕒 Iniciar Jornada")
        h_ini = st.time_input("Hora de salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            st.rerun()
    else:
        st.success(f"✅ Sesión: **{nombre}** | Inicio: **{st.session_state['hora_referencia']}**")
        
        c1, c2 = st.columns(2)
        with c1:
            # 1. SELECCIÓN DE EMPRESA (Buscador predictivo habilitado por defecto)
            empresa_sel = st.selectbox("🏢 Empresa/Grupo:", ["--"] + list(EMPRESAS_TIENDAS.keys()))
        with c2:
            prod_sel = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)

        info = None
        if empresa_sel != "--":
            # 2. SELECCIÓN DE TIENDA (Filtra según la empresa seleccionada)
            tiendas_dict = EMPRESAS_TIENDAS[empresa_sel]
            opciones_tienda = ["--"] + sorted(list(tiendas_dict.keys()))
            
            sel_tienda = st.selectbox("🏪 Digite o seleccione la Tienda:", opciones_tienda)
            
            if sel_tienda != "--":
                info = {"O": sel_tienda, "C1": tiendas_dict[sel_tienda]}

        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1)
            msg_status = st.empty()
            
            if st.button("ENVIAR A LA NUBE ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                t_ref = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                t_lleg = datetime.strptime(h_llegada, "%H:%M")
                duracion = int((t_lleg - t_ref).total_seconds() / 60)
                
                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"),
                    "Cedula": cedula, "Mensajero": nombre, "Empresa": empresa_sel, # Nueva columna
                    "Producto": prod_sel, "Tienda": info["O"], "Cod_Rec": str(info["C1"]),
                    "Inicio": st.session_state['hora_referencia'], "Llegada": h_llegada, "Minutos": duracion
                }
                
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    if "Éxito" in res.text:
                        msg_status.success(f"¡Sincronizado! {info['O']}")
                        st.session_state['hora_referencia'] = h_llegada
                        st.rerun()
                    else:
                        msg_status.error(f"Error: {res.text}")
                except Exception:
                    msg_status.error("Falla de conexión.")
