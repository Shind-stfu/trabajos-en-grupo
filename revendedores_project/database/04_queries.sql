-- Total de cada pedido
SELECT p.id_pedido, c.nombre AS cliente, p.fecha_pedido, p.estado,
       NVL(SUM(dp.cantidad * dp.precio_unitario), 0) AS total_pedido
FROM pedidos p
JOIN clientes c ON c.id_cliente = p.id_cliente
LEFT JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
GROUP BY p.id_pedido, c.nombre, p.fecha_pedido, p.estado
ORDER BY p.fecha_pedido DESC;

-- Productos mas vendidos
SELECT pr.id_producto, pr.nombre, SUM(dp.cantidad) AS unidades_vendidas,
       SUM(dp.cantidad * dp.precio_unitario) AS valor_vendido
FROM detalle_pedido dp
JOIN productos pr ON pr.id_producto = dp.id_producto
JOIN pedidos pe ON pe.id_pedido = dp.id_pedido
WHERE pe.estado <> 'CANCELADO'
GROUP BY pr.id_producto, pr.nombre
ORDER BY unidades_vendidas DESC;

-- Ventas por proveedor
SELECT pv.nombre AS proveedor, SUM(dp.cantidad * dp.precio_unitario) AS ventas
FROM proveedores pv
JOIN productos pr ON pr.id_proveedor = pv.id_proveedor
JOIN detalle_pedido dp ON dp.id_producto = pr.id_producto
JOIN pedidos pe ON pe.id_pedido = dp.id_pedido
WHERE pe.estado <> 'CANCELADO'
GROUP BY pv.nombre
ORDER BY ventas DESC;

-- Pagos registrados y saldo pendiente por pedido
SELECT pe.id_pedido,
       NVL((SELECT SUM(dp.cantidad * dp.precio_unitario) FROM detalle_pedido dp WHERE dp.id_pedido = pe.id_pedido), 0) AS total_pedido,
       NVL((SELECT SUM(pa.monto) FROM pagos pa WHERE pa.id_pedido = pe.id_pedido AND pa.estado = 'REGISTRADO'), 0) AS total_pagado
FROM pedidos pe
ORDER BY pe.id_pedido;
