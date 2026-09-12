
from sqlalchemy.orm import Session
from app.models.grafico_generado import GraficoGenerado


class GraficoRepository:
    def __init__(self, db):
        self.db = db
    
    # guarda un nuevo gráfico en la base de datos
    def create(self, archivo_id: int, columna_id: int,
               tipo_grafico: str, etiquetas: list[str], valores: list[int],
               nombre: str|None = None) -> GraficoGenerado:
        
        grafico = GraficoGenerado(archivo_id=archivo_id, columna_id=columna_id,
                                  tipo_grafico=tipo_grafico, nombre=nombre, etiquetas=etiquetas,
                                  valores=valores)
        
        self.db.add(grafico)
        self.db.flush() # necesitamos el id enseguida para devolverlo en la respuesta
        return grafico
    
    
    # busca un gráfico por su id
    def get(self, grafico_id) -> GraficoGenerado|None:
        grafico = self.db.get(GraficoGenerado, grafico_id)
        return grafico
    
    
    # devuelve todos los graficos del archivo
    def list_by_archivo(self, archivo_id) -> list[GraficoGenerado]:
        graficos = self.db.query(GraficoGenerado).filter(archivo_id == GraficoGenerado.archivo_id).all()
        return graficos
    
