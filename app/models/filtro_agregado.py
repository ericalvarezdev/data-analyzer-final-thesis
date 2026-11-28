from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


# filtro que se aplica DESPUÉS de agrupar, sobre el resultado del gráfico (por ejemplo
# "las 5 regiones con más ventas"). Va en una tabla aparte de FiltroAplicado porque no
# tiene columna, ni conector, ni NOT: no elige filas del archivo, elige categorías del resultado
class FiltroAgregado(Base):
    __tablename__ = "filtros_agregados"

    id = Column(Integer, primary_key=True, index=True)
    grafico_id = Column(Integer, ForeignKey("graficos_generados.id"), nullable=False)

    # mayores, menores o porcentaje_minimo (ver TIPOS_FILTRO_AGREGADO en services/graficos.py)
    tipo = Column(String, nullable=False)

    # en mayores/menores es cuántas categorías me quedo (por ejemplo 5),
    # en porcentaje_minimo es el % (por ejemplo 1)
    valor = Column(Float, nullable=False)

    grafico = relationship("GraficoGenerado", back_populates="filtros_agregados")