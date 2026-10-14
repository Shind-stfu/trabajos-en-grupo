from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from backend.config import settings
from backend.database.connection import get_connection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(user_id: int, role: str) -> str:
    if not settings.jwt_secret or settings.jwt_secret.startswith("CAMBIAR"):
        raise RuntimeError("Configure JWT_SECRET en .env antes de iniciar sesion")
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": expire}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido o expirado", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub", "0"))
    except (JWTError, ValueError, TypeError):
        raise credentials_error
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""SELECT u.id_usuario, u.nombre, u.correo, u.id_rol, r.nombre, u.activo
                       FROM usuarios u JOIN roles r ON r.id_rol=u.id_rol WHERE u.id_usuario=:id""", {"id": user_id})
        row = cur.fetchone()
        if not row or row[5] != 1:
            raise credentials_error
        return {"id_usuario": row[0], "nombre": row[1], "correo": row[2], "id_rol": row[3], "rol": row[4]}
    finally:
        conn.close()


def require_admin(user=Depends(get_current_user)):
    if user["rol"] != "ADMINISTRADOR":
        raise HTTPException(status_code=403, detail="Se requiere rol ADMINISTRADOR")
    return user
