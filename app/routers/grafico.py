
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_dependency import get_current_user
from app.models.usuario import Usuario
from app.database import get_db
from app.repositories.informe_repository import InformeRepository
from app.schemas.grafico import GraficoCreadoRequest, GraficoGeneradoResponse
from app.repositories.archivo_repository import ArchivoRepository
from app.repositories.columna_repository import ColumnaRepository
from app.repositories.grafico_repository import GraficoRepository
from app.repositories.filtro_repository import FiltroRepository
from app.services.graficos import OPERACIONES_VALIDAS, TIPOS_FILTRO_VALIDOS, TIPOS_VALIDOS, generar_datos_grafico


router = APIRouter(prefix="/informes/{informe_id}/graficos", tags=["Graficos"])

# endpoint que genera un grafico dentro de un informe
@router.post("/", response_model=GraficoGeneradoResponse)
def generar_grafico(informe_id: int, datos: GraficoCreadoRequest,
                    db: Session = Depends(get_db),
                    usuario_actual: Usuario = Depends(get_current_user)):
    
    # valido que el tipo de gráfico es soportado
    if datos.tipo_grafico not in TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Tipo de gráfico no soportado")
    
    if datos.operacion_agregacion not in OPERACIONES_VALIDAS:
        raise HTTPException(status_code=400, detail="Operación de agregación no soportada")
    
    
    # valido que el informe existe y que es del usuario logeado
    informe_repo = InformeRepository(db)
    informe = informe_repo.get(informe_id)
    if informe is None or informe.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    
    # el archivo lo saco del propio informe
    archivo = informe.archivo
    
    
    # valido que la columna existe y pertenece a este archivo
    columna_repo = ColumnaRepository(db)
    
    # columna del eje x (siempre obligatoria)
    columna_x = columna_repo.get(datos.columna_x_id)
    if columna_x is None or columna_x.archivo_id != archivo.id:
        raise HTTPException(status_code=404, detail="La columna X no existe o no es de este archivo")
    
    # columna del eje y (solo la uso si la operación lo necesita)
    columna_y = None
    # si se cumple necesitaremos la columna y ya que no es recuento
    if datos.operacion_agregacion != "recuento":
        # si la columna y esta vacía lanzamos error
        if datos.columna_y_id is None:
            raise HTTPException(status_code=400,
                                detail="La operación necesita una columna del eje Y")
        # cojo la columna y
        columna_y = columna_repo.get(datos.columna_y_id)
        if columna_y is None or columna_y.archivo_id != archivo.id:
            raise HTTPException(status_code=404, detail="La columna  Y no existe o no es de este archivo")
        
        # debido a que de momento solo usare la columna y para sumar o calcular la media,
        # la columna y de momento solo puede ser numérica
        if columna_y.tipo_dato != "numerico":
            raise HTTPException(status_code=400, 
                                detail="La columna del eje Y debe de ser numérica para sumar o calcular la media")
        
        
    # VALIDO LOS FILTROS ANTES DE CALCULAR NADA
    # convierto cada filtro a un diccionario con la posición de su columna,
    # que es lo que necesita el servicio de graficos.py
    filtros_para_calculo = []
    for filtro in datos.filtros:
        
        # Compruebo que todo sea válido
        if filtro.tipo_filtro not in TIPOS_FILTRO_VALIDOS:
            raise HTTPException(status_code=400, detail=f"Tipo de filtro no soportado: {filtro.tipo_filtro}")
        
        if filtro.tipo_filtro == "rango" and len(filtro.valores) != 2:
            raise HTTPException(status_code=400, detail="Un filtro de rango necesita exactamente 2 valores")

        if not filtro.valores:
            raise HTTPException(status_code=400, detail="Un filtro no puede tener la lista de valores vacía")

        # cojo la columna a la cual se aplica el filtro
        columna_filtro = columna_repo.get(filtro.columna_id)
        
        if columna_filtro is None or columna_filtro.archivo_id != archivo.id:
            raise HTTPException(status_code=404, detail="Una de las columnas de los filtros no es de este archivo")
        
        filtros_para_calculo.append({
            "posicion": columna_filtro.posicion,
            "tipo_filtro": filtro.tipo_filtro,
            "valores": filtro.valores,
        })
        
    # CALCULO EL RESULTADO
    try:
        resultado = generar_datos_grafico(ruta_archivo=archivo.ruta_almacenamiento,
                                        formato=archivo.formato,
                                        posicion_x=columna_x.posicion,
                                        posicion_y=columna_y.posicion if columna_y else None,
                                        operacion=datos.operacion_agregacion,
                                        filtros=filtros_para_calculo)
        
    except ValueError as e:
        # captura el "los filtros no dejan ninguna fila" del servicio de graficos
        raise HTTPException(status_code=400, detail=str(e))
    
    
    # GUARDO EL GRÁFICO
    grafico_repo = GraficoRepository(db)
    nuevo_grafico = grafico_repo.create(informe_id=informe_id,
                                        columna_x_id=datos.columna_x_id,
                                        columna_y_id=datos.columna_y_id,
                                        operacion_agregacion=datos.operacion_agregacion,
                                        tipo_grafico=datos.tipo_grafico,
                                        etiquetas=resultado["etiquetas"],
                                        valores=resultado["valores"],
                                        nombre=datos.nombre_grafico)
    
    # GUARDO LOS FILTROS
    # el id del gráfico ya existe porque en el create del repositorio de gráficos hago el flush
    
    filtro_repo = FiltroRepository(db)
    for filtro in datos.filtros:
        filtro_repo.create(grafico_id=nuevo_grafico.id,
                           columna_id=filtro.columna_id,
                           tipo_filtro=filtro.tipo_filtro,
                           valores=filtro.valores)
    
    db.commit()
    db.refresh(nuevo_grafico)
    return nuevo_grafico  
        
        
        
    

# endpoint que devuelve el gráfico buscado por id
@router.get("/{grafico_id}", response_model=GraficoGeneradoResponse)
def obtener_grafico(informe_id: int, grafico_id: int, db: Session = Depends(get_db),
                    usuario_actual: Usuario = Depends(get_current_user)):
    
    
    grafico_repo = GraficoRepository(db)
    grafico = grafico_repo.get(grafico_id)
    
    # compruebo que el gráfico existe y que es del informe indicado
    if grafico is None or grafico.informe_id!= informe_id:
        raise HTTPException(status_code=404, detail="Grafico no encontrado para este informe")
    
    # compruebo que el usuario logeado es el propietario del informe donde esta el gráfico
    if grafico.informe.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=404, detail="Grafico no encontrado para este informe")
    
    return grafico


# devuelve todos los graficos generados a partir de un informe
@router.get("/",response_model=list[GraficoGeneradoResponse]|None)
def listar_graficos_de_informe(informe_id: int, db: Session = Depends(get_db),
                               usuario_actual: Usuario = Depends(get_current_user)):
    
    informe_repo = InformeRepository(db)
    informe = informe_repo.get(informe_id)
    if informe is None or informe.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    
    grafico_repo = GraficoRepository(db)
    graficos = grafico_repo.list_by_informe(informe_id)
    return graficos