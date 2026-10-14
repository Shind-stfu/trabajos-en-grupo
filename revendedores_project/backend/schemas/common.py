from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from typing import Optional, Literal

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

class LoginIn(BaseModel):
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=128)

class RegisterIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=128)

class ProveedorIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    contacto: Optional[str] = Field(default=None, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=30)
    correo: Optional[EmailStr] = None
    direccion: Optional[str] = Field(default=None, max_length=250)
    activo: int = Field(default=1, ge=0, le=1)

class ProductoIn(BaseModel):
    id_proveedor: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    precio_compra: float = Field(ge=0, le=9999999999.99)
    margen_porcentaje: float = Field(default=0, ge=0, le=100000)
    existencia: int = Field(default=0, ge=0)
    activo: int = Field(default=1, ge=0, le=1)

class ClienteIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    telefono: Optional[str] = Field(default=None, max_length=30)
    correo: Optional[EmailStr] = None
    direccion: Optional[str] = Field(default=None, max_length=250)

class PedidoIn(BaseModel):
    id_cliente: int = Field(gt=0)
    estado: Literal['PENDIENTE','CONFIRMADO','ENVIADO','ENTREGADO','CANCELADO'] = 'PENDIENTE'
    observaciones: Optional[str] = Field(default=None, max_length=500)

class DetallePedidoIn(BaseModel):
    id_pedido: int = Field(gt=0)
    id_producto: int = Field(gt=0)
    cantidad: int = Field(gt=0)
    precio_unitario: Optional[float] = Field(default=None, ge=0)

class PagoIn(BaseModel):
    id_pedido: int = Field(gt=0)
    monto: float = Field(gt=0, le=9999999999.99)
    metodo: Literal['EFECTIVO','TRANSFERENCIA','TARJETA','OTRO']
    referencia: Optional[str] = Field(default=None, max_length=100)
    estado: Literal['REGISTRADO','ANULADO'] = 'REGISTRADO'
