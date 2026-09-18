
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import decodificar_token
from app.repositories.usuario_repository import UsuarioRepository
from app.models.usuario import Usuario

# Indica que el token JWT se enviará en el header Authorization y permite usarlo desde Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# cada vez que se ponga Depends(get_current_user) se obligará al usuario a estar logeado para seguir
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    
    usuario_id = decodificar_token(token)
    
    if usuario_id is None:
        raise HTTPException(status_code=401, detail="Token inválido o caducado")
    
    usuario_repo = UsuarioRepository(db)
    usuario = usuario_repo.get(usuario_id)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return usuario
    
    