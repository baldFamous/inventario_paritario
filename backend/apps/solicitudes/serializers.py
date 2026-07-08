from rest_framework import serializers
from .models import Solicitud, DetalleSolicitud
from apps.usuarios.serializers import UsuarioSerializer


class DetalleSolicitudSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    lote_orden_compra = serializers.CharField(source='lote.orden_compra', read_only=True, default=None)

    class Meta:
        model = DetalleSolicitud
        fields = ['id', 'producto', 'producto_nombre', 'producto_codigo',
                  'lote', 'lote_orden_compra', 'cantidad_solicitada', 'cantidad_aprobada']
        read_only_fields = ['id', 'lote', 'cantidad_aprobada']


class SolicitudSerializer(serializers.ModelSerializer):
    detalles = DetalleSolicitudSerializer(many=True, read_only=True)
    solicitante_nombre = serializers.SerializerMethodField()
    gestor_nombre = serializers.CharField(source='gestor.get_full_name', read_only=True, default=None)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Solicitud
        fields = ['id', 'solicitante', 'solicitante_nombre', 'correo_respaldo', 'gestor', 'gestor_nombre',
                  'estado', 'estado_display', 'motivo_rechazo', 'observaciones',
                  'detalles', 'created_at', 'updated_at']
        read_only_fields = ['id', 'solicitante', 'gestor', 'estado', 'created_at', 'updated_at']

    def get_solicitante_nombre(self, obj):
        if obj.solicitante_nombre:
            return obj.solicitante_nombre
        if obj.solicitante:
            return obj.solicitante.get_full_name() or obj.solicitante.username
        return ''


# --- Serializers de entrada para acciones ---

class ItemSolicitudInput(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad_solicitada = serializers.IntegerField(min_value=1)


class CrearSolicitudSerializer(serializers.Serializer):
    solicitante_nombre = serializers.CharField(required=False, default='', allow_blank=True)
    correo_respaldo = serializers.EmailField(required=False, default='', allow_blank=True)
    observaciones = serializers.CharField(required=False, default='', allow_blank=True)
    items = ItemSolicitudInput(many=True, min_length=1)


class AsignacionLoteInput(serializers.Serializer):
    detalle_id = serializers.IntegerField()
    lote_id = serializers.IntegerField()
    cantidad_aprobada = serializers.IntegerField(min_value=1)


class AprobarSolicitudSerializer(serializers.Serializer):
    asignaciones = AsignacionLoteInput(many=True, min_length=1)


class RechazarSolicitudSerializer(serializers.Serializer):
    motivo_rechazo = serializers.CharField(min_length=10)
