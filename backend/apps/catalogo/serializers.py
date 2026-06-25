from rest_framework import serializers
from django.db.models import Sum, Q
from .models import Categoria, Producto, AsignacionProducto


class CategoriaSerializer(serializers.ModelSerializer):
    productos_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'productos_count']


class AsignacionProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionProducto
        fields = ['id', 'producto', 'asignado_a', 'cantidad', 'fecha', 'observaciones']
        read_only_fields = ['fecha']


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    stock_disponible = serializers.IntegerField(read_only=True, default=0)
    stock_reservado = serializers.IntegerField(read_only=True, default=0)
    asignaciones_individuales = AsignacionProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'categoria', 'categoria_nombre', 'codigo', 'nombre',
                  'descripcion', 'unidad_medida', 'stock_minimo', 'is_active',
                  'stock_disponible', 'stock_reservado', 'asignado_a', 'asignaciones_individuales']


class ProductoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['categoria', 'codigo', 'nombre', 'descripcion',
                  'unidad_medida', 'stock_minimo', 'asignado_a']
