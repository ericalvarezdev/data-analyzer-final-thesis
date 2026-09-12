
from sqlalchemy.orm import Session

from app.models.archivo_subido import ArchivoSubido


class ArchivoRepository:
    
    def __init__(self, db: Session) -> None:
        self.db = db
    
    
    # Crea un nuevo archivo
    def create(self, nombre_archivo: str,
               ruta_almacenamiento: str, formato: str,
               tamaño: str) -> ArchivoSubido:
        
        archivo = ArchivoSubido(nombre_archivo=nombre_archivo, ruta_almacenamiento=ruta_almacenamiento,
                                formato=formato, tamaño=tamaño, estado_procesamiento="procesando")
         
        self.db.add(archivo)
        self.db.flush()
        return archivo
    
    
    # Busca un archivo por su id
    def get(self, archivo_id: int) -> ArchivoSubido:
        
        archivo = self.db.get(ArchivoSubido, archivo_id)
        return archivo
   
 
    # Para cuando se acabe de procesar el archivo guarda las estadísticas básicas
    def marcar_completado(self, archivo: ArchivoSubido, numero_filas: int, numero_columnas: int) -> ArchivoSubido:
        
        archivo.numero_filas = numero_filas
        archivo.numero_columnas = numero_columnas
        archivo.estado_procesamiento = "completado"
        
        self.db.add(archivo)
        self.db.flush() # Envia los cambios a la base de datos de forma provisional
        return archivo
    
    
    # Para cuando haya un error dejar el mensaje de error en la base de datos y 
    # cambiar el estado de procesamiento
    def marcar_error(self, archivo: ArchivoSubido, mensaje_error:str) -> ArchivoSubido:
        
        archivo.mensaje_error = mensaje_error
        archivo.estado_procesamiento = "error"
        
        self.db.add(archivo)
        self.db.flush() # Envia los cambios a la base de datos de forma provisional
        return archivo
        
        
        
        """
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
        
        columnas = relationship("Columna", back_populates="archivo")
        graficos = relationship("GraficoGenerado", back_populates="archivo")
        """
    
    
    # Devuelve todos los archivos ordenados del mas reciente al mas antiguo
    def list_all(self) -> list[ArchivoSubido]:
        archivos = self.db.query(ArchivoSubido).order_by(ArchivoSubido.fecha_subida.desc()).all()
        return archivos
    
    
    # Elimina un archivo, sus columnas y gráficas, ya que el borrado es en cascada
    def delete(self, archivo: ArchivoSubido) -> None:
        self.db.delete(archivo)
        
    
    