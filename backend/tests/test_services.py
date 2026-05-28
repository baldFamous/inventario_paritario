import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from apps.inventario.models import Lote, Movimiento
from apps.inventario.services import InventarioService


class TestRegistrarLote:
    def test_crea_lote_y_movimiento(self, db, producto, gestor):
        lote, mov = InventarioService.registrar_lote(
            producto=producto, orden_compra='OC-TEST-001',
            costo_unitario=Decimal('1500.00'), cantidad=50,
            fecha_ingreso=date.today(), fecha_caducidad=None,
            ejecutado_por=gestor,
        )
        assert lote.cantidad_disponible == 50
        assert lote.cantidad_inicial == 50
        assert lote.estado == Lote.Estado.ACTIVO
        assert mov.tipo == Movimiento.Tipo.INGRESO
        assert mov.stock_anterior == 0
        assert mov.stock_posterior == 50

    def test_sin_fecha_caducidad(self, db, producto, gestor):
        lote, _ = InventarioService.registrar_lote(
            producto=producto, orden_compra='OC-TEST-002',
            costo_unitario=Decimal('1000'), cantidad=10,
            fecha_ingreso=date.today(), fecha_caducidad=None,
            ejecutado_por=gestor,
        )
        assert lote.fecha_caducidad is None


class TestDarBaja:
    def test_baja_parcial(self, db, lote, gestor):
        lote_actualizado, mov = InventarioService.dar_baja(
            lote_id=lote.pk, cantidad=30,
            motivo='Productos dañados por humedad',
            ejecutado_por=gestor,
        )
        assert lote_actualizado.cantidad_disponible == 70
        assert mov.tipo == Movimiento.Tipo.BAJA
        assert mov.stock_anterior == 100
        assert mov.stock_posterior == 70

    def test_baja_total(self, db, lote, gestor):
        lote_actualizado, _ = InventarioService.dar_baja(
            lote_id=lote.pk, cantidad=100,
            motivo='Lote vencido completo - retiro de bodega',
            ejecutado_por=gestor,
        )
        assert lote_actualizado.cantidad_disponible == 0
        assert lote_actualizado.estado == Lote.Estado.BAJA

    def test_baja_sin_motivo_falla(self, db, lote, gestor):
        with pytest.raises(ValidationError, match='motivo'):
            InventarioService.dar_baja(
                lote_id=lote.pk, cantidad=10, motivo='',
                ejecutado_por=gestor,
            )

    def test_baja_excede_stock_falla(self, db, lote, gestor):
        with pytest.raises(ValidationError, match='excede'):
            InventarioService.dar_baja(
                lote_id=lote.pk, cantidad=999,
                motivo='Intento de baja excesiva',
                ejecutado_por=gestor,
            )

    def test_baja_lote_ya_dado_de_baja_falla(self, db, lote, gestor):
        InventarioService.dar_baja(
            lote_id=lote.pk, cantidad=100,
            motivo='Baja total del lote',
            ejecutado_por=gestor,
        )
        with pytest.raises(ValidationError, match='ya fue dado de baja'):
            InventarioService.dar_baja(
                lote_id=lote.pk, cantidad=1,
                motivo='Segundo intento', ejecutado_por=gestor,
            )


class TestReservarStock:
    def test_reserva_exitosa(self, db, lote, gestor):
        mov = InventarioService.reservar_stock(
            lote_id=lote.pk, cantidad=20,
            solicitud=None, ejecutado_por=gestor,
        )
        lote.refresh_from_db()
        assert lote.cantidad_disponible == 80
        assert lote.cantidad_reservada == 20
        assert mov.tipo == Movimiento.Tipo.RESERVA

    def test_reserva_insuficiente_falla(self, db, lote, gestor):
        with pytest.raises(ValidationError, match='insuficiente'):
            InventarioService.reservar_stock(
                lote_id=lote.pk, cantidad=999,
                solicitud=None, ejecutado_por=gestor,
            )


class TestLiberarStock:
    def test_liberacion_exitosa(self, db, lote, gestor):
        InventarioService.reservar_stock(
            lote_id=lote.pk, cantidad=30,
            solicitud=None, ejecutado_por=gestor,
        )
        mov = InventarioService.liberar_stock(
            lote_id=lote.pk, cantidad=30,
            solicitud=None, ejecutado_por=gestor,
        )
        lote.refresh_from_db()
        assert lote.cantidad_disponible == 100
        assert lote.cantidad_reservada == 0
        assert mov.tipo == Movimiento.Tipo.LIBERACION


class TestDespacharStock:
    def test_despacho_exitoso(self, db, lote, gestor):
        InventarioService.reservar_stock(
            lote_id=lote.pk, cantidad=25,
            solicitud=None, ejecutado_por=gestor,
        )
        mov = InventarioService.despachar_stock(
            lote_id=lote.pk, cantidad=25,
            solicitud=None, ejecutado_por=gestor,
        )
        lote.refresh_from_db()
        assert lote.cantidad_reservada == 0
        assert lote.cantidad_disponible == 75
        assert mov.tipo == Movimiento.Tipo.DESPACHO

    def test_despacho_excede_reserva_falla(self, db, lote, gestor):
        InventarioService.reservar_stock(
            lote_id=lote.pk, cantidad=10,
            solicitud=None, ejecutado_por=gestor,
        )
        with pytest.raises(ValidationError, match='excede'):
            InventarioService.despachar_stock(
                lote_id=lote.pk, cantidad=50,
                solicitud=None, ejecutado_por=gestor,
            )


class TestTrazabilidadCompleta:
    def test_flujo_ingreso_reserva_despacho(self, db, producto, gestor):
        """Verifica el flujo completo y la trazabilidad en movimientos."""
        lote, m1 = InventarioService.registrar_lote(
            producto=producto, orden_compra='OC-FLUJO-001',
            costo_unitario=Decimal('2000'), cantidad=50,
            fecha_ingreso=date.today(), fecha_caducidad=None,
            ejecutado_por=gestor,
        )
        m2 = InventarioService.reservar_stock(
            lote_id=lote.pk, cantidad=20,
            solicitud=None, ejecutado_por=gestor,
        )
        m3 = InventarioService.despachar_stock(
            lote_id=lote.pk, cantidad=20,
            solicitud=None, ejecutado_por=gestor,
        )

        lote.refresh_from_db()
        assert lote.cantidad_disponible == 30
        assert lote.cantidad_reservada == 0

        movimientos = list(Movimiento.objects.filter(lote=lote).order_by('created_at'))
        assert len(movimientos) == 3
        assert movimientos[0].tipo == Movimiento.Tipo.INGRESO
        assert movimientos[1].tipo == Movimiento.Tipo.RESERVA
        assert movimientos[2].tipo == Movimiento.Tipo.DESPACHO
