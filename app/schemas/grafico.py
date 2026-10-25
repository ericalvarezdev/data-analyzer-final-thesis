
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.columna import ColumnaResponse
from app.schemas.filtro import FiltroRequest, FiltroResponse


class GraficoCreadoRequest(BaseModel):
    columna_x_id: int
    columna_y_id: int | None = None
    operacion_agregacion: str = "recuento"

    tipo_grafico: str
    nombre_grafico: str|None = None


    filtros: list[FiltroRequest] = []



class GraficoGeneradoResponse(BaseModel):
    id: int
    informe_id: int
    nombre: str|None
    tipo_grafico: str

    # no hay riesgo de bucle porque ColumnaResponse no contiene ningún GraficoGeneradoResponse
    columna_x: ColumnaResponse
    columna_y: ColumnaResponse | None
    filtros: list[FiltroResponse] = []
    operacion_agregacion: str

    # ya no mando etiquetas y valores sueltos, mando directamente la especificación
    # de Plotly (data + layout) tal y como la calculé en services/graficos.py, así el
    # frontend solo tiene que pasarsela a Plotly.js sin tener que reconstruir nada
    especificacion: dict[str, Any]

    fecha_creacion: datetime

    class Config:
        from_attributes = True
