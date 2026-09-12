from pydantic_settings import BaseSettings

# Sirve para separar la configuración del código: puedo cambiar valores
# desde el .env sin modificar el código porque este obtiene los valores desde Settings
class Settings(BaseSettings):

    database_url: str = "sqlite:///./data_analyzer.db"
    upload_dir: str = "uploads"
    formatos_permitidos: set[str] = {"csv", "xlsx"}
    tamaño_maximo_mb: int = 10

    class Config:
        env_file = ".env"  # si existe un archivo .env, lee los valores de ahí


# Creo una única instancia, reutilizada en todo el proyecto
settings = Settings()