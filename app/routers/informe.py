
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth_dependency import get_current_user
from app.models.usuario import Usuario
from app.schemas.informe import InformeCreateRequest, InformeResponse
from app.repositories.archivo_repository import ArchivoRepository
from app.repositories.informe_repository import InformeRepository


router = APIRouter(prefix="/archivos/{archivo_id}/informes", tags=["Informes"])


# endpoint para crear un informe 
@router.post("/", response_model=InformeResponse)
def crear_informe(archivo_id: int, datos: InformeCreateRequest,
                  db: Session = Depends(get_db),
                  usuario_actual: Usuario = Depends(get_current_user)):
    
    
    archivo_repo = ArchivoRepository(db)
    archivo = archivo_repo.get(archivo_id)
    
    # Si el archivo no existe o no es del usuario indicado lanzamos error
    if archivo is None or archivo.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # creo el archivo y lo devuelvo
    informe_repo = InformeRepository(db)
    nuevo_informe = informe_repo.create(archivo_id=archivo_id, 
                                        usuario_id=usuario_actual.id,
                                        nombre=datos.nombre)
    
    db.commit()
    db.refresh(nuevo_informe)
    return nuevo_informe


# endpoint que devuelve todos los informes generados a partir de un archivo
@router.get("/", response_model=List[InformeResponse])
def listar_informes_de_archivo(archivo_id, db: Session = Depends(get_db),
                               usuario_actual: Usuario = Depends(get_current_user)):
    
    archivo_repo = ArchivoRepository(db)
    archivo = archivo_repo.get(archivo_id)
        
    # Si el archivo no existe o no es del usuario indicado lanzamos error
    if archivo is None or archivo.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    
    informe_repo = InformeRepository(db)
    lista_informes_archivo = informe_repo.list_by_archivo(archivo_id)
    return lista_informes_archivo


# Router para ver los informes de un usuario logeado
router_informes = APIRouter(prefix="/informes", tags=["Informes Usuario"])

@router_informes.get("/", response_model=list[InformeResponse])
def listar_informes_de_usuario(db: Session = Depends(get_db),
                               usuario_actual: Usuario = Depends(get_current_user)):
    informe_repo = InformeRepository(db)
    return informe_repo.list_by_usuario(usuario_actual.id)