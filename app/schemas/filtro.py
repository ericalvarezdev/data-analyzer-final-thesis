from pydantic import BaseModel
from typing import Any

# lo que el usuario manda al configurar un filtro
class FiltroRequest(BaseModel):
    columna_id: int
    tipo_filtro: str
    valores: list[Any] # Any puede ser texto, número o fecha
    conector: str = "AND" # AND u OR, con el primer filtro de la lista no se usa

# información que la api devuelve de un filtro
class FiltroResponse(BaseModel):
    id: int
    grafico_id: int
    columna_id: int
    tipo_filtro: str
    valores: list[Any]
    conector: str
    
    class Config:
        from_attributes=True

