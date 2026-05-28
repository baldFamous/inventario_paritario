from rest_framework.permissions import BasePermission


class IsGestor(BasePermission):
    """Permite acceso solo a usuarios con rol GESTOR."""
    message = 'Solo los gestores paritarios pueden realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == 'GESTOR'
        )


class IsSolicitante(BasePermission):
    """Permite acceso solo a usuarios con rol SOLICITANTE."""
    message = 'Solo los solicitantes pueden realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == 'SOLICITANTE'
        )


class IsGestorOrReadOnly(BasePermission):
    """Lectura para todos los autenticados, escritura solo gestores."""

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user and request.user.is_authenticated
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == 'GESTOR'
        )
