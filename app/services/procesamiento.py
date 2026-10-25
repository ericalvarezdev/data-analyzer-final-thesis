import pandas as pd
from sqlalchemy.orm import Session
from app.models.columna import Columna
from app.repositories.columna_repository import ColumnaRepository

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


# Función para marcar el tipo de dato de la columna,
# recibe una columna, que panda lo llama Series, y decide que tipo de dato es
def inferir_tipo(serie: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(serie):
        return "numerico"
    elif pd.api.types.is_datetime64_any_dtype(serie):
        return "fecha"
    
    # en un csv las fechas no llegan como fecha de verdad, llegan como texto
    # (a diferencia del excel, que pandas ya me la da bien), asi que si no es
    # ni numerico ni fecha de verdad, pruebo a convertirla antes de rendirme
    if len(serie) > 0:
        # errors="coerce" convierte los valores que no puede interpretar como fechas en NaT
        # (fecha no válida), en lugar de dar un error.
        convertida = pd.to_datetime(serie, errors="coerce")
        
        # con que la mayoría de valores se dejen convertir ya cuenta como fecha,
        # no hace falta que sean el 100% porque siempre puede haber alguna celda
        # vacía o mal escrita
        if convertida.notna().sum() / len(serie) >= 0.9:
            return "fecha"
    
    return "texto" # si no es ni numerico ni fecha será texto


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
        
        
    