from pydantic import BaseModel
from typing import Any

# lo que el usuario manda al configurar un filtro
class FiltroRequest(BaseModel):
    columna_id: int
    tipo_filtro: str
    valores: list[Any] # Any puede ser texto, número o fecha
    conector: str = "AND" # AND u OR, con el primer filtro de la lista no se usa
    negado: bool = False # NOT, si es True me quedo con las filas que NO cumplen el filtro

# información que la api devuelve de un filtro
class FiltroResponse(BaseModel):
    id: int
    grafico_id: int
    columna_id: int
    tipo_filtro: str
    valores: list[Any]
    conector: str
    negado: bool

    class Config:
        from_attributes=True