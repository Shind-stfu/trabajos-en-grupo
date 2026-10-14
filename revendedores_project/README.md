# Sistema de gestion para revendedores — Persona 1

Backend REST con **FastAPI + Python + Oracle Database (`oracledb`)** y scripts SQL para Oracle APEX/SQL Workshop. La interfaz web no se incluye porque corresponde al integrante de frontend.

## Contenido

- `database/01_tables.sql`: crea las ocho tablas, claves, restricciones e indices.
- `database/02_constraints.sql`: notas de reglas de negocio.
- `database/03_data.sql`: inserta roles y datos demo.
- `database/04_queries.sql`: consultas de reportes.
- `backend/`: API, autenticacion JWT, validaciones y conexion Oracle.
- `docs/MODELO_RELACIONAL.md`: relaciones y reglas del modelo.
- `docs/ENDPOINTS.md`: rutas principales.

## 1. Crear las tablas en Oracle APEX

1. Entra al workspace de Oracle APEX.
2. Abre **SQL Workshop → SQL Scripts**.
3. Carga y ejecuta `database/01_tables.sql`.
4. Ejecuta `database/03_data.sql` para insertar roles y datos de prueba.
5. Opcionalmente ejecuta las consultas de `database/04_queries.sql` una por una.

Ejecuta los scripts una sola vez en el esquema. Si ya existen las tablas, Oracle mostrara errores de objeto duplicado; no ejecutes el script de creacion repetidamente en una base con datos reales.

> Importante: APEX es una herramienta para administrar la base de datos, pero FastAPI se conecta a Oracle usando un usuario/servicio de base de datos. En Autonomous Database revisa la informacion de conexion y si tu instancia requiere wallet. No uses la URL de la aplicacion APEX como `ORACLE_DSN`.

## 2. Preparar Python en Visual Studio Code

Abre la carpeta raiz `revendedores_project` en VS Code. En una terminal, desde esa carpeta:

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edita `backend/.env` con los datos reales de Oracle y una clave JWT larga y aleatoria. No publiques el archivo `.env` ni el wallet en GitHub.

Ejemplo de variables:

```env
ORACLE_USER=MI_USUARIO
ORACLE_PASSWORD=MI_CLAVE
ORACLE_DSN=host:1521/servicio
TNS_ADMIN=
WALLET_PASSWORD=
JWT_SECRET=una_clave_aleatoria_larga_y_privada
```

Si usas Autonomous Database con wallet, sigue el formato de conexion indicado por Oracle para tu instancia. En esta plantilla `TNS_ADMIN` apunta a la carpeta local del wallet. Si el wallet necesita contraseña, configúrala mediante `WALLET_PASSWORD` en el archivo `.env`, nunca dentro del código.

La configuracion Thin de `python-oracledb` funciona en muchos entornos cloud sin instalar Oracle Client; la necesidad de wallet y los parametros dependen del tipo de base de datos y su configuracion de seguridad.

## 3. Crear el primer administrador

Primero verifica que `database/03_data.sql` se haya ejecutado. Desde la raiz del proyecto, con el entorno virtual activo:

```powershell
python -m backend.create_admin
```

Escribe nombre, correo y contraseña cuando el programa los solicite. La contraseña se almacena como hash, no en texto plano. El registro público `/api/auth/register` crea cuentas con rol **VENDEDOR**; solo el administrador puede consultar usuarios y desactivarlos.

## 4. Ejecutar la API

Desde la raiz del proyecto:

```powershell
uvicorn backend.main:app --reload
```

Abre:

- `http://127.0.0.1:8000/docs` — Swagger/OpenAPI.
- `http://127.0.0.1:8000/health` — comprobacion local.

`/health` solo confirma que la API responde; no verifica la conectividad con Oracle. La primera peticion a un endpoint que consulta datos probará la conexión real.

## 5. Autenticarse en Swagger

1. Ejecuta `POST /api/auth/login` con el correo y contraseña del administrador.
2. Copia `access_token` de la respuesta.
3. Pulsa **Authorize** y pega `Bearer <token>` si Swagger no agrega el prefijo automaticamente.
4. Prueba los endpoints protegidos.

## 6. Endpoints

Los CRUD principales están listados en `docs/ENDPOINTS.md`. Las rutas de creación/edición validan los datos con Pydantic. Los permisos se verifican en el backend, no solo en el frontend.

## 7. Conectar el frontend

El frontend debe llamar a rutas como `http://127.0.0.1:8000/api/proveedores` usando `fetch()`. Para rutas protegidas, envía `Authorization: Bearer <token>`. Configura `CORS_ORIGINS` en `.env` con el origen real desde el que se sirve el frontend. Nunca conectes el navegador directamente a Oracle.

## Alcance y decisiones

- Tablas: `roles`, `usuarios`, `proveedores`, `productos`, `clientes`, `pedidos`, `detalle_pedido`, `pagos`.
- El precio de venta se calcula en la API con `precio_compra * (1 + margen_porcentaje / 100)`.
- `detalle_pedido.precio_unitario` conserva el precio histórico aplicado al momento de la venta.
- Los pagos no pueden superar el total calculado del pedido en la validación de la API.
- La eliminación de pagos se implementa como anulación lógica para conservar trazabilidad.
- El proyecto es una base académica: antes de producción se deben agregar pruebas automatizadas completas, gestión de secretos, auditoría y controles transaccionales/concurrencia para pagos e inventario.
