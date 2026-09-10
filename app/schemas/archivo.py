
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.columna import ColumnaResponse

# Define que datos de un archivo subido se devuelven por la API
class ArchivoSubidoResponse(BaseModel):
    id: int
    nombre_archivo: str
    tamaño: int
    formato: str
    estado_procesamiento: str
    fecha_subida: datetime
    mensaje_error: Optional[str]
    numero_filas: Optional[int]
    numero_columnas: Optional[int]
    columnas: list[ColumnaResponse] = []
    hoja_seleccionada: Optional[str] = None
    
    # ruta_almacenamiento es un detalle interno del servidor y 
    # no lo pongo porque no es nada útil que el usuario tenga que ver
    
    
    # Por defecto Pydantic espera recibir un diccionario pero le pasaré
    # un objeto de SQLAlchemy (con atributos tipo objeto.campo, no diccionario["campo"])
    # from_attributes = True le dice a Pydantic que también puede leer los datos
    # directamente desde los atributos de un objeto, no solo desde un diccionario.
    class Config:
        from_attributes = True