from pydantic import BaseModel
from datetime import datetime
from app.schemas.grafico import GraficoGeneradoResponse


class InformeCreateRequest(BaseModel):
    nombre: str | None = None


class InformeResponse(BaseModel):
    id: int
    archivo_id: int
    usuario_id: int
    nombre: str | None
    fecha_creacion: datetime
    graficos: list[GraficoGeneradoResponse] = []
    
    class Config:
        from_attributes = True

