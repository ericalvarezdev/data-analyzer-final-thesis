
from fastapi import FastAPI
from app.database import Base, engine
from app import models # ejecuta el __init__.py y registrará los modelos
from app.routers import archivo
from app.routers import grafico

# Crea la aplicación FastAPI con el título "Data_Analyzer", que aparecerá en la documentación
app = FastAPI(title="Data_Analyzer")


# Connecto todos los endpoints del router de archivo a la aplicación principal
app.include_router(archivo.router)
app.include_router(grafico.router)


@app.get("/")
def health_check():
    return {"status": "ok"}

