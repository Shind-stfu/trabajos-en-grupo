from fastapi import APIRouter, Depends, HTTPException, Query
import oracledb
from backend.database.connection import get_connection
from backend.schemas.common import PedidoIn, DetallePedidoIn
from backend.security import get_current_user, require_admin

router = APIRouter(tags=["Pedidos"])

@router.get("/pedidos")
def listar_pedidos(estado: str | None = Query(default=None), id_cliente: int | None = Query(default=None, gt=0), user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); sql="""SELECT p.id_pedido,p.id_cliente,c.nombre AS cliente,p.id_usuario,u.nombre AS vendedor,
                 p.fecha_pedido,p.estado,p.observaciones,
                 NVL((SELECT SUM(d.cantidad*d.precio_unitario) FROM detalle_pedido d WHERE d.id_pedido=p.id_pedido),0) total
                 FROM pedidos p JOIN clientes c ON c.id_cliente=p.id_cliente JOIN usuarios u ON u.id_usuario=p.id_usuario WHERE 1=1"""
        binds={}
        if estado:
            estado=estado.upper()
            if estado not in {'PENDIENTE','CONFIRMADO','ENVIADO','ENTREGADO','CANCELADO'}: raise HTTPException(400,"Estado no valido")
            sql += " AND p.estado=:estado"; binds['estado']=estado
        if id_cliente: sql += " AND p.id_cliente=:id_cliente"; binds['id_cliente']=id_cliente
        if user['rol']!='ADMINISTRADOR': sql += " AND p.id_usuario=:usuario"; binds['usuario']=user['id_usuario']
        sql += " ORDER BY p.fecha_pedido DESC"
        cur.execute(sql,binds); names=[d[0].lower() for d in cur.description]
        return [dict(zip(names,row)) for row in cur.fetchall()]
    finally: conn.close()

@router.get('/pedidos/{item_id}')
def obtener_pedido(item_id:int,user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("""SELECT p.id_pedido,p.id_cliente,c.nombre,p.id_usuario,p.fecha_pedido,p.estado,p.observaciones,
            NVL((SELECT SUM(d.cantidad*d.precio_unitario) FROM detalle_pedido d WHERE d.id_pedido=p.id_pedido),0) total
            FROM pedidos p JOIN clientes c ON c.id_cliente=p.id_cliente WHERE p.id_pedido=:id""",{'id':item_id})
        row=cur.fetchone()
        if not row: raise HTTPException(404,"Pedido no encontrado")
        if user['rol']!='ADMINISTRADOR' and row[3]!=user['id_usuario']: raise HTTPException(403,"No puedes consultar este pedido")
        result={d[0].lower():v for d,v in zip(cur.description,row)}
        cur.execute("SELECT id_detalle,id_producto,cantidad,precio_unitario,cantidad*precio_unitario subtotal FROM detalle_pedido WHERE id_pedido=:id ORDER BY id_detalle",{'id':item_id})
        names=[d[0].lower() for d in cur.description]; result['detalles']=[dict(zip(names,r)) for r in cur.fetchall()]
        cur.execute("SELECT id_pago,monto,metodo,fecha_pago,referencia,estado FROM pagos WHERE id_pedido=:id ORDER BY fecha_pago",{'id':item_id})
        names=[d[0].lower() for d in cur.description]; result['pagos']=[dict(zip(names,r)) for r in cur.fetchall()]
        return result
    finally: conn.close()

@router.post('/pedidos',status_code=201)
def crear_pedido(data:PedidoIn,user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); out=cur.var(oracledb.NUMBER)
        cur.execute("INSERT INTO pedidos(id_cliente,id_usuario,estado,observaciones) VALUES(:cliente,:usuario,:estado,:obs) RETURNING id_pedido INTO :out_id",
          {'cliente':data.id_cliente,'usuario':user['id_usuario'],'estado':data.estado,'obs':data.observaciones,'out_id':out})
        item_id=int(out.getvalue()[0]); conn.commit(); return obtener_pedido(item_id,user)
    except HTTPException: conn.rollback(); raise
    except oracledb.IntegrityError: conn.rollback(); raise HTTPException(400,"El cliente indicado no existe")
    except Exception: conn.rollback(); raise HTTPException(500,"No fue posible crear el pedido")
    finally: conn.close()

@router.put('/pedidos/{item_id}')
def actualizar_pedido(item_id:int,data:PedidoIn,user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("SELECT id_usuario FROM pedidos WHERE id_pedido=:id",{'id':item_id}); owner=cur.fetchone()
        if not owner: raise HTTPException(404,"Pedido no encontrado")
        if user['rol']!='ADMINISTRADOR' and owner[0]!=user['id_usuario']: raise HTTPException(403,"No puedes modificar este pedido")
        cur.execute("UPDATE pedidos SET id_cliente=:cliente,estado=:estado,observaciones=:obs WHERE id_pedido=:id",
          {'cliente':data.id_cliente,'estado':data.estado,'obs':data.observaciones,'id':item_id})
        conn.commit(); return obtener_pedido(item_id,user)
    except HTTPException: conn.rollback(); raise
    except oracledb.IntegrityError: conn.rollback(); raise HTTPException(400,"El cliente indicado no existe")
    except Exception: conn.rollback(); raise HTTPException(500,"No fue posible actualizar el pedido")
    finally: conn.close()

@router.delete('/pedidos/{item_id}')
def eliminar_pedido(item_id:int,user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("SELECT id_usuario FROM pedidos WHERE id_pedido=:id",{'id':item_id}); owner=cur.fetchone()
        if not owner: raise HTTPException(404,"Pedido no encontrado")
        if user['rol']!='ADMINISTRADOR' and owner[0]!=user['id_usuario']: raise HTTPException(403,"No puedes eliminar este pedido")
        cur.execute("DELETE FROM pedidos WHERE id_pedido=:id",{'id':item_id}); conn.commit(); return {'mensaje':'Pedido eliminado'}
    except HTTPException: conn.rollback(); raise
    except oracledb.IntegrityError: conn.rollback(); raise HTTPException(409,"No se puede eliminar el pedido: puede tener pagos asociados")
    except Exception: conn.rollback(); raise HTTPException(500,"No fue posible eliminar el pedido")
    finally: conn.close()

@router.get('/detalle-pedidos')
def listar_detalles(id_pedido:int|None=Query(default=None,gt=0),user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); sql="""SELECT d.id_detalle,d.id_pedido,d.id_producto,p.nombre AS producto,d.cantidad,d.precio_unitario,
          d.cantidad*d.precio_unitario AS subtotal, pe.id_usuario FROM detalle_pedido d JOIN productos p ON p.id_producto=d.id_producto
          JOIN pedidos pe ON pe.id_pedido=d.id_pedido WHERE 1=1"""; binds={}
        if id_pedido: sql+=" AND d.id_pedido=:pedido"; binds['pedido']=id_pedido
        if user['rol']!='ADMINISTRADOR': sql+=" AND pe.id_usuario=:usuario"; binds['usuario']=user['id_usuario']
        sql+=" ORDER BY d.id_detalle DESC"; cur.execute(sql,binds); names=[d[0].lower() for d in cur.description]
        return [dict(zip(names,row)) for row in cur.fetchall()]
    finally: conn.close()

@router.post('/detalle-pedidos',status_code=201)
def crear_detalle(data:DetallePedidoIn,user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("SELECT id_usuario,estado FROM pedidos WHERE id_pedido=:id",{'id':data.id_pedido}); pedido=cur.fetchone()
        if not pedido: raise HTTPException(404,"Pedido no encontrado")
        if user['rol']!='ADMINISTRADOR' and pedido[0]!=user['id_usuario']: raise HTTPException(403,"No puedes modificar este pedido")
        if pedido[1] in ('CANCELADO','ENTREGADO'): raise HTTPException(400,"No se pueden agregar productos a un pedido cancelado o entregado")
        cur.execute("SELECT precio_venta,existencia,activo FROM productos WHERE id_producto=:id",{'id':data.id_producto}); prod=cur.fetchone()
        if not prod or prod[2]!=1: raise HTTPException(404,"Producto no encontrado o inactivo")
        if data.precio_unitario is not None and data.precio_unitario != float(prod[0]) and user['rol']!='ADMINISTRADOR':
            raise HTTPException(403,"Solo un administrador puede cambiar el precio unitario aplicado")
        price=float(prod[0]) if data.precio_unitario is None else data.precio_unitario
        out=cur.var(oracledb.NUMBER)
        cur.execute("INSERT INTO detalle_pedido(id_pedido,id_producto,cantidad,precio_unitario) VALUES(:pedido,:producto,:cantidad,:precio) RETURNING id_detalle INTO :out_id",
          {'pedido':data.id_pedido,'producto':data.id_producto,'cantidad':data.cantidad,'precio':price,'out_id':out})
        item_id=int(out.getvalue()[0])
        conn.commit(); return {'id_detalle':item_id,'id_pedido':data.id_pedido,'id_producto':data.id_producto,'cantidad':data.cantidad,'precio_unitario':price,'subtotal':round(data.cantidad*price,2)}
    except HTTPException: conn.rollback(); raise
    except oracledb.IntegrityError as exc:
        conn.rollback()
        if 'ORA-00001' in str(exc): raise HTTPException(409,"Ese producto ya esta en el detalle del pedido")
        raise HTTPException(400,"No se pudo agregar el producto; revise las referencias")
    except Exception: conn.rollback(); raise HTTPException(500,"No fue posible agregar el detalle")
    finally: conn.close()

@router.put('/detalle-pedidos/{item_id}')
def actualizar_detalle(item_id:int,data:DetallePedidoIn,user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("SELECT p.id_usuario,p.estado FROM detalle_pedido d JOIN pedidos p ON p.id_pedido=d.id_pedido WHERE d.id_detalle=:id",{'id':item_id}); owner=cur.fetchone()
        if not owner: raise HTTPException(404,"Detalle no encontrado")
        if user['rol']!='ADMINISTRADOR' and owner[0]!=user['id_usuario']: raise HTTPException(403,"No puedes modificar este detalle")
        if owner[1] in ('CANCELADO','ENTREGADO'): raise HTTPException(400,"El pedido no admite modificaciones")
        cur.execute("SELECT id_usuario,estado FROM pedidos WHERE id_pedido=:id",{'id':data.id_pedido}); target_order=cur.fetchone()
        if not target_order: raise HTTPException(404,"Pedido destino no encontrado")
        if user['rol']!='ADMINISTRADOR' and target_order[0]!=user['id_usuario']: raise HTTPException(403,"No puedes mover el detalle a un pedido de otro vendedor")
        cur.execute("SELECT precio_venta FROM productos WHERE id_producto=:id",{'id':data.id_producto}); prod=cur.fetchone()
        if not prod: raise HTTPException(404,"Producto no encontrado")
        price=float(prod[0]) if data.precio_unitario is None else data.precio_unitario
        if user['rol']!='ADMINISTRADOR' and price!=float(prod[0]): raise HTTPException(403,"Solo un administrador puede cambiar el precio")
        cur.execute("UPDATE detalle_pedido SET id_pedido=:pedido,id_producto=:producto,cantidad=:cantidad,precio_unitario=:precio WHERE id_detalle=:id",
          {'pedido':data.id_pedido,'producto':data.id_producto,'cantidad':data.cantidad,'precio':price,'id':item_id})
        conn.commit(); return {'mensaje':'Detalle actualizado','id_detalle':item_id,'subtotal':round(data.cantidad*price,2)}
    except HTTPException: conn.rollback(); raise
    except oracledb.IntegrityError: conn.rollback(); raise HTTPException(400,"Revise el pedido, producto y duplicados")
    except Exception: conn.rollback(); raise HTTPException(500,"No fue posible actualizar el detalle")
    finally: conn.close()

@router.delete('/detalle-pedidos/{item_id}')
def eliminar_detalle(item_id:int,user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("SELECT p.id_usuario,p.estado FROM detalle_pedido d JOIN pedidos p ON p.id_pedido=d.id_pedido WHERE d.id_detalle=:id",{'id':item_id}); owner=cur.fetchone()
        if not owner: raise HTTPException(404,"Detalle no encontrado")
        if user['rol']!='ADMINISTRADOR' and owner[0]!=user['id_usuario']: raise HTTPException(403,"No puedes modificar este detalle")
        if owner[1] in ('CANCELADO','ENTREGADO'): raise HTTPException(400,"El pedido no admite modificaciones")
        cur.execute("DELETE FROM detalle_pedido WHERE id_detalle=:id",{'id':item_id}); conn.commit(); return {'mensaje':'Detalle eliminado'}
    except HTTPException: conn.rollback(); raise
    except Exception: conn.rollback(); raise HTTPException(500,"No fue posible eliminar el detalle")
    finally: conn.close()
