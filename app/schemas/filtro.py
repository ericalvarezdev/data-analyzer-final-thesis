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
        


# lo que el usuario manda para un filtro que se aplica después de agrupar
# (ver TIPOS_FILTRO_AGREGADO en services/graficos.py)
class FiltroAgregadoRequest(BaseModel):
    tipo: str # mayores, menores o porcentaje_minimo
    valor: float # cuántas categorías (mayores/menores) o el % (porcentaje_minimo)

# información que la api devuelve de un filtro agregado
class FiltroAgregadoResponse(BaseModel):
    id: int
    grafico_id: int
    tipo: str
    valor: float

    class Config:
        from_attributes=True