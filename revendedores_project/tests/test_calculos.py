from decimal import Decimal


def calcular_precio_venta(precio_compra: float, margen_porcentaje: float) -> float:
    return round(precio_compra * (1 + margen_porcentaje / 100), 2)


def test_margen_25_por_ciento():
    assert calcular_precio_venta(40000, 25) == 50000


def test_margen_cero():
    assert calcular_precio_venta(12500, 0) == 12500
