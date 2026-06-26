from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, ProductoViewSet, AsignacionProductoViewSet

router = DefaultRouter()
router.register('categorias', CategoriaViewSet, basename='categoria')
router.register('productos', ProductoViewSet, basename='producto')
router.register('asignaciones-producto', AsignacionProductoViewSet, basename='asignacion-producto')

urlpatterns = [
    path('', include(router.urls)),
]
