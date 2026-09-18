
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True) # dos usuarios no pueden registrarse con el mismo gmail
    contraseña_hash = Column(String, nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    rol = Column(String, default="usuario")
    
    archivos = relationship("ArchivoSubido", back_populates="usuario")
    informes = relationship("InformeGenerado", back_populates="usuario")