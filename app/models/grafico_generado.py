from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class GraficoGenerado(Base):
    __tablename__ = "graficos_generados"
    
    id = Column(Integer, primary_key=True, index=True)
    archivo_id = Column(Integer, ForeignKey("archivos_subidos.id"), nullable=False) # En próximas iteraciones el gráfico generado apuntara al informe generado y no al archivo generado
    tipo_grafico = Column(String, nullable=False)
    columna_analizada = Column(Integer, ForeignKey("columnas.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow) # Cuando apunte a informe la fecha de creación ya estará en informe y no en gráfoico generado
    
    archivo = relationship("ArchivoSubido", back_populates="graficos")
    columna = relationship("Columna", back_populates="graficos")


# Como es la primera iteración solo generaré gráficos de una sola columna para simplificarlo un poco debido
# a que si no habria que crear otra clase intermedia ya que la cardinalidad seria de muchos a muchos