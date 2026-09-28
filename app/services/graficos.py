
from typing import Any
import pandas as pd
from app.services.procesamiento import leer_archivo

TIPOS_VALIDOS = {"barras", "lineas", "tarta"}
OPERACIONES_VALIDAS = {"recuento", "suma", "media"}
TIPOS_FILTRO_VALIDOS = {"rango", "valor_exacto", "lista_valores"}

# límite de categorías para que el gráfico no salga ilegible (categoria es un valor de una columna)
MAX_CATEGORIAS = 20

# aplicar_filtros() filtra por ejemplo Ciudad = "Barcelona", calcular_datos_grafico()
# calcula sus ventas por producto, generar_datos_grafico() lee el excel y coordina todo


# recibe la tabla completa y va cortandola filtro a filtro
# cada filtro trae la posición de la columna tipo de filtro y valores
# el filtro puede ser por muchas columnas por ejemplo, solo quiero que se vean el numero las ventas del producto A en todas las ciudades
def aplicar_filtros(df: pd.DataFrame, filtros: list[dict]) -> pd.DataFrame:
    
    for filtro in filtros:
        # recalculo la serie a partir del dataframe ya filtrado y no del original
        # para así poder aplicar filtros sobre filtros
        serie = df.iloc[:, filtro["posicion"]] # Es el índice de la columna dentro del dataframe
        tipo = filtro["tipo_filtro"]
        valores = filtro["valores"]
        
        if tipo == "valor_exacto":
            df = df[serie == valores[0]] # si es un valor exacto valores solo tendrá una posición 0
            
        elif tipo == "lista_valores":
            df = df[serie.isin(valores)]
            
        elif tipo == "rango":
            # el rango són dos valores (mínimo y máximo), por lo tanto tiene que ser
            # mayor que la posición 0 y menor que la posición 1
            df = df[(serie >= valores[0]) & (serie <= valores[1])]
            
    return df


# coge dos columnas (o una si es recuento) y calcula los datos del gráfico
def calcular_datos_grafico(df: pd.DataFrame, posicion_x: int,
                           posicion_y: int | None, operacion: str) -> dict:
    
    serie_x = df.iloc[:,posicion_x]
    
    # contar no necesita eje y, solo cuantas veces aparece cada valor de la columna x
    if operacion == "recuento":
        agrupado = serie_x.value_counts().head(MAX_CATEGORIAS)
        
    else:
        serie_y = df.iloc[:,posicion_y]
        
        temporal = pd.DataFrame({"x": serie_x, "y": serie_y})
        
        if operacion == "suma":
            agrupado = temporal.groupby("x")["y"].sum() # cojo los que se llaman igual en x y hago la suma en y
        
        else: # media
            agrupado = temporal.groupby("x")["y"].mean() # cojo los que se llaman igual en x y hago la media en y
        
        # me quedo con las 20 categorías de mayor valor
        agrupado = agrupado.sort_values(ascending=False).head(MAX_CATEGORIAS)
        
    return {
        "etiquetas": agrupado.index.astype(str).tolist(), # coge los nombres (eje x)
        "valores": [float(v) for v in agrupado.values], # coge los valores (eje y)
    }
    

# primero aplico filtros y luego calculo los datos del gráfico con el df ya filtrado
def generar_datos_grafico(ruta_archivo: str, formato: str, posicion_x: int,
                          posicion_y: int | None, operacion: str,
                          filtros: list[dict]) -> dict:
    
    df = leer_archivo(ruta_archivo,formato)
    df = aplicar_filtros(df,filtros)
    
    if df.empty:
        raise ValueError("Los filtros aplicados no dejan ninguna fila")
    
    return calcular_datos_grafico(df,posicion_x, posicion_y, operacion)
