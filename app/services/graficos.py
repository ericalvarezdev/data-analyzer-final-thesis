
from typing import Any
import numpy as np
import pandas as pd
from app.services.procesamiento import leer_archivo, convertir_a_fecha, es_columna_fecha

TIPOS_VALIDOS = {"barras", "lineas", "tarta", "caja", "histograma"}
OPERACIONES_VALIDAS = {"recuento", "suma", "media", "mediana", "minimo", "maximo",
                        "desviacion_estandar", "varianza", "recuento_distintos"}

# filtros que trabajan con fechas, solo se pueden usar en columnas de tipo fecha
TIPOS_FILTRO_FECHA = {"fecha_antes_de", "fecha_despues_de", "fecha_entre"}

TIPOS_FILTRO_VALIDOS = {"rango", "valor_exacto", "lista_valores", "diferente_de",
                         "contiene_texto", "mayor_que", "menor_que"} | TIPOS_FILTRO_FECHA

# para combinar varios filtros entre si. Por ahora sin NOT ni agrupaciones con
# paréntesis, de momento solo se van encadenando uno detrás de otro en el orden
# en el que llegan (de izquierda a derecha)
CONECTORES_VALIDOS = {"AND", "OR"}

# límite de categorías para que el gráfico no salga ilegible (categoria es un valor de una columna)
MAX_CATEGORIAS = 20

# operaciones que no tienen sentido como "parte de un total" (tarta) porque no sé suman,
# son más bien sobre cómo se reparten los valores de una columna (caja/histograma)
OPERACIONES_ESTADISTICAS = {"media", "mediana", "minimo", "maximo", "desviacion_estandar", "varianza"}

# la tarta solo tiene sentido si cada porción es una parte de un total (contar o sumar)
OPERACIONES_PERMITEN_TARTA = {"recuento", "suma"}

# caja/histograma muestran cómo se distribuyen los valores, por lo que solo tienen
# sentido con operaciones relacionadas con esa distribución
OPERACIONES_PERMITEN_DISTRIBUCION = {"media", "mediana", "desviacion_estandar", "varianza"}


# _calcular_mascara() calcula el true/false de un filtro, fila a fila (por ejemplo Ciudad == "Barcelona"),
# aplicar_filtros() junta las máscaras de todos los filtros en Y/O y recorta el dataframe de golpe,
# construir_especificacion() calcula sus ventas por producto, generar_especificacion_grafico()
# lee el excel y coordina todo


# calcula la máscara de los filtros de fecha. Comparo por días (sin la hora), así "antes
# del 1 de marzo" o "entre el 1 y el 31 de marzo" no dependen de a qué hora fue cada venta.
# Antes con horas fallaba: "entre el 1 y el 31 de marzo" se dejaba fuera el día 31 a partir
# de las 00:00. Las fechas de los filtros llegan del frontend en formato aaaa-mm-dd
def _mascara_fecha(serie: pd.Series, tipo: str, valores: list) -> pd.Series:
    # la columna puede venir como texto (csv) o ya como fecha (excel), convertir_a_fecha
    # sirve para los dos casos. Lo que no se puede leer como fecha queda vacío y no cumple
    # ningún filtro
    fechas = convertir_a_fecha(serie)
    dias = fechas.dt.normalize() # normalize() deja la fecha a las 00:00, es decir, quita la hora

    if tipo == "fecha_antes_de":
        return dias < pd.Timestamp(valores[0])

    elif tipo == "fecha_despues_de":
        return dias > pd.Timestamp(valores[0])

    elif tipo == "fecha_entre":
        # las dos fechas incluidas
        return (dias >= pd.Timestamp(valores[0])) & (dias <= pd.Timestamp(valores[1]))

    raise ValueError(f"Tipo de filtro de fecha no soportado: {tipo}")


# calcula la máscara (True/False por fila) de un solo filtro, sin tocar el dataframe
# la separo de aplicar_filtros para poder combinar varias máscaras con AND/OR antes
# de recortar el dataframe de una vez
def _calcular_mascara(serie: pd.Series, tipo: str, valores: list) -> pd.Series:

    if tipo in TIPOS_FILTRO_FECHA:
        return _mascara_fecha(serie, tipo, valores)

    if tipo == "valor_exacto":
        return serie == valores[0]  # si es un valor exacto valores solo tendrá una posición 0

    elif tipo == "diferente_de":
        return serie != valores[0]

    elif tipo == "lista_valores":
        return serie.isin(valores)

    elif tipo == "rango":
        # el rango són dos valores (mínimo y máximo), por lo tanto tiene que ser
        # mayor que la posición 0 y menor que la posición 1
        return (serie >= valores[0]) & (serie <= valores[1])

    elif tipo == "mayor_que":
        return serie > valores[0]

    elif tipo == "menor_que":
        return serie < valores[0]

    elif tipo == "contiene_texto":
        # na=False para que las filas vacías no cuenten como que "contienen" el texto
        return serie.astype(str).str.contains(str(valores[0]), na=False)

    raise ValueError(f"Tipo de filtro no soportado: {tipo}")


# recibe la tabla completa y la va filtrando
# cada filtro trae la posición de la columna, tipo de filtro, valores y el
# conector (AND/OR) con el que se une al resultado de los filtros anteriores
# el filtro puede ser por muchas columnas por ejemplo, solo quiero que se vean el numero las ventas del producto A en todas las ciudades
def aplicar_filtros(df: pd.DataFrame, filtros: list[dict]) -> pd.DataFrame:

    if not filtros:
        return df

    # antes iba recortando el dataframe filtro a filtro, pero así solo podía
    # encadenar en Y (cada filtro recortaba sobre lo que dejaba el anterior).
    # para poder hacer O necesito la máscara de cada filtro calculada sobre la
    # misma tabla y combinarlas luego, así que ahora guardo una máscara por
    # filtro y al final las uno con & (AND) o | (OR) según toque
    mascara_acumulada = None

    for filtro in filtros:
        # Es el índice de la columna dentro del dataframe
        serie = df.iloc[:, filtro["posicion"]]
        tipo = filtro["tipo_filtro"]
        valores = filtro["valores"]
        conector = filtro.get("conector", "AND")

        mascara = _calcular_mascara(serie, tipo, valores)

        if mascara_acumulada is None:
            # el primer filtro no tiene nada con lo que combinarse, así que su
            # conector (si trae uno) no se usa para nada
            mascara_acumulada = mascara
        elif conector == "OR":
            mascara_acumulada = mascara_acumulada | mascara
        else:
            mascara_acumulada = mascara_acumulada & mascara

    return df[mascara_acumulada]


# calcula el valor agregado (suma, media, etc.) de cada categoría de la columna x.
# lo usan barras y líneas, que necesitan un número por categoría, no los valores en bruto.
# todas_las_categorias=True no se queda solo con las MAX_CATEGORIAS más grandes, lo uso
# cuando el eje x son fechas
def _agregar(df: pd.DataFrame, posicion_x: int, posicion_y: int | None,
             operacion: str, todas_las_categorias: bool = False) -> tuple[list[str], list[float]]:

    serie_x = df.iloc[:, posicion_x]

    # si el eje x son fechas agrupo por día (quitando la hora). Si no, en un archivo de
    # ventas donde cada venta tiene su hora, cada venta salía como un punto distinto
    if es_columna_fecha(serie_x):
        serie_x = convertir_a_fecha(serie_x).dt.normalize()

    # contar no necesita eje y, solo cuantas veces aparece cada valor de la columna x
    if operacion == "recuento":
        agrupado = serie_x.value_counts()

    else:
        serie_y = df.iloc[:, posicion_y]
        grupo = pd.DataFrame({"x": serie_x, "y": serie_y}).groupby("x")["y"]

        metodo = {
            "suma": grupo.sum,
            "media": grupo.mean,
            "mediana": grupo.median,
            "minimo": grupo.min,
            "maximo": grupo.max,
            "desviacion_estandar": grupo.std,
            "varianza": grupo.var,
            "recuento_distintos": grupo.nunique,
        }[operacion]

        # fillna(0) porque con poca cantidad de datos por categoría la desviación
        # estándar/varianza puede salir vacía (NaN) en vez de 0
        agrupado = metodo().fillna(0)

    # en barras y tarta me quedo con las categorías más grandes para que se pueda leer.
    # Con fechas en el eje x no: ahí lo que importa es ver la evolución entera, y quedarme
    # con los 20 días más altos dejaba un gráfico con huecos que parecía otra cosa
    if not todas_las_categorias:
        agrupado = agrupado.sort_values(ascending=False).head(MAX_CATEGORIAS)

    return agrupado.index.astype(str).tolist(), [float(v) for v in agrupado.values]


# _agregar() deja las categorías ordenadas de mayor a menor valor, y eso tiene sentido para
# barras/tarta (quiero ver primero la categoría más grande). Pero para una línea NO: ahí el
# eje x tiene que seguir su propio orden (normalmente fechas) para que se vea una evolución
# real y no un zigzag sin sentido. Por eso construir_especificacion llama a esto justo
# después de _agregar() para "lineas", y también para "barras" cuando el eje x son fechas
#
# primero pruebo si son números y no fecha: un número como "2026" se podría leer como las
# dos cosas (es un año válido), pero probando primero como número me ahorro el caso raro de
# que pandas interprete un número normal (p.ej. un Mes del 1 al 12) como si fuera una fecha.
# una fecha de verdad (con guiones o barras) nunca se deja convertir a número, así que esto
# no quita ningún caso real de fecha
#
# si no son números pruebo si son fecha con convertir_a_fecha (la misma que usa inferir_tipo
# en procesamiento.py, así las fechas se leen igual en todas partes). Si tampoco, se quedan
# como texto, que para categorías sigue siendo mejor que el orden por valor
def _ordenar_por_x(etiquetas: list[str], valores: list[float]) -> tuple[list[str], list[float]]:
    # sin categorías no hay nada que ordenar (y abajo dividiría entre 0)
    if not etiquetas:
        return etiquetas, valores

    serie_etiquetas = pd.Series(etiquetas)

    como_numero = pd.to_numeric(serie_etiquetas, errors="coerce")
    como_fecha = convertir_a_fecha(serie_etiquetas)

    if como_numero.notna().sum() / len(etiquetas) >= 0.9:
        clave_orden = como_numero
    elif como_fecha.notna().sum() / len(etiquetas) >= 0.9:
        clave_orden = como_fecha
    else:
        clave_orden = serie_etiquetas

    orden = clave_orden.sort_values().index
    return [etiquetas[i] for i in orden], [valores[i] for i in orden]


# para caja/histograma no agrego nada: necesito los valores en bruto de cada categoría
# para que sea Plotly quien calcule los cuartiles (caja) o reparta los valores en barras (histograma)
def _valores_crudos_por_categoria(df: pd.DataFrame, posicion_x: int,
                                   posicion_y: int) -> tuple[list[str], list[list[float]]]:

    serie_x = df.iloc[:, posicion_x]
    serie_y = df.iloc[:, posicion_y]

    etiquetas = []
    listas_valores = []

    # me quedo con las categorías que más filas tienen, igual que en _agregar
    categorias = serie_x.value_counts().head(MAX_CATEGORIAS).index

    for categoria in categorias:
        valores_categoria = serie_y[serie_x == categoria].dropna()
        etiquetas.append(str(categoria))
        listas_valores.append([float(v) for v in valores_categoria])

    return etiquetas, listas_valores


# construye la especificación de Plotly (data + layout) según el tipo de gráfico.
# esta es la parte importante: tanto la web (Plotly.js) como el PDF (Plotly Python + Kaleido)
# dibujan exactamente esta especificación, así que el gráfico sale siempre igual en los dos sitios
def construir_especificacion(df: pd.DataFrame, posicion_x: int, posicion_y: int | None,
                              operacion: str, tipo_grafico: str,
                              nombre_columna_x: str, nombre_columna_y: str | None) -> dict[str, Any]:

    if tipo_grafico == "tarta":
        etiquetas, valores = _agregar(df, posicion_x, posicion_y, operacion)
        return {
            "data": [{"type": "pie", "labels": etiquetas, "values": valores}],
            "layout": {},
        }

    # si el eje x son fechas, en líneas y barras enseño todos los días y en orden de fecha
    eje_x_es_fecha = es_columna_fecha(df.iloc[:, posicion_x])

    if tipo_grafico == "lineas":
        etiquetas, valores = _agregar(df, posicion_x, posicion_y, operacion,
                                      todas_las_categorias=eje_x_es_fecha)
        etiquetas, valores = _ordenar_por_x(etiquetas, valores)
        return {
            "data": [{"type": "scatter", "mode": "lines+markers", "x": etiquetas, "y": valores}],
            "layout": {
                "xaxis": {"title": {"text": nombre_columna_x}},
                "yaxis": {"title": {"text": nombre_columna_y or operacion}},
            },
        }

    if tipo_grafico == "caja":
        etiquetas, listas = _valores_crudos_por_categoria(df, posicion_x, posicion_y)
        trazos = [{"type": "box", "y": listas[i], "name": etiquetas[i]} for i in range(len(etiquetas))]
        return {
            "data": trazos,
            "layout": {
                "xaxis": {"title": {"text": nombre_columna_x}},
                "yaxis": {"title": {"text": nombre_columna_y}},
            },
        }

    if tipo_grafico == "histograma":
        etiquetas, listas = _valores_crudos_por_categoria(df, posicion_x, posicion_y)
        trazos = [
            {"type": "histogram", "x": listas[i], "name": etiquetas[i], "opacity": 0.6}
            for i in range(len(etiquetas))
        ]

        # añado una línea vertical marcando la media de cada categoría, porque un
        # histograma normal no la muestra y así se ve dónde está centrada cada una
        lineas = []
        for i in range(len(etiquetas)):
            if not listas[i]:
                continue
            media_categoria = float(np.mean(listas[i]))
            lineas.append({
                "type": "line", "xref": "x", "yref": "paper",
                "x0": media_categoria, "x1": media_categoria, "y0": 0, "y1": 1,
                "line": {"dash": "dash"},
            })

        return {
            "data": trazos,
            "layout": {
                "barmode": "overlay",
                "shapes": lineas,
                # en el histograma el eje X muestra los VALORES en bruto, no categorías,
                # por eso el título es el de la columna Y (de donde salen esos valores)
                "xaxis": {"title": {"text": nombre_columna_y}},
                "yaxis": {"title": {"text": "Frecuencia"}},
            },
        }

    # barras (por defecto)
    etiquetas, valores = _agregar(df, posicion_x, posicion_y, operacion,
                                  todas_las_categorias=eje_x_es_fecha)
    if eje_x_es_fecha:
        etiquetas, valores = _ordenar_por_x(etiquetas, valores)
    return {
        "data": [{"type": "bar", "x": etiquetas, "y": valores}],
        "layout": {
            "xaxis": {"title": {"text": nombre_columna_x}},
            "yaxis": {"title": {"text": nombre_columna_y or operacion}},
        },
    }


# primero aplico filtros y luego construyo la especificación del gráfico con el df ya filtrado
def generar_especificacion_grafico(ruta_archivo: str, formato: str, posicion_x: int,
                                    posicion_y: int | None, operacion: str,
                                    filtros: list[dict], tipo_grafico: str,
                                    nombre_columna_x: str,
                                    nombre_columna_y: str | None) -> dict[str, Any]:

    df = leer_archivo(ruta_archivo, formato)
    df = aplicar_filtros(df, filtros)

    if df.empty:
        raise ValueError("Los filtros aplicados no dejan ninguna fila")

    return construir_especificacion(df, posicion_x, posicion_y, operacion, tipo_grafico,
                                     nombre_columna_x, nombre_columna_y)