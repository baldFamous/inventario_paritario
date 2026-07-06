from django.db import models


class Categoria(models.Model):
    """Agrupación lógica de productos (Higiene, EPP, Oficina, etc.)."""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Catálogo maestro de productos. NO almacena stock.
    El stock se calcula sumando cantidad_disponible de los lotes activos.
    """
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='productos'
    )
    codigo = models.CharField(max_length=50, unique=True, help_text='Código interno del producto')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    unidad_medida = models.CharField(max_length=30, help_text='Ej: unidad, caja, litro, par')
    stock_minimo = models.PositiveIntegerField(
        default=0, help_text='Umbral para alerta de stock crítico'
    )
    is_active = models.BooleanField(default=True)
    asignado_a = models.CharField(
        max_length=200, blank=True, null=True,
        help_text='Área o persona a la que está asignado este producto. Si está asignado, no se muestra en nueva solicitud.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class AsignacionProducto(models.Model):
    """
    Registro individual de asignación de un producto del catálogo a una persona.
    """
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='asignaciones_individuales')
    asignado_a = models.CharField(max_length=200, help_text='Nombre de la persona o área a la que se le asigna el producto')
    cantidad = models.PositiveIntegerField(default=1)
    fecha = models.DateField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = 'asignaciones_producto'
        verbose_name = 'Asignación de Producto'
        verbose_name_plural = 'Asignaciones de Producto'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre} asignado a {self.asignado_a}'
