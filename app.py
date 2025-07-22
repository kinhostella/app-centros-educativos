import streamlit as st
import pandas as pd
import io

# Título de la aplicación
st.set_page_config(
    page_title="Visualizador de Centros Educativos",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🗺️ Centros Educativos en Galicia")
st.markdown(
    """
    Esta aplicación te permite visualizar centros educativos en un mapa y filtrarlos
    por su distancia y tiempo de viaje a Santiago de Compostela.
    """
)

# --- Carga de datos ---
# Puedes cargar tu CSV aquí. Para este ejemplo, simularé un DataFrame.
# Asegúrate de que tu archivo CSV se llame 'centros.csv' y esté en la misma carpeta,
# o sube el tuyo usando el widget de carga.

uploaded_file = st.file_uploader("Sube tu archivo CSV de centros", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=',') # Asume que el separador es ','
        st.success("Archivo CSV cargado exitosamente.")

        original_rows = len(df)

        # Convertir 'Distancia_Santiago_km' y 'Tiempo_Santiago_min' a numérico,
        # forzando los valores no numéricos (como 'ERROR') a NaN.
        df['Distancia_Santiago_km'] = pd.to_numeric(df['Distancia_Santiago_km'], errors='coerce')
        df['Tiempo_Santiago_min'] = pd.to_numeric(df['Tiempo_Santiago_min'], errors='coerce')

        # Eliminar filas donde 'Distancia_Santiago_km' o 'Tiempo_Santiago_min' son NaN
        df.dropna(subset=['Distancia_Santiago_km', 'Tiempo_Santiago_min'], inplace=True)

        rows_after_cleaning = len(df)
        if original_rows > rows_after_cleaning:
            st.warning(f"Se han omitido {original_rows - rows_after_cleaning} filas debido a valores erróneos (como 'ERROR') en las columnas 'Distancia_Santiago_km' o 'Tiempo_Santiago_min'.")

    except Exception as e:
        st.error(f"Error al leer el archivo CSV: {e}. Asegúrate de que el formato sea correcto (ej. separador ';').")
        st.stop()
else:
    # Datos de ejemplo si no se carga ningún archivo
    st.info("No se ha cargado ningún archivo CSV. Se muestran datos de ejemplo.")
    data = {
        'Código': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'Nome': ['Centro A', 'Centro B', 'Centro C', 'Centro D', 'Centro E', 'Centro F', 'Centro G', 'Centro H', 'Centro I', 'Centro J'],
        'Enderezo': ['Calle Falsa 1', 'Avenida Real 2', 'Plaza Mayor 3', 'Rua do Sol 4', 'Calle Luna 5', 'Rua Estrela 6', 'Via Láctea 7', 'Paseo Marítimo 8', 'Ronda Exterior 9', 'Camiño Novo 10'],
        'Concello': ['Santiago', 'Santiago', 'A Coruña', 'Vigo', 'Santiago', 'Pontevedra', 'Lugo', 'Ourense', 'Ferrol', 'Vigo'],
        'Provincia': ['A Coruña', 'A Coruña', 'A Coruña', 'Pontevedra', 'A Coruña', 'Pontevedra', 'Lugo', 'Ourense', 'A Coruña', 'Pontevedra'],
        'Cód. postal': ['15701', '15702', '15001', '36201', '15703', '36001', '27001', '32001', '15401', '36202'],
        'Teléfono': ['981111111', '981222222', '981333333', '986444444', '981555555', '986666666', '982777777', '988888888', '981999999', '986000000'],
        'Tipo de centro': ['Colegio', 'Instituto', 'Colegio', 'Guardería', 'Colegio', 'Instituto', 'Colegio', 'Instituto', 'Guardería', 'Colegio'],
        'COORDENADA_X': [42.8782, 42.8790, 43.3623, 42.2328, 42.8750, 42.4336, 43.0128, 42.3364, 43.4839, 42.2400], # Latitud
        'COORDENADA_Y': [-8.5448, -8.5500, -8.4115, -8.7226, -8.5400, -8.6477, -7.5566, -7.8640, -8.2320, -8.7200], # Longitud
        'TITULARIDADE': ['Pública', 'Privada', 'Pública', 'Privada', 'Pública', 'Privada', 'Pública', 'Privada', 'Pública', 'Privada'],
        'ENSINO_CONCERTADO': ['No', 'Sí', 'No', 'No', 'Sí', 'Sí', 'No', 'Sí', 'No', 'Sí'],
        'DEPENDENTE': ['Sí', 'No', 'Sí', 'No', 'Sí', 'No', 'Sí', 'No', 'Sí', 'No'],
        'Distancia_Santiago_km': [0.5, 1.2, 60.0, 'ERROR', 0.8, 70.0, 100.0, 120.0, 75.0, 88.0], # Incluido 'ERROR' para prueba
        'Tiempo_Santiago_min': [2, 5, 45, 70, 3, 'ERROR', 80, 95, 60, 68] # Incluido 'ERROR' para prueba
    }
    df = pd.DataFrame(data)

    original_rows = len(df)
    df['Distancia_Santiago_km'] = pd.to_numeric(df['Distancia_Santiago_km'], errors='coerce')
    df['Tiempo_Santiago_min'] = pd.to_numeric(df['Tiempo_Santiago_min'], errors='coerce')
    df.dropna(subset=['Distancia_Santiago_km', 'Tiempo_Santiago_min'], inplace=True)
    rows_after_cleaning = len(df)
    if original_rows > rows_after_cleaning:
        st.warning(f"Se han omitido {original_rows - rows_after_cleaning} filas de los datos de ejemplo debido a valores erróneos (como 'ERROR') en las columnas de distancia o tiempo.")


# Renombrar columnas para que st.map las entienda
# st.map espera 'latitude' y 'longitude'
df = df.rename(columns={'COORDENADA_X': 'latitude', 'COORDENADA_Y': 'longitude'})

# --- Sidebar para los filtros ---
st.sidebar.header("Filtros")

# Slider para la distancia
max_distancia = float(df['Distancia_Santiago_km'].max()) if not df.empty else 100.0
min_distancia_slider = st.sidebar.slider(
    "Distancia máxima a Santiago (km)",
    min_value=0.0,
    max_value=max_distancia,
    value=max_distancia,
    step=0.1
)

# Slider para el tiempo
max_tiempo = float(df['Tiempo_Santiago_min'].max()) if not df.empty else 100.0
min_tiempo_slider = st.sidebar.slider(
    "Tiempo máximo a Santiago (min)",
    min_value=0.0,
    max_value=max_tiempo,
    value=max_tiempo,
    step=1.0
)

# --- Aplicar filtros ---
if not df.empty:
    df_filtrado = df[
        (df['Distancia_Santiago_km'] <= min_distancia_slider) &
        (df['Tiempo_Santiago_min'] <= min_tiempo_slider)
    ]
else:
    df_filtrado = pd.DataFrame() # DataFrame vacío si no hay datos

st.subheader(f"Centros encontrados: {len(df_filtrado)}")

# --- Mostrar el mapa ---
if not df_filtrado.empty:
    st.map(df_filtrado)
else:
    st.warning("No hay centros que cumplan los criterios de filtro seleccionados.")
    # Si no hay centros, muestra un mapa centrado en Santiago o un mensaje
    st.map(pd.DataFrame({'latitude': [42.8782], 'longitude': [-8.5448]})) # Centro de Santiago

# --- Mostrar la tabla con los centros filtrados ---
st.subheader("Detalles de los Centros Filtrados")
if not df_filtrado.empty:
    # Mostrar solo las columnas relevantes para la tabla
    columnas_tabla = [
        'Código', 'Nome', 'Enderezo', 'Concello', 'Provincia',
        'Distancia_Santiago_km', 'Tiempo_Santiago_min', 'Tipo de centro',
        'TITULARIDADE', 'ENSINO_CONCERTADO', 'DEPENDENTE'
    ]
    st.dataframe(df_filtrado[columnas_tabla], use_container_width=True)
else:
    st.info("La tabla se actualizará cuando haya centros que cumplan los filtros.")

st.markdown("---")
st.markdown("Desarrollado por solucións informáticas Tella e Streamlit.")
