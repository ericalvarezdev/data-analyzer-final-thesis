import pandas as pd
from sqlalchemy.orm import Session
from app.models.columna import Columna
from app.repositories.columna_repository import ColumnaRepository

# Convierte el archivo en un dataframe de pandas, que es como
# que representa el archivo en forma de tabla con filas y columnas
def leer_archivo(ruta: str, formato:str) -> pd.DataFrame:
    # Comprobamos que el formato sea excel o csv
    # y devolvemos convertimos el archivo en un dataframe
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
    else:
        return "texto" # si no es ni numerico ni fecha será texto


# Función que recorre todas las columnas del dataframe, analiza su tipo
# y calcula estadísticas básicas (nulos, mínimo, máximo y media) y guarda
# los resultados en la base de datos
def analizar_columnas(df: pd.DataFrame, archivo_id: int, db: Session):
    
    # Usaré esta instancia del repositorio para cada columna del archivo
    # No hace falta crear una instancia por cada columna
    columna_repo = ColumnaRepository(db)
    
    # Recorro cada columna del archivo con df.columns
    for nombre_columna in df.columns:
        serie = df[nombre_columna]
        tipo = inferir_tipo(serie)
        
        # Solo guardo mínimo media y máximo si se trata de valores numéricos
        # ya que hacerlo con fechas o texto no tendria sentido almenos en esta
        # iteración
        valor_minimo = str(serie.min()) if tipo == "numerico" else None
        valor_maximo = str(serie.max()) if tipo == "numerico" else None
        media = float(serie.mean()) if tipo == "numerico" else None
        
        contador_valores_nulos = int(serie.isnull().sum())
        
        # Creamos el registro Columna da través del repositorio, pero aun no se guarda
        # de forma permanente, solo lo apunta dentro de la sessión para guardarlo más
        # tarde en la base de datos usando el commit
        columna_repo.create(archivo_id=archivo_id, nombre_columna=nombre_columna,
                            tipo_dato=tipo,contador_valores_nulos=contador_valores_nulos,
                            valor_minimo=valor_minimo,valor_maximo=valor_maximo,
                            media=media)
    
    # Cuando el bucle termina enviamos todas las columnas creadas a la base de datos
    db.commit()
        
        
    