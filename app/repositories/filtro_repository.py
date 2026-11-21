from typing import Any
from sqlalchemy.orm import Session
from app.models.filtro_aplicado import FiltroAplicado

class FiltroRepository:
    
    def __init__(self, db: Session) -> None:
        self.db = db
        
    
    def create(self, grafico_id: int, columna_id: int,
               tipo_filtro: str, valores: list[Any], conector: str = "AND",
               negado: bool = False) -> FiltroAplicado:

        filtro = FiltroAplicado(grafico_id=grafico_id, columna_id=columna_id,
                                tipo_filtro=tipo_filtro, valores=valores, conector=conector,
                                negado=negado)
        
        # sin flush ya que se pueden crear varios filtros seguidos los cuales
        # el commit final del router los guarda todos de golpe
        self.db.add(filtro)
        return filtro