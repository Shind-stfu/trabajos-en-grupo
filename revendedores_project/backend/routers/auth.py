from fastapi import APIRouter, HTTPException, Depends
from backend.database.connection import get_connection
from backend.schemas.common import LoginIn, RegisterIn
from backend.security import hash_password, verify_password, create_access_token, get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["Autenticacion"])

@router.post("/register", status_code=201)
def register(data: RegisterIn):
    """Crea una cuenta de vendedor. Para crear administradores, use el flujo de provision inicial."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_rol FROM roles WHERE nombre='VENDEDOR'")
        role = cur.fetchone()
        if not role:
            raise HTTPException(500, "Falta el rol VENDEDOR. Ejecute database/03_data.sql")
        cur.execute("SELECT 1 FROM usuarios WHERE LOWER(correo)=LOWER(:correo)", {"correo": data.correo})
        if cur.fetchone():
            raise HTTPException(409, "Ya existe un usuario con ese correo")
        out_id = cur.var(int)
        cur.execute("""INSERT INTO usuarios (id_rol,nombre,correo,hash_contrasena,activo)
                       VALUES (:rol,:nombre,LOWER(:correo),:hash,1) RETURNING id_usuario INTO :new_id""",
                    {"rol": role[0], "nombre": data.nombre.strip(), "correo": data.correo,
                     "hash": hash_password(data.contrasena), "new_id": out_id})
        user_id = out_id.getvalue()[0]
        conn.commit()
        return {"id_usuario": user_id, "nombre": data.nombre.strip(), "correo": data.correo, "rol": "VENDEDOR"}
    except HTTPException:
        conn.rollback(); raise
    except Exception as exc:
        conn.rollback()
        if "ORA-00001" in str(exc):
            raise HTTPException(409, "El correo ya esta registrado")
        raise HTTPException(500, "No fue posible registrar el usuario")
    finally:
        conn.close()

@router.post("/login")
def login(data: LoginIn):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""SELECT u.id_usuario,u.nombre,u.correo,u.hash_contrasena,u.activo,r.nombre
                       FROM usuarios u JOIN roles r ON r.id_rol=u.id_rol
                       WHERE LOWER(u.correo)=LOWER(:correo)""", {"correo": data.correo})
        row = cur.fetchone()
        if not row or row[4] != 1 or not verify_password(data.contrasena, row[3]):
            raise HTTPException(401, "Correo o contrasena incorrectos")
        token = create_access_token(row[0], row[5])
        return {"access_token": token, "token_type": "bearer", "usuario": {"id_usuario": row[0], "nombre": row[1], "correo": row[2], "rol": row[5]}}
    finally:
        conn.close()

@router.get("/me")
def me(user=Depends(get_current_user)):
    return user

@router.post("/admin/usuarios", status_code=201)
def crear_usuario_admin(data: RegisterIn, admin=Depends(require_admin)):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_rol FROM roles WHERE nombre='VENDEDOR'")
        vendedor = cur.fetchone()
        cur.execute("SELECT 1 FROM usuarios WHERE LOWER(correo)=LOWER(:correo)", {"correo": data.correo})
        if cur.fetchone(): raise HTTPException(409, "Correo ya registrado")
        out_id = cur.var(int)
        cur.execute("INSERT INTO usuarios(id_rol,nombre,correo,hash_contrasena,activo) VALUES(:rol,:nombre,LOWER(:correo),:hash,1) RETURNING id_usuario INTO :out_id",
                    {"rol": vendedor[0], "nombre": data.nombre.strip(), "correo": data.correo, "hash": hash_password(data.contrasena), "out_id": out_id})
        new_id = out_id.getvalue()[0]
        conn.commit()
        return {"id_usuario": new_id, "nombre": data.nombre, "correo": data.correo, "rol": "VENDEDOR"}
    except HTTPException:
        conn.rollback(); raise
    except Exception:
        conn.rollback(); raise HTTPException(500, "No fue posible crear el usuario")
    finally: conn.close()

@router.get("/usuarios")
def listar_usuarios(admin=Depends(require_admin)):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT u.id_usuario,u.nombre,u.correo,r.nombre AS rol,u.activo,u.creado_en FROM usuarios u JOIN roles r ON r.id_rol=u.id_rol ORDER BY u.id_usuario")
        names = [d[0].lower() for d in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]
    finally:
        conn.close()

@router.put("/usuarios/{user_id}/estado")
def cambiar_estado_usuario(user_id: int, activo: int, admin=Depends(require_admin)):
    if activo not in (0, 1):
        raise HTTPException(400, "activo debe ser 0 o 1")
    if user_id == admin["id_usuario"] and activo == 0:
        raise HTTPException(400, "No puedes desactivar tu propia cuenta")
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET activo=:activo WHERE id_usuario=:id", {"activo": activo, "id": user_id})
        if cur.rowcount == 0:
            raise HTTPException(404, "Usuario no encontrado")
        conn.commit()
        return {"mensaje": "Estado actualizado", "id_usuario": user_id, "activo": activo}
    except HTTPException:
        conn.rollback(); raise
    finally:
        conn.close()

@router.get("/roles")
def listar_roles(admin=Depends(require_admin)):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_rol,nombre,descripcion FROM roles ORDER BY id_rol")
        names = [d[0].lower() for d in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]
    finally:
        conn.close()
