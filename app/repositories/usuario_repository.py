
from sqlalchemy.orm import Session
from app.models.usuario import Usuario

class UsuarioRepository:
    
    def __init__(self, db: Session) -> None:
        self.db = db
    
    
    # crea un usuario
    def create(self,nombre: str, email: str, contraseña_hash: str) -> Usuario:
        usuario = Usuario(nombre=nombre, email=email, contraseña_hash=contraseña_hash)
        
        self.db.add(usuario)
        self.db.flush()
        return usuario
    
    
    # busca un usuario por su id
    def get(self, usuario_id:int) -> Usuario | None:
        usuario = self.db.get(Usuario,usuario_id)
        return usuario
    
    # busca un usuario por su gmail
    def get_by_email(self, email:str) -> Usuario | None:
        usuario = self.db.query(Usuario).filter(Usuario.email == email).first()
        return usuario