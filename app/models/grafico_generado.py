from sqlalchemy import JSON, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class GraficoGenerado(Base):
    __tablename__ = "graficos_generados"
    
    id = Column(Integer, primary_key=True, index=True)
    informe_id = Column(Integer, ForeignKey("informes_generados.id"), nullable=False)

    columna_x_id = Column(Integer, ForeignKey("columnas.id"), nullable=False)
    columna_y_id = Column(Integer, ForeignKey("columnas.id"), nullable=True)
    operacion_agregacion = Column(String, nullable=False, default="recuento")
    
    nombre = Column(String, nullable=True)
    tipo_grafico = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow) # Cuando apunte a informe la fecha de creación ya estará en informe y no en gráfoico generado
    
    etiquetas = Column(JSON, nullable=True)
    valores = Column(JSON, nullable=True)
    
    # Como hay dos claves foráneas que provienen de la misma tabla "Columna" hay que indicar
    # SQLAlchemy no puede adivinar cual usa en cada relación, por eso hay que indicarselo explícitamente
    # con foreign_keys[]
    columna_x = relationship("Columna", foreign_keys=[columna_x_id], back_populates="graficos_x")
    columna_y = relationship("Columna", foreign_keys=[columna_y_id], back_populates="graficos_y")

    
    informe = relationship("InformeGenerado", back_populates="graficos")
    filtros = relationship("FiltroAplicado", back_populates="grafico", cascade="all, delete-orphan")

