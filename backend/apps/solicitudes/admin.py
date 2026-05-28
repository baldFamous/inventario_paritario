from django.contrib import admin
from .models import Solicitud, DetalleSolicitud


class DetalleSolicitudInline(admin.TabularInline):
    model = DetalleSolicitud
    extra = 0
    readonly_fields = ['producto', 'cantidad_solicitada', 'lote', 'cantidad_aprobada']


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['id', 'solicitante', 'estado', 'gestor', 'created_at']
    list_filter = ['estado', 'created_at']
    search_fields = ['solicitante__first_name', 'solicitante__last_name', 'solicitante__rut']
    readonly_fields = ['solicitante', 'created_at', 'updated_at']
    inlines = [DetalleSolicitudInline]
