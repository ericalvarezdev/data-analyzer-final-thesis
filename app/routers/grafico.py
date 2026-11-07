
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_dependency import get_current_user
from app.models.columna import Columna
from app.models.usuario import Usuario
from app.models.informe_generado import InformeGenerado
from app.models.grafico_generado import GraficoGenerado
from app.database import get_db
from app.repositories.informe_repository import InformeRepository
from app.schemas.grafico import GraficoCreadoRequest, GraficoGeneradoResponse
from app.repositories.archivo_repository import ArchivoRepository
from app.repositories.columna_repository import ColumnaRepository
from app.repositories.grafico_repository import GraficoRepository
from app.repositories.filtro_repository import FiltroRepository
from app.services.graficos import (OPERACIONES_VALIDAS, TIPOS_FILTRO_VALIDOS, TIPOS_VALIDOS,
                                   TIPOS_FILTRO_FECHA, OPERACIONES_PERMITEN_TARTA,
                                   OPERACIONES_PERMITEN_DISTRIBUCION, CONECTORES_VALIDOS,
                                   generar_especificacion_grafico)

# estos dos tipos de filtro necesitan dos valores (un mínimo y un máximo),
# el resto de tipos de filtro necesitan solo uno
TIPOS_FILTRO_DE_RANGO = {"rango", "fecha_entre"}

# tipos de gráfico que muestran los valores en bruto de una categoría (no un número agregado),
# por eso necesitan una operación relacionada con la distribución y no con un total
TIPOS_DE_DISTRIBUCION = {"caja", "histograma"}


router = APIRouter(prefix="/informes/{informe_id}/graficos", tags=["Graficos"])


# True si el valor es una fecha en formato aaaa-mm-dd, que es lo que manda el input de
# fecha del frontend
def _es_fecha_aaaa_mm_dd(valor) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(valor)):
        return False
    try:
        date.fromisoformat(str(valor)) # para que no cuele un 2025-02-31
        return True
    except ValueError:
        return False


# compruebo los filtros de fecha antes de calcular nada, así si algo está mal el usuario
# recibe un error que se entiende en vez de un gráfico vacío o un error interno
def _validar_filtro_de_fecha(tipo: str, valores: list, columna: Columna) -> None:

    if tipo not in TIPOS_FILTRO_FECHA:
        return

    # un filtro de fecha sobre una columna de texto no dejaría ninguna fila
    if columna.tipo_dato != "fecha":
        raise HTTPException(status_code=400,
                            detail=f"Los filtros de fecha solo se pueden usar en columnas de fechas, y '{columna.nombre_columna}' no lo es")

    if not all(_es_fecha_aaaa_mm_dd(valor) for valor in valores):
        raise HTTPException(status_code=400,
                            detail="Las fechas de los filtros tienen que estar en formato aaaa-mm-dd")

    # en formato aaaa-mm-dd comparar como texto ya ordena bien las fechas
    if tipo == "fecha_entre" and str(valores[0]) > str(valores[1]):
        raise HTTPException(status_code=400,
                            detail="En 'fecha entre' la primera fecha no puede ser posterior a la segunda")


# la separo del endpoint de abajo para reutilizarla desde el informe generado con IA, así
# los gráficos de la IA pasan por las mismas validaciones que los manuales. Si la IA llamase
# directamente al endpoint generar_grafico en vez de a esto habría dos problemas: 1) usuario_actual
# viene de Depends(get_current_user), que solo lo resuelve FastAPI con una petición HTTP real,
# no llamando a la función a pelo desde dentro de otro endpoint; 2) generar_grafico hace su
# propio commit, así que si la IA lo llamase una vez por gráfico y fallase el cuarto de cinco,
# los 3 anteriores ya se habrían guardado para siempre y el informe quedaría a medias
def crear_grafico(informe: InformeGenerado, datos: GraficoCreadoRequest, db: Session) -> GraficoGenerado:

    # valido que el tipo de gráfico es soportado
    if datos.tipo_grafico not in TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Tipo de gráfico no soportado")

    if datos.operacion_agregacion not in OPERACIONES_VALIDAS:
        raise HTTPException(status_code=400, detail="Operación de agregación no soportada")

    # la tarta solo tiene sentido si las porciones suman un total (recuento o suma)
    if datos.tipo_grafico == "tarta" and datos.operacion_agregacion not in OPERACIONES_PERMITEN_TARTA:
        raise HTTPException(status_code=400,
                            detail="La tarta solo se puede usar con recuento o suma")

    # caja e histograma muestran cómo se reparten los valores, así que necesitan
    # una operación de distribución y no un recuento o una suma
    if datos.tipo_grafico in TIPOS_DE_DISTRIBUCION and datos.operacion_agregacion not in OPERACIONES_PERMITEN_DISTRIBUCION:
        raise HTTPException(status_code=400,
                            detail="Ese tipo de gráfico necesita una operación de media, mediana, desviación estándar o varianza")


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

        # recuento_distintos solo cuenta cuántos valores diferentes hay, así que la
        # columna y puede ser de cualquier tipo. El resto de operaciones hacen cálculos
        # numéricos de verdad (suma, media...) y ahí sí que la columna y tiene que ser numérica
        if datos.operacion_agregacion != "recuento_distintos" and columna_y.tipo_dato != "numerico":
            raise HTTPException(status_code=400,
                                detail="La columna del eje Y debe de ser numérica para esta operación")


    # VALIDO LOS FILTROS ANTES DE CALCULAR NADA
    # convierto cada filtro a un diccionario con la posición de su columna,
    # que es lo que necesita el servicio de graficos.py
    filtros_para_calculo = []
    for filtro in datos.filtros:

        # Compruebo que todo sea válido
        if filtro.tipo_filtro not in TIPOS_FILTRO_VALIDOS:
            raise HTTPException(status_code=400, detail=f"Tipo de filtro no soportado: {filtro.tipo_filtro}")

        if filtro.tipo_filtro in TIPOS_FILTRO_DE_RANGO and len(filtro.valores) != 2:
            raise HTTPException(status_code=400, detail="Este filtro necesita exactamente 2 valores (mínimo y máximo)")

        if not filtro.valores:
            raise HTTPException(status_code=400, detail="Un filtro no puede tener la lista de valores vacía")

        if filtro.conector not in CONECTORES_VALIDOS:
            raise HTTPException(status_code=400, detail=f"Conector no soportado: {filtro.conector}")

        # cojo la columna a la cual se aplica el filtro
        columna_filtro = columna_repo.get(filtro.columna_id)

        if columna_filtro is None or columna_filtro.archivo_id != archivo.id:
            raise HTTPException(status_code=404, detail="Una de las columnas de los filtros no es de este archivo")

        _validar_filtro_de_fecha(filtro.tipo_filtro, filtro.valores, columna_filtro)

        filtros_para_calculo.append({
            "posicion": columna_filtro.posicion,
            "tipo_filtro": filtro.tipo_filtro,
            "valores": filtro.valores,
            "conector": filtro.conector,
        })

    # CALCULO EL RESULTADO
    try:
        especificacion = generar_especificacion_grafico(ruta_archivo=archivo.ruta_almacenamiento,
                                        formato=archivo.formato,
                                        posicion_x=columna_x.posicion,
                                        posicion_y=columna_y.posicion if columna_y else None,
                                        operacion=datos.operacion_agregacion,
                                        filtros=filtros_para_calculo,
                                        tipo_grafico=datos.tipo_grafico,
                                        nombre_columna_x=columna_x.nombre_columna,
                                        nombre_columna_y=columna_y.nombre_columna if columna_y else None)

    except ValueError as e:
        # captura el "los filtros no dejan ninguna fila" del servicio de graficos
        raise HTTPException(status_code=400, detail=str(e))


    # GUARDO EL GRÁFICO
    grafico_repo = GraficoRepository(db)
    nuevo_grafico = grafico_repo.create(informe_id=informe.id,
                                        columna_x_id=datos.columna_x_id,
                                        columna_y_id=datos.columna_y_id,
                                        operacion_agregacion=datos.operacion_agregacion,
                                        tipo_grafico=datos.tipo_grafico,
                                        especificacion=especificacion,
                                        nombre=datos.nombre_grafico)

    # GUARDO LOS FILTROS
    # el id del gráfico ya existe porque en el create del repositorio de gráficos hago el flush

    filtro_repo = FiltroRepository(db)
    for filtro in datos.filtros:
        filtro_repo.create(grafico_id=nuevo_grafico.id,
                           columna_id=filtro.columna_id,
                           tipo_filtro=filtro.tipo_filtro,
                           valores=filtro.valores,
                           conector=filtro.conector)

    return nuevo_grafico


# endpoint que genera un grafico dentro de un informe
@router.post("/", response_model=GraficoGeneradoResponse)
def generar_grafico(informe_id: int, datos: GraficoCreadoRequest,
                    db: Session = Depends(get_db),
                    usuario_actual: Usuario = Depends(get_current_user)):

    # valido que el informe existe y que es del usuario logeado
    informe_repo = InformeRepository(db)
    informe = informe_repo.get(informe_id)
    if informe is None or informe.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    nuevo_grafico = crear_grafico(informe, datos, db)

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