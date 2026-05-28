import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status as http_status
from apps.solicitudes.models import Solicitud, DetalleSolicitud
from apps.solicitudes.services import SolicitudService
from apps.inventario.models import Lote, Movimiento


# ==================== SERVICE LAYER ====================

class TestCrearSolicitud:
    def test_crear_solicitud_con_items(self, db, solicitante, producto):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='Urgente',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 10}],
        )
        assert solicitud.estado == Solicitud.Estado.PENDIENTE
        assert solicitud.detalles.count() == 1
        assert solicitud.detalles.first().cantidad_solicitada == 10

    def test_crear_sin_items_falla(self, db, solicitante):
        with pytest.raises(ValidationError, match='al menos un producto'):
            SolicitudService.crear_solicitud(
                solicitante=solicitante, observaciones='', items=[],
            )

    def test_crear_multiples_items(self, db, solicitante, producto, categoria):
        from apps.catalogo.models import Producto
        p2 = Producto.objects.create(
            categoria=categoria, codigo='HIG-099',
            nombre='Jabón', unidad_medida='unidad',
        )
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[
                {'producto_id': producto.pk, 'cantidad_solicitada': 5},
                {'producto_id': p2.pk, 'cantidad_solicitada': 3},
            ],
        )
        assert solicitud.detalles.count() == 2


class TestAprobarSolicitud:
    def test_aprobar_reserva_stock(self, db, solicitante, gestor, producto, lote):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 20}],
        )
        detalle = solicitud.detalles.first()

        solicitud = SolicitudService.aprobar_solicitud(
            solicitud_id=solicitud.pk, gestor=gestor,
            asignaciones=[{
                'detalle_id': detalle.pk,
                'lote_id': lote.pk,
                'cantidad_aprobada': 15,
            }],
        )

        assert solicitud.estado == Solicitud.Estado.APROBADA
        assert solicitud.gestor == gestor
        lote.refresh_from_db()
        assert lote.cantidad_disponible == 85
        assert lote.cantidad_reservada == 15

    def test_aprobar_cantidad_mayor_a_solicitada_falla(self, db, solicitante, gestor, producto, lote):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        )
        detalle = solicitud.detalles.first()

        with pytest.raises(ValidationError, match='exceder'):
            SolicitudService.aprobar_solicitud(
                solicitud_id=solicitud.pk, gestor=gestor,
                asignaciones=[{
                    'detalle_id': detalle.pk,
                    'lote_id': lote.pk,
                    'cantidad_aprobada': 50,
                }],
            )

    def test_aprobar_sin_asignaciones_falla(self, db, solicitante, gestor, producto):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        )
        with pytest.raises(ValidationError, match='asignar'):
            SolicitudService.aprobar_solicitud(
                solicitud_id=solicitud.pk, gestor=gestor, asignaciones=[],
            )

    def test_aprobar_solicitud_no_pendiente_falla(self, db, solicitante, gestor, producto, lote):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        )
        SolicitudService.rechazar_solicitud(
            solicitud_id=solicitud.pk, gestor=gestor,
            motivo_rechazo='Sin stock suficiente para cubrir',
        )
        with pytest.raises(ValidationError, match='No se puede aprobar'):
            SolicitudService.aprobar_solicitud(
                solicitud_id=solicitud.pk, gestor=gestor,
                asignaciones=[{
                    'detalle_id': solicitud.detalles.first().pk,
                    'lote_id': lote.pk, 'cantidad_aprobada': 5,
                }],
            )


class TestRechazarSolicitud:
    def test_rechazar_con_motivo(self, db, solicitante, gestor, producto):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        )
        solicitud = SolicitudService.rechazar_solicitud(
            solicitud_id=solicitud.pk, gestor=gestor,
            motivo_rechazo='No hay stock disponible actualmente',
        )
        assert solicitud.estado == Solicitud.Estado.RECHAZADA
        assert solicitud.motivo_rechazo == 'No hay stock disponible actualmente'

    def test_rechazar_sin_motivo_falla(self, db, solicitante, gestor, producto):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        )
        with pytest.raises(ValidationError, match='motivo'):
            SolicitudService.rechazar_solicitud(
                solicitud_id=solicitud.pk, gestor=gestor, motivo_rechazo='',
            )


class TestCancelarSolicitud:
    def test_cancelar_propia(self, db, solicitante, producto):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        )
        solicitud = SolicitudService.cancelar_solicitud(
            solicitud_id=solicitud.pk, solicitante=solicitante,
        )
        assert solicitud.estado == Solicitud.Estado.CANCELADA

    def test_cancelar_ajena_falla(self, db, solicitante, gestor, producto):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        )
        with pytest.raises(ValidationError, match='propias'):
            SolicitudService.cancelar_solicitud(
                solicitud_id=solicitud.pk, solicitante=gestor,
            )


class TestDespacharSolicitud:
    def test_despachar_libera_reserva(self, db, solicitante, gestor, producto, lote):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 10}],
        )
        detalle = solicitud.detalles.first()
        SolicitudService.aprobar_solicitud(
            solicitud_id=solicitud.pk, gestor=gestor,
            asignaciones=[{
                'detalle_id': detalle.pk,
                'lote_id': lote.pk, 'cantidad_aprobada': 10,
            }],
        )

        lote.refresh_from_db()
        assert lote.cantidad_reservada == 10

        solicitud = SolicitudService.despachar_solicitud(
            solicitud_id=solicitud.pk, gestor=gestor,
        )
        assert solicitud.estado == Solicitud.Estado.DESPACHADA
        lote.refresh_from_db()
        assert lote.cantidad_reservada == 0
        assert lote.cantidad_disponible == 90

    def test_despachar_pendiente_falla(self, db, solicitante, gestor, producto):
        solicitud = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        )
        with pytest.raises(ValidationError, match='No se puede despachar'):
            SolicitudService.despachar_solicitud(
                solicitud_id=solicitud.pk, gestor=gestor,
            )


class TestFlujoCompletoTrazabilidad:
    def test_flujo_pendiente_aprobada_despachada(self, db, solicitante, gestor, producto, lote):
        """Test del ciclo de vida completo con verificación de movimientos."""
        sol = SolicitudService.crear_solicitud(
            solicitante=solicitante, observaciones='Necesito para oficina',
            items=[{'producto_id': producto.pk, 'cantidad_solicitada': 25}],
        )
        assert sol.estado == Solicitud.Estado.PENDIENTE

        det = sol.detalles.first()
        sol = SolicitudService.aprobar_solicitud(
            solicitud_id=sol.pk, gestor=gestor,
            asignaciones=[{
                'detalle_id': det.pk,
                'lote_id': lote.pk, 'cantidad_aprobada': 25,
            }],
        )
        assert sol.estado == Solicitud.Estado.APROBADA

        sol = SolicitudService.despachar_solicitud(solicitud_id=sol.pk, gestor=gestor)
        assert sol.estado == Solicitud.Estado.DESPACHADA

        lote.refresh_from_db()
        assert lote.cantidad_disponible == 75
        assert lote.cantidad_reservada == 0

        movs = Movimiento.objects.filter(solicitud=sol).order_by('created_at')
        assert movs.count() == 2
        assert movs[0].tipo == Movimiento.Tipo.RESERVA
        assert movs[1].tipo == Movimiento.Tipo.DESPACHO


# ==================== API ENDPOINTS ====================

@pytest.fixture
def gestor_api(gestor):
    c = APIClient()
    c.force_authenticate(user=gestor)
    return c

@pytest.fixture
def solicitante_api(solicitante):
    c = APIClient()
    c.force_authenticate(user=solicitante)
    return c


class TestSolicitudAPICrear:
    def test_solicitante_crea_solicitud(self, solicitante_api, producto):
        resp = solicitante_api.post('/api/v1/solicitudes/crear/', {
            'items': [{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        }, format='json')
        assert resp.status_code == http_status.HTTP_201_CREATED
        assert resp.data['estado'] == 'PENDIENTE'

    def test_gestor_no_puede_crear(self, gestor_api, producto):
        resp = gestor_api.post('/api/v1/solicitudes/crear/', {
            'items': [{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        }, format='json')
        assert resp.status_code == http_status.HTTP_403_FORBIDDEN


class TestSolicitudAPIAprobar:
    def test_gestor_aprueba(self, solicitante_api, gestor_api, producto, lote, solicitante):
        # Crear como solicitante
        resp = solicitante_api.post('/api/v1/solicitudes/crear/', {
            'items': [{'producto_id': producto.pk, 'cantidad_solicitada': 10}],
        }, format='json')
        sol_id = resp.data['id']
        det_id = resp.data['detalles'][0]['id']

        # Aprobar como gestor
        resp = gestor_api.post(f'/api/v1/solicitudes/{sol_id}/aprobar/', {
            'asignaciones': [{
                'detalle_id': det_id, 'lote_id': lote.pk, 'cantidad_aprobada': 10,
            }],
        }, format='json')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['estado'] == 'APROBADA'


class TestSolicitudAPIRechazar:
    def test_gestor_rechaza(self, solicitante_api, gestor_api, producto, solicitante):
        resp = solicitante_api.post('/api/v1/solicitudes/crear/', {
            'items': [{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        }, format='json')
        sol_id = resp.data['id']

        resp = gestor_api.post(f'/api/v1/solicitudes/{sol_id}/rechazar/', {
            'motivo_rechazo': 'No hay presupuesto asignado este mes',
        }, format='json')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['estado'] == 'RECHAZADA'


class TestSolicitudAPICancelar:
    def test_solicitante_cancela_propia(self, solicitante_api, producto):
        resp = solicitante_api.post('/api/v1/solicitudes/crear/', {
            'items': [{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        }, format='json')
        sol_id = resp.data['id']

        resp = solicitante_api.post(f'/api/v1/solicitudes/{sol_id}/cancelar/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert resp.data['estado'] == 'CANCELADA'


class TestSolicitudAPIListado:
    def test_solicitante_ve_solo_las_suyas(self, solicitante_api, gestor_api, producto, solicitante):
        solicitante_api.post('/api/v1/solicitudes/crear/', {
            'items': [{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        }, format='json')

        resp = solicitante_api.get('/api/v1/solicitudes/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert len(resp.data['results']) == 1

    def test_gestor_ve_todas(self, solicitante_api, gestor_api, producto, solicitante):
        solicitante_api.post('/api/v1/solicitudes/crear/', {
            'items': [{'producto_id': producto.pk, 'cantidad_solicitada': 5}],
        }, format='json')

        resp = gestor_api.get('/api/v1/solicitudes/')
        assert resp.status_code == http_status.HTTP_200_OK
        assert len(resp.data['results']) >= 1
