from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Solicitud, DetalleSolicitud
from apps.inventario.services import InventarioService
from apps.inventario.models import Lote


class SolicitudService:
    """
    Service layer para el flujo de solicitudes.
    Gestiona transiciones de estado y operaciones de stock asociadas.
    """

    @staticmethod
    @transaction.atomic
    def crear_solicitud(solicitante, observaciones, items):
        """
        Crea una solicitud en estado PENDIENTE con sus líneas de detalle.
        items: lista de dicts con {producto_id, cantidad_solicitada}
        No reserva stock — solo valida que exista stock informativo.
        Returns: Solicitud
        """
        if not items:
            raise ValidationError('La solicitud debe tener al menos un producto.')

        solicitud = Solicitud.objects.create(
            solicitante=solicitante,
            observaciones=observaciones,
            estado=Solicitud.Estado.PENDIENTE,
        )

        for item in items:
            DetalleSolicitud.objects.create(
                solicitud=solicitud,
                producto_id=item['producto_id'],
                cantidad_solicitada=item['cantidad_solicitada'],
            )

        return solicitud

    @staticmethod
    @transaction.atomic
    def aprobar_solicitud(solicitud_id, gestor, asignaciones):
        """
        Aprueba una solicitud y reserva stock de los lotes asignados.
        asignaciones: lista de dicts con {detalle_id, lote_id, cantidad_aprobada}
        Returns: Solicitud
        """
        solicitud = Solicitud.objects.select_for_update().get(pk=solicitud_id)

        if not solicitud.puede_transitar_a(Solicitud.Estado.APROBADA):
            raise ValidationError(
                f'No se puede aprobar una solicitud en estado {solicitud.estado}.'
            )

        if not asignaciones:
            raise ValidationError('Debe asignar al menos un lote para aprobar.')

        for asig in asignaciones:
            detalle = DetalleSolicitud.objects.get(
                pk=asig['detalle_id'], solicitud=solicitud
            )

            if asig['cantidad_aprobada'] > detalle.cantidad_solicitada:
                raise ValidationError(
                    f'Cantidad aprobada ({asig["cantidad_aprobada"]}) no puede '
                    f'exceder la solicitada ({detalle.cantidad_solicitada}).'
                )

            # Asignar lote y cantidad al detalle
            detalle.lote_id = asig['lote_id']
            detalle.cantidad_aprobada = asig['cantidad_aprobada']
            detalle.save()

            # Reservar stock en el lote
            InventarioService.reservar_stock(
                lote_id=asig['lote_id'],
                cantidad=asig['cantidad_aprobada'],
                solicitud=solicitud,
                ejecutado_por=gestor,
            )

        solicitud.estado = Solicitud.Estado.APROBADA
        solicitud.gestor = gestor
        solicitud.save()
        return solicitud

    @staticmethod
    @transaction.atomic
    def rechazar_solicitud(solicitud_id, gestor, motivo_rechazo):
        """
        Rechaza una solicitud. No modifica stock (no se había reservado nada).
        Returns: Solicitud
        """
        solicitud = Solicitud.objects.select_for_update().get(pk=solicitud_id)

        if not solicitud.puede_transitar_a(Solicitud.Estado.RECHAZADA):
            raise ValidationError(
                f'No se puede rechazar una solicitud en estado {solicitud.estado}.'
            )

        if not motivo_rechazo or not motivo_rechazo.strip():
            raise ValidationError('El motivo de rechazo es obligatorio.')

        solicitud.estado = Solicitud.Estado.RECHAZADA
        solicitud.gestor = gestor
        solicitud.motivo_rechazo = motivo_rechazo
        solicitud.save()
        return solicitud

    @staticmethod
    @transaction.atomic
    def cancelar_solicitud(solicitud_id, solicitante):
        """
        Cancela una solicitud propia en estado PENDIENTE.
        No modifica stock (no se había reservado nada).
        Returns: Solicitud
        """
        solicitud = Solicitud.objects.select_for_update().get(pk=solicitud_id)

        if solicitud.solicitante_id != solicitante.pk:
            raise ValidationError('Solo puedes cancelar tus propias solicitudes.')

        if not solicitud.puede_transitar_a(Solicitud.Estado.CANCELADA):
            raise ValidationError(
                f'No se puede cancelar una solicitud en estado {solicitud.estado}.'
            )

        solicitud.estado = Solicitud.Estado.CANCELADA
        solicitud.save()
        return solicitud

    @staticmethod
    @transaction.atomic
    def despachar_solicitud(solicitud_id, gestor):
        """
        Confirma despacho físico. Convierte stock reservado en despachado.
        Returns: Solicitud
        """
        solicitud = Solicitud.objects.select_for_update().get(pk=solicitud_id)

        if not solicitud.puede_transitar_a(Solicitud.Estado.DESPACHADA):
            raise ValidationError(
                f'No se puede despachar una solicitud en estado {solicitud.estado}.'
            )

        detalles = solicitud.detalles.select_related('lote').filter(
            lote__isnull=False, cantidad_aprobada__isnull=False
        )

        if not detalles.exists():
            raise ValidationError('No hay detalles con lotes asignados para despachar.')

        for detalle in detalles:
            InventarioService.despachar_stock(
                lote_id=detalle.lote_id,
                cantidad=detalle.cantidad_aprobada,
                solicitud=solicitud,
                ejecutado_por=gestor,
            )

        solicitud.estado = Solicitud.Estado.DESPACHADA
        solicitud.gestor = gestor
        solicitud.save()
        return solicitud
