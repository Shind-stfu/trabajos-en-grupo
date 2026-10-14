from typing import Type
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import oracledb
from backend.database.connection import get_connection
from backend.security import get_current_user, require_admin
from backend.schemas.common import ProveedorIn, ProductoIn, ClienteIn

router = APIRouter(tags=["Catalogos"])

# Las tablas/columnas provienen de esta lista fija; nunca se toman identificadores SQL del usuario.
CONFIG = {
    "proveedores": {"table":"proveedores", "pk":"id_proveedor", "schema":ProveedorIn, "cols":["nombre","contacto","telefono","correo","direccion","activo"], "admin_delete":True},
    "productos": {"table":"productos", "pk":"id_producto", "schema":ProductoIn, "cols":["id_proveedor","nombre","descripcion","precio_compra","margen_porcentaje","existencia","activo"], "admin_delete":False},
    "clientes": {"table":"clientes", "pk":"id_cliente", "schema":ClienteIn, "cols":["nombre","telefono","correo","direccion"], "admin_delete":False},
}


def _create(resource: str, data: BaseModel):
    cfg=CONFIG[resource]; values=data.model_dump()
    if resource == "productos":
        values["precio_venta"] = round(values["precio_compra"] * (1 + values["margen_porcentaje"] / 100), 2)
        cfg_cols = cfg["cols"] + ["precio_venta"]
    else: cfg_cols=cfg["cols"]
    binds={col: values.get(col) for col in cfg_cols}
    names=", ".join(cfg_cols); placeholders=", ".join(':'+c for c in cfg_cols)
    conn=get_connection()
    try:
        cur=conn.cursor(); out=cur.var(oracledb.NUMBER)
        cur.execute(f"INSERT INTO {cfg['table']} ({names}) VALUES ({placeholders}) RETURNING {cfg['pk']} INTO :out_id", {**binds,"out_id":out})
        new_id=int(out.getvalue()[0]); conn.commit()
        return _get(resource,new_id)
    except oracledb.IntegrityError as exc:
        conn.rollback(); msg=str(exc)
        if "ORA-02291" in msg: raise HTTPException(400,"La referencia indicada no existe")
        raise HTTPException(409,"No se pudo crear el registro por una restriccion de integridad")
    except HTTPException: conn.rollback(); raise
    except Exception: conn.rollback(); raise HTTPException(500,"No fue posible crear el registro")
    finally: conn.close()


def _get(resource: str, item_id: int):
    cfg=CONFIG[resource]; conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute(f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']}=:id",{"id":item_id})
        row=cur.fetchone()
        if not row: raise HTTPException(404,"Registro no encontrado")
        return {d[0].lower():v for d,v in zip(cur.description,row)}
    finally: conn.close()


def _list(resource: str, q: str | None = None, activo: int | None = None):
    cfg=CONFIG[resource]; conn=get_connection()
    try:
        cur=conn.cursor(); sql=f"SELECT * FROM {cfg['table']} WHERE 1=1"; binds={}
        if q and resource in ("proveedores","productos","clientes"):
            column="nombre"; sql += f" AND LOWER({column}) LIKE LOWER(:q)"; binds["q"]="%"+q.strip()+"%"
        if activo is not None and "activo" in cfg["cols"]:
            sql += " AND activo=:activo"; binds["activo"]=activo
        sql += f" ORDER BY {cfg['pk']} DESC"
        cur.execute(sql,binds); names=[d[0].lower() for d in cur.description]
        return [dict(zip(names,row)) for row in cur.fetchall()]
    finally: conn.close()


def _update(resource: str, item_id: int, data: BaseModel):
    cfg=CONFIG[resource]; values=data.model_dump()
    if resource == "productos":
        values["precio_venta"] = round(values["precio_compra"] * (1 + values["margen_porcentaje"] / 100), 2)
        cols=cfg["cols"]+["precio_venta"]
    else: cols=cfg["cols"]
    binds={col:values.get(col) for col in cols}; binds["id"]=item_id
    assignments=", ".join(f"{col}=:{col}" for col in cols)
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute(f"UPDATE {cfg['table']} SET {assignments} WHERE {cfg['pk']}=:id",binds)
        if cur.rowcount==0: raise HTTPException(404,"Registro no encontrado")
        conn.commit(); return _get(resource,item_id)
    except HTTPException: conn.rollback(); raise
    except oracledb.IntegrityError: conn.rollback(); raise HTTPException(400,"No se puede actualizar: hay referencias invalidas")
    except Exception: conn.rollback(); raise HTTPException(500,"No fue posible actualizar el registro")
    finally: conn.close()


def _delete(resource: str, item_id: int):
    cfg=CONFIG[resource]; conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute(f"DELETE FROM {cfg['table']} WHERE {cfg['pk']}=:id",{"id":item_id})
        if cur.rowcount==0: raise HTTPException(404,"Registro no encontrado")
        conn.commit(); return {"mensaje":"Registro eliminado"}
    except HTTPException: conn.rollback(); raise
    except oracledb.IntegrityError: conn.rollback(); raise HTTPException(409,"No se puede eliminar: el registro esta relacionado con otros datos")
    except Exception: conn.rollback(); raise HTTPException(500,"No fue posible eliminar el registro")
    finally: conn.close()


def add_routes(resource: str, plural: str, schema: Type[BaseModel]):
    @router.get(f"/{plural}", name=f"listar_{plural}")
    def listar(q: str | None = Query(default=None, max_length=100), activo: int | None = Query(default=None, ge=0, le=1), user=Depends(get_current_user)):
        return _list(resource,q,activo)
    @router.get(f"/{plural}/{{item_id}}", name=f"obtener_{plural}")
    def obtener(item_id: int, user=Depends(get_current_user)):
        return _get(resource,item_id)
    @router.post(f"/{plural}", status_code=201, name=f"crear_{plural}")
    def crear(data: schema, user=Depends(get_current_user)):
        return _create(resource,data)
    @router.put(f"/{plural}/{{item_id}}", name=f"actualizar_{plural}")
    def actualizar(item_id: int, data: schema, user=Depends(get_current_user)):
        return _update(resource,item_id,data)
    @router.delete(f"/{plural}/{{item_id}}", name=f"eliminar_{plural}")
    def eliminar(item_id: int, user=Depends(require_admin)):
        return _delete(resource,item_id)

add_routes("proveedores","proveedores",ProveedorIn)
add_routes("productos","productos",ProductoIn)
add_routes("clientes","clientes",ClienteIn)
