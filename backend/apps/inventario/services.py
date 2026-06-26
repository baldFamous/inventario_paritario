from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Lote, Movimiento


class InventarioService:
    """
    Service layer para operaciones transaccionales de inventario.
    Toda lógica de negocio que modifica stock pasa por aquí.
    """

    @staticmethod
    @transaction.atomic
    def registrar_lote(producto, orden_compra, costo_unitario, cantidad,
                       fecha_ingreso, fecha_caducidad, ejecutado_por, archivo_adjunto=None):
        """
        Crea un nuevo lote y registra el movimiento de INGRESO.
        Returns: (Lote, Movimiento)
        """
        lote = Lote.objects.create(
            producto=producto,
            orden_compra=orden_compra,
            costo_unitario=costo_unitario,
            cantidad_inicial=cantidad,
            cantidad_disponible=cantidad,
            cantidad_reservada=0,
            fecha_ingreso=fecha_ingreso,
            fecha_caducidad=fecha_caducidad,
            archivo_adjunto=archivo_adjunto,
            estado=Lote.Estado.ACTIVO,
        )

        movimiento = Movimiento.objects.create(
            lote=lote,
            ejecutado_por=ejecutado_por,
            tipo=Movimiento.Tipo.INGRESO,
            cantidad=cantidad,
            stock_anterior=0,
            stock_posterior=cantidad,
            motivo=f'Ingreso inicial - OC: {orden_compra}',
        )

        return lote, movimiento

    @staticmethod
    @transaction.atomic
    def dar_baja(lote_id, cantidad, motivo, ejecutado_por):
        """
        Da de baja parcial o total un lote. Exige motivo y responsable.
        Usa select_for_update para prevenir race conditions.
        Returns: (Lote, Movimiento)
        """
        if not motivo or not motivo.strip():
            raise ValidationError('El motivo es obligatorio para dar de baja.')

        lote = Lote.objects.select_for_update().get(pk=lote_id)

        if lote.estado == Lote.Estado.BAJA:
            raise ValidationError('Este lote ya fue dado de baja completamente.')

        if cantidad > lote.cantidad_disponible:
            raise ValidationError(
                f'Cantidad a dar de baja ({cantidad}) excede el stock disponible ({lote.cantidad_disponible}).'
            )

        stock_anterior = lote.cantidad_disponible
        lote.cantidad_disponible -= cantidad
        if lote.cantidad_disponible == 0 and lote.cantidad_reservada == 0:
            lote.estado = Lote.Estado.BAJA
        lote.save()

        movimiento = Movimiento.objects.create(
            lote=lote,
            ejecutado_por=ejecutado_por,
            tipo=Movimiento.Tipo.BAJA,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_posterior=lote.cantidad_disponible,
            motivo=motivo,
        )

        return lote, movimiento

    @staticmethod
    @transaction.atomic
    def reservar_stock(lote_id, cantidad, solicitud, ejecutado_por):
        """
        Reserva stock de un lote para una solicitud aprobada.
        Returns: Movimiento
        """
        lote = Lote.objects.select_for_update().get(pk=lote_id)

        if cantidad > lote.cantidad_disponible:
            raise ValidationError(
                f'Stock insuficiente en lote #{lote_id}. '
                f'Disponible: {lote.cantidad_disponible}, solicitado: {cantidad}.'
            )

        stock_anterior = lote.cantidad_disponible
        lote.cantidad_disponible -= cantidad
        lote.cantidad_reservada += cantidad
        lote.save()

        return Movimiento.objects.create(
            lote=lote,
            solicitud=solicitud,
            ejecutado_por=ejecutado_por,
            tipo=Movimiento.Tipo.RESERVA,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_posterior=lote.cantidad_disponible,
        )

    @staticmethod
    @transaction.atomic
    def liberar_stock(lote_id, cantidad, solicitud, ejecutado_por):
        """
        Libera stock reservado (rechazo/cancelación de solicitud).
        Returns: Movimiento
        """
        lote = Lote.objects.select_for_update().get(pk=lote_id)

        stock_anterior = lote.cantidad_disponible
        lote.cantidad_disponible += cantidad
        lote.cantidad_reservada -= cantidad
        lote.save()

        return Movimiento.objects.create(
            lote=lote,
            solicitud=solicitud,
            ejecutado_por=ejecutado_por,
            tipo=Movimiento.Tipo.LIBERACION,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_posterior=lote.cantidad_disponible,
        )

    @staticmethod
    @transaction.atomic
    def despachar_stock(lote_id, cantidad, solicitud, ejecutado_por):
        """
        Confirma despacho físico (stock reservado sale del inventario).
        Returns: Movimiento
        """
        lote = Lote.objects.select_for_update().get(pk=lote_id)

        if cantidad > lote.cantidad_reservada:
            raise ValidationError(
                f'Cantidad a despachar ({cantidad}) excede lo reservado ({lote.cantidad_reservada}).'
            )

        lote.cantidad_reservada -= cantidad
        lote.actualizar_estado()
        lote.save()

        return Movimiento.objects.create(
            lote=lote,
            solicitud=solicitud,
            ejecutado_por=ejecutado_por,
            tipo=Movimiento.Tipo.DESPACHO,
            cantidad=cantidad,
            stock_anterior=lote.cantidad_disponible,
            stock_posterior=lote.cantidad_disponible,
        )
