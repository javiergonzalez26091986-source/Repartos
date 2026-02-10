import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="App Repartos Cali", page_icon="🚚")

# --- DATOS MAESTROS ---
# Sedes con códigos asignados (E=Éxito, C=Cañaveral, R=Carulla)
DATOS_SEDES = {
    'Éxito': {
        'San Fernando': 'EX-001', 'Unicentro': 'EX-002', 'Chipichape': 'EX-003', 
        'Palmetto': 'EX-004', 'Pasoancho': 'EX-005', 'Norte': 'EX-006'
    },
    'Cañaveral': {
        'Centenario': 'CA-101', 'Pasoancho': 'CA-102', 'Pance': 'CA-103', 
        'El Ingenio': 'CA-104', 'Limonar': 'CA-105', 'La Primera': 'CA-106'
    },
    'Carulla': {
        'Pance': 'CR-201', 'San Fernando': 'CR-202', 'El Peñón': 'CR-203', 'Ciudad Jardín': 'CR-204'
    }
}

MENSAJEROS = ["Carlos Alberto", "Duberney", "Jhon Jairo", "Wilson", "Mauricio"]

# --- LÓGICA DE ALMACENAMIENTO ---
archivo_db = "base_entregas.csv"

def guardar_en_csv(nuevo_dato):
    df = pd.DataFrame([nuevo_dato])
    if not os.path.isfile(archivo_db):
        df.to_csv(archivo_db, index=False, encoding='utf-8')
    else:
        df.to_csv(archivo_db, mode='a', header=False, index=False, encoding='utf-8')

# --- INTERFAZ DE USUARIO ---
st.title("🚚 Registro de Repartos")
st.markdown("---")

# 1. Perfil del Mensajero
st.sidebar.header("Perfil")
nombre = st.sidebar.selectbox("Seleccione su nombre:", MENSAJEROS)
st.sidebar.write(f"Conectado como: **{nombre}**")

# 2. Formulario de Entrega
with st.container():
    st.subheader("Nueva Entrega")
    
    col1, col2 = st.columns(2)
    with col1:
        hora_salida = st.time_input("Hora de salida de bodega:")
    with col2:
        empresa = st.selectbox("Empresa:", list(DATOS_SEDES.keys()))

    sedes_disponibles = list(DATOS_SEDES[empresa].keys())
    sede = st.selectbox("Sede / Tienda:", sedes_disponibles)
    
    # Mostrar el código de forma destacada como pidió la cliente
    codigo_tienda = DATOS_SEDES[empresa][sede]
    st.info(f"Código de Tienda para cobro: **{codigo_tienda}**")

    producto = st.radio("Producto:", ["Pollo", "Pan"], horizontal=True)
    cantidad = st.number_input("Cantidad entregada:", min_value=1, step=1)

    if st.button("REGISTRAR ENTREGA ✅", use_container_width=True):
        # Cálculo de tiempos
        hora_llegada = datetime.now()
        dt_salida = datetime.combine(datetime.today(), hora_salida)
        minutos_totales = int((hora_llegada - dt_salida).total_seconds() / 60)
        
        # Crear registro
        registro = {
            "Fecha": datetime.now().strftime("%d/%m/%Y"),
            "Mensajero": nombre,
            "Empresa": empresa,
            "Sede": sede,
            "Código": codigo_tienda,
            "Producto": producto,
            "Cantidad": cantidad,
            "Hora_Salida": hora_salida.strftime("%H:%M"),
            "Hora_Entrega": hora_llegada.strftime("%H:%M"),
            "Tiempo_Minutos": minutos_totales
        }
        
        guardar_en_csv(registro)
        st.success(f"¡Registrado! Tiempo de reparto: {minutos_totales} min.")
        st.balloons()

# 3. Historial (Para que el mensajero vea lo que ha hecho)
st.markdown("---")
st.subheader("📋 Últimos registros de hoy")
if os.path.isfile(archivo_db):
    df_historial = pd.read_csv(archivo_db)
    st.dataframe(df_historial.tail(5), use_container_width=True)
else:
    st.write("Aún no hay registros hoy.")