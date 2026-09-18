
from re import S

from pydantic import BaseModel, EmailStr
from datetime import datetime

# lo que el usuario debe mandar al registrarse
class UsuarioCreateRequest(BaseModel):
    nombre: str
    email: EmailStr # EmailStr valida automáticamente que el formato sea un email real
    contraseña: str
    

# lo que el usuario debe mandar al hacer el login
class LoginRequest(BaseModel):
    email: EmailStr
    contraseña: str
    

# lo que devuelve la API sobre el usuario
class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str
    fecha_registro: datetime
    
    class Config:
        from_attributes = True

   
# lo que devuelve el endpoint de login
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer" # bearer indica que quien tenga el access_token puede utilizarlo para autenticarse
    