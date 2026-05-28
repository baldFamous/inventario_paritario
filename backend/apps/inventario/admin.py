from django.contrib import admin
from .models import Lote, Movimiento


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'producto', 'orden_compra', 'cantidad_inicial',
                    'cantidad_disponible', 'cantidad_reservada', 'estado',
                    'fecha_ingreso', 'fecha_caducidad']
    list_filter = ['estado', 'producto__categoria']
    search_fields = ['orden_compra', 'producto__nombre']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando un lote existente
            return ['cantidad_inicial', 'producto', 'created_at', 'updated_at']
        return ['created_at', 'updated_at']  # Creando nuevo


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ['id', 'tipo', 'lote', 'cantidad', 'stock_anterior',
                    'stock_posterior', 'ejecutado_por', 'created_at']
    list_filter = ['tipo', 'created_at']
    search_fields = ['lote__orden_compra', 'motivo']
    readonly_fields = ['lote', 'solicitud', 'ejecutado_por', 'tipo', 'cantidad',
                       'stock_anterior', 'stock_posterior', 'motivo', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
