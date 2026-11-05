

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class InformeGenerado(Base):
    __tablename__ = "informes_generados"
    
    id = Column(Integer, primary_key=True, index=True)
    archivo_id = Column(Integer, ForeignKey("archivos_subidos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    nombre = Column(String, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Text y no String porque esto puede ser un párrafo entero, no una palabra suelta.
    # nullable porque un informe recién creado todavía no tiene resumen generado
    resumen_ia = Column(Text, nullable=True)
    
    archivo = relationship("ArchivoSubido", back_populates="informes")
    usuario = relationship("Usuario", back_populates="informes")
    graficos = relationship("GraficoGenerado", back_populates="informe", cascade="all, delete-orphan")