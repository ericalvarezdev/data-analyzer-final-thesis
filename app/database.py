from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings


# URL de connexión a la base de datos
SQLALCHEMY_DATABASE_URL = settings.database_url

# engine es la connexión real entre el código de python y la base de datos
# el objeto engine se encargará de hablar con SQLite/Postgres
# connect_args={"check_same_thread": False} restricción para que funcione con SQLite
# Para postgres no hará falta esa restricción
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})



# SessionLocal funciona como una fábrica de sessiones (cada vez que se necesite acceder
# a la base de datos para leer, guardar, actualizar y luego cerrar la sessión) se creará 
# una nueva sessión a partir de SessionLocal

# autocommit=False hace que los cambios no se guarden automáticamente y haya que confirmarlos
# con commit
# autoflush=False evita que se envíen cambios a la base de datos sin pedirlo explicitamente
# bind=engine le dice a la fábrica de sessiones SessionLocal que use la connexión engine
# creada arriba
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es una classe especial que la heredan todos los modelos (columna, archivo_subido, etc.).
# Gracias a heredar de Base sabe que esas classes representan tablas de la base de datos,
# y puede encargarse de crearlas, relacionarlas entre sí, etc.
Base = declarative_base()


# Esta función se usa para abrir y cerrar sesiones en la base de datos en los endpoints
def get_db():
    db = SessionLocal()
    
    try:
        yield db # abre la sessión y la deja abierta hasta llegar al finally
    finally:
        db.close() # cierra la sessión siempre, incluso si hay un error
        
