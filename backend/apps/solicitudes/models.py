from django.conf import settings
from django.db import models


class Solicitud(models.Model):
    """
    Encabezado de solicitud de insumos. Implementa máquina de estados:
    PENDIENTE -> APROBADA -> DESPACHADA
    PENDIENTE -> RECHAZADA
    PENDIENTE -> CANCELADA
    """

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        APROBADA = 'APROBADA', 'Aprobada'
        DESPACHADA = 'DESPACHADA', 'Despachada'
        RECHAZADA = 'RECHAZADA', 'Rechazada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='solicitudes_creadas', null=True, blank=True,
    )
    solicitante_nombre = models.CharField(
        max_length=200, blank=True, 
        help_text='Nombre del solicitante cuando no tiene usuario en el sistema'
    )
    correo_respaldo = models.EmailField(
        blank=True,
        help_text='Correo electrónico para notificaciones (si no tiene usuario en el sistema)'
    )
    gestor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='solicitudes_gestionadas', null=True, blank=True,
    )
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
    motivo_rechazo = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Transiciones válidas de estado
    TRANSICIONES_VALIDAS = {
        Estado.PENDIENTE: [Estado.APROBADA, Estado.RECHAZADA, Estado.CANCELADA],
        Estado.APROBADA: [Estado.DESPACHADA],
    }

    class Meta:
        db_table = 'solicitudes'
        verbose_name = 'Solicitud'
        verbose_name_plural = 'Solicitudes'
        ordering = ['-created_at']

    def __str__(self):
        return f'Solicitud #{self.pk} - {self.estado}'

    def puede_transitar_a(self, nuevo_estado):
        """Verifica si la transición de estado es válida."""
        permitidos = self.TRANSICIONES_VALIDAS.get(self.estado, [])
        return nuevo_estado in permitidos


class DetalleSolicitud(models.Model):
    """
    Línea de detalle de una solicitud. Al crear solo tiene producto + cantidad_solicitada.
    Al aprobar, el gestor asigna lote + cantidad_aprobada.
    """
    solicitud = models.ForeignKey(
        Solicitud, on_delete=models.CASCADE, related_name='detalles'
    )
    producto = models.ForeignKey(
        'catalogo.Producto', on_delete=models.PROTECT, related_name='detalle_solicitudes'
    )
    lote = models.ForeignKey(
        'inventario.Lote', on_delete=models.PROTECT,
        related_name='detalle_solicitudes', null=True, blank=True,
        help_text='Asignado por el gestor al aprobar',
    )
    cantidad_solicitada = models.PositiveIntegerField()
    cantidad_aprobada = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'detalle_solicitudes'
        verbose_name = 'Detalle de Solicitud'
        verbose_name_plural = 'Detalles de Solicitud'

    def __str__(self):
        return f'{self.producto.nombre} x{self.cantidad_solicitada}'
