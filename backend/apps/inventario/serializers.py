from rest_framework import serializers
from .models import Lote, Movimiento


class LoteSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    costo_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Lote
        fields = ['id', 'producto', 'producto_nombre', 'producto_codigo',
                  'orden_compra', 'costo_unitario', 'costo_total',
                  'cantidad_inicial', 'cantidad_disponible', 'cantidad_reservada',
                  'fecha_ingreso', 'fecha_caducidad', 'estado', 'created_at']
        read_only_fields = ['id', 'cantidad_disponible', 'cantidad_reservada',
                            'estado', 'created_at']


class LoteCreateSerializer(serializers.Serializer):
    producto = serializers.IntegerField()
    orden_compra = serializers.CharField(max_length=100)
    costo_unitario = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    cantidad = serializers.IntegerField(min_value=1)
    fecha_ingreso = serializers.DateField()
    fecha_caducidad = serializers.DateField(required=False, allow_null=True)


class BajaSerializer(serializers.Serializer):
    cantidad = serializers.IntegerField(min_value=1)
    motivo = serializers.CharField(min_length=10)


class MovimientoSerializer(serializers.ModelSerializer):
    ejecutado_por_nombre = serializers.CharField(
        source='ejecutado_por.get_full_name', read_only=True
    )
    lote_info = serializers.CharField(source='lote.__str__', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Movimiento
        fields = ['id', 'lote', 'lote_info', 'solicitud', 'ejecutado_por',
                  'ejecutado_por_nombre', 'tipo', 'tipo_display', 'cantidad',
                  'stock_anterior', 'stock_posterior', 'motivo', 'created_at']
