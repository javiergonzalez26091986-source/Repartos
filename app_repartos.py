import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM - Control Maestro v4.0", layout="wide")

# --- NUEVOS LINKS DE IMPLEMENTACIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbxacaWE8zr6C3j3dWtONO1a1JG82wslcnPfOT1WK2rGv6-vfBU46wk3m-BZE_1MtOk/exec"
DB_FILE = "registro_diario.csv"

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state['hora_referencia'] = ""
        st.rerun()
    st.write("---")
    st.caption("v4.0 - Estructura Alineada (13 Col)")

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

# --- IDENTIFICACIÓN ---
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
        
        # --- FILTROS DE REPARTO ---
        c1, c2, c3 = st.columns(3)
        with c1:
            ciudad_sel = st.selectbox("📍 Ciudad:", ["--", "CALI", "MEDELLÍN", "BOGOTÁ", "MANIZALES"])
        with c2:
            prod_sel = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)
        with c3:
            empresa_sel = st.selectbox("🏢 Empresa/Grupo:", ["--"] + list(EMPRESAS_TIENDAS.keys()))

        info = None
        if empresa_sel != "--" and ciudad_sel != "--":
            tiendas_dict = EMPRESAS_TIENDAS[empresa_sel]
            opciones_tienda = ["--"] + sorted(list(tiendas_dict.keys()))
            
            if prod_sel == "PANADERÍA":
                st.markdown("### 🥖 Ruta Flexible")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    origen = st.selectbox("📦 Recoge en:", opciones_tienda, key="orig_pan")
                with col_p2:
                    destino = st.selectbox("🏠 Entrega en:", opciones_tienda, key="dest_pan")
                
                if origen != "--" and destino != "--":
                    info = {"TO": origen, "CO": tiendas_dict[origen], "TD": destino, "CD": tiendas_dict[destino]}
            else:
                sel_tienda = st.selectbox("🏪 Tienda de Entrega:", opciones_tienda, key="pollos_sel")
                if sel_tienda != "--":
                    info = {"TO": sel_tienda, "CO": tiendas_dict[sel_tienda], "TD": sel_tienda, "CD": "N/A"}

        if info:
            cant = st.number_input("Cantidad:", min_value=1, step=1)
            msg_status = st.empty()
            
            if st.button("ENVIAR A LA NUBE ✅", use_container_width=True):
                ahora = datetime.now(col_tz)
                h_llegada = ahora.strftime("%H:%M")
                
                t_ref = datetime.strptime(st.session_state['hora_referencia'], "%H:%M")
                t_lleg = datetime.strptime(h_llegada, "%H:%M")
                duracion = int((t_lleg - t_ref).total_seconds() / 60)
                
                # PAYLOAD ALINEADO CON EL APPS SCRIPT
                payload = {
                    "Fecha": ahora.strftime("%d/%m/%Y"),
                    "Cedula": cedula,
                    "Mensajero": nombre,
                    "Empresa": empresa_sel,
                    "Ciudad": ciudad_sel,
                    "Producto": prod_sel,
                    "Tienda_O": info["TO"],
                    "Cod_O": str(info["CO"]),
                    "Cod_D": str(info["CD"]),
                    "Tienda_D": info["TD"],
                    "Cant": int(cant),
                    "Inicio": st.session_state['hora_referencia'],
                    "Llegada": h_llegada,
                    "Minutos": duracion
                }
                
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    if "Éxito" in res.text:
                        msg_status.success(f"¡Sincronizado! {info['TD']}")
                        st.session_state['hora_referencia'] = h_llegada
                        pd.DataFrame([payload]).to_csv(DB_FILE, mode='a', index=False, header=not os.path.exists(DB_FILE))
                        st.rerun()
                    else:
                        msg_status.error(f"Error: {res.text}")
                except Exception:
                    msg_status.error("Falla de conexión.")

    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE).tail(5)
            st.markdown("---")
            st.subheader("📋 Respaldo Local (Últimos 5)")
            st.dataframe(df, use_container_width=True)
        except: pass
