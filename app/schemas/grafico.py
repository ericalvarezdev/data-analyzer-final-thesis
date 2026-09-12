
from datetime import datetime

from pydantic import BaseModel

from app.schemas.columna import ColumnaResponse


class GraficoGeneradoResponse(BaseModel):
    id: int
    archivo_id: int
    nombre: str|None
    tipo_grafico: str
    
    # como en la primera iteración un gráfico solo puede ser de una columna lo hago asi
    # no hay riesgo de bucle porque ColumnaResponse no contiene ningún GraficoGeneradoResponse
    columna: ColumnaResponse 
    fecha_creacion: datetime # en siguientes iteraciones la fecha vendrá en el informe y no el gráfico
    
    etiquetas: list[str]
    valores: list[int]
    
    
    class Config:
        from_attributes = True
        

class GraficoCreadoRequest(BaseModel):
    columna_id: int
    tipo_grafico: str
    nombre_grafico: str|None = None
        
    