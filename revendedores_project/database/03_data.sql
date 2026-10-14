-- Datos iniciales de catalogos. Ejecutar despues de 01_tables.sql.
INSERT INTO roles (nombre, descripcion) VALUES ('ADMINISTRADOR', 'Gestion total del sistema');
INSERT INTO roles (nombre, descripcion) VALUES ('VENDEDOR', 'Gestion de clientes, productos y pedidos autorizados');

INSERT INTO proveedores (nombre, contacto, telefono, correo, direccion) VALUES
('Proveedor Demo', 'Contacto Comercial', '3000000000', 'proveedor@example.com', 'Cali, Colombia');
INSERT INTO clientes (nombre, telefono, correo, direccion) VALUES
('Cliente Demo', '3100000000', 'cliente@example.com', 'Cali, Colombia');

-- Crear un usuario real con la API /api/auth/register. No insertar contrasenas en texto plano.
COMMIT;
