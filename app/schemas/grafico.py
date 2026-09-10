
from datetime import datetime

from pydantic import BaseModel

from app.schemas.columna import ColumnaResponse


class GraficoGeneradoResponse(BaseModel):
    id: int
    nombre_grafico: str
    tipo_grafico: str
    columna: ColumnaResponse # como en la primera iteración un gráfico solo puede ser de una columna lo hago asi
    fecha_creacion: datetime # en siguientes iteraciones la fecha vendrá en el informe y no el gráfico
    
    class Config:
        from_attributes = True
        
    