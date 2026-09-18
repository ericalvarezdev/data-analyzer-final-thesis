
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class FiltroAplicado(Base):
    __tablename__ = "filtros_aplicados"
    
    id = Column(Integer, primary_key=True, index=True)
    grafico_id = Column(Integer, ForeignKey("graficos_generados.id"), nullable=False)
    columna_id = Column(Integer, ForeignKey("columnas.id"), nullable=False)
    tipo_filtro =  Column(String, nullable=False) # como un rango, un valor exacto, o una lista de valores
    
    # JSON porque los valores pueden ser muy variados, por ejemplo un rango son dos valores,
    # un valor exacto es uno, y una lista pueden ser cinco
    valores = Column(JSON, nullable=False)
    

    grafico = relationship("GraficoGenerado", back_populates="filtros")
    columna = relationship("Columna", back_populates="filtros")

    
    
