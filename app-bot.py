import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import json
import os

# Título de la aplicación
st.set_page_config(
    page_title="Visualizador de Centros Educativos",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🗺️ Centros Educativos en Galicia")

# --- Resumen al principio de la app ---
st.markdown(
    """
    Bienvenido/a al visualizador de centros educativos en Galicia. Aquí podrás
    ver centros en un mapa y en una tabla. **Usa el chat en la barra lateral para
    filtrar los centros por distancia o tiempo de viaje a Santiago de Compostela.**

    Ejemplos de preguntas:
    * "Muestra los centros a 50 km de Santiago."
    * "Quiero ver los centros a 45 minutos de Santiago."
    """
)

# Configuración de la API de Gemini
# --- Configuración de la API de Gemini ---
API_KEY = 'AIzaSyCPGUZKN8l1BJGkOE8gTkuXvylxjNj12Fo' # Reemplaza con tu clave
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- Carga de datos ---
uploaded_file = st.file_uploader("Sube tu archivo CSV de centros", type="csv")
df = pd.DataFrame()

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

# --- Sidebar para el chat ---
st.sidebar.header("Chatbot de Filtros")


# Inicializar el historial de chat y el dataframe filtrado en session_state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df_filtrado" not in st.session_state:
    st.session_state.df_filtrado = df.copy()


# Muestra mensajes del historial
for message in st.session_state.messages:
    with st.sidebar.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Lógica de filtrado con Gemini ---
def get_filters_from_gemini(query):
    """
    Utiliza Gemini para extraer los valores de filtro de la consulta del usuario.
    """
    # El prompt para la API de Gemini
    prompt_with_schema = f"""
    Eres un asistente experto en analizar peticiones sobre filtros de datos. Tu tarea es extraer de la siguiente consulta el valor numérico y la unidad de medida (kilómetros o minutos) para filtrar un conjunto de datos.
    Tu respuesta DEBE ser ÚNICAMENTE un objeto JSON que contenga las claves "valor" (un número entero) y "unidad" (un string que puede ser "km" o "minutos").
    Si la consulta no contiene información de distancia o tiempo, devuelve un JSON vacío: {{}}.
    NO DEBES incluir ningún otro texto, ni explicaciones, ni etiquetas de código, solo el objeto JSON.

    Ejemplo de salida para: "Quiero ver los centros a 50 km de Santiago." -> {{"valor": 50, "unidad": "km"}}
    Ejemplo de salida para: "Quiero ver los centros a 100 kilometros." -> {{"valor": 100, "unidad": "km"}}
    Ejemplo de salida para: "Muestra los centros a 40 minutos." -> {{"valor": 40, "unidad": "minutos"}}
    Ejemplo de salida para: "Centros a 20 minutos de Santiago." -> {{"valor": 20, "unidad": "minutos"}}
    Ejemplo de salida para: "Dime centros a 20 kilometros de Santiago." -> {{"valor": 20, "unidad": "km"}}
    Ejemplo de salida para: "Simplemente quiero ver los centros." -> {{}}
    Ejemplo de salida para: "Filtra por 100." -> {{}}

    Consulta: "{query}"
    """
    
    try:
        response = model.generate_content(prompt_with_schema)
        # Asegurarse de que la respuesta no está vacía y es un JSON válido
        if response and response.text:
            filters = json.loads(response.text.strip())
            return filters
    except Exception as e:
        print(f"Error al llamar a la API de Gemini o parsear JSON: {e}")
        return {}
    return {}

# Inicializar un DataFrame filtrado por defecto
df_filtrado = df.copy()

# Aceptar la entrada del usuario en el chat
if prompt := st.sidebar.chat_input("Escribe tu filtro (ej. 'a 50 km')"):
    # Borra el historial antes de agregar la nueva consulta
    st.session_state.messages.clear()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.sidebar.chat_message("user"):
        st.markdown(prompt)

   
    filters = get_filters_from_gemini(prompt)

    with st.sidebar.chat_message("assistant"):
        if filters and "valor" in filters and "unidad" in filters:
            valor = filters['valor']
            unidad = filters['unidad']

            if unidad == "km":
                st.markdown(f"**Aplicando filtro:** Mostrando centros a un máximo de **{valor} km** de Santiago.")
                st.session_state.df_filtrado = df[df['Distancia_Santiago_km'] <= valor]
            elif unidad == "minutos":
                st.markdown(f"**Aplicando filtro:** Mostrando centros a un máximo de **{valor} minutos** de Santiago.")
                st.session_state.df_filtrado = df[df['Tiempo_Santiago_min'] <= valor]
            else:
                st.markdown("No he podido entender tu petición. Por favor, especifica la distancia en 'km' o el tiempo en 'minutos'.")
        else:
            st.markdown("No he encontrado filtros válidos en tu mensaje. Por favor, intenta una pregunta como 'Quiero los centros a 50 km'.")
else:
    # Si no hay prompt activo, usar el dataframe del estado de sesión
    pass

# Muestra el número de centros encontrados
st.subheader(f"Centros encontrados: {len(st.session_state.df_filtrado)}")

# --- Mostrar el mapa con Folium y Tooltips ---
if not st.session_state.df_filtrado.empty:
    map_center_lat = st.session_state.df_filtrado['latitude'].mean()
    map_center_lon = st.session_state.df_filtrado['longitude'].mean()
    m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=8)
    for idx, row in st.session_state.df_filtrado.iterrows():
        tooltip_html = f"""
        <b>{row['Nome']}</b><br>
        Distancia: {row['Distancia_Santiago_km']:.1f} km<br>
        Tiempo: {row['Tiempo_Santiago_min']:.0f} min
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            tooltip=tooltip_html,
        ).add_to(m)
    st_folium(m, width=700, height=500)
else:
    st.warning("No hay centros que cumplan los criterios de filtro para mostrar en el mapa.")
    m = folium.Map(location=[42.8782, -8.5448], zoom_start=8)
    st_folium(m, width=700, height=500)

# --- Mostrar la tabla con los centros filtrados ---
st.subheader("Detalles de los Centros Filtrados")
if not st.session_state.df_filtrado.empty:
    columnas_tabla = [
        'Código', 'Nome', 'Enderezo', 'Concello', 'Provincia',
        'Distancia_Santiago_km', 'Tiempo_Santiago_min', 'Tipo de centro',
        'TITULARIDADE', 'ENSINO_CONCERTADO', 'DEPENDENTE'
    ]
    st.dataframe(st.session_state.df_filtrado[columnas_tabla], use_container_width=True)
else:
    st.info("La tabla se actualizará cuando haya centros que cumplan los filtros.")

st.markdown("---")
st.markdown("Desarrollado con Streamlit y la API de Gemini.")
