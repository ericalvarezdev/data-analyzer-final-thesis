from pydantic import BaseModel
from typing import Any

# lo que el usuario manda al configurar un filtro
class FiltroRequest(BaseModel):
    columna_id: int
    tipo_filtro: str
    valores: list[Any] # Any puede ser texto, número o fecha
    

# información que la api devuelve de un filtro
class FiltroResponse(BaseModel):
    id: int
    grafico_id: int
    columna_id: int
    tipo_filtro: str
    valores: list[Any]
    
    class Config:
        from_attributes=True

