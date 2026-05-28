import pytest
from datetime import date, timedelta
from decimal import Decimal
from apps.usuarios.models import Usuario
from apps.catalogo.models import Categoria, Producto
from apps.inventario.models import Lote


@pytest.fixture
def gestor(db):
    return Usuario.objects.create_user(
        username='gestor1', password='Test1234!',
        rut='11.111.111-1', first_name='María', last_name='González',
        rol=Usuario.Rol.GESTOR, unidad='Comité Paritario',
    )


@pytest.fixture
def solicitante(db):
    return Usuario.objects.create_user(
        username='solicitante1', password='Test1234!',
        rut='22.222.222-2', first_name='Juan', last_name='Pérez',
        rol=Usuario.Rol.SOLICITANTE, unidad='Recursos Humanos',
    )


@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nombre='Higiene', descripcion='Productos de higiene')


@pytest.fixture
def producto(db, categoria):
    return Producto.objects.create(
        categoria=categoria, codigo='HIG-001', nombre='Alcohol Gel',
        unidad_medida='litro', stock_minimo=5,
    )


@pytest.fixture
def lote(db, producto):
    return Lote.objects.create(
        producto=producto, orden_compra='OC-2026-001',
        costo_unitario=Decimal('3500.00'), cantidad_inicial=100,
        cantidad_disponible=100, cantidad_reservada=0,
        fecha_ingreso=date.today(),
        fecha_caducidad=date.today() + timedelta(days=365),
        estado=Lote.Estado.ACTIVO,
    )
