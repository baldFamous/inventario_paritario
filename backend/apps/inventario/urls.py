from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoteViewSet, MovimientoViewSet

router = DefaultRouter()
router.register('lotes', LoteViewSet, basename='lote')
router.register('movimientos', MovimientoViewSet, basename='movimiento')

urlpatterns = [
    path('', include(router.urls)),
]
