from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator


class Lote(models.Model):
    """
    Entidad central del inventario físico. Cada ingreso de mercancía crea un lote.
    El stock se gestiona a nivel de lote, no de producto.
    Invariante: cantidad_disponible + cantidad_reservada <= cantidad_inicial
    """

    class Estado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        AGOTADO = 'AGOTADO', 'Agotado'
        VENCIDO = 'VENCIDO', 'Vencido'
        BAJA = 'BAJA', 'Dado de baja'

    producto = models.ForeignKey(
        'catalogo.Producto', on_delete=models.PROTECT, related_name='lotes'
    )
    orden_compra = models.CharField(max_length=100, help_text='Número de orden de compra')
    costo_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    cantidad_inicial = models.PositiveIntegerField()
    cantidad_disponible = models.PositiveIntegerField()
    cantidad_reservada = models.PositiveIntegerField(default=0)
    fecha_ingreso = models.DateField()
    fecha_caducidad = models.DateField(null=True, blank=True)
    archivo_adjunto = models.FileField(upload_to='lotes/', null=True, blank=True, help_text='Archivo adjunto (PDF/ZIP) del ingreso')
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lotes'
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = ['fecha_caducidad', 'fecha_ingreso']

    def __str__(self):
        return f'Lote #{self.pk} - {self.producto.nombre} (OC: {self.orden_compra})'

    @property
    def costo_total(self):
        return self.costo_unitario * self.cantidad_inicial

    def actualizar_estado(self):
        """Recalcula el estado basado en cantidades."""
        if self.cantidad_disponible == 0 and self.cantidad_reservada == 0:
            self.estado = self.Estado.AGOTADO


class Movimiento(models.Model):
    """
    Tabla transaccional INMUTABLE (append-only). Cada cambio en el inventario
    se registra como un movimiento. NO se permiten UPDATE ni DELETE.
    """

    class Tipo(models.TextChoices):
        INGRESO = 'INGRESO', 'Ingreso'
        DESPACHO = 'DESPACHO', 'Despacho'
        BAJA = 'BAJA', 'Baja'
        RESERVA = 'RESERVA', 'Reserva'
        LIBERACION = 'LIBERACION', 'Liberación'

    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name='movimientos')
    solicitud = models.ForeignKey(
        'solicitudes.Solicitud', on_delete=models.PROTECT,
        related_name='movimientos', null=True, blank=True
    )
    ejecutado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='movimientos_ejecutados'
    )
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    stock_anterior = models.PositiveIntegerField(help_text='Stock disponible antes del movimiento')
    stock_posterior = models.PositiveIntegerField(help_text='Stock disponible después del movimiento')
    motivo = models.TextField(blank=True, help_text='Obligatorio para bajas')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movimientos'
        verbose_name = 'Movimiento'
        verbose_name_plural = 'Movimientos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.cantidad} uds - Lote #{self.lote_id}'

    def save(self, *args, **kwargs):
        """Bloquea updates en registros existentes para inmutabilidad."""
        if self.pk:
            raise ValueError('Los movimientos son inmutables. No se permiten actualizaciones.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Bloquea eliminaciones para inmutabilidad."""
        raise ValueError('Los movimientos son inmutables. No se permiten eliminaciones.')
