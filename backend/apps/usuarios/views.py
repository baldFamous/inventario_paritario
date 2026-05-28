from rest_framework import generics, permissions
from .models import Usuario
from .serializers import UsuarioSerializer


class MeView(generics.RetrieveAPIView):
    """Retorna el perfil del usuario autenticado."""
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
