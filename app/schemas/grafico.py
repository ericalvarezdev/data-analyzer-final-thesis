
from datetime import datetime

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

    
    etiquetas: list[str]
    valores: list[float]
    
    fecha_creacion: datetime

    class Config:
        from_attributes = True
        


        
    