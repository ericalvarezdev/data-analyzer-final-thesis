from pydantic_settings import BaseSettings

# Sirve para separar la configuración del código: puedo cambiar valores
# desde el .env sin modificar el código porque este obtiene los valores desde Settings
class Settings(BaseSettings):

    database_url: str = "sqlite:///./data_analyzer.db"
    upload_dir: str = "uploads"
    formatos_permitidos: set[str] = {"csv", "xlsx"}
    tamaño_maximo_mb: int = 10
    
    # Para JWT
    secret_key: str = "a8Kx92LmQp7Vz4NtR6Yw3Hs9Df1Jk5Pc" # clave secreta que firma los tokens
    algorithm: str = "HS256" # utilizare el algoritmo HS256 para hashear
    token_expira_minutos: int = 60 * 24 # el token dura 24 horas antes de expirarse

    class Config:
        env_file = ".env"  # si existe un archivo .env, lee los valores de ahí






# Creo una única instancia, reutilizada en todo el proyecto
settings = Settings()