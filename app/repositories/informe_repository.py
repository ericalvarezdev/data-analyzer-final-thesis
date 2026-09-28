from sqlalchemy.orm import Session
from app.models.informe_generado import InformeGenerado

class InformeRepository:
    
    def __init__(self,db: Session) -> None:
        self.db = db
        
    
    # crea un nuevo informe
    def create(self, archivo_id: int, usuario_id: int, nombre: str|None = None) -> InformeGenerado:
        nuevo_informe = InformeGenerado(archivo_id=archivo_id, usuario_id=usuario_id, nombre=nombre)
        
        self.db.add(nuevo_informe)
        self.db.flush()
        return nuevo_informe
    

    # devuelve el informe por id
    def get(self, informe_id: int) -> InformeGenerado | None:
        informe = self.db.get(InformeGenerado,informe_id)
        return informe
    
    
    # devuelve todos los informes generados a partir de un archivo en orden de fecha de creación
    def list_by_archivo(self, archivo_id:int) -> list[InformeGenerado]:
        informes = self.db.query(InformeGenerado).filter(InformeGenerado.archivo_id == archivo_id).order_by(InformeGenerado.fecha_creacion.desc()).all()
        return informes
    
    
    # devuelve todos los informes generados de un usuario en orden de fecha de creación
    def list_by_usuario(self, usuario_id:int) -> list[InformeGenerado]:
        informes = self.db.query(InformeGenerado).filter(InformeGenerado.usuario_id == usuario_id).order_by(InformeGenerado.fecha_creacion.desc()).all()
        return informes


    # borra el informe que recibe por parámetro
    # al borrar el informe se borrará en cascada todos sus gráficos y los filtros de esos gráficos
    def delete(self, informe: InformeGenerado) -> None:
        self.db.delete(informe)


    # actualiza el nombre de un informe
    def actualizar_informe(self, informe: InformeGenerado, nuevo_nombre: str) -> InformeGenerado:
        informe.nombre = nuevo_nombre
        return informe