import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import requests

# 1. Configuración de Zona Horaria y Página
col_tz = pytz.timezone('America/Bogota')
st.set_page_config(page_title="SERGEM - Control Maestro", layout="wide")

# --- URL DE TU IMPLEMENTACIÓN ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbxBtAsWq2jhnVrqwhGIVXQ8Ue-aKybwZGp5WwvqIa4p5-Bdi7CROvos1dzy1su8_1Lh/exec"
DB_FILE = "registro_diario.csv"

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Gestión")
    if st.button("🗑️ REINICIAR DÍA"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state['hora_referencia'] = ""
        st.rerun()
    st.write("---")
    st.caption("v3.6 - Panadería Flexible + Buscador")

# --- BASE DE DATOS UNIFICADA ---
TIENDAS_POR_CIUDAD = {
    'CALI': {
        'SUPER INTER POPULAR': '4210', 'SUPER INTER GUAYACANES': '4206', 'SUPER INTER UNICO SALOMIA': '4218', 
        'SUPER INTER VILLA COLOMBIA': '4215', 'SUPER INTER EL SEMBRADOR': '4216', 'SUPER INTER SILOE': '4223', 
        'CARULLA LA MARIA': '4781', 'ÉXITO CRA OCTAVA (L)': '650', 'CARULLA CIUDAD JARDIN': '2732540',
        'CARULLA HOLGUINES': '2596540', 'CARULLA PANCE': '2594540', 'ÉXITO UNICALI': '2054056', 
        'ÉXITO JAMUNDI': '2054049', 'CARULLA AV COLOMBIA': '4219540'
    },
    'MEDELLÍN': {
        'ÉXITO EXPRESS CIUDAD DEL RIO': '197', 'CARULLA SAO PAULO': '341', 'ÉXITO GARDEL': '4070', 
        'SURTIMAX CALDAS': '4534', 'SURTIMAX PILARICA': '4557'
    },
    'BOGOTÁ': {
        'CARULLA EXPRESS CEDRITOS': '468', 'ÉXITO PLAZA BOLIVAR': '558', 'SURTIMAX BRASIL BOSA': '311', 
        'SURTIMAX LA ESPAÑOLA': '449', 'SURTIMAX SAN ANTONIO': '450'
    },
    'MANIZALES': {
        'ÉXITO MANIZALES Centro': '383', 'CARULLA CABLE PLAZA': '2334', 'CARULLA SAN MARCEL': '4805',
        'SUPERINTER CRISTO REY': '4301540', 'SUPERINTER ALTA SUIZA': '4302540', 'SUPERINTER MANIZALES CENTRO': '4273540'
    }
}

if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = ""

st.title("🛵 Control Maestro SERGEM")

# --- IDENTIFICACIÓN ---
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
        st.success(f"✅ Registro para: **{nombre}** | Inicio: **{st.session_state['hora_referencia']}**")
        
        c1, c2 = st.columns(2)
        with c1:
            ciudad_sel = st.selectbox("📍 Ciudad:", ["--", "CALI", "MEDELLÍN", "BOGOTÁ", "MANIZALES"])
        with c2:
            prod_sel = st.radio("📦 Producto:", ["POLLOS", "PANADERÍA"], horizontal=True)

        info = None
        if ciudad_sel != "--":
            tiendas_dict = TIENDAS_POR_CIUDAD.get(ciudad_sel, {})
            opciones = ["--"] + sorted(list(tiendas_dict.keys()))
            
            if prod_sel == "PANADERÍA":
                # Selección libre de Origen y Destino para Panadería
                st.markdown("### 🥖 Configuración de Ruta")
                origen = st.selectbox("🏬 Punto de Recogida (Origen):", opciones, key="orig_pan")
                destino = st.selectbox("🏪 Punto de Entrega (Destino):", opciones, key="dest_pan")
                
                if origen != "--" and destino != "--":
                    info = {
                        "O": origen, "C1": tiendas_dict[origen],
                        "D": destino, "C2": tiendas_dict[destino]
                    }
            else:
                # Selección única para Pollos
                sel_tienda = st.selectbox("🏪 Tienda/Cliente:", opciones, key="pollos_sel")
                if sel_tienda != "--":
                    info = {
                        "O": sel_tienda, "C1": tiendas_dict[sel_tienda],
                        "D": sel_tienda, "C2": "N/A"
                    }

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
                    "Cedula": cedula, "Mensajero": nombre, "Ciudad": ciudad_sel, "Producto": prod_sel,
                    "Tienda": info["O"], "Cod_Rec": str(info["C1"]), "Cod_Ent": str(info["C2"]), "Destino": info["D"],
                    "Cant": int(cant), "Inicio": st.session_state['hora_referencia'], "Llegada": h_llegada, "Minutos": duracion
                }
                
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=payload, timeout=15)
                    if "Éxito" in res.text:
                        msg_status.success(f"¡Sincronizado! De {info['O']} a {info['D']}")
                        st.session_state['hora_referencia'] = h_llegada
                        pd.DataFrame([payload]).to_csv(DB_FILE, mode='a', index=False, header=not os.path.exists(DB_FILE))
                        st.rerun()
                    else:
                        msg_status.error(f"Error en servidor: {res.text}")
                except Exception:
                    msg_status.error("Falla de conexión. Intente de nuevo.")

    # Respaldo local
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if not df.empty:
                st.markdown("---")
                st.subheader("📋 Respaldo local")
                st.dataframe(df.tail(5), use_container_width=True)
        except Exception: pass
