
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, JSON
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
    
    # con que se une este filtro al resultado de los filtros anteriores (AND/OR).
    # en el primer filtro de la lista no se usa para nada, pero lo guardo igual
    # para no complicar el modelo con un caso especial
    conector = Column(String, nullable=False, default="AND")

    # NOT: si es True me quedo con las filas que NO cumplen este filtro.
    # server_default="0" porque en la base de datos ya hay filtros guardados de antes, y
    # al añadir la columna necesitan un valor (0 = False, es decir, sin negar)
    negado = Column(Boolean, nullable=False, default=False, server_default="0")

    grafico = relationship("GraficoGenerado", back_populates="filtros")
    columna = relationship("Columna", back_populates="filtros")