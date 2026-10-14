# Endpoints principales

Todas las rutas se documentan automáticamente en `/docs`. Salvo `/`, `/health`, `/api/auth/register` y `/api/auth/login`, requieren un token JWT Bearer.

| Método | Ruta | Función / acceso |
|---|---|---|
| POST | `/api/auth/register` | Registrar vendedor |
| POST | `/api/auth/login` | Iniciar sesión y obtener token |
| GET | `/api/auth/me` | Usuario autenticado |
| GET | `/api/auth/usuarios` | Listar usuarios (administrador) |
| POST | `/api/auth/admin/usuarios` | Crear vendedor (administrador) |
| PUT | `/api/auth/usuarios/{user_id}/estado?activo=0/1` | Activar/desactivar usuario (administrador) |
| GET | `/api/auth/roles` | Listar roles (administrador) |
| GET/POST | `/api/proveedores` | Listar / crear proveedor |
| GET/PUT/DELETE | `/api/proveedores/{item_id}` | Consultar / editar / eliminar proveedor; eliminación admin |
| GET/POST | `/api/productos` | Listar / crear producto |
| GET/PUT/DELETE | `/api/productos/{item_id}` | Consultar / editar / eliminar producto; eliminación admin |
| GET/POST | `/api/clientes` | Listar / crear cliente |
| GET/PUT/DELETE | `/api/clientes/{item_id}` | Consultar / editar / eliminar cliente; eliminación admin |
| GET/POST | `/api/pedidos` | Listar / crear pedido |
| GET/PUT/DELETE | `/api/pedidos/{item_id}` | Consultar / editar / eliminar pedido con control de propietario |
| GET/POST | `/api/detalle-pedidos` | Listar / agregar detalle de pedido |
| PUT/DELETE | `/api/detalle-pedidos/{item_id}` | Editar / eliminar detalle |
| GET/POST | `/api/pagos` | Listar / registrar pago |
| PUT/DELETE | `/api/pagos/{item_id}` | Editar / anular pago (administrador) |
| GET | `/api/dashboard` | Indicadores del mes, pendientes y top productos |
| GET | `/api/reportes/ventas-cliente` | Ventas agrupadas por cliente |
| GET | `/api/reportes/ventas-proveedor` | Ventas agrupadas por proveedor |
| GET | `/api/reportes/ventas-periodo?desde=YYYY-MM-DD&hasta=YYYY-MM-DD` | Ventas por mes en el intervalo |

## Códigos HTTP esperados

- `200`: consulta o actualización exitosa.
- `201`: registro creado.
- `400`: datos o regla de negocio inválidos.
- `401`: token o credenciales inválidos.
- `403`: el usuario no tiene permisos.
- `404`: registro no encontrado.
- `409`: conflicto de integridad (por ejemplo, eliminar un proveedor usado por productos).
- `422`: validación automática de entrada de FastAPI/Pydantic.
- `500`: error interno sin exponer detalles técnicos al usuario.

## Ejemplo de creación de producto

```json
{
  "id_proveedor": 1,
  "nombre": "Camiseta deportiva",
  "descripcion": "Talla M",
  "precio_compra": 40000,
  "margen_porcentaje": 25,
  "existencia": 10,
  "activo": 1
}
```

El backend calcula `precio_venta` como `50000.00`; no es necesario enviarlo desde el frontend.
