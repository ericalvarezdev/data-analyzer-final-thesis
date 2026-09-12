import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.archivo_subido import ArchivoSubido
from app.schemas.archivo import ArchivoSubidoResponse
from app.services.procesamiento import leer_archivo, analizar_columnas
from app.repositories.archivo_repository import ArchivoRepository
from app.config import settings

router = APIRouter(prefix="/archivos", tags=["archivos"])



# enpoint para subir un archivo
@router.post("/", response_model=ArchivoSubidoResponse)
def subir_archivo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    
    # VALIDAMOS EL FORMATO DEL ARCHIVO
    extension = file.filename.split(".")[-1].lower() # El -1 significa coger el último elemento de la lista que devuelve split()
    if extension not in settings.formatos_permitidos:
        raise HTTPException(status_code=400, detail="Formato de archivo no permitido")
    
    # GUARDO EL ARCHIVO FÍSICAMENTE EN EL DISCO
    ruta_destino = f"{settings.upload_dir}/{file.filename}"
    os.makedirs(settings.upload_dir, exist_ok=True) # Si no existe la carpeta uploads la crea, exist_ok hace que no de error si ya existe
    with open(ruta_destino, "wb") as buffer: # crea/abre el archivo vacío en esa ruta, "wb" es para que se pueda escribir en el
        shutil.copyfileobj(file.file, buffer) # copia el archivo subido por el usuario (file.file) al archivo vacío "buffer"
        
    # VALIDO EL TAMAÑO DEL ARCHIVO
    tamaño_bytes = os.path.getsize(ruta_destino)
    if tamaño_bytes > settings.tamaño_maximo_mb * 1024 * 1024:
        os.remove(ruta_destino) # Borramos el archivo guardado anteriormente
        raise HTTPException(status_code=400, detail="El archivo supera el tamaño máximo permitido")
    
    # GUARDO EL ARCHIVO EN LA BASE DE DATOS (EN "PROCESAMIENTO")
    archivo_repo = ArchivoRepository(db)
    nuevo_archivo = archivo_repo.create(nombre_archivo=file.filename, ruta_almacenamiento=ruta_destino,
                        formato=extension, tamaño=tamaño_bytes)
    db.commit() # Lo guardamos en la base de datos y generamos el id
    
    # PROCESO EL ARCHVIO CON PANDAS
    try:
       df = leer_archivo(ruta_destino, extension)
       # Calcula estadísticas y guarda todas las columnas en la base de datos
       analizar_columnas(df,nuevo_archivo.id,db)
       
       nuevo_archivo = archivo_repo.marcar_completado(nuevo_archivo, numero_filas=len(df),
                                                      numero_columnas=len(df.columns))
    
    except Exception as e:
        # Aunque entre al except luego hará el commit y el return ya que dentro del except no hay return ni raise
        nuevo_archivo = archivo_repo.marcar_error(nuevo_archivo, mensaje_error=str(e))
    
    # Guardamos en la base de datos el archivo
    db.commit()
    
    # Para asegurarnos que nuevo_archivo tiene los valores más actualizados antes de devolverlo
    db.refresh(nuevo_archivo)
    
    return nuevo_archivo


# endpoint para obtener las datos de un archivo subido (no es la previsualización del archivo)
@router.get("/{archivo_id}", response_model=ArchivoSubidoResponse)
def obtener_archivo(archivo_id: int, db: Session = Depends(get_db)):
    archivo_repo = ArchivoRepository(db)
    archivo = archivo_repo.get(archivo_id)
    
    if archivo is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return archivo


# devuelve la lista de archivos de toda la base de datos, más adelante solo devolverá del usuario
@router.get("/", response_model=list[ArchivoSubidoResponse]|None)
def listar_archivos(db: Session = Depends(get_db)):
    archivo_repo = ArchivoRepository(db)
    list_archivos = archivo_repo.list_all()
    return list_archivos


# endpoint para previsualizar las x filas que elija el usuario (por defecto 10)
@router.get("/{archivo_id}/preview")
def previsualizar_archivo(archivo_id: int, filas: int = 10, db: Session = Depends(get_db)):
    
    archivo_repo = ArchivoRepository(db)
    archivo = archivo_repo.get(archivo_id)
    
    # Si el archivo no existe devolvemos un error
    if archivo is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Transformo el archivo en un dataframe
    df = leer_archivo(archivo.ruta_almacenamiento, archivo.formato)
    
    
    # .head(filas) coge solo las primeras N filas (por defecto 10)
    # .fillna("") sustituye los valores vacíos (NaN) por texto vacío, porque
    # NaN no se puede convertir directamente a JSON (daría error)
    # .to_dict(orient="records") convierte cada dila en un diccionario y cada columna 
    # en una clave de ese diccionario
    primeras_filas = df.head(filas).fillna("").to_dict(orient="records")
    
    return {
        "columnas": list(df.columns),
        "filas": primeras_filas,
    }
    
    """
    queda asi en JSON:
        {
        "columnas": ["nombre", "edad"],
        "filas": [
            {"nombre": "Eric", "edad": 24},
            {"nombre": "Ana", "edad": 22}
        ]
        }
    """


# endpoint que borra un archivo, y todos sus graficos y columnas (en cascada) por id de archivo
@router.delete("/{archivo_id}", status_code=204)
def borrar_archivo(archivo_id: int, db: Session = Depends(get_db)):
    archivo_repo = ArchivoRepository(db)
    archivo = archivo_repo.get(archivo_id)
    
    if archivo is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # borro el archivo físico del disco
    if os.path.exists(archivo.ruta_almacenamiento):
        os.remove(archivo.ruta_almacenamiento)
    
    archivo_repo.delete(archivo)
    db.commit()


    