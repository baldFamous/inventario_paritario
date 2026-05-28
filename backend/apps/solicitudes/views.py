from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from core.permissions import IsGestor, IsSolicitante
from .models import Solicitud
from .serializers import (
    SolicitudSerializer, CrearSolicitudSerializer,
    AprobarSolicitudSerializer, RechazarSolicitudSerializer,
)
from .services import SolicitudService


class SolicitudViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Solicitudes: Solicitante ve las suyas, Gestor ve todas.
    Acciones custom para crear, aprobar, rechazar, cancelar y despachar.
    """
    serializer_class = SolicitudSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Solicitud.objects.select_related('solicitante', 'gestor').prefetch_related(
            'detalles__producto', 'detalles__lote'
        )
        if user.es_gestor:
            return qs
        return qs.filter(solicitante=user)

    def get_permissions(self):
        if self.action == 'crear':
            return [IsSolicitante()]
        if self.action in ('aprobar', 'rechazar', 'despachar'):
            return [IsGestor()]
        if self.action == 'cancelar':
            return [IsSolicitante()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='crear')
    def crear(self, request):
        serializer = CrearSolicitudSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            solicitud = SolicitudService.crear_solicitud(
                solicitante=request.user,
                observaciones=serializer.validated_data.get('observaciones', ''),
                items=serializer.validated_data['items'],
            )
            return Response(
                SolicitudSerializer(solicitud).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        serializer = AprobarSolicitudSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            solicitud = SolicitudService.aprobar_solicitud(
                solicitud_id=pk,
                gestor=request.user,
                asignaciones=serializer.validated_data['asignaciones'],
            )
            return Response(SolicitudSerializer(solicitud).data)
        except ValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        serializer = RechazarSolicitudSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            solicitud = SolicitudService.rechazar_solicitud(
                solicitud_id=pk,
                gestor=request.user,
                motivo_rechazo=serializer.validated_data['motivo_rechazo'],
            )
            return Response(SolicitudSerializer(solicitud).data)
        except ValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        try:
            solicitud = SolicitudService.cancelar_solicitud(
                solicitud_id=pk,
                solicitante=request.user,
            )
            return Response(SolicitudSerializer(solicitud).data)
        except ValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def despachar(self, request, pk=None):
        try:
            solicitud = SolicitudService.despachar_solicitud(
                solicitud_id=pk,
                gestor=request.user,
            )
            return Response(SolicitudSerializer(solicitud).data)
        except ValidationError as e:
            return Response({'error': str(e.message)}, status=status.HTTP_400_BAD_REQUEST)
