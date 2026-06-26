from rest_framework import viewsets
from django.db.models import Sum, Q, Count
from core.permissions import IsGestorOrReadOnly
from .models import Categoria, Producto, AsignacionProducto
from .serializers import CategoriaSerializer, ProductoSerializer, ProductoCreateSerializer, AsignacionProductoSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsGestorOrReadOnly]
    serializer_class = CategoriaSerializer
    search_fields = ['nombre']

    def get_queryset(self):
        return Categoria.objects.annotate(
            productos_count=Count('productos')
        )


class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsGestorOrReadOnly]
    filterset_fields = ['categoria', 'is_active']
    search_fields = ['codigo', 'nombre']
    ordering_fields = ['nombre', 'codigo']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProductoCreateSerializer
        return ProductoSerializer

    def get_queryset(self):
        lotes_activos = Q(lotes__estado='ACTIVO')
        return Producto.objects.select_related('categoria').prefetch_related('asignaciones_individuales').annotate(
            stock_disponible=Sum('lotes__cantidad_disponible', filter=lotes_activos, default=0),
            stock_reservado=Sum('lotes__cantidad_reservada', filter=lotes_activos, default=0),
        )

class AsignacionProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsGestorOrReadOnly]
    serializer_class = AsignacionProductoSerializer
    queryset = AsignacionProducto.objects.all()
    filterset_fields = ['producto']
