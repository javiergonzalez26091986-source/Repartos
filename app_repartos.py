import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Repartos Cali - Doña Yesenia", page_icon="🛵")

# --- CONFIGURACIÓN DE RUTAS ---
# Nota: En Streamlit Cloud, el archivo se guardará temporalmente en la nube.
DB_FILE = "base_general_repartos.csv"

# --- DATOS MAESTROS (Sin tildes para evitar errores en Excel) ---
DATOS = {
    'Exito': {'San Fernando': 'EX-001', 'Unicentro': 'EX-002', 'Chipichape': 'EX-003', 'Pasoancho': 'EX-005'},
    'Canaveral': {'Centenario': 'CA-101', 'Pasoancho': 'CA-102', 'Pance': 'CA-103', 'Limonar': 'CA-105'},
    'Carulla': {'Pance': 'CR-201', 'San Fernando': 'CR-202', 'El Penon': 'CR-203'}
}
MENSAJEROS = ["Carlos Alberto", "Duberney", "Jhon Jairo", "Wilson", "Mauricio"]

# --- GESTIÓN DE SESIÓN ---
if 'sesion' not in st.session_state:
    st.session_state['sesion'] = False
if 'hora_referencia' not in st.session_state:
    st.session_state['hora_referencia'] = ""

# --- PANTALLA DE LOGIN ---
if not st.session_state['sesion']:
    st.title("🔐 Acceso Domiciliarios")
    nombre_sel = st.selectbox("Seleccione su nombre:", [""] + MENSAJEROS)
    cedula_sel = st.text_input("Ingrese su número de cédula:", type="password")
    
    if st.button("INGRESAR AL SISTEMA"):
        if nombre_sel != "" and cedula_sel:
            st.session_state['sesion'] = True
            st.session_state['nombre'] = nombre_sel
            st.session_state['cedula'] = cedula_sel
            st.rerun()
        else:
            st.error("Por favor, complete sus datos.")
else:
    st.sidebar.title(f"👤 {st.session_state['nombre']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    st.title("🚚 Registro de Reparto")

    # --- PASO 1: HORA CON DOS PUNTOS PREDETERMINADOS ---
    if st.session_state['hora_referencia'] == "":
        st.subheader("Paso 1: Hora de salida CEDI")
        st.write("Digite la hora de salida de bodega (Formato 24h):")
        
        # Columnas para simular HH : MM
        c1, c2, c3 = st.columns([2, 1, 2])
        with c1:
            h_in = st.text_input("HH", max_chars=2, placeholder="06", key="h_input")
        with c2:
            # Mostramos los dos puntos fijos en el centro
            st.markdown("<h3 style='text-align: center; margin-top: 25px;'>:</h3>", unsafe_allow_html=True)
        with c3:
            m_in = st.text_input("MM", max_chars=2, placeholder="30", key="m_input")
        
        if st.button("FIJAR HORA DE SALIDA"):
            if h_in.isdigit() and m_in.isdigit() and len(h_in) == 2 and len(m_in) == 2:
                st.session_state['hora_referencia'] = f"{h_in}:{m_in}"
                st.rerun()
            else:
                st.error("Use 2 números para cada campo (ej: 07 : 00)")
    else:
        # --- PASO 2: DATOS DEL PEDIDO (ENCADENADO) ---
        st.info(f"🕒 Hora de inicio para este pedido: **{st.session_state['hora_referencia']}**")
        if st.button("🔄 Volví al CEDI (Resetear Hora)"):
            st.session_state['hora_referencia'] = ""
            st.rerun()

        st.markdown("---")
        
        empresa = st.selectbox("Empresa Cliente:", list(DATOS.keys()))
        sede = st.selectbox("Sede de Entrega:", list(DATOS[empresa].keys()))
        producto = st.radio("Producto:", ["Pollo", "Pan"], horizontal=True)
        cantidad = st.number_input("Cantidad de unidades:", min_value=1, step=1)

        if st.button("GUARDAR REGISTRO ✅", use_container_width=True):
            ahora = datetime.now()
            # Cálculo de tiempo desde la salida anterior
            dt_inicio = datetime.strptime(st.session_state['hora_referencia'], "%H:%M").replace(
                year=ahora.year, month=ahora.month, day=ahora.day
            )
            minutos = int((ahora - dt_inicio).total_seconds() / 60)
            
            registro = {
                "Fecha": ahora.strftime("%d/%m/%Y"),
                "Cedula": st.session_state['cedula'],
                "Mensajero": st.session_state['nombre'],
                "Empresa": empresa,
                "Sede": sede,
                "Codigo": DATOS[empresa][sede],
                "Producto": producto,
                "Cantidad": cantidad,
                "Salida": st.session_state['hora_referencia'],
                "Entrega": ahora.strftime("%H:%M"),
                "Minutos": minutos
            }
            
            # Guardado Local/Nube
            df_nuevo = pd.DataFrame([registro])
            archivo_existe = os.path.exists(DB_FILE)
            df_nuevo.to_csv(DB_FILE, mode='a', index=False, header=not archivo_existe, encoding='utf-8-sig')
            
            # ACTUALIZACIÓN AUTOMÁTICA: La entrega de hoy es la salida de la próxima
            st.session_state['hora_referencia'] = ahora.strftime("%H:%M")
            st.success(f"¡Pedido guardado! Próxima salida: {st.session_state['hora_referencia']}")
            st.rerun()

    # --- HISTORIAL INDIVIDUAL ---
    if os.path.exists(DB_FILE):
        st.markdown("---")
        df_dia = pd.read_csv(DB_FILE)
        st.subheader("📋 Mi actividad de hoy")
        mis_datos = df_dia[df_dia['Cedula'].astype(str) == str(st.session_state['cedula'])]
        st.dataframe(mis_datos, use_container_width=True)
        
        with open(DB_FILE, "rb") as file:
            st.download_button("📥 Descargar Reporte (CSV)", data=file, file_name="repartos_diarios.csv", mime="text/csv")
