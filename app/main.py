
from fastapi import FastAPI
from app.database import Base, engine
from app import models # ejecuta el __init__.py y registrará los modelos
from app.routers import archivo, grafico, auth, informe

from fastapi.middleware.cors import CORSMiddleware

# Crea la aplicación FastAPI con el título "Data_Analyzer", que aparecerá en la documentación
app = FastAPI(title="Data_Analyzer")



# Le digo a FastAPI que acepte peticiones desde el frontend en http://localhost:5173
# sino el navegador bloquearia la respuesta antes de que React la reciba
app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:5173"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"]
)





# Connecto todos los endpoints del router de archivo a la aplicación principal
app.include_router(auth.router)
app.include_router(archivo.router)
app.include_router(informe.router)
app.include_router(informe.router_informes)
app.include_router(grafico.router)


@app.get("/")
def health_check():
    return {"status": "ok"}

