# Modelo relacional

## Entidades y relaciones

- **roles (1) — (N) usuarios**: cada usuario tiene un rol; un rol puede asignarse a muchos usuarios.
- **proveedores (1) — (N) productos**: cada producto referencia al proveedor que lo suministra.
- **clientes (1) — (N) pedidos**: un cliente puede realizar varios pedidos.
- **usuarios (1) — (N) pedidos**: cada pedido queda asociado al vendedor que lo registró.
- **pedidos (1) — (N) detalle_pedido**: un pedido contiene una o varias líneas de producto.
- **productos (1) — (N) detalle_pedido**: un producto puede aparecer en muchas líneas de pedido.
- **pedidos (1) — (N) pagos**: un pedido puede pagarse mediante uno o varios pagos parciales.

## Diccionario resumido

| Tabla | Clave primaria | Claves foráneas | Propósito |
|---|---|---|---|
| roles | id_rol | — | Perfiles de acceso ADMINISTRADOR y VENDEDOR |
| usuarios | id_usuario | id_rol → roles | Usuarios y hash de contraseña |
| proveedores | id_proveedor | — | Catálogo de proveedores |
| productos | id_producto | id_proveedor → proveedores | Producto, costo, margen, precio y existencia |
| clientes | id_cliente | — | Clientes de los revendedores |
| pedidos | id_pedido | id_cliente → clientes; id_usuario → usuarios | Cabecera del pedido y estado |
| detalle_pedido | id_detalle | id_pedido → pedidos; id_producto → productos | Cantidad y precio unitario histórico |
| pagos | id_pago | id_pedido → pedidos | Pagos parciales y anulaciones |

## Reglas importantes

1. Los precios y montos se almacenan con precisión decimal `NUMBER(12,2)`.
2. Cantidades deben ser positivas y existencia no puede ser negativa.
3. `precio_venta` se calcula en el backend a partir del costo y el margen porcentual.
4. El precio guardado en el detalle no cambia cuando se modifica el precio actual del catálogo.
5. Un pedido tiene un único registro por producto en `detalle_pedido`; la restricción única evita duplicados. Si el usuario vuelve a agregar el mismo producto, debe actualizarse la cantidad del detalle existente.
6. Las restricciones de estado impiden valores distintos a los definidos en el SQL.
7. El hash de contraseña nunca debe ser la contraseña original.

## Modelo lógico (cardinalidades)

```text
ROLES 1 ───── N USUARIOS 1 ───── N PEDIDOS N ───── 1 CLIENTES
PROVEEDORES 1 ───── N PRODUCTOS 1 ───── N DETALLE_PEDIDO N ───── 1 PEDIDOS
PEDIDOS 1 ───── N PAGOS
```

El modelo físico implementa estas relaciones mediante las claves primarias, foráneas, restricciones `CHECK`, restricciones `UNIQUE` e índices del archivo `database/01_tables.sql`.
