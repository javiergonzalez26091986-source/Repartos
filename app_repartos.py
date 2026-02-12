import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM - Control Maestro v3.8", layout="wide")

# --- NUEVOS LINKS DE IMPLEMENTACIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbxYzRm6O2lkLCYwwnGjnlPc83gp40pEQ-S0Rj2znpvlHNk3e_lKZt7iGJydxOrr70s/exec"
DB_FILE = "registro_diario.csv"

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state['hora_referencia'] = ""
        st.rerun()
    st.write("---")
    st.caption("v3.8 - Grupos Empresariales Activos")

# --- BASE DE DATOS DE TIENDAS POR GRUPO ---
EMPRESAS_TIENDAS = {
    'EXITO-CARULLA-SUPERINTER-SURTIMAX': {
        'ÉXITO UNICALI': '2054056', 'ÉXITO JAMUNDI': '2054049', 'ÉXITO PLAZA BOLIVAR': '558',
        'CARULLA CIUDAD JARDIN': '2732540', 'CARULLA PANCE': '2594540', 'CARULLA HOLGUINES': '2596540',
        'CARULLA AV COLOMBIA': '4219540', 'CARULLA LA MARIA': '4781', 'SUPER INTER POPULAR': '4210',
        'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 'SUPER INTER VILLA COLOMBIA': '4215',
        'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 'SURTIMAX CALDAS': '4534',
        'SURTIMAX PILARICA': '4557', 'SURTIMAX BRASIL BOSA': '311'
    },
    'CAÑAVERAL': {
        'CAÑAVERAL PASOANCHO': 'CAN01', 'CAÑAVERAL SUR': 'CAN02', 'CAÑAVERAL NORTE': 'CAN03',
        'CAÑAVERAL QUINTA CON QUINTA': 'CAN04'
    },
    'OTROS / INDEPENDIENTES': {
        'TIENDA LOCAL 1': 'LOC01', 'BASE CENTRAL': 'BASE01', 'LOGÍSTICA': 'LOG01'
    }
}

if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = ""

st.title("🛵 Control Maestro SERGEM")

# --- SECCIÓN 1: IDENTIFICACIÓN ---
col_id1, col_id2 = st.columns(2)
with col_id1:
    cedula = st.text_input("Número de Cédula:")
with col_id2:
    nombre = st.text_input("Nombre del Mensajero:").upper()

if cedula and nombre:
    if st.session_state['hora_referencia'] == "":
        st.subheader("🕒 Iniciar Jornada")
        h_ini = st.time_input("Hora de salida de Base:", datetime.now(col_tz))
        if st.button("COMENZAR RECORRIDO"):
            st.session_state['hora_referencia'] = h_ini.strftime("%H:%M")
            st.rerun()
    else:
        st.success(f"✅ Mensajero: **{nombre}** | Inicio: **{st.session_state['hora_referencia']}**")
        
        # --- SECCIÓN 2: SELECCIÓN DE CLIENTE ---
        c1, c2 = st.columns(2)
        with c1:
            empresa_sel = st.selectbox("🏢 Seleccione Empresa/Grupo:", ["--"] + list(EMPRESAS_TIENDAS.keys()))
        with c2:
            prod_sel = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)

        info = None
        if empresa_sel != "--":
            # Buscador predictivo de tiendas basado en la empresa
            tiendas_dict = EMPRESAS_TIENDAS[empresa_sel]
            opciones_tienda = ["--"] + sorted(list(tiendas_dict.keys()))
            
            sel_tienda = st.selectbox("🏪 Busque y seleccione la Tienda:", opciones_tienda)
            
            if sel_tienda != "--":
                info = {"O": sel_tienda, "C1": tiendas_dict[sel_tienda]}

        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1)
            msg_status = st.empty()
            
            if st.button("ENVIAR A LA NUBE ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                # Cálculo de tiempo
                t_ref = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                t_lleg = datetime.strptime(h_llegada, "%H:%M")
                duracion = int((t_lleg - t_ref).total_seconds() / 60)
                
                # Preparamos el envío (Asegúrate que el AppScript reciba estos nombres)
                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"),
                    "Cedula": cedula, 
                    "Mensajero": nombre, 
                    "Empresa": empresa_sel, 
                    "Producto": prod_sel, 
                    "Tienda": info["O"], 
                    "Cod_Rec": str(info["C1"]),
                    "Inicio": st.session_state['hora_referencia'], 
                    "Llegada": h_llegada, 
                    "Minutos": duracion
                }
                
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    if "Éxito" in res.text:
                        msg_status.success(f"¡Guardado! Destino: {info['O']}")
                        st.session_state['hora_referencia'] = h_llegada
                        # Guardado local de respaldo
                        pd.DataFrame([payload]).to_csv(DB_FILE, mode='a', index=False, header=not os.path.exists(DB_FILE))
                        st.rerun()
                    else:
                        msg_status.error(f"Error en servidor: {res.text}")
                except Exception:
                    msg_status.error("Falla de conexión. Revisa tu internet.")

    # Respaldo visual
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if not df.empty:
                st.markdown("---")
                st.subheader("📋 Últimos registros (Local)")
                st.dataframe(df.tail(5), use_container_width=True)
        except Exception: pass
