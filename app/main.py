
from fastapi import FastAPI
from app.database import Base, engine
from app import models # ejecutará el __init__.py y registrará los modelos

# Crea la aplicación FastAPI con el título "Data_Analyzer", que aparecerá en la documentación
app = FastAPI(title="Data_Analyzer")

# Crea todas las tablas de la base de datos a partir de todos los modelos que hereden de Base
# Si las tablas ya existen no hace nada (no las borra ni las duplica)
Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {"status": "ok"}

