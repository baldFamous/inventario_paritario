from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.usuarios.urls')),
    path('api/v1/', include('apps.catalogo.urls')),
    path('api/v1/', include('apps.inventario.urls')),
    path('api/v1/', include('apps.solicitudes.urls')),
]
