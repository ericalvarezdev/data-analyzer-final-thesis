
import pandas as pd
from app.services.procesamiento import leer_archivo

# Tipos de gráfico que acepto por ahora
TIPOS_VALIDOS = {"barras","lineas","tarta"}

# Lee el archivo de nuevo, y calcula para la columna elegida, cuantas veces
# aparece cada elemento (frecuencia de elementos)
# para la primera iteración de momento solo haré el gráfico de frecuencias
def generar_datos_grafico(ruta_archivo: str, formato: str, nombre_columna: str) -> dict:
    
    df = leer_archivo(ruta_archivo,formato)
    serie = df[nombre_columna] # Aqui si el nombre_columna se repito dos veces o más en el archivo daría error
    
    # value_counts calcula cuantas veces aparece cada valor distinto (frecuencia)
    # y los ordena de más a menos
    # head(10) hace que se muestren solo los 10 valores con más apariciones
    conteo = serie.value_counts().head(10)
    
    return {
        "etiquetas": conteo.index.astype(str).to_list(), # conteo.index = valores eje x
        "valores": conteo.values.tolist() # conteo.values = valores eje y
    }
    
    """
    ejemplo del return
    {
    "etiquetas": ["Barcelona", "Madrid", "Valencia"],
    "valores": [3, 2, 1]
    }
    """
    

    