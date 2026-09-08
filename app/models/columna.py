from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Columna(Base):
    __tablename__ = "columnas"
    
    id = Column(Integer, primary_key=True, index=True)
    archivo_id = Column(Integer, ForeignKey("archivos_subidos.id"), nullable=False)
    nombre_columna = Column(String, nullable=False)
    tipo_dato = Column(String, nullable=True )
    contador_valores_nulos = Column(Integer, nullable=True)
    valor_minimo = Column(String, nullable=True)
    valor_maximo = Column(String, nullable=True)
    media = Column(Float, nullable=True)
    
    archivo = relationship("ArchivoSubido", back_populates="columnas")
    graficos = relationship("GraficoGenerado", back_populates="columna")
    