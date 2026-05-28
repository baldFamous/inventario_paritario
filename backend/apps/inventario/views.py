from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from apps.catalogo.models import Producto
from core.permissions import IsGestor
from .models import Lote, Movimiento
from .serializers import LoteSerializer, LoteCreateSerializer, BajaSerializer, MovimientoSerializer
from .services import InventarioService


class LoteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsGestor]
    filterset_fields = ['producto', 'estado']
    search_fields = ['orden_compra', 'producto__nombre']
    ordering_fields = ['fecha_ingreso', 'fecha_caducidad', 'cantidad_disponible']

    def get_serializer_class(self):
        if self.action == 'create':
            return LoteCreateSerializer
        if self.action == 'baja':
            return BajaSerializer
        return LoteSerializer

    def get_queryset(self):
        return Lote.objects.select_related('producto')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        producto = Producto.objects.get(pk=data['producto'])
        lote, movimiento = InventarioService.registrar_lote(
            producto=producto,
            orden_compra=data['orden_compra'],
            costo_unitario=data['costo_unitario'],
            cantidad=data['cantidad'],
            fecha_ingreso=data['fecha_ingreso'],
            fecha_caducidad=data.get('fecha_caducidad'),
            ejecutado_por=request.user,
        )
        return Response(LoteSerializer(lote).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='baja')
    def baja(self, request, pk=None):
        serializer = BajaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lote, movimiento = InventarioService.dar_baja(
            lote_id=pk,
            cantidad=serializer.validated_data['cantidad'],
            motivo=serializer.validated_data['motivo'],
            ejecutado_por=request.user,
        )
        return Response(LoteSerializer(lote).data)


class MovimientoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """Solo lectura. Los movimientos se crean a través del service layer."""
    permission_classes = [IsGestor]
    serializer_class = MovimientoSerializer
    filterset_fields = ['tipo', 'lote', 'ejecutado_por']
    ordering_fields = ['created_at']

    def get_queryset(self):
        return Movimiento.objects.select_related('lote', 'ejecutado_por', 'lote__producto')
