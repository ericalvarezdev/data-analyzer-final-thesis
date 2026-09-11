
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.grafico import GraficoCreadoRequest, GraficoGeneradoResponse
from app.repositories.archivo_repository import ArchivoRepository
from app.repositories.columna_repository import ColumnaRepository
from app.repositories.grafico_repository import GraficoRepository
from app.services.graficos import TIPOS_VALIDOS, generar_datos_grafico


router = APIRouter(prefix="/archivos/{archivo_id}/graficos", tags=["Graficos"])


# El usuario sube el archivo, indica de que columna y el tipo de gráfico que quiere
# el grafico se calcula y se guardan los datos del registro del gráfico generado
# en la base de datos, aun no se guarda el gráfico en si, de momento solo guardo el
# registro y lo retorno
@router.post("/", response_model=GraficoGeneradoResponse)
def generar_grafico(archivo_id: int, datos: GraficoCreadoRequest, db: Session = Depends(get_db)):
    
    # valido que el tipo de gráfico es soportado
    if datos.tipo_grafico not in TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Tipo de gráfico no soportado")
    
    # valido que el archivo existe
    archivo_repo = ArchivoRepository(db)
    archivo = archivo_repo.get(archivo_id)
    if archivo is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # valido que la columna existe y pertenece a este archivo
    columna_repo = ColumnaRepository(db)
    columna = columna_repo.get(datos.columna_id)
    if columna is None or columna.archivo_id != archivo_id:
        raise HTTPException(status_code=404, detail="La columna no existe o no es de este archivo")
    
    print("antes")
    # calculo los datos del gráfico
    generar_datos_grafico(ruta_archivo=archivo.ruta_almacenamiento, formato =archivo.formato,
                          nombre_columna=columna.nombre_columna)
    print("despues")

    # guardo el registro de el gráfico generado (no el gráfico con las frecuencias en si)
    grafico_repo = GraficoRepository(db)
    nuevo_grafico = grafico_repo.create(archivo_id=archivo_id,columna_id=datos.columna_id,
                        tipo_grafico=datos.tipo_grafico)
    db.commit()
    db.refresh(nuevo_grafico)
    
    return nuevo_grafico