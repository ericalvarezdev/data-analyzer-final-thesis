

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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
    
    archivo = relationship("ArchivoSubido", back_populates="informes")
    usuario = relationship("Usuario", back_populates="informes")
    graficos = relationship("GraficoGenerado", back_populates="informe", cascade="all, delete-orphan")