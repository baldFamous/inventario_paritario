from django.contrib import admin
from .models import Categoria, Producto, AsignacionProducto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


class AsignacionProductoInline(admin.TabularInline):
    model = AsignacionProducto
    extra = 0
    readonly_fields = ['fecha']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'unidad_medida', 'stock_minimo', 'asignado_a', 'is_active']
    list_filter = ['categoria', 'is_active']
    search_fields = ['codigo', 'nombre', 'asignado_a']
    inlines = [AsignacionProductoInline]


@admin.register(AsignacionProducto)
class AsignacionProductoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'asignado_a', 'cantidad', 'fecha']
    list_filter = ['fecha', 'producto__categoria']
    search_fields = ['asignado_a', 'producto__nombre']
