from django.contrib import admin
from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'unidad_medida', 'stock_minimo', 'is_active']
    list_filter = ['categoria', 'is_active']
    search_fields = ['codigo', 'nombre']
