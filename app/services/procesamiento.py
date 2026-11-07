import warnings
import pandas as pd
from sqlalchemy.orm import Session
from app.models.columna import Columna
from app.repositories.columna_repository import ColumnaRepository



# un texto solo lo doy por fecha si empieza como una: año-mes-día (2025-03-01) o
# día/mes/año (01/03/2025, 01-03-25, 01.03.2025...). Sin esto pandas se "inventa" fechas a
# partir de cosas que no lo son: "T1" o "10:30" los convierte en el día de hoy y "Jan" en
# el año 1900, así que una columna de trimestres o de horas acababa marcada como fecha
PATRON_PARECE_FECHA = r"^\s*(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})"

# antes de convertir una columna entera miro solo sus primeros valores. Si ahí ya se ve
# que no son fechas no sigo, así en un archivo grande no pierdo tiempo convirtiendo
# columnas enteras de texto que no van a ser fechas nunca
TAMAÑO_MUESTRA_FECHAS = 200

# con que la mayoría de valores se dejen convertir ya cuenta como fecha, no hace falta
# que sean el 100% porque siempre puede haber alguna celda mal escrita
PORCENTAJE_MINIMO_FECHAS = 0.9

# formas de leer el texto que voy probando en orden: primero ISO (2025-03-01, que es como
# lo guardan casi todos los programas), después día/mes/año (el formato de España) y al
# final mes/día/año (el de EEUU), por si el archivo viene de allí
FORMAS_DE_LEER_FECHAS = ({"format": "ISO8601"}, {"dayfirst": True}, {"dayfirst": False})


# convierte un texto a fecha con una de las formas de arriba. Lo que no se pueda convertir,
# o no tenga forma de fecha, queda vacío (NaT). El utc=True es porque si en la misma
# columna hay fechas con zonas horarias distintas pandas da error en vez de dejarlas vacías,
# así que las paso todas a la misma zona y luego le quito la zona, para poder compararlas
# con las fechas de los filtros (que no llevan zona)
def _texto_a_fecha(texto: pd.Series, forma: dict) -> pd.Series:
    with warnings.catch_warnings():
        # cuando el texto no tiene un formato claro pandas avisa con un warning, pero aquí es
        # normal porque justamente estoy probando si la columna es de fechas o no
        warnings.simplefilter("ignore", UserWarning)
        fechas = pd.to_datetime(texto, errors="coerce", utc=True, **forma).dt.tz_localize(None)

    parece_fecha = texto.astype(str).str.match(PATRON_PARECE_FECHA)
    return fechas.where(parece_fecha)


# convierte una columna a fechas (lo que no se pueda convertir queda vacío, NaT).
# si ya son fechas de verdad (excel) las devuelvo tal cual. Si es texto (csv) pruebo las
# formas de leer con una muestra y me quedo con la primera que sirve para casi toda la
# muestra, así toda la columna se lee igual. Antes usaba to_datetime sin más, y pandas
# deducía el formato mirando solo la primera fila: si era 02/03/2025 lo leía como mes/día
# y toda la columna salía mal. Con dayfirst=True un 02/03/2025 siempre es 2 de marzo
def convertir_a_fecha(serie: pd.Series) -> pd.Series:
    vacia = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")

    if pd.api.types.is_datetime64_any_dtype(serie):
        # si la fecha lleva zona horaria se la quito, por lo mismo que en _texto_a_fecha
        if serie.dt.tz is not None:
            return serie.dt.tz_convert("UTC").dt.tz_localize(None)
        return serie

    # un número no lo trato nunca como fecha (pandas lo leería como nanosegundos desde 1970)
    if pd.api.types.is_numeric_dtype(serie) or pd.api.types.is_bool_dtype(serie):
        return vacia

    muestra = serie.dropna().head(TAMAÑO_MUESTRA_FECHAS)
    if muestra.empty:
        return vacia

    for forma in FORMAS_DE_LEER_FECHAS:
        if _texto_a_fecha(muestra, forma).notna().mean() >= PORCENTAJE_MINIMO_FECHAS:
            return _texto_a_fecha(serie, forma)

    return vacia


# dice si una columna es de fechas: si al menos el 90% de los valores que tiene se dejan
# convertir. Las celdas vacías no cuentan: antes sí contaban, y una columna de fechas con
# más de un 10% de celdas vacías acababa marcada como texto
def es_columna_fecha(serie: pd.Series) -> bool:
    valores_con_dato = serie.notna().sum()
    if valores_con_dato == 0:
        return False

    return convertir_a_fecha(serie).notna().sum() / valores_con_dato >= PORCENTAJE_MINIMO_FECHAS


# Función para marcar el tipo de dato de la columna,
# recibe una columna, que panda lo llama Series, y decide que tipo de dato es
def inferir_tipo(serie: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(serie):
        return "numerico"

    # en un csv las fechas no llegan como fecha de verdad, llegan como texto (a diferencia
    # del excel, que pandas ya me la da bien). es_columna_fecha() mira los dos casos
    if es_columna_fecha(serie):
        return "fecha"

    return "texto" # si no es ni numerico ni fecha será texto



# Convierto el archivo en un dataframe de pandas, que es como
# se representa el archivo en forma de tabla con filas y columnas
def leer_archivo(ruta: str, formato:str) -> pd.DataFrame:
    # Compruebo que el formato sea excel o csv
    # y devuelvo el archivo en forma de un dataframe
    if formato == "csv":
        return pd.read_csv(ruta)
    if formato == "xlsx":
        return pd.read_excel(ruta)
    
    # Si no es formato excel o csv creamos un error que lo captura el try
    # except del router y ahí marca el archivo como error
    else:
        raise ValueError(f"formato no soportado: {formato}")



# Función que recorre todas las columnas del dataframe, analiza su tipo
# y calcula estadísticas básicas (nulos, mínimo, máximo y media) y guarda
# los resultados en la base de datos
def analizar_columnas(df: pd.DataFrame, archivo_id: int, db: Session):
    
    # Usaré esta instancia del repositorio para cada columna del archivo
    # No hace falta crear una instancia por cada columna
    columna_repo = ColumnaRepository(db)
    
    # Recorro cada columna del archivo con df.columns
    # el enumerate da en cada vuelta la posición (0,1,2...)
    for posicion, nombre_columna in enumerate(df.columns):
        serie = df[nombre_columna]
        tipo = inferir_tipo(serie)
        
        # Solo guardo mínimo media y máximo si se trata de valores numéricos
        # ya que hacerlo con fechas o texto no tendria sentido almenos en esta
        # iteración
        valor_minimo = str(serie.min()) if tipo == "numerico" else None
        valor_maximo = str(serie.max()) if tipo == "numerico" else None
        media = float(serie.mean()) if tipo == "numerico" else None
        
        contador_valores_nulos = int(serie.isnull().sum())
        
        # Creo el registro Columna da través del repositorio, pero aun no se guarda
        # de forma permanente, solo lo apunta dentro de la sessión para guardarlo más
        # tarde en la base de datos usando el commit
        columna_repo.create(archivo_id=archivo_id, nombre_columna=nombre_columna, posicion=posicion,
                            tipo_dato=tipo,contador_valores_nulos=contador_valores_nulos,
                            valor_minimo=valor_minimo,valor_maximo=valor_maximo,
                            media=media)
    
    # Cuando el bucle termina envio todas las columnas creadas a la base de datos
    db.commit()
        
        
    