from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ArchivoSubido(Base):
    __tablename__ = "archivos_subidos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String, nullable=False)
    ruta_almacenamiento = Column(String, nullable=False)
    formato = Column(String, nullable=False)
    tamaño = Column(Integer, nullable=False)
    estado_procesamiento = Column(String, default="pendiente")
    mensaje_error = Column(String, nullable=True)
    numero_filas = Column(Integer, nullable=True)
    numero_columnas = Column(Integer, nullable=True)
    fecha_subida = Column(DateTime, default=datetime.utcnow)
    hoja_seleccionada = Column(String, nullable=True) # lo usaré en el futuro cuando de la opción de seleccionar hoja
    
    columnas = relationship("Columna", back_populates="archivo")
    graficos = relationship("GraficoGenerado", back_populates="archivo")
    

    # El ForeignKey guarda el número que conecta las tablas
    # (el archivo_id de cada columna apuntando al id del archivo).
    # El relationship() es solo una comodidad de Python: gracias a él puedes escribir archivo.
    # columnas para ver todas las columnas de ese archivo, o columna.archivo para ver a qué archivo pertenece,
    # sin tener que hacer la consulta SQL para buscarlo.
    
    # En el caso de uno a muchos se hace asi:
    
    # En ClaseA:
    # hijos = relationship("ClaseB", back_populates="padre")

    # En ClaseB:
    # padre = relationship("ClaseA", back_populates="hijos")