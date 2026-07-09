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
    def crear_solicitud(observaciones, items, solicitante=None, solicitante_nombre='', correo_respaldo=''):
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
            solicitante_nombre=solicitante_nombre,
            correo_respaldo=correo_respaldo,
            observaciones=observaciones,
            estado=Solicitud.Estado.PENDIENTE,
        )

        detalles_creados = []
        for item in items:
            detalle = DetalleSolicitud.objects.create(
                solicitud=solicitud,
                producto_id=item['producto_id'],
                cantidad_solicitada=item['cantidad_solicitada'],
            )
            detalles_creados.append(detalle)

        # Enviar correo de notificación
        try:
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            subject = f"Nueva Solicitud de Insumos / Equipos #{solicitud.id}"
            message = f"Se ha registrado una nueva solicitud en el sistema.\n\n"
            message += f"Solicitante: {solicitante_nombre}\n"
            if observaciones:
                message += f"Observaciones: {observaciones}\n"
            message += "\nDetalle de los insumos solicitados:\n"
            
            for detalle in detalles_creados:
                # detalle.producto es la instancia gracias a la ForeignKey
                message += f"- {detalle.producto.nombre}: {detalle.cantidad_solicitada} unidades\n"
            
            message += "\nPor favor ingrese al sistema para revisar y gestionar esta solicitud."

            # TODO (PRODUCCION): Usar recipient_list real. Ej: ['francisco.valenzuela@mineduc.cl'] o un grupo.
            recipient_list = ['bastian.rodriguez@mineduc.cl']
            
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
            )
            
            # TODO (PRODUCCION): Enviar copia de respaldo al usuario.
            # cc_list = []
            # if correo_respaldo:
            #     cc_list.append(correo_respaldo)
            # elif solicitante and solicitante.email:
            #     cc_list.append(solicitante.email)
            # if cc_list:
            #     email.cc = cc_list
            
            # Por ahora, solo mandamos copia de respaldo a bastian para pruebas
            email.cc = ['bastian.rodriguez@mineduc.cl']
                
            email.send(fail_silently=True)
        except Exception as e:
            # Si el envío de correo falla, no queremos revertir la creación de la solicitud
            pass

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

        # Enviar correo de notificación de aprobación
        try:
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            subject = f"Aprobación de Solicitud #{solicitud.id}"
            message = f"Su solicitud #{solicitud.id} ha sido APROBADA.\n\n"
            message += f"El insumo será despachado próximamente por la unidad de adquisiciones y/o informática.\n\n"
            message += "Detalles de la aprobación:\n"
            
            for asig in asignaciones:
                detalle = DetalleSolicitud.objects.select_related('producto').get(
                    pk=asig['detalle_id'], solicitud=solicitud
                )
                message += f"- {detalle.producto.nombre}: {asig['cantidad_aprobada']} unidades asignadas\n"
            
            message += "\nSaludos cordiales."

            # TODO (PRODUCCION): El "to" debería ser el correo_respaldo del usuario o su email de cuenta
            # to_email = solicitud.correo_respaldo or (solicitud.solicitante.email if solicitud.solicitante else None)
            
            # TODO (PRODUCCION): El "cc" debería ser el email del gestor
            # cc_email = gestor.email

            # Por ahora forzamos todo a bastian.rodriguez@mineduc.cl para pruebas
            to_email = 'bastian.rodriguez@mineduc.cl'
            cc_email = 'bastian.rodriguez@mineduc.cl'
            
            if to_email:
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[to_email],
                    cc=[cc_email] if cc_email else []
                )
                email.send(fail_silently=True)
        except Exception as e:
            pass

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

        # Enviar correo de notificación de rechazo
        try:
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            subject = f"Rechazo de Solicitud #{solicitud.id}"
            message = f"Su solicitud #{solicitud.id} ha sido RECHAZADA.\n\n"
            message += f"Motivo del rechazo: {motivo_rechazo}\n\n"
            message += "Saludos cordiales."

            # TODO (PRODUCCION): El "to" debería ser el correo_respaldo del usuario o su email de cuenta
            # to_email = solicitud.correo_respaldo or (solicitud.solicitante.email if solicitud.solicitante else None)
            
            # TODO (PRODUCCION): El "cc" debería ser el email del gestor
            # cc_email = gestor.email

            # Por ahora forzamos todo a bastian.rodriguez@mineduc.cl para pruebas
            to_email = 'bastian.rodriguez@mineduc.cl'
            cc_email = 'bastian.rodriguez@mineduc.cl'
            
            if to_email:
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[to_email],
                    cc=[cc_email] if cc_email else []
                )
                email.send(fail_silently=True)
        except Exception as e:
            pass

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
        Crea registro en AsignacionProducto para tener historial múltiple.
        Returns: Solicitud
        """
        solicitud = Solicitud.objects.select_for_update().get(pk=solicitud_id)

        if not solicitud.puede_transitar_a(Solicitud.Estado.DESPACHADA):
            raise ValidationError(
                f'No se puede despachar una solicitud en estado {solicitud.estado}.'
            )

        detalles = solicitud.detalles.select_related('lote', 'producto').filter(
            lote__isnull=False, cantidad_aprobada__isnull=False
        )

        if not detalles.exists():
            raise ValidationError('No hay detalles con lotes asignados para despachar.')

        from apps.catalogo.models import AsignacionProducto
        
        # Determinar nombre del solicitante
        nombre_solicitante = solicitud.solicitante_nombre
        if not nombre_solicitante and solicitud.solicitante:
            nombre_solicitante = solicitud.solicitante.get_full_name() or solicitud.solicitante.username
        if not nombre_solicitante:
            nombre_solicitante = "Desconocido"

        for detalle in detalles:
            InventarioService.despachar_stock(
                lote_id=detalle.lote_id,
                cantidad=detalle.cantidad_aprobada,
                solicitud=solicitud,
                ejecutado_por=gestor,
            )
            
            # Crear historial de asignación individual
            AsignacionProducto.objects.create(
                producto=detalle.producto,
                asignado_a=nombre_solicitante,
                cantidad=detalle.cantidad_aprobada,
                observaciones=f"Despacho automático - Solicitud #{solicitud.id}"
            )

        solicitud.estado = Solicitud.Estado.DESPACHADA
        solicitud.gestor = gestor
        solicitud.save()
        return solicitud
