
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.usuario import UsuarioCreateRequest, LoginRequest, UsuarioResponse, TokenResponse
from app.repositories.usuario_repository import UsuarioRepository
from app.security import hashear_contraseña, verificar_contraseña, crear_token_acceso
from fastapi.security import OAuth2PasswordRequestForm
from app.auth_dependency import get_current_user
from app.models.usuario import Usuario


router = APIRouter(prefix="/auth", tags=["Autenticación"])

# endpoint para registrar nuevo usuario
@router.post("/registro", response_model=UsuarioResponse)
def registrar_usuario(datos: UsuarioCreateRequest, db: Session = Depends(get_db)):
    
    usuario_repo = UsuarioRepository(db)
    
    # valido que el gmail no está ya en uso
    if usuario_repo.get_by_email(datos.email) is not None:
        raise HTTPException(status_code=400, detail="Este email ya registrado")
    
    # guardo la contraseña con su hash
    contraseña_hash = hashear_contraseña(datos.contraseña)
    
    # creo el usuario y lo devuelvo
    nuevo_usuario = usuario_repo.create(nombre=datos.nombre, email=datos.email, contraseña_hash=contraseña_hash)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    
    usuario_repo = UsuarioRepository(db)
    usuario = usuario_repo.get_by_email(form_data.username)
    
    # compruevo que el gmail y la contraseña sean los correctos
    if usuario is None or not verificar_contraseña(form_data.password, usuario.contraseña_hash):
        raise HTTPException(status_code=400, detail="Email o contraseña incorrectos")
    
    # si el gmail y la contraseña son correctos creo el token de acceso y lo devuelvo
    token = crear_token_acceso(usuario.id)
    return TokenResponse(access_token=token)



@router.get("/me", response_model=UsuarioResponse)
def obtener_usuario_actual(usuario_actual: Usuario = Depends(get_current_user)):
    return usuario_actual

    