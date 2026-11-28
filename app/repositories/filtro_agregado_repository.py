from sqlalchemy.orm import Session
from app.models.filtro_agregado import FiltroAgregado


class FiltroAgregadoRepository:

    def __init__(self, db: Session) -> None:
        self.db = db


    # sin flush, igual que en FiltroRepository: se pueden crear varios seguidos y el
    # commit final del router los guarda todos de golpe
    def create(self, grafico_id: int, tipo: str, valor: float) -> FiltroAgregado:
        filtro = FiltroAgregado(grafico_id=grafico_id, tipo=tipo, valor=valor)
        self.db.add(filtro)
        return filtro