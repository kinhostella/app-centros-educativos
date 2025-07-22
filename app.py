import streamlit as st
import pandas as pd
import io
import folium # Importamos folium para crear mapas más personalizados
from streamlit_folium import st_folium # Importamos para mostrar mapas de folium en Streamlit

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
    Al pasar el ratón sobre cada centro en el mapa, verás su nombre, distancia y tiempo.
    """
)

# --- Carga de datos ---
uploaded_file = st.file_uploader("Sube tu archivo CSV de centros", type="csv")

df = pd.DataFrame() # Inicializamos df como un DataFrame vacío

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=',') # Asume que el separador es ','
        st.success("Archivo CSV cargado exitosamente.")

        original_rows = len(df)

        # Convertir 'Distancia_Santiago_km' y 'Tiempo_Santiago_min' a numérico,
        # forzando los valores no numéricos (como 'ERROR') a NaN.
        df['Distancia_Santiago_km'] = pd.to_numeric(df['Distancia_Santiago_km'], errors='coerce')
        df['Tiempo_Santiago_min'] = pd.to_numeric(df['Tiempo_Santiago_min'], errors='coerce')

        # --- FIX: Convert COORDENADA_X and COORDENADA_Y to numeric ---
        # Convertir 'COORDENADA_X' y 'COORDENADA_Y' a numérico,
        # forzando los valores no numéricos a NaN.
        df['COORDENADA_X'] = pd.to_numeric(df['COORDENADA_X'], errors='coerce')
        df['COORDENADA_Y'] = pd.to_numeric(df['COORDENADA_Y'], errors='coerce')
        # --- END FIX ---

        # --- NEW FIX: Correct swapped COORDENADA_X and COORDENADA_Y ---
        # Identificar filas donde COORDENADA_X parece ser una longitud (>90 o <-90)
        # y COORDENADA_Y parece ser una latitud (entre -90 y 90).
        # Esto indica que las coordenadas podrían estar intercambiadas.
        swapped_mask = (df['COORDENADA_X'] < 0) & (df['COORDENADA_Y'] > 0)

        # Aplicar el intercambio para las filas identificadas
        # Se usa una variable temporal para el intercambio seguro de columnas
        temp_x = df.loc[swapped_mask, 'COORDENADA_X'].copy()
        df.loc[swapped_mask, 'COORDENADA_X'] = df.loc[swapped_mask, 'COORDENADA_Y']
        df.loc[swapped_mask, 'COORDENADA_Y'] = temp_x

        if swapped_mask.any():
            st.info(f"Se han corregido {swapped_mask.sum()} pares de coordenadas (COORDENADA_X y COORDENADA_Y) que parecían estar intercambiadas.")
        # --- END NEW FIX ---

        # Eliminar filas donde 'Distancia_Santiago_km', 'Tiempo_Santiago_min',
        # 'COORDENADA_X' o 'COORDENADA_Y' son NaN
        df.dropna(subset=['Distancia_Santiago_km', 'Tiempo_Santiago_min', 'COORDENADA_X', 'COORDENADA_Y'], inplace=True)

        rows_after_cleaning = len(df)
        if original_rows > rows_after_cleaning:
            st.warning(f"Se han omitido {original_rows - rows_after_cleaning} filas debido a valores erróneos (como 'ERROR' o coordenadas inválidas) en las columnas de distancia, tiempo o coordenadas.")

    except Exception as e:
        st.error(f"Error al leer el archivo CSV: {e}. Asegúrate de que el formato sea correcto (ej. separador ',').")
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
        'COORDENADA_X': [42.8782, 42.8790, 43.3623, -8.7226, 42.8750, 42.4336, 43.0128, 42.3364, 43.4839, 42.2400], # Latitud (D4 y E4 intercambiadas para prueba)
        'COORDENADA_Y': [-8.5448, -8.5500, -8.4115, 42.2328, -8.5400, -8.6477, -7.5566, -7.8640, -8.2320, -8.7200], # Longitud
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
    
    # --- FIX: Convert COORDENADA_X and COORDENADA_Y to numeric for example data ---
    df['COORDENADA_X'] = pd.to_numeric(df['COORDENADA_X'], errors='coerce')
    df['COORDENADA_Y'] = pd.to_numeric(df['COORDENADA_Y'], errors='coerce')
    # --- END FIX ---

    # --- NEW FIX: Correct swapped COORDENADA_X and COORDENADA_Y for example data ---
    swapped_mask = (df['COORDENADA_X'].abs() > 90) & (df['COORDENADA_Y'].abs() <= 90)
    temp_x = df.loc[swapped_mask, 'COORDENADA_X'].copy()
    df.loc[swapped_mask, 'COORDENADA_X'] = df.loc[swapped_mask, 'COORDENADA_Y']
    df.loc[swapped_mask, 'COORDENADA_Y'] = temp_x
    if swapped_mask.any():
        st.info(f"Se han corregido {swapped_mask.sum()} pares de coordenadas (COORDENADA_X y COORDENADA_Y) en los datos de ejemplo que parecían estar intercambiadas.")
    # --- END NEW FIX ---

    df.dropna(subset=['Distancia_Santiago_km', 'Tiempo_Santiago_min', 'COORDENADA_X', 'COORDENADA_Y'], inplace=True)
    rows_after_cleaning = len(df)
    if original_rows > rows_after_cleaning:
        st.warning(f"Se han omitido {original_rows - rows_after_cleaning} filas de los datos de ejemplo debido a valores erróneos (como 'ERROR' o coordenadas inválidas) en las columnas de distancia, tiempo o coordenadas.")

# Verificar si df está vacío después de la carga/limpieza
if df.empty:
    st.error("No se han podido cargar datos válidos de centros. Por favor, sube un archivo CSV con el formato correcto y asegúrate de que las columnas de coordenadas son numéricas.")
    st.stop() # Detiene la ejecución de la aplicación si no hay datos válidos

# Renombrar columnas para que Folium las entienda (espera 'latitude' y 'longitude')
df = df.rename(columns={'COORDENADA_X': 'latitude', 'COORDENADA_Y': 'longitude'})

# --- Sidebar para los filtros ---
st.sidebar.header("Filtros")

# Slider para la distancia
# Asegurarse de que max_distancia sea un float y no un valor nulo
max_distancia = float(df['Distancia_Santiago_km'].max()) if not df['Distancia_Santiago_km'].empty else 100.0
min_distancia_slider = st.sidebar.slider(
    "Distancia máxima a Santiago (km)",
    min_value=0.0,
    max_value=max_distancia,
    value=max_distancia,
    step=0.1
)

# Slider para el tiempo
# Asegurarse de que max_tiempo sea un float y no un valor nulo
max_tiempo = float(df['Tiempo_Santiago_min'].max()) if not df['Tiempo_Santiago_min'].empty else 100.0
min_tiempo_slider = st.sidebar.slider(
    "Tiempo máximo a Santiago (min)",
    min_value=0.0,
    max_value=max_tiempo,
    value=max_tiempo,
    step=1.0
)

# --- Aplicar filtros ---
df_filtrado = df[
    (df['Distancia_Santiago_km'] <= min_distancia_slider) &
    (df['Tiempo_Santiago_min'] <= min_tiempo_slider)
]

st.subheader(f"Centros encontrados: {len(df_filtrado)}")

# --- Mostrar el mapa con Folium y Tooltips ---
if not df_filtrado.empty:
    # Centrar el mapa en la media de las coordenadas de los centros filtrados
    # Si no hay centros filtrados, se centrará en Santiago por defecto
    map_center_lat = df_filtrado['latitude'].mean()
    map_center_lon = df_filtrado['longitude'].mean()
    
    # Inicializar el mapa de Folium
    m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=8)

    # Añadir marcadores para cada centro filtrado con tooltip
    for idx, row in df_filtrado.iterrows():
        # Contenido HTML para el tooltip
        tooltip_html = f"""
        <b>{row['Nome']}</b><br>
        Distancia: {row['Distancia_Santiago_km']:.1f} km<br>
        Tiempo: {row['Tiempo_Santiago_min']:.0f} min
        """
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            tooltip=tooltip_html, # Esto es para el hover
            # Opcional: Puedes añadir un popup para el click si lo deseas
            # popup=folium.Popup(tooltip_html, max_width=300)
        ).add_to(m)
    
    # Mostrar el mapa de Folium en Streamlit
    st_folium(m, width=700, height=500) # Ajusta el ancho y alto según necesites
else:
    st.warning("No hay centros que cumplan los criterios de filtro seleccionados para mostrar en el mapa.")
    # Si no hay centros filtrados, muestra un mapa centrado en Santiago
    m = folium.Map(location=[42.8782, -8.5448], zoom_start=8) # Centro de Santiago
    st_folium(m, width=700, height=500)


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
