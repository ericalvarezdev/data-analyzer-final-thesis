import json
import statistics
import time

from google import genai
from google.genai import types

from app.config import settings
from app.models.archivo_subido import ArchivoSubido
from app.models.grafico_generado import GraficoGenerado
from app.models.informe_generado import InformeGenerado
from app.services.graficos import TIPOS_VALIDOS, OPERACIONES_VALIDAS


# le pido a la IA que no se enrolle y que no use markdown, porque el resumen se
# muestra tal cual, en texto plano, en la página del informe
INSTRUCCIONES = (
    "Eres un analista de datos. Te paso los datos de los gráficos de un informe y "
    "tienes que escribir un resumen en español explicando las conclusiones más "
    "importantes: tendencias, qué categoría destaca, comparaciones entre los "
    "gráficos si tiene sentido. Máximo 150 palabras, en texto plano, sin markdown "
    "ni listas, como si fuera un párrafo de un informe de verdad."
)

# máximo de gráficos que le dejo proponer a la IA de una vez, para que el informe
# generado no salga interminable
MAX_GRAFICOS_PROPUESTOS = 6

# Gemini a veces devuelve un 503 porque el modelo está saturado de peticiones (no es
# culpa mía, es su servidor). Suele arreglarse solo al cabo de unos segundos, así
# que antes de rendirme lo reintento unas pocas veces
MAX_INTENTOS_IA = 2
ESPERA_ENTRE_INTENTOS_SEGUNDOS = 5



# cuando va saturado, Google a veces no contesta el 503 al momento sino que deja la
# petición esperando varios minutos (en una prueba tardó casi 5 minutos en dar el error),
# así que le pongo un tiempo máximo: si en 30 segundos no ha respondido, lo trato como
# saturado y paso al siguiente intento. Va en milisegundos porque así lo pide google-genai
TIEMPO_MAXIMO_RESPUESTA_MS = 30_000




# modelos que voy probando en orden. Primero un Flash-Lite, que piensa menos antes de
# responder (para devolver un JSON con unos gráficos no hace falta más) y suele estar
# menos saturado que el Flash más nuevo. Uso versiones fijas y no los alias "-latest"
# porque el alias es el que usa todo el mundo y el que más se satura. Si el Lite falla
# pruebo con un Flash normal, y al final con un Lite más antiguo que casi nadie usa
MODELOS_IA = ("gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-2.5-flash-lite")



# LO QUE HABLA CON GEMINI
# llama a Gemini con el prompt indicado y devuelve el texto de la respuesta.
# si la IA está saturada (503) o tarda más de TIEMPO_MAXIMO_RESPUESTA_MS (504 o timeout)
# espera un poco y lo vuelve a intentar con el mismo modelo; si se queda sin intentos,
# pasa al siguiente modelo de MODELOS_IA antes de rendirse del todo. Si el fallo es de
# otro tipo (clave mal puesta, sin conexión...) no tiene sentido reintentar ni cambiar
# de modelo, así que corta a la primera
def _generar_contenido(prompt: str) -> str:
    cliente = genai.Client(api_key=settings.gemini_api_key,
                           http_options=types.HttpOptions(timeout=TIEMPO_MAXIMO_RESPUESTA_MS))
    ultimo_error = None

    for modelo in MODELOS_IA:
        for intento in range(1, MAX_INTENTOS_IA + 1):
            try:
                respuesta = cliente.models.generate_content(model=modelo, contents=prompt)
                return respuesta.text
            except Exception as e:
                ultimo_error = e
                # si se ha pasado del tiempo máximo (lo corte mi cliente o Google con un 504)
                # cuenta igual que un 503
                tiempo_agotado = "timeout" in type(e).__name__.lower() or "timed out" in str(e).lower()
                saturada = ("503" in str(e) or "UNAVAILABLE" in str(e)
                            or "504" in str(e) or "DEADLINE_EXCEEDED" in str(e)
                            or tiempo_agotado)
                if not saturada:
                    raise ValueError(f"No se ha podido contactar con la IA: {e}")
                if intento < MAX_INTENTOS_IA:
                    time.sleep(ESPERA_ENTRE_INTENTOS_SEGUNDOS)
        # aquí el modelo se ha quedado sin intentos por saturación, así que el bucle
        # de fuera pasa al siguiente modelo de MODELOS_IA (o, si era el último, se acaba)

    raise ValueError(f"No se ha podido contactar con la IA: {ultimo_error}")


# PREPARA QUE DATOS VE LA IA
# paso las columnas del archivo a texto para que la IA sepa con qué datos cuenta.
# no le mando ninguna fila de datos de verdad (no le hace falta para proponer
# gráficos, y así tampoco le llegan datos que puedan ser sensibles)
def _describir_columnas(archivo: ArchivoSubido) -> str:
    lineas = []
    for columna in sorted(archivo.columnas, key=lambda c: c.posicion):
        descripcion = f"- {columna.nombre_columna} (tipo: {columna.tipo_dato}"
        if columna.tipo_dato == "numerico" and columna.media is not None:
            descripcion += f", entre {columna.valor_minimo} y {columna.valor_maximo}, media {columna.media:.2f}"
        descripcion += f", {columna.contador_valores_nulos} valores vacíos)"
        lineas.append(descripcion)
    return "\n".join(lineas)


# PIDE LA PROPUESTA DE GRÁFICOS (FUNCIÓN QUE JUNTA LAS DOS ANTERIORES Y GENERA INFORME CON IA)
# le pido a la IA una lista de gráficos en JSON (tipo, operación, columnas y nombre)
# a partir de las columnas del archivo. Esta función solo habla con la IA y devuelve
# la lista ya convertida a diccionarios, no crea nada en la base de datos: eso lo hace
# el router, llamando a crear_grafico() de grafico.py, que es la misma función que usa
# el flujo manual
def proponer_graficos(archivo: ArchivoSubido) -> list[dict]:

    if not settings.gemini_api_key:
        raise ValueError("Falta configurar la clave de la API de Gemini (GEMINI_API_KEY en el .env)")

    if not archivo.columnas:
        raise ValueError("El archivo no tiene columnas analizadas todavía")

    prompt = (
        "Eres un analista de datos. Te doy las columnas de un archivo y tienes que "
        f"proponer entre 3 y {MAX_GRAFICOS_PROPUESTOS} gráficos interesantes para un informe.\n\n"
        "Responde ÚNICAMENTE con una lista JSON (sin texto ni markdown alrededor), donde "
        "cada elemento tiene exactamente estas claves:\n"
        f'- "tipo_grafico": uno de estos valores: {sorted(TIPOS_VALIDOS)}\n'
        f'- "operacion_agregacion": uno de estos valores: {sorted(OPERACIONES_VALIDAS)}\n'
        '- "columna_x": el nombre EXACTO de una de las columnas de abajo\n'
        '- "columna_y": el nombre EXACTO de otra columna, o null si usas "recuento"\n'
        '- "nombre": un título corto en español para el gráfico\n\n'
        'Reglas: usa "recuento" cuando columna_y sea null. Para el resto de operaciones '
        'columna_y tiene que ser una columna numérica (salvo "recuento_distintos", que vale '
        'con cualquier tipo). "tarta" solo se puede usar con "recuento" o "suma". "caja" e '
        '"histograma" solo se pueden usar con "media", "mediana", "desviacion_estandar" o "varianza".\n\n'
        "Columnas disponibles:\n"
        f"{_describir_columnas(archivo)}"
    )

    texto = _generar_contenido(prompt)

    # a veces la IA envuelve el JSON en ```json ... ``` aunque le pida que no lo haga,
    # así que lo quito antes de intentar convertirlo
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.strip("`")
        if texto.lower().startswith("json"):
            texto = texto[4:]
        texto = texto.strip()

    try:
        propuestas = json.loads(texto)
    except json.JSONDecodeError:
        raise ValueError("La IA no ha devuelto una lista de gráficos válida, prueba otra vez")

    if not isinstance(propuestas, list) or not propuestas:
        raise ValueError("La IA no ha propuesto ningún gráfico")

    return propuestas[:MAX_GRAFICOS_PROPUESTOS]








# PASA UN GRÁFICO A TEXTO
# paso un gráfico a texto para meterlo en el prompt. Cada tipo de gráfico guarda sus
# datos de una forma distinta dentro de especificacion["data"] (son los trazos de
# Plotly), así que miro el "type" de cada trazo para saber cómo leerlo
def _describir_grafico(grafico: GraficoGenerado) -> str:
    nombre = grafico.nombre or f"Gráfico #{grafico.id}"
    lineas = [f"{nombre} (tipo {grafico.tipo_grafico}, operación {grafico.operacion_agregacion}):"]

    for trazo in grafico.especificacion["data"]:
        tipo_trazo = trazo.get("type")

        if tipo_trazo == "pie":
            # la tarta no tiene x/y, tiene labels/values
            for etiqueta, valor in zip(trazo["labels"], trazo["values"]):
                lineas.append(f"  {etiqueta}: {valor}")

        elif tipo_trazo in ("bar", "scatter"):
            for etiqueta, valor in zip(trazo["x"], trazo["y"]):
                lineas.append(f"  {etiqueta}: {valor}")

        elif tipo_trazo in ("box", "histogram"):
            # aquí dentro no hay valores agregados, son TODOS los valores en bruto de
            # la categoría (pueden ser cientos), así que en vez de mandarlos todos a
            # la IA le mando solo un resumen de esa categoría (cuántos hay, media,
            # mínimo y máximo)
            valores = trazo["y"] if tipo_trazo == "box" else trazo["x"]
            if valores:
                lineas.append(f"  {trazo['name']}: {len(valores)} valores, "
                              f"media {statistics.mean(valores):.2f}, "
                              f"entre {min(valores):.2f} y {max(valores):.2f}")

    return "\n".join(lineas)


# PIDE EL RESUMEN EN LENGUAJE NATURAL A LA IA
# junta los datos de todos los gráficos del informe y se los manda a Gemini para que
# devuelva el resumen en lenguaje natural. Esta función solo habla con la IA, no
# guarda nada en la base de datos, eso ya lo hace el router con el repositorio
def generar_resumen_informe(informe: InformeGenerado) -> str:

    if not settings.gemini_api_key:
        raise ValueError("Falta configurar la clave de la API de Gemini (GEMINI_API_KEY en el .env)")

    if not informe.graficos:
        raise ValueError("El informe no tiene gráficos todavía, no hay nada que resumir")

    datos_graficos = "\n\n".join(_describir_grafico(g) for g in informe.graficos)
    prompt = f"{INSTRUCCIONES}\n\n{datos_graficos}"

    return _generar_contenido(prompt)



