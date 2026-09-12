
from pydantic import BaseModel
from typing import Optional


# Define que datos de una columna se devuelven por la API
class ColumnaResponse(BaseModel):
    id: int
    nombre_columna: str
    archivo_id: int # aqui al solo guardar el id y no el objeto entero no se crea referencia circular
    posicion: int
    tipo_dato: Optional[str]
    contador_valores_nulos: Optional[int]
    valor_minimo: Optional[str]
    valor_maximo: Optional[str]
    media: Optional[float]
    
    # no guardo archivo perteneciente aqui ya que en ArchivoResponse ya guardo las columnas
    # de un archivo, si lo guardase aqui se crearia una referencia circular que acabaria en
    # un bucle infinito
    
    # los Optional indican que el campo puede ser vacío y si lo es no dará error
    
    
    class Config:
        from_attributes = True