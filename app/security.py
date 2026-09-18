
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from app.config import settings


# CryptContext es el motor que sabe como convertir contraseñas en texto plano a hash
# también sabe como comparar una contraseña con texto plano con un hash ya guardado
# guardo el CryptContext en la variable pwd_context
# schemes=["bcrypt"] indica que se usará bcrypt para hashear las contraseñas
# deprecated="auto" gestiona automáticamente qué métodos para hashear están obsoletos
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# convierte una contraseña en texto plano en un hash
def hashear_contraseña(contraseña_plana: str) -> str:
    return pwd_context.hash(contraseña_plana)


# comprueba si una contraseña en texto plano coincide con un hash guardado
def verificar_contraseña(contraseña_plana: str, contraseña_hash: str) -> bool:
    return pwd_context.verify(contraseña_plana, contraseña_hash)


# crea un jwt que representa que este usuario está logueado
# el token contiene el id del usuario y una fecha de caducidad todo firmado con la clave secreta
def crear_token_acceso(usuario_id: int) -> str:
    expiracion = datetime.utcnow() + timedelta(minutes=settings.token_expira_minutos)
    
    # "sub" (subject) es el campo estandar para identificar de quien es el token
    datos={"sub": str(usuario_id), "exp": expiracion}
    
    # convierte los datos en un JWT usando la clave secreta y el algoritmo indicado
    return jwt.encode(datos, key=settings.secret_key, algorithm=settings.algorithm)


# verifica un token y devuelve el id del usuario o none si no lo verifica
def decodificar_token(token: str) -> int|None:
    try:
        payload = jwt.decode(token=token, key=settings.secret_key, algorithms=[settings.algorithm])
        return int(payload.get("sub"))
    except jwt.JWTError: # si ocurre un error relacionado con el JWT entra aqui
        return None
    
    

