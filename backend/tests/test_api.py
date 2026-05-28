import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework.test import APIClient
from rest_framework import status


@pytest.fixture
def gestor_client(gestor):
    client = APIClient()
    client.force_authenticate(user=gestor)
    return client


@pytest.fixture
def solicitante_client(solicitante):
    client = APIClient()
    client.force_authenticate(user=solicitante)
    return client


@pytest.fixture
def anon_client():
    return APIClient()


# ==================== AUTH ====================

class TestAuthEndpoints:
    def test_login_exitoso(self, db, gestor):
        client = APIClient()
        resp = client.post('/api/v1/auth/login/', {
            'username': 'gestor1', 'password': 'Test1234!'
        })
        assert resp.status_code == status.HTTP_200_OK
        assert 'access' in resp.data
        assert 'refresh' in resp.data

    def test_login_fallido(self, db):
        client = APIClient()
        resp = client.post('/api/v1/auth/login/', {
            'username': 'noexiste', 'password': 'wrong'
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_autenticado(self, gestor_client, gestor):
        resp = gestor_client.get('/api/v1/auth/me/')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['rut'] == gestor.rut

    def test_me_no_autenticado(self, anon_client):
        resp = anon_client.get('/api/v1/auth/me/')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ==================== CATEGORÍAS ====================

class TestCategoriaAPI:
    def test_crear_categoria_gestor(self, gestor_client):
        resp = gestor_client.post('/api/v1/categorias/', {'nombre': 'EPP'})
        assert resp.status_code == status.HTTP_201_CREATED

    def test_crear_categoria_solicitante_denegado(self, solicitante_client):
        resp = solicitante_client.post('/api/v1/categorias/', {'nombre': 'EPP'})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_listar_categorias_solicitante(self, solicitante_client, categoria):
        resp = solicitante_client.get('/api/v1/categorias/')
        assert resp.status_code == status.HTTP_200_OK


# ==================== PRODUCTOS ====================

class TestProductoAPI:
    def test_crear_producto_gestor(self, gestor_client, categoria):
        resp = gestor_client.post('/api/v1/productos/', {
            'categoria': categoria.pk, 'codigo': 'HIG-002',
            'nombre': 'Jabón Líquido', 'unidad_medida': 'litro',
        })
        assert resp.status_code == status.HTTP_201_CREATED

    def test_listar_productos_con_stock(self, solicitante_client, lote):
        resp = solicitante_client.get('/api/v1/productos/')
        assert resp.status_code == status.HTTP_200_OK
        producto_data = resp.data['results'][0]
        assert producto_data['stock_disponible'] == 100

    def test_crear_producto_solicitante_denegado(self, solicitante_client, categoria):
        resp = solicitante_client.post('/api/v1/productos/', {
            'categoria': categoria.pk, 'codigo': 'X',
            'nombre': 'X', 'unidad_medida': 'x',
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ==================== LOTES ====================

class TestLoteAPI:
    def test_crear_lote(self, gestor_client, producto):
        resp = gestor_client.post('/api/v1/lotes/', {
            'producto': producto.pk, 'orden_compra': 'OC-API-001',
            'costo_unitario': '2500.00', 'cantidad': 30,
            'fecha_ingreso': str(date.today()),
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['cantidad_disponible'] == 30

    def test_dar_baja_lote(self, gestor_client, lote):
        resp = gestor_client.post(f'/api/v1/lotes/{lote.pk}/baja/', {
            'cantidad': 10, 'motivo': 'Productos dañados durante almacenamiento',
        })
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['cantidad_disponible'] == 90

    def test_dar_baja_sin_motivo_falla(self, gestor_client, lote):
        resp = gestor_client.post(f'/api/v1/lotes/{lote.pk}/baja/', {
            'cantidad': 10, 'motivo': 'corto',
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_solicitante_no_accede_lotes(self, solicitante_client):
        resp = solicitante_client.get('/api/v1/lotes/')
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ==================== MOVIMIENTOS ====================

class TestMovimientoAPI:
    def test_listar_movimientos_gestor(self, gestor_client, lote, gestor):
        from apps.inventario.services import InventarioService
        InventarioService.dar_baja(
            lote_id=lote.pk, cantidad=5,
            motivo='Test de listado de movimientos',
            ejecutado_por=gestor,
        )
        resp = gestor_client.get('/api/v1/movimientos/')
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data['results']) >= 1

    def test_movimientos_solo_lectura(self, gestor_client):
        resp = gestor_client.post('/api/v1/movimientos/', {})
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_solicitante_no_accede_movimientos(self, solicitante_client):
        resp = solicitante_client.get('/api/v1/movimientos/')
        assert resp.status_code == status.HTTP_403_FORBIDDEN
