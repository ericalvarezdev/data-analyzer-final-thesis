from sqlalchemy import JSON, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.services.texto_filtros import describir_filtros, describir_filtros_agregados

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

    # antes aquí tenía etiquetas y valores por separado, pero con tarta/caja/histograma
    # cada tipo de gráfico necesita una forma distinta de datos, así que ahora guardo
    # directamente el "data"+"layout" de Plotly ya calculado, y tanto la web como el
    # PDF lo pintan tal cual sin volver a tocarlo
    especificacion = Column(JSON, nullable=False)

    # Como hay dos claves foráneas que provienen de la misma tabla "Columna" hay que indicar
    # SQLAlchemy no puede adivinar cual usa en cada relación, por eso hay que indicarselo explícitamente
    # con foreign_keys[]
    columna_x = relationship("Columna", foreign_keys=[columna_x_id], back_populates="graficos_x")
    columna_y = relationship("Columna", foreign_keys=[columna_y_id], back_populates="graficos_y")


    informe = relationship("InformeGenerado", back_populates="graficos")
    filtros = relationship("FiltroAplicado", back_populates="grafico", cascade="all, delete-orphan")

    #los filtros que se aplican después de agrupar. order_by para que se apliquen siempre
    # en el orden en que se crearon, y el cascade para que se borren solos con el gráfico
    filtros_agregados = relationship("FiltroAgregado", back_populates="grafico",
                                     cascade="all, delete-orphan", order_by="FiltroAgregado.id")
    
    # texto de los filtros, el mismo que sale en el PDF debajo del título. Es una propiedad y
    # no una columna de la tabla: no se guarda en la base de datos, se calcula cada vez a
    # partir de los filtros, así que no hace falta migración. El schema lo lee como un campo más
    @property
    def filtros_texto(self) -> str:
        # primero los filtros normales y después los agregados, que es el orden en que se
        # aplican. Ej: "Region es West · las 5 categorías con el valor más alto"
        textos = [describir_filtros(self.filtros), describir_filtros_agregados(self.filtros_agregados)]
        return " · ".join(texto for texto in textos if texto)