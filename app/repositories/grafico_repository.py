
from sqlalchemy.orm import Session
from app.models.grafico_generado import GraficoGenerado


class GraficoRepository:
    def __init__(self, db):
        self.db = db
    
    # guarda un nuevo gráfico en la base de datos
    def create(self, informe_id: int, columna_x_id: int, columna_y_id: int | None,
               tipo_grafico: str, etiquetas: list[str], operacion_agregacion: str,
               valores: list[int], nombre: str|None = None) -> GraficoGenerado:
        
        grafico = GraficoGenerado(informe_id=informe_id, columna_x_id=columna_x_id,
                                  columna_y_id=columna_y_id, tipo_grafico=tipo_grafico,
                                  nombre=nombre, etiquetas=etiquetas,
                                  valores=valores, operacion_agregacion=operacion_agregacion)
        
        self.db.add(grafico)
        self.db.flush() # necesitamos el id enseguida para devolverlo en la respuesta
        return grafico
    
    
    # busca un gráfico por su id
    def get(self, grafico_id) -> GraficoGenerado|None:
        grafico = self.db.get(GraficoGenerado, grafico_id)
        return grafico
    
    
    # devuelve todos los graficos de un informe
    def list_by_informe(self, informe_id:int) -> list[GraficoGenerado]:
        graficos = self.db.query(GraficoGenerado).filter(GraficoGenerado.informe_id == informe_id).all()
        return graficos
    
