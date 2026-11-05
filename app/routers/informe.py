
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth_dependency import get_current_user
from app.models.usuario import Usuario
from app.schemas.informe import InformeCreateRequest, InformeResponse, InformeUpdateRequest
from app.schemas.grafico import GraficoCreadoRequest
from app.repositories.archivo_repository import ArchivoRepository
from app.repositories.informe_repository import InformeRepository
from app.services.pdf import generar_pdf_informe
from app.services.ia import generar_resumen_informe, proponer_graficos
from app.routers.grafico import crear_grafico


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


# endpoint que crea un informe entero de golpe: le pide a la IA que proponga unos
# gráficos para el archivo y los crea de verdad, pasando cada uno por crear_grafico()
# (la misma función que usa el endpoint manual de arriba). A diferencia de crear_informe,
# que deja el informe vacío para que el usuario añada el primer gráfico a mano, este
# ya viene con gráficos reales dentro
@router.post("/ia", response_model=InformeResponse)
def crear_informe_con_ia(archivo_id: int, datos: InformeCreateRequest,
                         db: Session = Depends(get_db),
                         usuario_actual: Usuario = Depends(get_current_user)):

    archivo_repo = ArchivoRepository(db)
    archivo = archivo_repo.get(archivo_id)

    if archivo is None or archivo.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    try:
        propuestas = proponer_graficos(archivo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    informe_repo = InformeRepository(db)
    nuevo_informe = informe_repo.create(archivo_id=archivo_id,
                                        usuario_id=usuario_actual.id,
                                        nombre=datos.nombre)

    # diccionario nombre de columna -> columna, para traducir lo que proponga la IA
    # (que solo conoce nombres) a columna_id, que es lo que pide GraficoCreadoRequest
    columnas_por_nombre = {columna.nombre_columna: columna for columna in archivo.columnas}

    # cada propuesta se intenta por su cuenta: si la IA se ha inventado una columna o
    # una combinación no permitida, me salto esa propuesta y sigo con las demás, mejor
    # un informe con menos gráficos que quedarnos sin ninguno por un solo fallo
    graficos_creados = 0
    for propuesta in propuestas:
        try:
            columna_x = columnas_por_nombre.get(propuesta.get("columna_x"))
            columna_y = columnas_por_nombre.get(propuesta.get("columna_y"))

            if columna_x is None:
                continue

            datos_grafico = GraficoCreadoRequest(
                columna_x_id=columna_x.id,
                columna_y_id=columna_y.id if columna_y else None,
                operacion_agregacion=propuesta.get("operacion_agregacion", "recuento"),
                tipo_grafico=propuesta.get("tipo_grafico", "barras"),
                nombre_grafico=propuesta.get("nombre"),
            )
            crear_grafico(nuevo_informe, datos_grafico, db)
            graficos_creados += 1

        except Exception:
            continue

    if graficos_creados == 0:
        raise HTTPException(status_code=400,
                            detail="La IA no ha propuesto ningún gráfico válido, prueba otra vez")

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


@router_informes.get("/{informe_id}", response_model=InformeResponse)
def obtener_informe(informe_id: int,
                    db: Session = Depends(get_db),
                    usuario_actual: Usuario = Depends(get_current_user)):
    informe_repo = InformeRepository(db)
    informe = informe_repo.get(informe_id)
    if(informe is None or informe.usuario_id != usuario_actual.id):
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    return informe


@router_informes.delete("/{informe_id}", status_code=204)
def borrar_informe(informe_id: int,
                   db: Session = Depends(get_db),
                   usuario_actual: Usuario = Depends(get_current_user)):
    informe_repo = InformeRepository(db)
    informe = informe_repo.get(informe_id)
    if(informe is None or informe.usuario_id != usuario_actual.id):
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    informe_repo.delete(informe)
    db.commit()
    
    return None


@router_informes.patch("/{informe_id}", response_model = InformeResponse)
def renombrar_informe(informe_id: int,
                      datos: InformeUpdateRequest,
                      db: Session = Depends(get_db),
                      usuario_actual: Usuario = Depends(get_current_user)):
    informe_repo = InformeRepository(db)
    informe = informe_repo.get(informe_id)
    
    if(informe is None or informe.usuario_id != usuario_actual.id):
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    informe_actualizado = informe_repo.actualizar_informe(informe,datos.nombre)
    db.commit()
    db.refresh(informe_actualizado)
    return informe_actualizado


# endpoint para descargar un informe entero como PDF con todos sus gráficos
@router_informes.get("/{informe_id}/pdf")
def descargar_informe_pdf(informe_id: int,
                          db: Session = Depends(get_db),
                          usuario_actual: Usuario = Depends(get_current_user)):
    informe_repo = InformeRepository(db)
    informe = informe_repo.get(informe_id)

    if informe is None or informe.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    try:
        pdf_bytes = generar_pdf_informe(informe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    nombre_archivo = informe.nombre or f"informe_{informe.id}"
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}.pdf"'})


# endpoint que genera (o regenera) el resumen en lenguaje natural del informe con IA
@router_informes.post("/{informe_id}/resumen", response_model=InformeResponse)
def generar_resumen(informe_id: int,
                    db: Session = Depends(get_db),
                    usuario_actual: Usuario = Depends(get_current_user)):
    informe_repo = InformeRepository(db)
    informe = informe_repo.get(informe_id)

    if informe is None or informe.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    try:
        resumen = generar_resumen_informe(informe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    informe_actualizado = informe_repo.guardar_resumen_ia(informe, resumen)
    db.commit()
    db.refresh(informe_actualizado)
    return informe_actualizado