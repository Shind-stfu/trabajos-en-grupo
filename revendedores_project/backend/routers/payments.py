from fastapi import APIRouter, Depends, HTTPException, Query
import oracledb
from backend.database.connection import get_connection
from backend.schemas.common import PagoIn
from backend.security import get_current_user, require_admin

router=APIRouter(tags=["Pagos"])

@router.get('/pagos')
def listar_pagos(id_pedido:int|None=Query(default=None,gt=0),estado:str|None=None,user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); sql="""SELECT pa.id_pago,pa.id_pedido,pa.monto,pa.metodo,pa.fecha_pago,pa.referencia,pa.estado,p.id_usuario
          FROM pagos pa JOIN pedidos p ON p.id_pedido=pa.id_pedido WHERE 1=1"""; binds={}
        if id_pedido: sql+=" AND pa.id_pedido=:pedido"; binds['pedido']=id_pedido
        if estado:
            estado=estado.upper()
            if estado not in ('REGISTRADO','ANULADO'): raise HTTPException(400,'Estado de pago no valido')
            sql+=" AND pa.estado=:estado"; binds['estado']=estado
        if user['rol']!='ADMINISTRADOR': sql+=" AND p.id_usuario=:usuario"; binds['usuario']=user['id_usuario']
        sql+=" ORDER BY pa.fecha_pago DESC"; cur.execute(sql,binds); names=[d[0].lower() for d in cur.description]
        return [dict(zip(names,row)) for row in cur.fetchall()]
    finally: conn.close()

@router.post('/pagos',status_code=201)
def crear_pago(data:PagoIn,user=Depends(get_current_user)):
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("SELECT id_usuario,estado FROM pedidos WHERE id_pedido=:id",{'id':data.id_pedido}); pedido=cur.fetchone()
        if not pedido: raise HTTPException(404,'Pedido no encontrado')
        if user['rol']!='ADMINISTRADOR' and pedido[0]!=user['id_usuario']: raise HTTPException(403,'No puedes registrar pagos de este pedido')
        if pedido[1]=='CANCELADO': raise HTTPException(400,'No se puede pagar un pedido cancelado')
        cur.execute("SELECT NVL(SUM(cantidad*precio_unitario),0) FROM detalle_pedido WHERE id_pedido=:id",{'id':data.id_pedido}); total=float(cur.fetchone()[0])
        cur.execute("SELECT NVL(SUM(monto),0) FROM pagos WHERE id_pedido=:id AND estado='REGISTRADO'",{'id':data.id_pedido}); pagado=float(cur.fetchone()[0])
        if total<=0: raise HTTPException(400,'Agregue productos al pedido antes de registrar pagos')
        if data.estado=='REGISTRADO' and round(pagado+data.monto,2)>round(total,2): raise HTTPException(400,'El pago supera el saldo pendiente del pedido')
        out=cur.var(oracledb.NUMBER)
        cur.execute("INSERT INTO pagos(id_pedido,monto,metodo,referencia,estado) VALUES(:pedido,:monto,:metodo,:ref,:estado) RETURNING id_pago INTO :out_id",
          {'pedido':data.id_pedido,'monto':data.monto,'metodo':data.metodo,'ref':data.referencia,'estado':data.estado,'out_id':out})
        payment_id=int(out.getvalue()[0]); conn.commit()
        return {'id_pago':payment_id,'id_pedido':data.id_pedido,'monto':data.monto,'metodo':data.metodo,'estado':data.estado,'total_pedido':total,'total_pagado':pagado+(data.monto if data.estado=='REGISTRADO' else 0)}
    except HTTPException: conn.rollback(); raise
    except oracledb.IntegrityError: conn.rollback(); raise HTTPException(400,'Revise los datos del pago')
    except Exception: conn.rollback(); raise HTTPException(500,'No fue posible registrar el pago')
    finally: conn.close()

@router.put('/pagos/{item_id}')
def actualizar_pago(item_id:int,data:PagoIn,user=Depends(require_admin)):
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("SELECT id_pago FROM pagos WHERE id_pago=:id",{'id':item_id})
        if not cur.fetchone(): raise HTTPException(404,'Pago no encontrado')
        cur.execute("SELECT NVL(SUM(cantidad*precio_unitario),0) FROM detalle_pedido WHERE id_pedido=:id",{'id':data.id_pedido}); total=float(cur.fetchone()[0])
        cur.execute("SELECT NVL(SUM(monto),0) FROM pagos WHERE id_pedido=:id AND estado='REGISTRADO' AND id_pago<>:pago",{'id':data.id_pedido,'pago':item_id}); other=float(cur.fetchone()[0])
        if data.estado=='REGISTRADO' and other+data.monto>total: raise HTTPException(400,'El pago supera el saldo pendiente')
        cur.execute("UPDATE pagos SET id_pedido=:pedido,monto=:monto,metodo=:metodo,referencia=:ref,estado=:estado WHERE id_pago=:id",
          {'pedido':data.id_pedido,'monto':data.monto,'metodo':data.metodo,'ref':data.referencia,'estado':data.estado,'id':item_id})
        conn.commit(); return {'mensaje':'Pago actualizado','id_pago':item_id}
    except HTTPException: conn.rollback(); raise
    except Exception: conn.rollback(); raise HTTPException(500,'No fue posible actualizar el pago')
    finally: conn.close()

@router.delete('/pagos/{item_id}')
def anular_pago(item_id:int,user=Depends(require_admin)):
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("UPDATE pagos SET estado='ANULADO' WHERE id_pago=:id",{'id':item_id})
        if cur.rowcount==0: raise HTTPException(404,'Pago no encontrado')
        conn.commit(); return {'mensaje':'Pago anulado'}
    except HTTPException: conn.rollback(); raise
    except Exception: conn.rollback(); raise HTTPException(500,'No fue posible anular el pago')
    finally: conn.close()
