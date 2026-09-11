from sqlalchemy.orm import Session

from app.models.columna import Columna

class ColumnaRepository:
    
    def __init__(self, db: Session) -> None:
        self.db = db
    
    # crea una columna    
    def create(self, archivo_id: int, nombre_columna: str, tipo_dato: str,
               contador_valores_nulos: int|None, valor_minimo: str|None, valor_maximo: str|None,
               media: float|None) -> Columna:
        
        columna = Columna(archivo_id=archivo_id, nombre_columna=nombre_columna,
                          contador_valores_nulos=contador_valores_nulos,
                          valor_minimo=valor_minimo, valor_maximo=valor_maximo,
                          media=media, tipo_dato=tipo_dato)
        
        self.db.add(columna)
        # No hacemos el flush porque en el endpoint creará muchas columnas y el flush de todas ellas se hará
        # una sola vez después de crear todas las columnas, para que sea más eficiente y también porque no
        # necesitamos el id de la columna nada más crearla como en el archivo para asignar el id del archivo
        # a cada columna
        return columna

    
        
        """
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
        """
    
    # busca una columna por su id
    def get(self, columna_id: int) -> Columna|None:
        columna = self.db.get(Columna,columna_id)
        return columna
    
    